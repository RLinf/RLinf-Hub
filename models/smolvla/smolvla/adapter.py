# Copyright 2026 The RLinf Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import torch
from omegaconf import DictConfig
from rlinf.models.embodiment.base_policy import BasePolicy, ForwardType
from torch import nn


def _to_chw_float(images: torch.Tensor) -> torch.Tensor:
    """Convert batched HWC or CHW images to FP32 CHW, scaling integers to [0, 1]."""
    if images.ndim != 4:
        raise ValueError(
            f"Expected a batched 4D image tensor, got {tuple(images.shape)}"
        )
    if images.shape[1] == 3:
        chw = images
    elif images.shape[-1] == 3:
        chw = images.permute(0, 3, 1, 2)
    else:
        raise ValueError(
            f"Expected an image channel dimension of 3, got {tuple(images.shape)}"
        )
    if torch.is_floating_point(chw):
        return chw.to(dtype=torch.float32).contiguous()
    return chw.to(dtype=torch.float32).div(255.0).contiguous()


class SmolVLAForRLActionPrediction(nn.Module, BasePolicy):
    """Inference-only RLinf wrapper around the upstream LeRobot SmolVLA policy."""

    def __init__(self, cfg: DictConfig, torch_dtype: torch.dtype | None = None) -> None:
        super().__init__()
        import draccus
        from huggingface_hub import hf_hub_download
        from lerobot.policies.factory import make_pre_post_processors
        from lerobot.policies.smolvla.configuration_smolvla import SmolVLAConfig
        from lerobot.policies.smolvla.modeling_smolvla import (
            SmolVLAPolicy as LeRobotSmolVLAPolicy,
        )
        from lerobot.processor.batch_processor import AddBatchDimensionProcessorStep

        self.cfg = cfg
        model_path = Path(cfg.model_path)
        if model_path.is_dir():
            local_config = model_path / "config.json"
            if not local_config.is_file():
                raise FileNotFoundError(
                    f"Local checkpoint directory {model_path} does not contain "
                    "config.json"
                )
            config_path = str(local_config)
        else:
            config_path = hf_hub_download(
                repo_id=cfg.model_path,
                filename="config.json",
                revision=cfg.model_revision,
            )
        with open(config_path, encoding="utf-8") as handle:
            config_data = json.load(handle)
        # Newer checkpoints add a registry tag that LeRobot 0.4.4 rejects.
        config_data.pop("type", None)
        with TemporaryDirectory() as directory:
            sanitized_path = Path(directory) / "config.json"
            sanitized_path.write_text(json.dumps(config_data), encoding="utf-8")
            with draccus.config_type("json"):
                model_config = draccus.parse(
                    SmolVLAConfig, str(sanitized_path), args=[]
                )
        model_config.device = "cpu"
        model_config.dtype = torch.float32
        model_config.load_vlm_weights = False
        model_config.compile_model = False
        model_config.rtc_config = None

        self.policy = LeRobotSmolVLAPolicy.from_pretrained(
            cfg.model_path,
            config=model_config,
            revision=cfg.model_revision,
            strict=True,
        )
        self.policy.to(dtype=torch.float32)
        self.policy.eval()
        self.compute_dtype = torch_dtype or torch.float32

        state_shape = model_config.input_features[cfg.state_key].shape
        action_shape = model_config.output_features["action"].shape
        if int(action_shape[0]) != int(cfg.action_dim):
            raise ValueError(
                f"Configured action_dim={cfg.action_dim}, but the checkpoint expects "
                f"{action_shape[0]}"
            )
        if int(model_config.chunk_size) != int(cfg.num_action_chunks):
            raise ValueError(
                f"Configured num_action_chunks={cfg.num_action_chunks}, but the "
                f"checkpoint expects {model_config.chunk_size}"
            )
        self.state_dim = int(state_shape[0])

        self.image_keys = {
            str(source): [str(target)]
            if isinstance(target, str)
            else [str(item) for item in target]
            for source, target in cfg.image_keys.items()
        }
        expected_image_keys = {
            key
            for key in model_config.input_features
            if key.startswith("observation.images.")
        }
        configured_image_keys = {
            target for targets in self.image_keys.values() for target in targets
        }
        if configured_image_keys != expected_image_keys:
            raise ValueError(
                "Configured image keys do not match the checkpoint: "
                f"expected {sorted(expected_image_keys)}, got "
                f"{sorted(configured_image_keys)}"
            )

        dataset_stats = self._load_dataset_stats(model_config)
        self.preprocessor, self.postprocessor = make_pre_post_processors(
            model_config,
            pretrained_path=None,
            dataset_stats=dataset_stats,
        )
        # RLinf already supplies a batch; LeRobot's default step would add another.
        self.preprocessor.steps = [
            step
            for step in self.preprocessor.steps
            if not isinstance(step, AddBatchDimensionProcessorStep)
        ]

    def _load_dataset_stats(self, model_config: Any) -> dict[str, Any]:
        """Load current feature-keyed stats or use unit stats for a shape-only smoke."""
        if self.cfg.stats_path is not None:
            with open(self.cfg.stats_path, encoding="utf-8") as handle:
                stats = json.load(handle)
        else:
            stats = {}
            for key, feature in (
                (self.cfg.state_key, model_config.input_features[self.cfg.state_key]),
                ("action", model_config.output_features["action"]),
            ):
                dim = int(feature.shape[0])
                stats[key] = {"mean": [0.0] * dim, "std": [1.0] * dim}

        for key, feature in (
            (self.cfg.state_key, model_config.input_features[self.cfg.state_key]),
            ("action", model_config.output_features["action"]),
        ):
            if key not in stats:
                raise ValueError(
                    f"Normalization stats are missing required key {key!r}"
                )
            dim = int(feature.shape[0])
            for name in ("mean", "std"):
                if name not in stats[key]:
                    raise ValueError(
                        f"Normalization stats are missing required key {key!r}.{name}"
                    )
                values = stats[key][name]
                if len(values) != dim:
                    raise ValueError(
                        f"Normalization stats {key!r}.{name} has length {len(values)}; "
                        f"expected {dim}"
                    )
                stats[key][name] = torch.tensor(values, dtype=torch.float32)
        return stats

    def _prepare_observation(self, env_obs: dict[str, Any]) -> dict[str, Any]:
        """Map RLinf observations to the current LeRobot checkpoint feature keys."""
        states = env_obs["states"].to(dtype=torch.float32)
        if states.ndim != 2 or states.shape[1] != self.state_dim:
            raise ValueError(
                f"Expected states with shape [B, {self.state_dim}], got "
                f"{tuple(states.shape)}"
            )
        batch_size = states.shape[0]
        tasks = env_obs["task_descriptions"]
        if isinstance(tasks, str):
            tasks = [tasks] * batch_size
        if len(tasks) != batch_size:
            raise ValueError(
                f"Expected {batch_size} task descriptions, got {len(tasks)}"
            )

        batch: dict[str, Any] = {self.cfg.state_key: states, "task": tasks}
        for source, targets in self.image_keys.items():
            images = env_obs[source]
            if isinstance(images, (list, tuple)):
                views = list(images)
            elif images.ndim == 5:
                views = [images[:, index] for index in range(images.shape[1])]
            elif images.ndim == 4:
                views = [images]
            else:
                raise ValueError(
                    f"Expected {source!r} to be a 4D or 5D image tensor, got "
                    f"{tuple(images.shape)}"
                )
            if len(views) != len(targets):
                raise ValueError(
                    f"Observation {source!r} has {len(views)} views, but "
                    f"{len(targets)} checkpoint keys are configured"
                )
            for target, view in zip(targets, views, strict=True):
                if view.shape[0] != batch_size:
                    raise ValueError(
                        f"Observation {source!r} has batch {view.shape[0]}, but "
                        f"states has batch {batch_size}"
                    )
                batch[target] = _to_chw_float(view)
        return batch

    def _move_batch_to_policy(self, batch: dict[str, Any]) -> dict[str, Any]:
        """Move processed tensors to the policy device without casting integer IDs."""
        parameter = next(self.policy.parameters())
        moved = {}
        for key, value in batch.items():
            if isinstance(value, torch.Tensor):
                moved[key] = value.to(
                    device=parameter.device,
                    dtype=parameter.dtype
                    if torch.is_floating_point(value)
                    else value.dtype,
                )
            else:
                moved[key] = value
        return moved

    def forward(self, forward_type: ForwardType = ForwardType.DEFAULT, **kwargs):
        """Dispatch RLinf forward calls to the supported training branch."""
        if forward_type == ForwardType.DEFAULT:
            return self.default_forward(**kwargs)
        raise NotImplementedError(
            f"SmolVLA does not support RLinf forward type {forward_type!r}"
        )

    def default_forward(
        self,
        forward_inputs: dict[str, Any],
        compute_logprobs: bool = True,
        compute_entropy: bool = False,
        compute_values: bool = False,
        use_cache: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Reject training replay until a stochastic policy objective is defined."""
        raise NotImplementedError(
            "The SmolVLA Hub adapter currently supports deterministic evaluation "
            "only; PPO/GRPO replay and logprobs are not implemented"
        )

    @torch.no_grad()
    def predict_action_batch(
        self,
        env_obs: dict[str, Any],
        mode: str | None = None,
        calculate_logprobs: bool = False,
        calculate_values: bool = False,
        noise: torch.Tensor | None = None,
        **kwargs: Any,
    ) -> tuple[torch.Tensor, dict[str, Any]]:
        """Return a postprocessed action chunk as contiguous CPU FP32."""
        if calculate_logprobs or calculate_values:
            raise NotImplementedError(
                "SmolVLA evaluation does not provide PPO/GRPO logprobs or values"
            )
        batch = self.preprocessor(self._prepare_observation(env_obs))
        batch = self._move_batch_to_policy(batch)
        parameter = next(self.policy.parameters())
        if noise is not None:
            noise = noise.to(device=parameter.device, dtype=torch.float32)

        if self.compute_dtype in (torch.float16, torch.bfloat16):
            with torch.autocast(
                device_type=parameter.device.type, dtype=self.compute_dtype
            ):
                normalized_actions = self.policy.predict_action_chunk(
                    batch, noise=noise
                )
        else:
            normalized_actions = self.policy.predict_action_chunk(batch, noise=noise)
        actions = self.postprocessor(
            normalized_actions.detach().to(device="cpu", dtype=torch.float32)
        )
        actions = torch.as_tensor(actions, dtype=torch.float32, device="cpu")
        actions = actions.detach().contiguous()
        batch_size = env_obs["states"].shape[0]
        expected_shape = (
            batch_size,
            int(self.cfg.num_action_chunks),
            int(self.cfg.action_dim),
        )
        if tuple(actions.shape) != expected_shape:
            raise ValueError(
                f"Expected postprocessed actions with shape {expected_shape}, got "
                f"{tuple(actions.shape)}"
            )
        result = {
            "prev_logprobs": None,
            "prev_values": None,
            "forward_inputs": {"action": actions.flatten(1)},
        }
        return actions, result


def build_smolvla(
    cfg: DictConfig, torch_dtype: torch.dtype | None = None
) -> SmolVLAForRLActionPrediction:
    """Build the LeRobot-backed SmolVLA policy for RLinf."""
    return SmolVLAForRLActionPrediction(cfg, torch_dtype)
