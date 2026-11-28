# SmolVLA (450M) for RLinf

[English](README.md) | [简体中文](README.zh-CN.md)

A self-contained, inference-only RLinf-Hub adapter for the official
[`lerobot/smolvla_base`](https://huggingface.co/lerobot/smolvla_base) checkpoint.
The adapter calls the upstream LeRobot implementation; it does not copy model code
or modify RLinf. Training, actor replay, and PPO/GRPO logprobs are not implemented
and raise `NotImplementedError`.

## Supported contract

- RLinf `0.3.0` with the `embodied` extra (tag `v0.3`, commit
  `0505431899574619da86f551bad70b71e0ea2177`; the PyPI 0.3.0 sdist matches this tag).
- LeRobot `0.4.4` with the `smolvla` extra and Transformers `4.57.1`.
- Validated with CUDA 12.8 builds of Torch `2.10.0` and TorchVision `0.25.0`.
- Checkpoint revision `5e8d12a6e2975b0e5e5fce7c8caf47c371d257b6`.
- The adapter removes only the checkpoint's `type` registry tag before LeRobot
  0.4.4 parses the config; model fields and weights are unchanged.
- Three `observation.images.camera*` inputs, a 6D state, and a 6D action chunk of
  length 50.
- `precision=fp32` runs FP32; `precision=fp16` enables FP16 autocast;
  `precision=bf16` enables BF16 autocast. All modes keep FP32 model parameters and
  return CPU FP32 actions.
- `model_path` accepts a Hugging Face repo ID or a local checkpoint directory.

## Package layout

```text
models/smolvla/
├── README.md
├── README.zh-CN.md
├── requirements.txt
├── configs/
│   └── smolvla.yaml
├── smolvla/
│   ├── __init__.py
│   └── adapter.py
└── tests/
    ├── test_smolvla.py
    └── ray_smoke.py
```

## Install

### 1. Install RLinf 0.3.0

From an RLinf checkout, install the embodied environment:

```bash
cd /path/to/RLinf
git checkout 0505431899574619da86f551bad70b71e0ea2177  # v0.3
bash requirements/install.sh embodied --env dummy
source .venv/bin/activate
```

The install script activates its virtual environment only inside its own process.
Run `source .venv/bin/activate` in your shell before installing the model extras.
If you use the official RLinf Docker image, use the environment already active in
the container instead.

### 2. Install the SmolVLA extras from the RLinf-Hub root

```bash
cd /path/to/RLinf-Hub
export PYTHONPATH="$PWD/models/smolvla${PYTHONPATH:+:$PYTHONPATH}"
uv pip install -r models/smolvla/requirements.txt
```

`requirements.txt` contains only dependencies beyond RLinf and records the tested
RLinf version in its header. LeRobot `0.7.0` is intentionally not used: its
SmolVLA extra requires Transformers 5.x, while RLinf `0.3.0[embodied]` caps
Transformers at `4.57.6`. The lock also uses `datasets==4.8.0` because
`datasets 5.2` requires Hugging Face Hub 1.x, which conflicts with Transformers
4.57's `<1.0` requirement. `torchcodec==0.10.0` satisfies LeRobot 0.4.4's
`<0.11.0` cap.

On minimal Linux images, `torchcodec` also needs the system FFmpeg shared
libraries. If importing LeRobot fails with a missing `libavcodec`/`libavformat`,
install FFmpeg (for example, `apt-get install -y ffmpeg`).

The adapter downloads the pinned checkpoint on first use. To prefetch it with the
installed `huggingface-hub` package:

```bash
python -c "from huggingface_hub import snapshot_download; snapshot_download('lerobot/smolvla_base', revision='5e8d12a6e2975b0e5e5fce7c8caf47c371d257b6')"
```

### Local checkpoints

Set `model_path` to a local directory containing `config.json` and
`model.safetensors`. The adapter reads that local config directly and passes the
same directory to `SmolVLAPolicy.from_pretrained`; `model_revision` remains in the
call but is ignored by LeRobot for local directories. If the path is an existing
directory without `config.json`, the adapter raises `FileNotFoundError` instead
of misclassifying the directory as a Hugging Face repo ID. Non-directory paths
use the original Hugging Face repo ID download path.

## Register with RLinf

Run commands from the Hub root:

```bash
export PYTHONPATH="$PWD/models/smolvla${PYTHONPATH:+:$PYTHONPATH}"
export RLINF_EXT_MODULE=smolvla
python -c "from smolvla import register; register(); print('smolvla registered')"
```

`RLINF_EXT_MODULE` performs registration in every Ray worker. An external driver
must also register before calling `validate_cfg()`:

```python
from smolvla import register

register()
cfg = validate_cfg(cfg)
```

## Hydra model fragment

`models/smolvla/configs/smolvla.yaml` is a model-group fragment. Add the config
directory to Hydra's search path and include it for both actor and rollout when
building a complete RLinf recipe:

```yaml
hydra:
  searchpath:
    - file://${oc.env:SMOLVLA_CONFIG_DIR}
```

```bash
export SMOLVLA_CONFIG_DIR="$PWD/models/smolvla/configs"
```

```yaml
defaults:
  - smolvla@actor.model
  - smolvla@rollout.model
```

The fragment uses `num_action_chunks: 50` because the adapter returns the full
`predict_action_chunk()` result. It does not call `select_action()` or maintain a
second action queue.

## Observation and normalization contract

| RLinf input | Shape | LeRobot target |
|---|---|---|
| `main_images` | `[B,H,W,C]` or `[B,1,H,W,C]` | `observation.images.camera1` |
| `extra_view_images` | `[B,2,H,W,C]` or two `[B,H,W,C]` tensors | `observation.images.camera2`, `camera3` |
| `states` | `[B,6]` | `observation.state` |
| `task_descriptions` | `list[str]` of length `B` | `task` |

Integer images are divided by 255; floating images are treated as already being in
`[0,1]`. HWC inputs are converted to CHW. The upstream processor performs
tokenization, image normalization, and optional state/action normalization. Its
automatic add-batch step is removed because RLinf observations are already
batched.

The adapter rebuilds processors from the checkpoint config instead of loading the
base checkpoint's stale saved pipeline. The base checkpoint contains only
ambiguous legacy per-robot action statistics, so `stats_path: null` uses unit
mean/std statistics for a shape-only smoke test. For meaningful physical action
values, point `stats_path` at a JSON file using the current feature keys:

```json
{
  "observation.state": {"mean": [0, 0, 0, 0, 0, 0], "std": [1, 1, 1, 1, 1, 1]},
  "action": {"mean": [0, 0, 0, 0, 0, 0], "std": [1, 1, 1, 1, 1, 1]}
}
```

## Verify

Run all commands from the RLinf-Hub root.

CPU contract tests do not download weights. Expected result for the updated
suite: `13 passed, 5 deselected`.

```bash
PYTHONPATH="$PWD/models/smolvla${PYTHONPATH:+:$PYTHONPATH}" \
  python -m pytest -q models/smolvla/tests/test_smolvla.py -k 'not gpu and not network'
```

Resolve the real Hugging Face repo ID and both checkpoint files:

```bash
PYTHONPATH="$PWD/models/smolvla${PYTHONPATH:+:$PYTHONPATH}" \
SMOLVLA_NETWORK_SMOKE=1 \
  python -m pytest -q models/smolvla/tests/test_smolvla.py -k 'network_remote_checkpoint'
```

Real-checkpoint GPU smoke tests. The first command loads the same official weights
through a local checkpoint directory; the remaining three use the remote repo ID:

```bash
PYTHONPATH="$PWD/models/smolvla${PYTHONPATH:+:$PYTHONPATH}" \
CUDA_VISIBLE_DEVICES=0 SMOLVLA_GPU_SMOKE=1 \
  python -m pytest -q --log-cli-level=INFO models/smolvla/tests/test_smolvla.py -k 'gpu_local_checkpoint'

PYTHONPATH="$PWD/models/smolvla${PYTHONPATH:+:$PYTHONPATH}" \
CUDA_VISIBLE_DEVICES=0 SMOLVLA_GPU_SMOKE=1 \
  python -m pytest -q --log-cli-level=INFO models/smolvla/tests/test_smolvla.py -k 'gpu_checkpoint_smoke and fp32'

PYTHONPATH="$PWD/models/smolvla${PYTHONPATH:+:$PYTHONPATH}" \
CUDA_VISIBLE_DEVICES=0 SMOLVLA_GPU_SMOKE=1 \
  python -m pytest -q --log-cli-level=INFO models/smolvla/tests/test_smolvla.py -k 'gpu_checkpoint_smoke and fp16'

PYTHONPATH="$PWD/models/smolvla${PYTHONPATH:+:$PYTHONPATH}" \
CUDA_VISIBLE_DEVICES=0 SMOLVLA_GPU_SMOKE=1 \
  python -m pytest -q --log-cli-level=INFO models/smolvla/tests/test_smolvla.py -k 'gpu_checkpoint_smoke and bf16'
```

Each GPU test returns one finite CPU FP32 tensor with shape `[1, 50, 6]` and logs
the checkpoint source, latency, GPU name, and peak CUDA memory.

Ray two-worker registration and inference smoke test (requires two visible
BF16-capable GPUs):

```bash
PYTHONPATH="$PWD/models/smolvla${PYTHONPATH:+:$PYTHONPATH}" \
RLINF_EXT_MODULE=smolvla CUDA_VISIBLE_DEVICES=0,1 \
  python models/smolvla/tests/ray_smoke.py
```

Expected output: one JSON record per worker followed by `RAY_SMOKE_OK`. For a
single GPU, run `SMOLVLA_RAY_WORKERS=1 CUDA_VISIBLE_DEVICES=0` instead. The script
uses the normal Hugging Face cache/network settings; set `HF_HOME` or
`HF_ENDPOINT` in the shell if needed.

## Evidence

### Linux A100 validation (primary)

Validated on Ubuntu 26.04.1 LTS with 2x NVIDIA A100-SXM4-80GB GPUs (driver
595.99.02, 400 W power limit), Python 3.12.16, PyTorch 2.10.0+cu128 (CUDA 12.8),
Ray 2.60.1, RLinf 0.3.0 (tag `v0.3`, commit
`0505431899574619da86f551bad70b71e0ea2177`), LeRobot 0.4.4, Transformers
4.57.1, and torchcodec 0.10.0. The checkpoint contains 906,712,520 bytes with SHA256
`7cd549ac2351fb069c0ddb3c34ad2d09cfc92b56a15dccdfc2e41467aaca01eb`
(revision `5e8d12a6e2975b0e5e5fce7c8caf47c371d257b6`); loading it took 32.0 s.

The baseline `e41c39a` suite passed 11/11 tests in 112.77 s (8 CPU contract tests
and 3 real-checkpoint GPU tests); those numbers are retained as historical
baseline evidence.

The F1–F6 patch was revalidated on this A100 host:

- CPU contract suite: **13 passed, 5 deselected** in 27.13 s.
- Real Hugging Face repo-ID resolution: **1 passed** in 5.64 s.
- Real-checkpoint GPU suite: **4 passed** in 114.35 s — one local-directory
  FP32 load plus remote FP32/FP16/BF16 loads, all returning finite CPU FP32
  `[1, 50, 6]` actions.
- Ray two-worker check: both workers registered solely through
  `RLINF_EXT_MODULE=smolvla`, loaded the official checkpoint, ran BF16 autocast
  inference, and returned finite `[1, 50, 6]` actions (281.12 ms and 275.99 ms).
  The driver finished with `RAY_SMOKE_OK` and exit code 0.
- Ruff check and Ruff format check passed.

The installed RLinf Python tree hash
`ab9d8de97599ea82de91e0e70d39b49079b517bdbb10cafac69833fc8ec15a2d` matches tag
`v0.3` (`0505431899574619da86f551bad70b71e0ea2177`) exactly; the PyPI 0.3.0
sdist contains the same 583 Python files.

### A100 steady latency (baseline e41c39a)

Batch size is 1. Each precision ran three rounds of two warmup calls plus 30
measured calls (90 measured samples). Timing covered the full
`adapter.predict_action_batch`, including preprocessing, tokenization,
flow-matching inference, and postprocessing. Every measured call was wrapped in
`torch.cuda.synchronize()`; `empty_cache()` was not called during timing. The GPU
reported P0 at 34.53 W before the run and P0 at 50.11 W after it (32% utilization).

| Precision | First forward | P50 | P95 | Mean | Std | Min | Max |
|---|---:|---:|---:|---:|---:|---:|---:|
| FP32 | 946.82 | 251.80 | 261.82 | 253.49 | 5.85 | 248.71 | 297.88 |
| FP16 autocast | 3,995.21 | 275.47 | 285.15 | 276.39 | 4.61 | 270.67 | 295.17 |
| BF16 autocast | 294.11 | 269.32 | 278.06 | 270.54 | 3.91 | 265.68 | 284.41 |

Values are milliseconds. The first call after each mode switch is reported
separately and excluded from the steady-state columns.

### Windows RTX 5070 Ti cross-platform check (supplementary)

The F1–F6 patch also passed 13 CPU tests, 1 real remote-resolution test, and 4
real-checkpoint GPU tests on Windows 11 with Python 3.12.16, Torch 2.10.0+cu128,
an RTX 5070 Ti (sm_120), driver 621.14, and a 300 W power limit. Latency was not
remeasured for the patch. The table below is baseline `e41c39a` evidence: 11/11
tests passed, model loading took 45.4 s, and the same 90-sample protocol produced
the following shared-desktop measurements:

| Precision | P50 | P95 | Mean | Std | Min | Max |
|---|---:|---:|---:|---:|---:|---:|
| FP32 | 525.33 | 6,329.80 | 1,553.76 | 4,019.25 | 481.26 | 25,322.57 |
| FP16 autocast | 657.75 | 680.02 | 722.40 | 433.60 | 616.39 | 4,220.54 |
| BF16 autocast | 648.54 | 668.99 | 648.24 | 15.85 | 582.13 | 686.48 |

Per-round P50 values were stable. FP32 and FP16 had long-tail outliers on the
shared desktop; they are retained rather than trimmed. These are preliminary
end-to-end numbers, not a controlled benchmark, and no FP16/BF16 speedup is
claimed.

### Weight storage vs compute vs output dtype

The precision switch only enables CUDA autocast; it does not quantize or
re-store weights. The Linux audit reproduced the same histogram as the Windows
run.

| Stage | FP32 mode | FP16 mode | BF16 mode |
|---|---|---|---|
| Checkpoint tensor storage (on disk) | mixed: 474 BF16 tensors (446,772,624 elements) + 26 F32 tensors (3,273,552 elements) | same checkpoint | same checkpoint |
| Loaded parameters in the adapter | 500 `torch.float32` tensors (450,046,176 elements) + 2 FP32 buffers (64 elements) | same FP32 model parameters | same FP32 model parameters |
| Autocast state during inference | disabled (`actual_autocast_dtype=None`) | enabled, `torch.float16` | enabled, `torch.bfloat16` |
| Probe `nn.Linear` output dtype | `torch.float32` | `torch.float16` | `torch.bfloat16` |
| Adapter output | CPU `torch.float32` `[B,50,6]` | CPU `torch.float32` `[B,50,6]` | CPU `torch.float32` `[B,50,6]` |

The evidence covers contract tests, strict checkpoint loading, and distributed
registration/inference. It does not include a task-level benchmark rollout or a
success-rate measurement.
