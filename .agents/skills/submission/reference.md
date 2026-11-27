# RLinf-Hub submission contracts

Reference for [SKILL.md](SKILL.md). Every RLinf-Hub project follows the repository contract in [README.md](../../../README.md) and its category README (`algorithms/README.md`, `models/README.md`, `envs/README.md`, `robots/README.md`).

## 1. Directory layout and naming

Every contribution lives in one self-contained folder:

```text
<category>/<project_name>/
├── README.md          # English setup, commands, tested RLinf version, scope, results
├── README.zh-CN.md    # Native Chinese README
├── requirements.txt   # Extra dependencies beyond `rlinf`
├── configs/           # Hydra YAML configs or model fragments (*.yaml)
├── <module>/          # Python package registered via RLINF_EXT_MODULE (or EnvWorker / scripts)
└── tests/             # Offline CPU contract tests + optional gated GPU smoke tests
```

- `<category>` is one of `algorithms`, `models`, `envs`, `robots`.
- `<project_name>` is lowercase ASCII `[a-z0-9][a-z0-9_-]*` (prefer concise names like `smolvla`, `gr00t`, `calvin`, `so101`).
- Keep raw benchmark logs, TensorBoard event files, checkpoints, and large videos outside git.

## 2. RLinf registration hooks by category

Core RLinf loads `RLINF_EXT_MODULE` in every Ray worker by importing the module and calling `register()` if defined (`rlinf/scheduler/cluster/utils.py`). Driver scripts that call `validate_cfg()` or `get_model()` before launching Ray must also run the same registration. Make `register()` idempotent so calling it in both driver and worker never raises a duplicate-registration error.

| Category | Expected hook | Notes |
|---|---|---|
| `algorithms/` | `@register_advantage("<name>")`, `@register_policy_loss("<name>")` in `rlinf.algorithms.registry`, or `register_reward("<name>", cls)` in `rlinf.algorithms.rewards` | Load via `RLINF_EXT_MODULE`; include a runnable Hydra config under `configs/`. |
| `models/` | `register_model(model_type, builder, category=...)` in `rlinf.models` and `SupportedModel.register(model_type, force=True)` in `rlinf.config`; embodied policies subclass `BasePolicy` | Ship either a complete recipe YAML or a Hydra model fragment (`configs/<model>.yaml`) with documented `hydra.searchpath` composition. |
| `envs/` | Custom `EnvWorker` subclass or launch script inside `envs/<name>/` (core `get_env_cls()` does not yet support dynamic `register_env()`) | Use `RLINF_EXT_MODULE` for any companion models or algorithms; document render backend (`MUJOCO_GL`, `egl`/`osmesa`) and asset setup. |
| `robots/` | RLinf robotics interfaces (`Connection`, `RobotPart`, real-world task adapters) registered via `RLINF_EXT_MODULE` | Document hardware prerequisites, safety/e-stop notes, and mock/dry-run verification. |

## 3. Dependency layering (`requirements.txt`)

- Install official RLinf first (via `requirements/install.sh` or an official RLinf Docker image), then layer `pip install -r <category>/<project>/requirements.txt`.
- Record the exact tested RLinf version or commit in the top comment of `requirements.txt` (for example `# Tested with rlinf[embodied]==0.3.0`).
- Explain any non-obvious version pin in a brief comment (for example why a newer upstream package conflicts with RLinf's `transformers` cap).
- Keep `requirements.txt` cross-platform:
  - No local filesystem paths (`file://`, `/home/...`, `/Users/...`, `C:\...`).
  - No platform-specific local wheel versions (`+cu128`, `+rocm6.2`).
  - No unpinned git URLs (`git+https://...` must end in `@<commit-or-tag>`).
  - Do not pin `ray` in a project's `requirements.txt`; let RLinf own the Ray version.
- Document any required OS packages (such as `ffmpeg` or `libgl1`) in the project README's Install section.

## 4. Catalog table updates

Every new project adds one row to the matching section of both root `README.md` and `README.zh-CN.md`:

- Root `README.md` links to `<category>/<project_name>/`.
- Root `README.zh-CN.md` links to `<category>/<project_name>/README.zh-CN.md`.
- Columns: `Work` (`作品`), `Paper / Upstream` (`论文 / 上游仓库` or `Hardware / SDK` / `硬件 / SDK`), `Contributor` (`贡献者`), `RLinf Version` (`RLinf 版本`), `Summary` (`简介`).
- Keep the summary concise and accurate about scope (for example explicitly note "Inference-only" if training is not implemented).

## 5. Verification evidence standards

RLinf-Hub accepts well-scoped contributions at different maturity levels as long as claims match evidence:

1. **Offline CPU contract tests:** verify registration, Hydra config loading, observation/action shapes, normalization round trips, and `NotImplementedError` boundaries without downloading checkpoints.
2. **Real-checkpoint / GPU smoke tests:** verify checkpoint loading, finite outputs, dtype/autocast behavior, and multi-worker Ray `RLINF_EXT_MODULE` registration on actual GPUs.
3. **Task-level benchmarks or real-robot demos:** training/evaluation logs, reward or success curves, or a short real-robot demo video.

Never present a shape-only smoke test as a task-level benchmark result. State clearly in both the PR description and the project README what was verified and what remains out of scope.
