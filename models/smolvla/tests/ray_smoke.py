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

"""Run a minimal Ray registration-and-inference smoke test for SmolVLA."""

import json
import os
from pathlib import Path

import ray
import torch

MODULE_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path(
    os.environ.get("SMOLVLA_CONFIG", str(MODULE_ROOT / "configs" / "smolvla.yaml"))
)
WORKERS = int(os.environ.get("SMOLVLA_RAY_WORKERS", "2"))
PRECISION = os.environ.get("SMOLVLA_RAY_PRECISION", "bf16")
WORKER_ENV = {
    "PYTHONPATH": str(MODULE_ROOT) + os.pathsep + os.environ.get("PYTHONPATH", ""),
    "RLINF_EXT_MODULE": "smolvla",
    "TOKENIZERS_PARALLELISM": "false",
}
for key in ("HF_HOME", "HF_ENDPOINT"):
    if os.environ.get(key):
        WORKER_ENV[key] = os.environ[key]


@ray.remote(num_gpus=1, num_cpus=1, runtime_env={"env_vars": WORKER_ENV})
def run_worker(rank: int) -> dict:
    import time

    import torch
    from omegaconf import OmegaConf
    from rlinf.config import SupportedModel
    from rlinf.models import get_model
    from rlinf.scheduler.cluster import load_user_extension_module

    # Registration must happen only through RLINF_EXT_MODULE in this process.
    load_user_extension_module()
    registered = SupportedModel.get("smolvla")
    cfg = OmegaConf.load(str(CONFIG_PATH))
    cfg.load_to_device = False
    cfg.precision = PRECISION
    torch.manual_seed(100 + rank)
    model = get_model(cfg)
    if model is None:
        raise RuntimeError("get_model returned None: smolvla was not registered")
    model = model.to("cuda").eval()

    env_obs = {
        "main_images": torch.rand(1, 32, 32, 3),
        "extra_view_images": torch.rand(1, 2, 32, 32, 3),
        "states": torch.zeros(1, 6),
        "task_descriptions": ["pick up the block"],
    }
    noise = torch.randn(1, cfg.num_action_chunks, model.policy.config.max_action_dim)
    with torch.no_grad():
        warm_actions, _ = model.predict_action_batch(env_obs, mode="eval", noise=noise)
        torch.cuda.synchronize()
        start = time.perf_counter()
        actions, _ = model.predict_action_batch(env_obs, mode="eval", noise=noise)
        torch.cuda.synchronize()
        latency_ms = (time.perf_counter() - start) * 1000.0

    return {
        "rank": rank,
        "pid": os.getpid(),
        "gpu": torch.cuda.get_device_name(0),
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "ext_module_env": os.environ.get("RLINF_EXT_MODULE"),
        "registered": str(registered),
        "registered_value": registered.value,
        "warm_shape": list(warm_actions.shape),
        "shape": list(actions.shape),
        "dtype": str(actions.dtype),
        "finite": bool(torch.isfinite(actions).all()),
        "latency_ms": latency_ms,
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
    }


def main() -> None:
    if WORKERS < 1:
        raise ValueError("SMOLVLA_RAY_WORKERS must be at least 1")
    available_gpus = torch.cuda.device_count()
    if available_gpus < WORKERS:
        raise RuntimeError(
            f"SMOLVLA_RAY_WORKERS={WORKERS}, but only {available_gpus} CUDA devices "
            "are visible"
        )

    ray.init(
        num_cpus=WORKERS,
        num_gpus=WORKERS,
        include_dashboard=False,
        log_to_driver=True,
        runtime_env={"env_vars": WORKER_ENV},
    )
    try:
        results = ray.get([run_worker.remote(rank) for rank in range(WORKERS)])
        print("RAY_RESULTS=" + json.dumps(results, indent=2))
        for item in results:
            if item["registered_value"] != "smolvla":
                raise RuntimeError(f"worker {item['rank']} did not register smolvla")
            if item["shape"] != [1, 50, 6] or not item["finite"]:
                raise RuntimeError(f"worker {item['rank']} returned invalid actions")
        print("RAY_SMOKE_OK")
    finally:
        ray.shutdown()


if __name__ == "__main__":
    main()
