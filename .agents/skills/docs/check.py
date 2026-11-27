#!/usr/bin/env python3
# Copyright 2026 The RLinf Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Check changed RLinf-Hub Markdown docs: syntax, parity, links, structure, and writing.

Usage::

    python3 .agents/skills/docs/check.py              # docs changed against main
    python3 .agents/skills/docs/check.py FILE ...     # specific Markdown files
    python3 .agents/skills/docs/check.py --all-lines FILE ...
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import check_writing
import route

FENCE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
MD_LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)\)")
REDIRECT_RAW = re.compile(r"https?://github\.com/[^/\s]+/[^/\s]+/raw/")
PLACEHOLDER_URL = re.compile(
    r"https?://(?:www\.)?(?:example\.(?:com|org|net)|your-username)\b", re.IGNORECASE
)
SHELL_LANGS = frozenset({"bash", "sh", "shell", "zsh", "console"})
PROMPT_PREFIX = re.compile(r"^\$\s+\S")


def counterpart(path: str) -> str | None:
    """Return the paired EN/ZH README path, or ``None`` if not a bilingual README."""
    p = Path(path)
    if p.name == "README.md":
        return (p.parent / "README.zh-CN.md").as_posix().lstrip("./")
    if p.name == "README.zh-CN.md":
        return (p.parent / "README.md").as_posix().lstrip("./")
    return None


def check_parity(
    changes: list[route.Change] | tuple[route.Change, ...],
    root: Path | None = None,
) -> list[route.Finding]:
    """Check that every EN/ZH README has its counterpart and both are updated together."""
    base = root or route.REPO_ROOT
    changed = {c.path for c in changes}
    findings: list[route.Finding] = []
    for change in changes:
        other = counterpart(change.path)
        if other is None:
            continue
        exists = (base / other).exists()
        if change.status == "D" and exists and other not in changed:
            findings.append(
                route.Finding(
                    "major",
                    change.path,
                    None,
                    "docs/parity",
                    f"deleted, but counterpart {other} still exists",
                )
            )
        elif change.status != "D" and not exists:
            findings.append(
                route.Finding(
                    "major",
                    change.path,
                    None,
                    "docs/parity",
                    f"missing bilingual counterpart {other}",
                )
            )
        elif change.status != "D" and other not in changed:
            findings.append(
                route.Finding(
                    "minor",
                    change.path,
                    None,
                    "docs/parity",
                    f"updated, while counterpart {other} was not",
                )
            )
    return findings


def check_markdown_syntax(path: Path, rel: str) -> list[route.Finding]:
    """Check unclosed code fences, indented tables, and `$ ` prompts in bash blocks."""
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines()
    findings: list[route.Finding] = []

    fence = ""
    fence_line = 0
    fence_lang = ""
    table_block: list[int] = []

    def flush_table() -> None:
        if len(table_block) >= 2:
            indents = {
                len(lines[i - 1]) - len(lines[i - 1].lstrip(" \t")) for i in table_block
            }
            if len(indents) > 1 or (indents and min(indents) >= 4):
                findings.append(
                    route.Finding(
                        "major",
                        rel,
                        table_block[0],
                        "docs/markdown",
                        "table rows have inconsistent or >=4-space leading indentation; "
                        "keep Markdown tables flush left",
                    )
                )
        table_block.clear()

    for n, line in enumerate(lines, 1):
        m = FENCE.match(line)
        if not fence:
            if m:
                flush_table()
                fence = m[1]
                fence_line = n
                fence_lang = m[2].strip().split()[0].lower() if m[2].strip() else ""
            elif line.strip().startswith("|") and line.strip().count("|") >= 2:
                table_block.append(n)
            else:
                flush_table()
        elif m and m[1][0] == fence[0] and len(m[1]) >= len(fence) and not m[2].strip():
            fence = ""
            fence_lang = ""
        else:
            if fence_lang in SHELL_LANGS and PROMPT_PREFIX.match(line.strip()):
                findings.append(
                    route.Finding(
                        "minor",
                        rel,
                        n,
                        "docs/markdown",
                        "drop leading '$ ' prompt from shell commands so they copy-paste cleanly",
                    )
                )

    flush_table()
    if fence:
        findings.append(
            route.Finding(
                "critical",
                rel,
                fence_line,
                "docs/markdown",
                "code fence opened here is never closed",
            )
        )
    return findings


def check_links(path: Path, rel: str, root: Path | None = None) -> list[route.Finding]:
    """Check relative links resolve, and flag placeholder or redirecting raw image URLs."""
    base = (root or route.REPO_ROOT).resolve()
    source = path.read_text(encoding="utf-8")
    findings: list[route.Finding] = []
    for n, line in check_writing.unfenced_lines(source):
        for match in MD_LINK.finditer(check_writing.INLINE_CODE.sub(" ", line)):
            raw_target = match.group(1).strip("<>")
            if PLACEHOLDER_URL.search(raw_target):
                findings.append(
                    route.Finding(
                        "major",
                        rel,
                        n,
                        "docs/links",
                        f"placeholder URL {raw_target!r}; replace with a real link",
                    )
                )
                continue
            if REDIRECT_RAW.search(raw_target):
                findings.append(
                    route.Finding(
                        "minor",
                        rel,
                        n,
                        "docs/links",
                        "use direct https://raw.githubusercontent.com/... instead of redirecting github.com/.../raw/...",
                    )
                )
                continue
            if raw_target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target_path = raw_target.split("#", 1)[0].split("?", 1)[0]
            if not target_path:
                continue
            if target_path.startswith("/"):
                resolved = (base / target_path.lstrip("/")).resolve()
            else:
                resolved = (path.parent / target_path).resolve()
            try:
                resolved.relative_to(base)
                inside_repo = True
            except ValueError:
                inside_repo = False
            if not inside_repo or not resolved.exists():
                findings.append(
                    route.Finding(
                        "major",
                        rel,
                        n,
                        "docs/links",
                        f"broken relative link {raw_target!r}",
                    )
                )
    return findings


def check_file(
    full: Path,
    change: route.Change,
    selection: route.Selection,
    root: Path | None = None,
) -> list[route.Finding]:
    """Run all Markdown checks for one file, keeping critical/major syntax errors unfiltered."""
    findings: list[route.Finding] = []
    syntax_findings = check_markdown_syntax(full, change.path)
    findings += [f for f in syntax_findings if f.severity in ("critical", "major")]
    findings += selection.relevant(
        [f for f in syntax_findings if f.severity == "minor"]
    )
    findings += selection.relevant(check_links(full, change.path, root=root))
    findings += selection.relevant(
        check_writing.check_page(full, change.path, new=change.status == "A")
    )
    return findings


def main() -> int:
    args = route.check_parser(__doc__.splitlines()[0]).parse_args()
    selection = route.select("docs", args)
    changes = selection.changes
    present = [c for c in changes if c.status != "D" and c.path.endswith(".md")]

    findings: list[route.Finding] = []
    findings += check_parity(changes)
    for change in present:
        full = route.REPO_ROOT / change.path
        if not full.is_file():
            continue
        findings += check_file(full, change, selection)

    return route.report("docs", findings)


if __name__ == "__main__":
    raise SystemExit(main())
