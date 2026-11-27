# Rules for every Markdown page

Every README in RLinf-Hub follows this file. Before writing, also read the page-type rules ([project-readme.md](project-readme.md) or [catalog.md](catalog.md)) and the language rules ([english.md](english.md), [chinese.md](chinese.md)). Before finishing, check [mistakes.md](mistakes.md).

## Lead with purpose and scope

- Open with one or two direct sentences stating what the component is, what upstream work or hardware it connects to, and what it supports today (for example, SFT + RL training, inference-only evaluation, or a simulator wrapper).
- State requirements and capabilities positively. Keep a limitation explicit in a short Scope note (such as "Training and PPO/GRPO logprobs are not implemented yet"), rather than repeating what the project is not throughout the page.

## Write for someone running the component, not reading its source

- The reader wants to install, configure, run, and verify the component on top of RLinf.
- Name files, config keys, env vars, and commands the reader actually runs or edits. Leave out internal helper names or step-by-step code tours unless the user must import or subclass them.
- Before each command block, state in one sentence what it does. After a verification or launch command, show the expected output or success signal.
- Write shell commands without `$ ` prompts. Mark placeholders as `<name>` and define each placeholder once.

## Prefer clarity and brevity over exhaustive dumps

- **Plain, direct language:** explain concepts as you would to a colleague—no marketing hype, stiff spec-sheet wording, or defensive caveats.
- **Say each thing once:** do not repeat the same dependency explanation, config key, or scope disclaimer across the intro, install section, and results section.
- **Short paragraphs and scannable layout:** keep paragraphs to 1–3 sentences; use numbered lists for ordered steps, bullet lists for concise specs, and Markdown tables for input/output contracts, metrics, or catalog rows.
- **No negative-contrast padding:** avoid "this is not A, not B, but C" / "不是……而是……". State directly what it is and does.

## Accuracy and links

- Verify every command, file path, Hydra config key, env var, package pin, and metric against the PR's actual code and run logs.
- Use relative links between files inside RLinf-Hub (`README.zh-CN.md`, `models/<name>/`) and full HTTPS URLs for external papers, Hugging Face checkpoints, and RLinf docs.
- Never leave placeholder URLs (`example.com`, `your-username`, `TODO`).
- For images, prefer direct `https://raw.githubusercontent.com/<org>/<repo>/<branch>/<path>` URLs over redirecting `github.com/.../raw/...` links, and keep large videos or checkpoints outside git.

## Two languages

- Every README exists in both English (`README.md`) and Chinese (`README.zh-CN.md`) in the same folder. Update both in the same PR and keep sections, commands, config keys, numbers, and links aligned.
- Write Chinese natively from the section plan—never machine-translate or translate English sentence by sentence.
- Never translate code identifiers, config keys, CLI flags, env vars, or model/env names.
- Keep each paragraph on one line in Markdown source (especially in Chinese, where line breaks inside a paragraph render as stray spaces on GitHub).
