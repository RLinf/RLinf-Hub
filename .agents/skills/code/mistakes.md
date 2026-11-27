# Mistakes agents make in RLinf-Hub code

Review this checklist before marking a change ready. Each row pairs a common mistake with the expected fix and the rule behind it.

## Integration and design

| Mistake | Fix | Rule |
|---|---|---|
| Copying an entire upstream model or simulator repo into RLinf-Hub | Pin the upstream package in `requirements.txt` and write a thin adapter | patterns.md § Design philosophy |
| Registering a model/algorithm only in a driver script or `__main__` block | Export an idempotent `register()` loaded via `RLINF_EXT_MODULE` so every Ray worker registers it | patterns.md § Design philosophy |
| Silently returning zero logprobs or dummy values on unsupported training/eval paths | Raise `NotImplementedError` with a clear message stating what is supported | patterns.md § Design philosophy |
| Editing files outside `<category>/<project_name>/` (other than catalog rows in root READMEs) | Keep all project code, configs, and tests inside one project folder | AGENTS.md § Rules |
| Duplicating action queues or double-batching observations when RLinf already batches/chunks | Align with RLinf's batch and `num_action_chunks` contract directly | patterns.md § Models |

## Portability and dependencies

| Mistake | Fix | Rule |
|---|---|---|
| Hardcoding `/home/<user>/...`, `/Users/...`, `CUDA_VISIBLE_DEVICES=0`, or local checkpoint paths in code or YAML | Read paths and device settings from Hydra config or environment variables | patterns.md § Design philosophy |
| Hardcoding `torch.cuda` / `.cuda()` in runtime library code | Use `Worker.torch_platform`, `self.torch_platform`, or `tensor.device` | AGENTS.md § Rules |
| Top-level imports of heavy or hardware-specific vendor SDKs that break registration or CPU tests | Import optional packages lazily inside the builder, method, or branch that uses them | AGENTS.md § Rules |
| Unpinned git dependencies or machine-specific local wheel URLs in `requirements.txt` | Pin `@<rev>` and keep `requirements.txt` cross-platform | AGENTS.md § Rules |

## Defensive code, conventions, and tests

| Mistake | Fix | Rule |
|---|---|---|
| Replacing direct member access with `getattr`/`hasattr` or adding guards so incomplete mocks pass | Keep product code direct and construct complete fixtures in tests | patterns.md § Design philosophy |
| Swallowing errors with bare `except:` or `except Exception: pass` | Catch specific exceptions and re-raise with expected vs. found context (`raise ... from exc`) | patterns.md § Code conventions |
| Using `print` in adapter/worker modules | Use `get_logger()` or `logging.getLogger(__name__)` | patterns.md § Code conventions |
| Missing Apache-2.0 header on new `.py` files or missing `__init__.py` in package folders | Add the standard header and `__init__.py`; `code/check.py` catches both | patterns.md § Code conventions |
| Tests that download multi-GB weights unconditionally or require a GPU on default `pytest` | Keep default tests offline on CPU; gate real-checkpoint GPU smoke tests behind an env var | patterns.md § Tests |
| Claiming task-level benchmark validity from shape-only smoke tests | Report CPU contract tests, GPU smoke tests, and benchmark curves separately and honestly | AGENTS.md § Working with a human submitter |
