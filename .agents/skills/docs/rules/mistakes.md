# Mistakes agents make in RLinf-Hub docs

Check this table before finishing any README change.

| Mistake | Fix | Rule |
|---|---|---|
| Hard-wrapping Chinese paragraphs at 80 columns in `README.zh-CN.md` | Keep each Chinese paragraph and list item on a single line | rules/chinese.md § Markdown 排版 |
| Translating `README.md` sentence by sentence into stiff Chinese ("一个自包含的适配器", "支持的契约", "当……时") | Write `README.zh-CN.md` natively from the section plan | rules/chinese.md § 先理解，再用中文写 |
| Missing `README.zh-CN.md` or updating only one language | Ship and update `README.md` and `README.zh-CN.md` together | rules/base.md § Two languages |
| Forgetting to add the catalog row in root `README.md` and `README.zh-CN.md` | Add matching rows in both root READMEs | rules/catalog.md |
| Including `$ ` prompts, hardcoded `/home/...` paths, or `example.com` placeholders in commands | Provide clean, copy-pasteable commands with documented `<placeholders>` | rules/base.md § Write for someone running the component |
| Unclear working directory (mixing RLinf checkout commands and RLinf-Hub root commands without saying which) | State explicitly when a command runs in RLinf vs. RLinf-Hub root | rules/project-readme.md |
| Repeating scope disclaimers or negative-contrast framing ("not A, not B, but C") across multiple sections | State scope clearly once upfront in positive terms | rules/base.md § Prefer clarity and brevity |
| Presenting shape-only GPU smoke numbers as task-level benchmark results | Separate CPU contract tests, GPU smoke tests, and task-level benchmarks/curves | rules/project-readme.md |
| Redirecting `github.com/<org>/<repo>/raw/...` image URLs or broken relative links | Use `raw.githubusercontent.com` for external images and verify every relative link | rules/base.md § Accuracy and links |
| Leaving an unclosed code fence or mismatched Markdown table columns | Run `python3 .agents/skills/docs/check.py` and fix every reported line | docs/SKILL.md § Check |
