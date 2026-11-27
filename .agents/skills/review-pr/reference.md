# RLinf-Hub PR review checklist

Checklist for step 5 of [SKILL.md](SKILL.md), ordered by finding category. Code rules live in [code/patterns.md](../code/patterns.md), submission rules in [submission/reference.md](../submission/reference.md), and Markdown rules in [docs/SKILL.md](../docs/SKILL.md). Cite `path:line` on `$PR_HEAD`.

## correctness

- [ ] **RLinf registration**: `RLINF_EXT_MODULE` registration is idempotent and registers in both the driver (before `validate_cfg()` / `get_model()`) and Ray workers.
- [ ] **Observation, action, and normalization contracts**: image channel order (HWC vs. CHW), scaling (`[0, 255]` vs. `[0, 1]`), state/action shapes, batch dimensions (no accidental double-batching), action chunking (`num_action_chunks`), and stats loading match RLinf and upstream.
- [ ] **Numerics and device placement**: FP32/FP16/BF16 autocast matches weights and device type; integer IDs/masks are not cast to float; no hardcoded `cuda:0` that breaks multi-GPU or non-CUDA setups.
- [ ] **Unsupported paths fail loudly**: unimplemented training, replay, logprob, or value paths raise `NotImplementedError` rather than returning zeros or dummy stats.
- [ ] **Config & Hydra composition**: YAML configs load cleanly, keys match code consumers, and model fragments document exact `hydra.searchpath` + `defaults` wiring.
- [ ] **Resources and lifecycle**: simulator/robot handles, subprocesses, or temp files are cleaned up on exceptions and `close()` is idempotent.
- [ ] **Claims vs. diff**: PR description claims (RLinf version, checkpoint revision, test results, Ray multi-worker run, latency/metrics) match the actual code, config, and evidence.

## design

- [ ] **Self-containment**: all component files stay inside `<category>/<project_name>/`; root files change only for catalog rows in `README.md` and `README.zh-CN.md`.
- [ ] **Thin wrapper over upstream**: wraps installable upstream packages rather than copying whole model/simulator codebases into RLinf-Hub.
- [ ] **Portability**: no hardcoded local paths (`/home/...`, `/Users/...`), credentials, hostnames, or fixed GPU ordinals in code, configs, or scripts; optional heavy SDKs imported lazily.
- [ ] **No unnecessary protection code**: boundary validation states expected vs. found; no `getattr`/`hasattr` fallbacks added to product code to appease incomplete test mocks; no bare `except: pass`.
- [ ] **No committed artifacts**: no checkpoints, logs, `outputs/`, `wandb/`, or large media (> 5 MB) in git.

## reuse

- [ ] **Upstream and RLinf reuse**: reuses RLinf's registries, `BasePolicy`, logging, and upstream pre/post-processors instead of duplicating them by hand.

## tests, docs, and docs-style

Area scripts and checklists run in step 6 ([code § Check](../code/SKILL.md#check), [submission § Check](../submission/SKILL.md#check), [docs § Check](../docs/SKILL.md#check)). Verify alongside them:

- [ ] **Easy to run & reproduce**: `requirements.txt` layers cleanly on top of the stated RLinf version with cross-platform pins, pinned git URLs, no `ray` pin, and documented OS packages (`ffmpeg`, `libgl1`, etc.).
- [ ] **Offline tests & honest evidence**: includes offline CPU contract tests that run without downloading weights; GPU smoke tests are opt-in; CPU contract tests, GPU smoke tests, and task-level benchmarks/curves/demos are reported separately.
- [ ] **Easy to understand (fresh-agent readability pass)**: both `README.md` and `README.zh-CN.md` open with clear purpose and scope, provide copy-pasteable commands with explicit working directories, read naturally in English and native Chinese (no translationese or hard-wrapped CJK paragraphs), and match the code and catalog tables.

## style

- [ ] **Headers, layout, commits, PR metadata**: Apache-2.0 header on new `.py` files, `__init__.py` in package directories, Ruff-clean formatting, Conventional Commits + `Signed-off-by:` DCO sign-off on every commit, and valid PR title/body (`lint_pr.py lint --pr <N>`).
