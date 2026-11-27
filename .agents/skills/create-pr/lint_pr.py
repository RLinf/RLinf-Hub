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

"""Lint an RLinf-Hub pull-request title and body against .github/PULL_REQUEST_TEMPLATE.md.

Checks Conventional Commits title format, PR template section structure
(``Description``, ``Verification Evidence``, ``Scope and Limitations``,
``Checklist``), and common Markdown rendering defects (uniform paste indent,
mismatched table indentation, unbalanced fences, unticked checklists).

Subcommands::

    lint      --pr N | --title T [--body-file F]   check a PR or a draft
    fix       --pr N | --body-file F               emit a de-indented body
    template                                       print a clean skeleton

Exit code is 1 when any ERROR is reported, 0 otherwise (warnings pass).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field

ALLOWED_TYPES = (
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "test",
    "chore",
    "perf",
    "build",
    "ci",
    "revert",
)

TITLE_RE = re.compile(
    r"^(?P<type>[a-zA-Z]+)(?:\((?P<scope>[^)]*)\))?(?P<bang>!?): (?P<desc>.+)$"
)

VAGUE_SCOPES = {
    "new",
    "update",
    "updates",
    "change",
    "changes",
    "misc",
    "various",
    "code",
    "main",
    "all",
    "general",
    "tmp",
    "temp",
    "wip",
    "pr",
}

# Section headings of .github/PULL_REQUEST_TEMPLATE.md, in order.
TEMPLATE_SECTIONS = (
    ("Description", True),
    ("Verification Evidence", False),
    ("Scope and Limitations", False),
    ("Checklist", True),
)

# Section aliases accepted on community PRs while keeping template order.
SECTION_ALIASES = {
    "Description": ("description", "summary"),
    "Verification Evidence": (
        "verification evidence",
        "testing",
        "how has this been tested",
    ),
    "Scope and Limitations": ("scope and limitations", "scope", "limitations"),
    "Checklist": ("checklist",),
}

TITLE_DESC_MAX = 72
SCOPE_RE = re.compile(r"^[a-z0-9_-]+$")
NON_ASCII_RE = re.compile(r"[^\x20-\x7e]")
DESCRIPTION_MAX_WORDS = 250

COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
HEADING_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<hashes>#{1,6})\s+(?P<text>.*?)\s*:?\s*$"
)
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
CHECKED_RE = re.compile(r"^\s*[-*]\s*\[[xX]\]")
UNCHECKED_RE = re.compile(r"^\s*[-*]\s*\[\s*\]")
LIST_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
ISSUE_SUFFIX_RE = re.compile(r"\(#\d+\)\s*$")

NON_IMPERATIVE_ERROR = {
    "added",
    "adds",
    "adding",
    "updated",
    "updates",
    "updating",
    "fixed",
    "fixes",
    "fixing",
    "removed",
    "removes",
    "removing",
    "deleted",
    "deletes",
    "deleting",
}
PAST_TENSE_WARN = {
    "changed",
    "refactored",
    "implemented",
    "supported",
    "improved",
}
DROPS_E = {"updat", "remov", "delet", "creat", "mov", "renam", "merg"}

TEMPLATE = """\
## Description

<!-- Summarize what this PR adds or changes, upstream links, and if an AI assistant was used. -->

## Verification Evidence

<!-- Record tested RLinf version, hardware, exact commands run, and outcomes. -->

## Scope and Limitations

<!-- State what is supported and what is explicitly out of scope. -->

## Checklist

- [ ] Self-contained code, Hydra config, and `requirements.txt` (recording the tested `rlinf` release or commit)
- [ ] `README.md` and `README.zh-CN.md` with install steps, launch command, and expected metrics or behavior
- [ ] Catalog row added in root `README.md` and `README.zh-CN.md` (for new Hub entries)
- [ ] Proof that it runs: training/evaluation logs, tests, reward or success curve, or a short real-robot demo video
- [ ] Apache-2.0 license header on source files and DCO sign-off on commits (`git commit -s`)
"""


@dataclass
class Finding:
    level: str  # "ERROR" | "WARN"
    where: str  # "title" | "body"
    code: str
    message: str
    fix: str = ""


@dataclass
class Section:
    name: str
    start: int
    lines: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.text

    @property
    def text(self) -> str:
        return COMMENT_RE.sub("", "\n".join(self.lines)).strip()


def fence_mask(lines: Iterable[str]) -> tuple[list[bool], bool]:
    """Return ``(per-line in-code mask, has_unclosed_fence)`` using CommonMark rules."""
    mask: list[bool] = []
    fence = ""
    for line in lines:
        m = FENCE_RE.match(line)
        if not fence:
            if m:
                fence = m[1]
                mask.append(True)
            else:
                mask.append(False)
        elif m and m[1][0] == fence[0] and len(m[1]) >= len(fence) and not m[2].strip():
            fence = ""
            mask.append(True)
        else:
            mask.append(True)
    return mask, bool(fence)


def split_sections(body: str) -> list[Section]:
    """Split a PR body into top-level ``##`` sections (``###`` stays inside its parent)."""
    lines = body.splitlines()
    in_code, _ = fence_mask(lines)
    sections: list[Section] = []
    for i, line in enumerate(lines):
        if in_code[i]:
            if sections:
                sections[-1].lines.append(line)
            continue
        m = HEADING_RE.match(line)
        if m and len(m.group("hashes")) <= 2:
            sections.append(Section(name=m.group("text").strip(), start=i))
        elif sections:
            sections[-1].lines.append(line)
    return sections


def _matches_template_section(heading: str, canonical: str) -> bool:
    key = heading.lower().rstrip(":?").strip()
    return any(key.startswith(alias) for alias in SECTION_ALIASES[canonical])


def find_section(sections: list[Section], canonical: str) -> Section | None:
    for sec in sections:
        if _matches_template_section(sec.name, canonical):
            return sec
    return None


def fetch_pr(number: str, repo: str) -> tuple[str, str]:
    """Return ``(title, body)`` for a PR via the ``gh`` CLI."""
    out = subprocess.run(
        ["gh", "pr", "view", str(number), "--repo", repo, "--json", "title,body"],
        check=False,
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        sys.exit(f"error: gh pr view {number} failed:\n{out.stderr.strip()}")
    data = json.loads(out.stdout)
    return data["title"], (data.get("body") or "").replace("\r\n", "\n")


def imperative_of(word: str) -> str:
    stem = word.lower()
    for suffix in ("ing", "ed", "es", "s"):
        if stem.endswith(suffix):
            base = stem[: -len(suffix)]
            return base + "e" if suffix in ("ing", "ed") and base in DROPS_E else base
    return stem


def check_title(title: str) -> list[Finding]:
    out: list[Finding] = []
    if not title.strip():
        return [Finding("ERROR", "title", "title-empty", "PR title is empty.")]

    bad = NON_ASCII_RE.findall(title)
    if bad:
        out.append(
            Finding(
                "ERROR",
                "title",
                "title-non-ascii",
                f"Title contains non-ASCII characters: {''.join(sorted(set(bad)))!r}",
                "Use plain ASCII (32-126) in the PR title.",
            )
        )

    m = TITLE_RE.match(title)
    if not m:
        out.append(
            Finding(
                "ERROR",
                "title",
                "title-format",
                f"Title is not Conventional Commits: {title!r}",
                "Rewrite as `<type>(<scope>): <description>`, e.g. "
                "`feat(models): add smolvla inference adapter`.",
            )
        )
        return out

    typ, scope, desc = m.group("type"), m.group("scope"), m.group("desc")

    if typ.lower() not in ALLOWED_TYPES:
        out.append(
            Finding(
                "ERROR",
                "title",
                "title-type",
                f"Unknown type {typ!r}.",
                "Use one of: " + ", ".join(ALLOWED_TYPES) + ".",
            )
        )
    elif typ != typ.lower():
        out.append(
            Finding(
                "ERROR", "title", "title-type-case", f"Type {typ!r} must be lowercase."
            )
        )

    if scope is not None:
        if not scope.strip():
            out.append(
                Finding(
                    "ERROR",
                    "title",
                    "title-scope-empty",
                    "Empty scope `()`.",
                    "Drop the parentheses or name the category/component.",
                )
            )
        elif scope.strip().lower() in VAGUE_SCOPES:
            out.append(
                Finding(
                    "WARN",
                    "title",
                    "title-scope-vague",
                    f"Scope {scope!r} says nothing about what changed.",
                    "Name the category or component (e.g. `models`, `algorithms`, `envs`, `robots`, `skills`), or drop the scope.",
                )
            )
        elif not SCOPE_RE.match(scope):
            out.append(
                Finding(
                    "ERROR",
                    "title",
                    "title-scope-format",
                    f"Scope {scope!r} is not lowercase [a-z0-9_-].",
                    "Use lowercase letters, digits, hyphens, or underscores only.",
                )
            )

    if len(desc) > TITLE_DESC_MAX:
        out.append(
            Finding(
                "ERROR",
                "title",
                "title-desc-long",
                f"Description is {len(desc)} chars; limit is {TITLE_DESC_MAX} after `: `.",
                "State the main change concisely and move detail into Description.",
            )
        )

    if desc != desc.rstrip():
        out.append(
            Finding(
                "ERROR", "title", "title-trailing-space", "Drop the trailing space."
            )
        )
    if re.search(r":\s{2,}", title):
        out.append(
            Finding(
                "ERROR",
                "title",
                "title-colon-spacing",
                "Use exactly one space after the colon.",
            )
        )
    if "!" in desc:
        out.append(
            Finding(
                "ERROR",
                "title",
                "title-bang-position",
                "`!` may only appear immediately before the colon.",
            )
        )

    desc = desc.strip()
    if desc.endswith("."):
        out.append(
            Finding("ERROR", "title", "title-period", "Drop the trailing period.")
        )

    first = desc.split()[0] if desc.split() else ""
    if not re.match(r"^[a-z]", desc):
        out.append(
            Finding(
                "ERROR",
                "title",
                "title-capital",
                f"Description must start with a lowercase a-z, not {first!r}.",
                "Start with a lowercase imperative verb (e.g. `add ...`, `fix ...`).",
            )
        )
    if first.lower() in NON_IMPERATIVE_ERROR:
        out.append(
            Finding(
                "ERROR",
                "title",
                "title-mood",
                f"Use the imperative mood, not {first!r} (e.g. {imperative_of(first)}).",
            )
        )
    elif first.lower() in PAST_TENSE_WARN:
        out.append(
            Finding(
                "WARN",
                "title",
                "title-mood",
                f"Use the imperative mood, not {first!r} (e.g. {imperative_of(first)}).",
            )
        )
    if desc.lower().startswith(("this pr", "pr ", "a pr")):
        out.append(
            Finding(
                "WARN", "title", "title-throat-clearing", "Drop the 'this PR' preamble."
            )
        )
    if ISSUE_SUFFIX_RE.search(desc):
        out.append(
            Finding(
                "WARN",
                "title",
                "title-pr-number",
                "Drop the trailing `(#N)`; GitHub appends it on merge.",
            )
        )
    return out


def line_indent(line: str) -> int:
    return len(line) - len(line.lstrip(" \t"))


def continues_list(lines: list[str], i: int, in_code: list[bool]) -> bool:
    for j in range(i - 1, -1, -1):
        if in_code[j]:
            return False
        if not lines[j].strip():
            continue
        if LIST_RE.match(lines[j]):
            return line_indent(lines[i]) > line_indent(lines[j])
        return False
    return False


def check_tables(lines: list[str], in_code: list[bool]) -> list[Finding]:
    out: list[Finding] = []
    block: list[int] = []

    def flush(rows: list[int]) -> None:
        if len(rows) < 2:
            return
        indents = {line_indent(lines[i]) for i in rows}
        if len(indents) > 1:
            out.append(
                Finding(
                    "ERROR",
                    "body",
                    "body-table-indent",
                    f"Table at line {rows[0] + 1} mixes row indentation {sorted(indents)}.",
                    "Give every row of the table zero leading indentation.",
                )
            )
        elif indents and min(indents) >= 4:
            out.append(
                Finding(
                    "ERROR",
                    "body",
                    "body-table-indent",
                    f"Table at line {rows[0] + 1} is indented {min(indents)} spaces.",
                    "Un-indent the table so GitHub renders it as a table.",
                )
            )

    for i, line in enumerate(lines):
        if not in_code[i] and line.strip().count("|") >= 2:
            block.append(i)
        else:
            flush(block)
            block = []
    flush(block)
    return out


def check_indentation(body: str) -> list[Finding]:
    out: list[Finding] = []
    lines = body.splitlines()
    in_code, _ = fence_mask(lines)

    indented_headings = [
        i
        for i, line in enumerate(lines)
        if not in_code[i] and (m := HEADING_RE.match(line)) and m.group("indent")
    ]
    if indented_headings:
        out.append(
            Finding(
                "ERROR",
                "body",
                "body-indented-heading",
                f"{len(indented_headings)} heading(s) have leading whitespace (first at line {indented_headings[0] + 1}).",
                "Run `lint_pr.py fix` to strip leading indentation.",
            )
        )

    prose = [
        i
        for i, line in enumerate(lines)
        if not in_code[i] and line.strip() and not HEADING_RE.match(line)
    ]
    if prose:
        indented = [
            i
            for i in prose
            if line_indent(lines[i]) and not continues_list(lines, i, in_code)
        ]
        if len(indented) >= max(4, 0.3 * len(prose)):
            out.append(
                Finding(
                    "ERROR",
                    "body",
                    "body-indented",
                    f"{len(indented)}/{len(prose)} prose lines start with whitespace.",
                    "Run `lint_pr.py fix` to remove uniform paste indentation.",
                )
            )

    out.extend(check_tables(lines, in_code))
    return out


def check_body(body: str, *, docs_only: bool = False) -> list[Finding]:
    out: list[Finding] = []
    if not body.strip():
        return [
            Finding(
                "ERROR",
                "body",
                "body-empty",
                "PR body is empty.",
                "Start from `lint_pr.py template`.",
            )
        ]

    out.extend(check_indentation(body))

    lines = body.splitlines()
    in_code, unclosed = fence_mask(lines)
    if unclosed:
        out.append(
            Finding(
                "ERROR",
                "body",
                "body-fence",
                "Unbalanced fenced code block — later text is swallowed.",
            )
        )

    sections = split_sections(body)
    for name, must_fill in TEMPLATE_SECTIONS:
        sec = find_section(sections, name)
        if sec is None:
            out.append(
                Finding(
                    "ERROR" if must_fill else "WARN",
                    "body",
                    "section-missing",
                    f"Template section `## {name}` is missing.",
                    "Keep every heading from .github/PULL_REQUEST_TEMPLATE.md.",
                )
            )
            continue
        if must_fill and sec.is_empty:
            out.append(
                Finding(
                    "ERROR",
                    "body",
                    "section-empty",
                    f"Required section `## {name}` is empty.",
                    "Fill in Description and Checklist before requesting review.",
                )
            )

    # Check template section ordering
    matched_order: list[int] = []
    for sec in sections:
        for idx, (canonical, _) in enumerate(TEMPLATE_SECTIONS):
            if _matches_template_section(sec.name, canonical):
                matched_order.append(idx)
                break
    if len(matched_order) > 1 and matched_order != sorted(matched_order):
        out.append(
            Finding(
                "WARN",
                "body",
                "section-order",
                "Template sections are out of template order.",
            )
        )

    if sections:
        head = COMMENT_RE.sub("", "\n".join(lines[: sections[0].start])).strip()
        if head:
            out.append(
                Finding(
                    "WARN",
                    "body",
                    "body-preamble",
                    f"{len(head.split())} word(s) sit above the first `##` heading.",
                    "Move that text into `## Description`.",
                )
            )

    checklist = find_section(sections, "Checklist")
    if checklist is not None:
        checked = [ln for ln in checklist.lines if CHECKED_RE.match(ln)]
        boxes = checked + [ln for ln in checklist.lines if UNCHECKED_RE.match(ln)]
        if not boxes:
            out.append(
                Finding(
                    "ERROR",
                    "body",
                    "checkbox-missing",
                    "`## Checklist` has no checkboxes.",
                    "Restore the checklist from .github/PULL_REQUEST_TEMPLATE.md.",
                )
            )
        elif not checked:
            out.append(
                Finding(
                    "ERROR",
                    "body",
                    "checkbox-unticked",
                    "Nothing is ticked in `## Checklist`.",
                    "Tick every item that applies.",
                )
            )

    desc = find_section(sections, "Description")
    if desc is not None and not desc.is_empty:
        words = len(desc.text.split())
        if words > DESCRIPTION_MAX_WORDS:
            out.append(
                Finding(
                    "WARN",
                    "body",
                    "description-bloated",
                    f"`## Description` is {words} words (target <= {DESCRIPTION_MAX_WORDS}).",
                    "Summarize the key changes concisely and keep details in the project README.",
                )
            )
        bullets = [ln for ln in desc.lines if LIST_RE.match(ln)]
        if len(bullets) > 12:
            out.append(
                Finding(
                    "WARN",
                    "body",
                    "description-bullets",
                    f"{len(bullets)} bullets in `## Description`.",
                    "Group related bullets so reviewers can scan quickly.",
                )
            )

    verified = find_section(sections, "Verification Evidence")
    if verified is not None and verified.is_empty and not docs_only:
        out.append(
            Finding(
                "WARN",
                "body",
                "verification-empty",
                "`## Verification Evidence` is empty.",
                "Record the tested RLinf version, exact commands run, and outcomes.",
            )
        )

    comments = COMMENT_RE.findall(body)
    if len(comments) >= 3:
        out.append(
            Finding(
                "WARN",
                "body",
                "body-comments",
                f"{len(comments)} template `<!-- ... -->` hints remain in the body.",
                "Delete template comments once sections are filled.",
            )
        )

    wrapped = 0
    for i in range(len(lines) - 1):
        a, b = lines[i], lines[i + 1]
        if in_code[i] or in_code[i + 1]:
            continue
        if HEADING_RE.match(a) or HEADING_RE.match(b) or LIST_RE.match(b):
            continue
        if (
            a.strip()
            and b.strip()
            and 40 <= len(a.rstrip()) <= 90
            and not a.rstrip().endswith((".", ":", "|"))
        ):
            wrapped += 1
    if wrapped >= 6:
        out.append(
            Finding(
                "WARN",
                "body",
                "body-hardwrap",
                f"~{wrapped} hard-wrapped prose lines.",
                "Keep one line per paragraph; GitHub reflows automatically.",
            )
        )
    return out


def fix_body(body: str, *, unwrap: bool = False) -> str:
    """De-indent a mangled body, align headings/tables flush left, and drop HTML hints."""
    cleaned = COMMENT_RE.sub("", body.replace("\r\n", "\n"))
    lines = cleaned.splitlines()
    in_code, _ = fence_mask(lines)

    indent_issues = check_indentation(cleaned)
    if any(f.code == "body-indented" for f in indent_issues):
        positive = [
            line_indent(lines[i])
            for i in range(len(lines))
            if not in_code[i] and lines[i].strip() and line_indent(lines[i]) > 0
        ]
        offset = min(positive) if positive else 0
        if offset:
            lines = [
                line[offset:] if not in_code[i] and line[:offset].isspace() else line
                for i, line in enumerate(lines)
            ]

    in_code, _ = fence_mask(lines)
    fixed: list[str] = []
    for i, line in enumerate(lines):
        if not in_code[i] and (HEADING_RE.match(line) or line.strip().startswith("|")):
            fixed.append(line.lstrip(" \t"))
        else:
            fixed.append(line)

    if unwrap:
        in_code, _ = fence_mask(fixed)
        unwrapped: list[str] = []
        for i, line in enumerate(fixed):
            if (
                unwrapped
                and not in_code[i]
                and i > 0
                and not in_code[i - 1]
                and line.strip()
                and unwrapped[-1].strip()
                and not HEADING_RE.match(line)
                and not HEADING_RE.match(unwrapped[-1])
                and not LIST_RE.match(line)
                and not line.strip().startswith(("|", ">"))
                and not unwrapped[-1].strip().startswith(("|", ">"))
            ):
                unwrapped[-1] = unwrapped[-1].rstrip() + " " + line.strip()
            else:
                unwrapped.append(line)
        fixed = unwrapped

    # Collapse >2 blank lines
    result: list[str] = []
    blanks = 0
    for line in fixed:
        if line.strip():
            blanks = 0
            result.append(line.rstrip())
        else:
            blanks += 1
            if blanks <= 1 and result:
                result.append("")
    return "\n".join(result).strip() + "\n"


def report(findings: list[Finding], *, quiet: bool = False) -> int:
    errors = [f for f in findings if f.level == "ERROR"]
    warns = [f for f in findings if f.level == "WARN"]
    print(f"{len(errors)} error(s), {len(warns)} warning(s)")
    for f in errors + warns:
        print(f"[{f.level[0]}] {f.where}/{f.code}: {f.message}")
        if f.fix and not quiet:
            print(f"    fix: {f.fix}")
    return 1 if errors else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--repo", default="RLinf/RLinf-Hub", help="owner/name of the GitHub repo"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("template", help="print a clean PR body skeleton")

    p_lint = sub.add_parser("lint", help="check a PR or draft title/body")
    p_lint.add_argument("--pr", help="PR number to inspect via gh")
    p_lint.add_argument("--title", help="PR title to check")
    p_lint.add_argument("--body-file", help="path to Markdown file with PR body")
    p_lint.add_argument(
        "--docs-only",
        action="store_true",
        help="suppress empty Verification Evidence warning on docs-only PRs",
    )
    p_lint.add_argument("--quiet", action="store_true", help="omit fix suggestions")

    p_fix = sub.add_parser("fix", help="de-indent and clean a PR body")
    p_fix.add_argument("--pr", help="PR number to fetch via gh")
    p_fix.add_argument("--body-file", help="path to Markdown file with PR body")
    p_fix.add_argument(
        "--unwrap",
        action="store_true",
        help="join hard-wrapped paragraphs onto single lines",
    )

    args = parser.parse_args(argv)

    if args.cmd == "template":
        print(TEMPLATE, end="")
        return 0

    if args.cmd == "fix":
        if args.pr:
            _, body = fetch_pr(args.pr, args.repo)
        elif args.body_file:
            with open(args.body_file, encoding="utf-8") as fh:
                body = fh.read()
        else:
            sys.exit("error: pass --pr N or --body-file PATH")
        print(fix_body(body, unwrap=args.unwrap), end="")
        return 0

    findings: list[Finding] = []
    title = args.title
    body: str | None = None
    if args.pr:
        pr_title, pr_body = fetch_pr(args.pr, args.repo)
        if title is None:
            title = pr_title
        body = pr_body
    if args.body_file:
        with open(args.body_file, encoding="utf-8") as fh:
            body = fh.read()

    if title is None and body is None:
        sys.exit("error: pass --pr N, --title TITLE, and/or --body-file PATH")
    if title is not None:
        findings += check_title(title)
    if body is not None:
        findings += check_body(body, docs_only=args.docs_only)
    return report(findings, quiet=args.quiet)


if __name__ == "__main__":
    raise SystemExit(main())
