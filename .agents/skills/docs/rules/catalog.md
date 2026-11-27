# Catalog and category README rules

Applies to root `README.md`, `README.zh-CN.md`, and category READMEs (`algorithms/README*.md`, `envs/README*.md`, `models/README*.md`, `robots/README*.md`).

## Root catalog tables

When adding a new project under `<category>/<project_name>/`, add one row to the matching table in both `README.md` and `README.zh-CN.md`:

- **English (`README.md`):**
  ```markdown
  | [<Project Title>](<category>/<project_name>/) | [<Upstream>](<url>) | [@<handle>](https://github.com/<handle>) | `<rlinf_version>` | <Concise one-line summary including scope> |
  ```
- **Chinese (`README.zh-CN.md`):**
  ```markdown
  | [<项目名>](<category>/<project_name>/README.zh-CN.md) | [<上游>](<url>) | [@<handle>](https://github.com/<handle>) | `<rlinf_version>` | <简洁的一句话中文简介，标明适用范围> |
  ```

Rules:

- Replace the `*Open for contributions*` / `*欢迎贡献*` placeholder row when adding the first project to an empty category table; append new rows thereafter.
- Keep the summary under ~15 English words (or ~35 Chinese characters), factual, and free of sales adjectives. State scope honestly (for example "Inference-only" / "仅推理" when training is not supported).
- Ensure the `RLinf Version` column matches the tested version documented in `<category>/<project_name>/requirements.txt` and `README.md`.
- Verify both relative links resolve cleanly.

## Category READMEs

- Keep category READMEs concise: describe the category scope, standard directory layout, RLinf integration hooks, and links to RLinf's extending guides.
- Update English and Chinese category READMEs together whenever registration hooks or directory conventions change.
