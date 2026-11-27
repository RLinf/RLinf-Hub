# RLinf-Hub code and integration patterns

This guide sets the engineering standard for code contributed to RLinf-Hub. Authors follow it when building an algorithm, model, simulator, or robot integration, and reviewers measure PRs against it. Each pattern explains what RLinf-Hub expects and what to flag.

## Design philosophy

RLinf-Hub bridges community works and core [RLinf](https://github.com/RLinf/RLinf) with a lightweight, self-contained structure. Good Hub code is thin, explicit, and portable:

1. **Wrap upstream; do not fork-copy it.** Install the upstream library in `requirements.txt` and write a clean adapter to RLinf's interface. Copy upstream code only when no installable package exists or a small, clearly attributed vendored file is unavoidable (preserving its upstream license header).
2. **Stay self-contained.** Every project lives strictly inside `<category>/<project_name>/`. It never requires patching core `RLinf/RLinf` files or modifying sibling Hub projects. If an integration exposes a missing hook in core RLinf, open an issue in `RLinf/RLinf` and document the workaround cleanly inside your project folder.
3. **Register per process.** Ray workers do not inherit registrations executed only in the driver script. Export an idempotent `register()` function (or register on module import) loaded via `RLINF_EXT_MODULE` so every Ray worker and driver process sees the same component.
4. **Fail explicitly on unsupported paths.** An inference-only model adapter, single-arm robot driver, or eval-only environment wrapper is welcome in RLinf-Hub when scoped honestly. Unsupported methods (such as `default_forward` or `calculate_logprobs=True`) must raise `NotImplementedError` with a clear message—never return fabricated zeros or dummy logprobs.
5. **Validate at the boundary, trust inside.** Validate config shapes, action/state dimensions, image channel order, normalization stats, and vendor SDK payloads once at the adapter boundary with messages stating expected vs. actual values. Keep internal helpers direct without `hasattr`/`getattr` ladders or bare `except: pass`.
6. **Keep configs static and composable.** Provide Hydra YAML configs or model fragments under `configs/` with static values and clear defaults. Never hardcode local filesystem paths, user names, credentials, or fixed GPU indices.
7. **Prove contracts offline on CPU.** Ship fast CPU unit tests that verify registration, config parsing, preprocessing/postprocessing round trips, shape/dtype invariants, and error branches without downloading multi-GB weights. Gate real-checkpoint GPU smoke tests behind an explicit opt-in environment variable.

## Category integration patterns

### Algorithms (`algorithms/<name>/`)

- Register via `RLINF_EXT_MODULE` using `@register_advantage("<name>")`, `@register_policy_loss("<name>")`, or `register_reward("<name>", cls)`.
- Keep tensor operations device- and dtype-safe (avoid silent float16 overflows in advantage normalization, loss masks, or KL terms).
- Preserve RLinf batch/mask conventions (boolean loss masks, finite outputs under all-zero masks or batch size 1).

### Models (`models/<name>/`)

- Subclass `BasePolicy` (for embodied policies) and register through both `register_model(model_type, builder, category=...)` and `SupportedModel.register(model_type, force=True)` inside an idempotent `register()` entry point.
- Keep `configs/<model>.yaml` composable via Hydra `searchpath` (e.g. `defaults: - <model>@actor.model`) or ship a complete runnable recipe config alongside it.
- Clearly define observation mapping (image layout HWC/CHW, `[0, 255]` vs. `[0, 1]`, state/action dimensions, action chunking, and normalization stats). Do not silently double-batch or maintain a hidden second action queue when RLinf already manages batching or chunk execution.
- Prefer `parameter.device` / `Worker.torch_platform` / `torch.autocast(device_type=device.type, ...)` over hardcoded `cuda` calls.

### Simulators & Benchmarks (`envs/<name>/`)

- Until core RLinf provides dynamic `register_env()`, supply a self-contained `EnvWorker` subclass or entry script inside `envs/<name>/`, and use `RLINF_EXT_MODULE` for any companion models or algorithms.
- Make render backends (`MUJOCO_GL`, `egl`/`osmesa`), asset roots, and task suites configurable via Hydra YAML or documented environment variables rather than hardcoded paths.
- Ensure reset/step/close lifecycle is idempotent and releases simulator/subprocess handles on exceptions.

### Real-World Robots (`robots/<name>/`)

- Follow RLinf's robotics contracts (`Connection`, `RobotPart`, task env adapters) and register via `RLINF_EXT_MODULE`.
- Keep hardware safety explicit: document e-stop, workspace/joint limits, dry-run/mock mode, and controller host setup.
- Isolate vendor SDK imports inside constructors or methods so offline tests and config checks run without hardware SDKs installed.

## Code conventions

- **License headers:** Start every new `.py` file with the Apache-2.0 `# Copyright <current year> The RLinf Authors.` header. Vendored files keep their original upstream header and license notice.
- **Package layout:** Include `__init__.py` in every Python package directory under `<category>/<project>/<module>/`.
- **Logging:** Use `rlinf.utils.logging.get_logger()` or `logging.getLogger(__name__)` in library code; avoid `print` outside CLI/demo entry scripts.
- **Typing & docstrings:** Add type hints and concise Google-style docstrings to public builders, classes, and functions. Keep inline comments short and focused on invariants or non-obvious reasons (never narrate obvious lines or paste debug history).
- **Error messages:** State what was expected and what was found, preserving original exceptions (`raise ... from exc`).
- **No dead scaffolding:** Remove unused imports, commented-out code, debug dumps, `TODO(agent)`, and unrelated edits outside your project folder.

## Tests

- Put tests under `<category>/<project>/tests/test_<name>.py`.
- Test through the public adapter/registration contract on CPU so reviewers and CI can verify core logic quickly.
- Mock only external boundaries (Hugging Face downloads, upstream policy forward pass, simulator/hardware SDKs). Do not weaken production code (e.g., adding `getattr` fallbacks) just to accommodate incomplete test mocks.
- Gate GPU or real-checkpoint smoke tests with an explicit env var (for example `pytest.mark.skipif(not os.environ.get("<NAME>_GPU_SMOKE"), ...)`) so `pytest -q <category>/<project>/tests` passes cleanly on CPU.
