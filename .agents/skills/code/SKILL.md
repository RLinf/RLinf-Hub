---
name: code
description: "RLinf-Hub Python code, Hydra configs, shell scripts, tests, and CI (**/*.py, **/*.yaml, **/*.yml, **/*.sh, tests/**, .github/**): read before writing or changing them, then check the change. Covers out-of-tree RLinf integration patterns (RLINF_EXT_MODULE, BasePolicy, algorithm/env/robot contracts, lazy imports, static Hydra configs, device portability), code conventions, offline contract tests, and license headers. Use before adding or changing a Hub component's code, config, script, or test, and to check such a change."
paths:
  - "**/*.py"
  - "**/*.yaml"
  - "**/*.yml"
  - "**/*.sh"
  - tests/**
  - .github/**
---

# Code

RLinf-Hub's coding and integration patterns are in [patterns.md](patterns.md), and repository-wide rules are in [AGENTS.md](../../../AGENTS.md). This skill covers writing and checking Python modules, Hydra YAML configs, shell scripts, tests, and CI files. Submission layout, dependency pins, RLinf registration wiring, and catalog entries belong to [submission](../submission/SKILL.md); Markdown READMEs belong to [docs](../docs/SKILL.md).

## Write

1. Check the closest existing sibling under `algorithms/`, `models/`, `envs/`, or `robots/` (or its category `README.md`) to follow the established directory and adapter conventions.
2. Read [patterns.md](patterns.md) before writing code: keep the integration self-contained, wrap upstream libraries rather than copying them, and register through `RLINF_EXT_MODULE` (or provide a custom `EnvWorker` / entry script for `envs/`).
3. Keep Hydra YAML configs static, minimal, and free of hardcoded local paths, credentials, or machine-specific GPU ordinals.
4. Keep heavy or vendor-specific imports lazy (inside builders, methods, or branches) so registration, config inspection, and offline CPU tests work without optional packages or GPUs.
5. Add offline CPU contract tests under `<category>/<project>/tests/` that verify registration, config loading, shape/dtype/normalization contracts, and explicit `NotImplementedError` paths without downloading multi-GB weights. Mock only external vendor SDKs or upstream checkpoint loaders.
6. Before finishing, review [mistakes.md](mistakes.md), run the check below, and run your project's offline tests.

## Check

```bash
python3 .agents/skills/code/check.py              # files changed against main
python3 .agents/skills/code/check.py FILE ...
```

Findings use the shared format of [README.md](../README.md#findings):

| Rule | Severity | Reports |
|---|---|---|
| `code/syntax` | critical | a changed Python file that fails `ast.parse` |
| `code/shell-syntax` | critical | a changed `.sh` script that fails `bash -n` |
| `code/yaml` | critical | a changed `.yaml`/`.yml` file that fails YAML parsing |
| `code/ruff` | major | `pre-commit` or `ruff` lint/format failure on changed Python files (skipped if neither is installed) |
| `code/init` | major | a Python package directory under `<category>/<project>/<module>/` with `.py` files and no `__init__.py` |
| `code/license` | major or minor | a new `.py` file without `# Copyright <year> The RLinf Authors.` (major; vendored files keep upstream headers) or with a non-current year (minor) |
| `code/hardcoded-path` | major | a hardcoded local home path (`/home/...`, `/Users/...`, `C:\Users\...`) in added code, YAML, or shell lines |
| `code/cuda` | minor | direct `torch.cuda` / `.cuda(` calls in added runtime Python lines where `Worker.torch_platform` or `tensor.device` improves portability |

Then check what a script cannot decide ([mistakes.md](mistakes.md) lists concrete forms):

- [ ] No vendored copy of an upstream model, simulator, or SDK codebase when the upstream package can be installed and wrapped cleanly.
- [ ] Out-of-tree registration is idempotent and works in every Ray worker via `RLINF_EXT_MODULE` as well as in the driver before `validate_cfg()`.
- [ ] Unsupported RLinf hooks (for example training replay or PPO/GRPO logprobs on an inference-only adapter) raise `NotImplementedError` explicitly rather than returning fake tensors or silently no-oping.
- [ ] Validation happens once at external boundaries (user config, observation shapes, stats files, vendor outputs) with messages stating what was expected and what was found; no unnecessary `getattr`/`hasattr` guards added to satisfy incomplete test stubs.
- [ ] No `print` in runtime library code (use `rlinf.utils.logging.get_logger()` or `logging.getLogger(__name__)`); public APIs carry type hints and concise Google-style docstrings.
- [ ] Tests fail without the implementation, cover real adapter contracts on CPU, and separate gated GPU smoke tests from offline tests.
