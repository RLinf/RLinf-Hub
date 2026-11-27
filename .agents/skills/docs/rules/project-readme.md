# Project README rules

Applies to `<category>/<project_name>/README.md` and `<category>/<project_name>/README.zh-CN.md`. Start from [../templates/project-readme.md](../templates/project-readme.md) and [../templates/project-readme.zh-CN.md](../templates/project-readme.zh-CN.md).

## Required elements

Every project README must let a reader understand, install, run, and verify the component without reading its source code:

1. **Title (H1) and language switcher:** `[English](README.md) | [简体中文](README.zh-CN.md)` directly under the H1.
2. **Overview and scope:** 1–2 sentences on what the integration does, link to the upstream paper/repo/checkpoint, tested RLinf version, and clear scope (e.g., training + eval vs. inference-only; supported tasks or hardware).
3. **Installation:** exact RLinf base setup (official Docker image or `requirements/install.sh` target), `pip install -r <category>/<project>/requirements.txt`, any required system packages (e.g., `ffmpeg`, `libgl1`), and checkpoint/asset download commands with pinned revisions when applicable.
4. **Usage / Launch:** exact `PYTHONPATH` and `RLINF_EXT_MODULE` exports (or custom entry script for `envs/`), how to compose or run the Hydra YAML config under `configs/`, and the key observation/action or config keys a user edits.
5. **Verification and results:** exact offline CPU test command, optional GPU/multi-worker/hardware smoke command, expected output, and any training/evaluation curves, latency tables, or demo video links. Separate offline contract tests, GPU smoke tests, and task-level benchmarks explicitly.

## Category-specific notes

- **Algorithms (`algorithms/<name>/`):** state which RLinf registries are registered (`adv_type`, `loss_type`, `reward_type`), key hyperparameters in `configs/`, and comparison curves or logs against the baseline.
- **Models (`models/<name>/`):** state checkpoint ID/revision, observation/action shapes and normalization stats requirements, precision/autocast behavior, and whether training/logprobs are implemented.
- **Simulators & Benchmarks (`envs/<name>/`):** state simulator version, render backend (`MUJOCO_GL`, `egl`/`osmesa`), asset download steps, and how the custom `EnvWorker` or launch script connects to RLinf.
- **Real-World Robots (`robots/<name>/`):** state hardware model, SDK setup, controller/network prerequisites, safety/e-stop notes, and dry-run or mock test commands before live robot operation.

## Checklist

- [ ] A user with a clean RLinf environment can copy-paste Installation and Usage commands from the repo root without editing hidden paths.
- [ ] Tested RLinf version, upstream version, and checkpoint revision match `requirements.txt` and `configs/*.yaml`.
- [ ] Every command runs from the Hub repository root (or explicitly states when a command runs inside an RLinf checkout).
- [ ] Scope and unimplemented paths are stated upfront once, without repeating defensive caveats.
- [ ] `README.md` and `README.zh-CN.md` match on sections, commands, keys, and numbers, and Chinese reads naturally with no hard-wrapped paragraphs.
