---
name: submission
description: "RLinf-Hub component submissions, dependencies, registration, catalog wiring, and artifacts (algorithms/**, models/**, envs/**, robots/**, README.md, README.zh-CN.md): read before adding or updating a Hub project, then check the submission. Ensures every algorithm, model, env, or robot folder is self-contained, properly registered with RLinf, cross-platform installable, indexed in both root READMEs, free of committed checkpoints or logs, and easy to reproduce. Use before creating or reviewing any RLinf-Hub component contribution."
paths:
  - algorithms/**
  - models/**
  - envs/**
  - robots/**
  - README.md
  - README.zh-CN.md
---

# Submission

Every contribution in RLinf-Hub is a self-contained project under `algorithms/<name>/`, `models/<name>/`, `envs/<name>/`, or `robots/<name>/`. This skill enforces the packaging, dependency, RLinf registration, catalog, and reproducibility contract described in [reference.md](reference.md). Python and YAML code quality belong to [code](../code/SKILL.md); Markdown writing and bilingual parity belong to [docs](../docs/SKILL.md).

## Write

1. **Choose the category and project slug.** Place all files under `<category>/<project_name>/` using a lowercase slug matching `[a-z0-9][a-z0-9_-]*` (for example `models/smolvla/`).
2. **Read [reference.md](reference.md)** for the category's RLinf integration hooks (`RLINF_EXT_MODULE` for `algorithms/`, `models/`, `robots/`; custom `EnvWorker` or entry script for `envs/`), Hydra config composition, dependency layering, and verification evidence standards.
3. **Create the standard layout:**

   ```text
   <category>/<project_name>/
   ├── README.md          # Setup, registration/launch commands, tested RLinf version, results
   ├── README.zh-CN.md    # Native Chinese README
   ├── requirements.txt   # Extra dependencies beyond `rlinf` + tested `rlinf` version header
   ├── configs/           # Hydra YAML configs or model fragments
   ├── <module>/          # Python package or entry script
   └── tests/             # Offline CPU contract tests (and optional gated GPU smoke tests)
   ```

4. **Layer `requirements.txt` cleanly on top of RLinf.** Record the tested `rlinf` release or commit in a comment header (e.g. `# Tested with rlinf[embodied]==0.3.0`), pin only dependencies beyond `rlinf`, pin every git dependency to `@<rev>`, and avoid local filesystem paths, `ray` pins, or OS/CUDA-specific wheel suffixes.
5. **Update both catalog tables.** Add a row to the matching category table in root `README.md` and `README.zh-CN.md` (linking to `<category>/<project_name>/` in EN and `<category>/<project_name>/README.zh-CN.md` in ZH, and replacing the placeholder row only when adding the first entry to an empty table).
6. **Keep artifacts out of git.** Never commit checkpoints (`.pt`, `.pth`, `.safetensors`, `.ckpt`), datasets, run logs (`outputs/`, `logs/`, `wandb/`), or large media (> 5 MB). Host weights on Hugging Face and large demos on external links or GitHub PR attachments.
7. **Run the check below** and verify reproduction steps from a clean environment.

## Check

```bash
python3 .agents/skills/submission/check.py              # submissions changed against main
python3 .agents/skills/submission/check.py FILE ...
```

Findings use the shared format of [README.md](../README.md#findings):

| Rule | Severity | Reports |
|---|---|---|
| `submission/layout` | major | invalid project slug or missing required files (`README.md`, `README.zh-CN.md`, `requirements.txt`, `configs/*.yaml`, Python code) in a touched `<category>/<project>/` |
| `submission/requirements` | major or minor | local paths, unpinned git URLs, `ray` pins, or platform-specific `+cu`/`+rocm` pins in `requirements.txt` (major); missing tested RLinf version reference in `requirements.txt` (minor, or major if also absent from `README.md`) |
| `submission/registration` | major | `algorithms/`, `models/`, or `robots/` project missing an RLinf registration hook (`register()` or `register_*` / `SupportedModel.register`), or `envs/` project missing an `EnvWorker`/entry point |
| `submission/catalog` | major | touched project missing its catalog link in root `README.md` or `README.zh-CN.md`, or broken relative link in a catalog table |
| `submission/artifacts` | critical or major | committed checkpoint/binary weight files (critical) or `outputs/`/`logs/`/`wandb/` artifacts or files over 5 MB (major) |

Then judge what a script cannot decide:

- [ ] **Self-containment:** the PR touches only `<category>/<project_name>/` and the catalog rows in root `README.md` / `README.zh-CN.md`, with no edits to unrelated projects or core RLinf expectations.
- [ ] **Easy to run:** a user starting from a fresh official RLinf environment can follow `README.md` copy-pasteably without guessing hidden env vars, undocumented system libraries, or private paths.
- [ ] **Honest verification evidence:** the PR and README clearly separate offline CPU contract tests, GPU smoke tests, and task-level benchmarks/curves/real-robot demos, naming the exact RLinf version, checkpoint revision, hardware, and limitations.
- [ ] **No upstream bloat:** upstream model or simulator code is installed via `requirements.txt` rather than copied into the Hub repo, unless justified and properly attributed.

## Verify

1. **Offline contract tests (CPU):**

   ```bash
   PYTHONPATH="$PWD/<category>/<project>" pytest -q <category>/<project>/tests
   ```

2. **RLinf registration check (in a clean RLinf environment):**

   ```bash
   export PYTHONPATH="$PWD/<category>/<project>${PYTHONPATH:+:$PYTHONPATH}"
   export RLINF_EXT_MODULE=<module>
   python -c "import <module>; <module>.register() if hasattr(<module>, 'register') else None"
   ```

3. **Multi-worker / GPU / real-robot check:** follow the exact launch or smoke command in `<category>/<project>/README.md` on a host with the declared RLinf version, GPU, or hardware, and verify that `RLINF_EXT_MODULE` registers cleanly inside Ray workers as well as the driver.
