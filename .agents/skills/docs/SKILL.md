---
name: docs
description: "RLinf-Hub bilingual Markdown documentation (README.md, README.zh-CN.md, algorithms/**/*.md, models/**/*.md, envs/**/*.md, robots/**/*.md): write, edit, or check a project README or catalog page in English and Chinese. Holds Markdown writing rules (base, project README, catalog, English, Chinese, common mistakes), templates, and automated checks for EN/ZH parity, section structure, links, Markdown syntax, CJK hard-wrapping, and prose style. Use before creating or editing any RLinf-Hub README or Markdown guide, and to check docs."
paths:
  - README.md
  - README.zh-CN.md
  - "algorithms/**/*.md"
  - "models/**/*.md"
  - "envs/**/*.md"
  - "robots/**/*.md"
---

# Docs

RLinf-Hub documents every component in Markdown through paired `README.md` and `README.zh-CN.md` files. All writing rules live in [rules/](rules/), split into shared rules, page-type rules, and language rules.

## Write

1. **Identify the page type:**
   - **Project README** (`<category>/<project>/README.md` and `README.zh-CN.md`): read [rules/base.md](rules/base.md), [rules/project-readme.md](rules/project-readme.md), [rules/english.md](rules/english.md), and [rules/chinese.md](rules/chinese.md). Start from [templates/project-readme.md](templates/project-readme.md) and [templates/project-readme.zh-CN.md](templates/project-readme.zh-CN.md).
   - **Root catalog or category README** (`README.md`, `README.zh-CN.md`, `<category>/README*.md`): read [rules/base.md](rules/base.md), [rules/catalog.md](rules/catalog.md), [rules/english.md](rules/english.md), and [rules/chinese.md](rules/chinese.md).
2. **Verify every fact against the code.** Check every command, `requirements.txt` path, Hydra config path, env var (`RLINF_EXT_MODULE`, `PYTHONPATH`), checkpoint revision, and tested RLinf version.
3. **Write English and Chinese from the same plan.** Keep sections, commands, config keys, numbers, and links identical, but write Chinese natively rather than translating English sentences one by one. Keep each Chinese paragraph on a single line (no hard wraps inside paragraphs).
4. **Go through [rules/mistakes.md](rules/mistakes.md).**
5. **Run a fresh-agent readability pass.** Give a fresh agent (with no code context) only the changed Markdown pages, [rules/base.md](rules/base.md), and the language files. Ask it to cut filler, long-winded internals, repeated facts, defensive disclaimers, and negative-contrast framing ("not A, not B, but C" / "不是……而是……"), and to rewrite any stiff or translated Chinese.
6. **Run the check below** and fix every finding it reports.

## Check

```bash
python3 .agents/skills/docs/check.py              # docs changed against main
python3 .agents/skills/docs/check.py FILE ...     # specific Markdown files
python3 .agents/skills/docs/check.py --all-lines FILE ...
```

Line findings count only on lines the change adds unless `--all-lines` is given. Findings use the shared format of [../README.md](../README.md#findings):

| Rule | Severity | Reports |
|---|---|---|
| `docs/markdown` | critical, major, or minor | unclosed fenced code block (critical), malformed/indented table (major), or `$ ` prompt prefix inside a shell code block (minor) |
| `docs/parity` | major or minor | missing EN/ZH counterpart or deleted while counterpart stays (major); one language edited without updating the other (minor) |
| `docs/structure` | major or minor | new project README missing H1, install, run/register, or verification/results sections (major), or missing language switcher link (minor) |
| `docs/links` | major or minor | broken relative Markdown link or placeholder URL like `example.com` (major); redirecting `github.com/.../raw/...` image URL instead of `raw.githubusercontent.com` (minor) |
| `docs/en-style` | minor | hype, filler, or wordy phrasing banned by [rules/english.md](rules/english.md) |
| `docs/zh-style` | minor | `您`, `「」`, `值得注意的是`, `进行`, `当……时`, `不是/并非……而是……`, half-width punctuation in Chinese prose, or missing space between Chinese and English/digits ([rules/chinese.md](rules/chinese.md)) |
| `docs/zh-hard-wrap` | minor | Chinese prose hard-wrapped across lines inside a paragraph or list item, which renders as stray spaces on GitHub |

Then read every changed README in full in both languages as a new RLinf-Hub user who has not read the code:

- [ ] **Easy to understand:** opening sentence states what the component does, which RLinf version it supports, and its exact scope (for example inference-only vs. training).
- [ ] **Readability and native prose:** plain, scannable English and native Chinese (never sentence-by-sentence machine translation), short paragraphs, no walls of prose, no internal implementation tours, and no repeated negative-contrast framing.
- [ ] **Easy to run:** install steps, `RLINF_EXT_MODULE` / `PYTHONPATH` registration, Hydra config usage, and verification commands are copy-pasteable from a clean RLinf environment with no hidden steps or hardcoded local paths.
- [ ] **Accurate claims and parity:** commands, flags, config keys, numbers, and links match the code and agree between `README.md` and `README.zh-CN.md`.
- [ ] **Honest scope and results:** CPU contract checks, GPU smoke checks, and task-level benchmarks/curves/demos are reported separately with hardware and checkpoint revision details.
- [ ] None of the mistakes in [rules/mistakes.md](rules/mistakes.md) remains.

Rate a page `major` when it fails readability, native Chinese quality, command usability, docs-to-code accuracy, or EN/ZH parity as a whole; rate isolated wording or spacing issues `minor`.
