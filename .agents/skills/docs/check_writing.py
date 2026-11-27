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

"""Markdown-aware writing rules for RLinf-Hub documentation.

Checks English and Chinese prose style, CJK hard-wrapping inside paragraphs,
and required section structure on new project READMEs.
"""

from __future__ import annotations

import re
from pathlib import Path

import route

PROJECT_README = re.compile(
    r"^(?:algorithms|models|envs|robots)/[^/]+/(README(?:\.zh-CN)?\.md)$"
)
FENCE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
TABLE_SEP = re.compile(r"^\s*\|?(?:\s*:?-+:?\s*\|)+\s*:?-+:?\s*\|?\s*$")

INLINE_CODE = re.compile(r"(`+).+?\1")
MD_IMAGE = re.compile(r"!\[([^\]]*)\]\([^)]+\)")
MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
RAW_URL = re.compile(r"https?://\S+")

EN_PHRASES = re.compile(
    r"\b(simply|easily|obviously|basically|seamless(?:ly)?|powerful|robust|"
    r"comprehensive|cutting-edge|state-of-the-art|leverag(?:e|es|ed|ing)|crucial|"
    r"pivotal|delve|showcases?|empowers?|it is worth noting|please note|note that|"
    r"in order to|allows you to|enables you to|a wide range of|not just)\b",
    re.IGNORECASE,
)

HAN = r"\u4e00-\u9fff"
HAS_HAN = re.compile(f"[{HAN}]")
ZH_PATTERNS = (
    (re.compile("您"), "address the reader as 你, or omit the subject"),
    (re.compile("[「」]"), "use “” for quotes"),
    (
        re.compile("值得注意的是|需要注意的是"),
        "state the fact directly, or move it into a callout",
    ),
    (re.compile("进行"), "use the verb directly: 进行训练 → 训练"),
    (
        re.compile("当[^，。；：！？]{1,30}时"),
        "drop 当……时 where ……后 or ……时 alone reads naturally",
    ),
    (
        re.compile("(?:不是|并非)[^。！？\n]{1,40}而是"),
        "state directly what it is instead of framing it as 不是……而是……",
    ),
    (
        re.compile(f"(?<=[{HAN}\u3001-\u301f\uff01-\uff5e])[,;:!?](?=\\s|$|[{HAN}])"),
        "use full-width punctuation in a Chinese sentence",
    ),
    (
        re.compile(f"[{HAN}][A-Za-z0-9]|[A-Za-z0-9][{HAN}]"),
        "put a space between Chinese and English or digits",
    ),
)

# Section heading groups checked on new project READMEs
SECTION_GROUPS = {
    "en": (
        ("install", ("install", "setup", "prerequisites", "getting started")),
        (
            "usage",
            ("usage", "run", "launch", "register", "quick start", "config", "hydra"),
        ),
        (
            "verification",
            ("verif", "validat", "result", "benchmark", "eval", "test", "evidence"),
        ),
    ),
    "zh": (
        ("安装", ("安装", "环境", "准备")),
        ("使用/运行", ("使用", "运行", "启动", "注册", "配置", "快速开始")),
        ("验证/结果", ("验证", "结果", "评测", "评估", "测试", "基准")),
    ),
}


def strip_markdown_noise(line: str) -> str:
    """Remove inline code, link URLs, and raw URLs so prose checks stay accurate."""
    text = INLINE_CODE.sub(" ", line)
    text = MD_IMAGE.sub(r"\1", text)
    text = MD_LINK.sub(r"\1", text)
    text = RAW_URL.sub(" ", text)
    return text


def unfenced_lines(source: str) -> list[tuple[int, str]]:
    """Return ``(1-based line number, line)`` outside fenced code blocks."""
    out: list[tuple[int, str]] = []
    fence = ""
    for n, line in enumerate(source.splitlines(), 1):
        m = FENCE.match(line)
        if not fence:
            if m:
                fence = m[1]
            else:
                out.append((n, line))
        elif m and m[1][0] == fence[0] and len(m[1]) >= len(fence) and not m[2].strip():
            fence = ""
    return out


def check_project_structure(
    rel: str, lang: str, source: str, lines: list[tuple[int, str]]
) -> list[route.Finding]:
    """Check that a new project README has H1, switcher, install, usage, and verification."""
    findings: list[route.Finding] = []
    headings: list[tuple[int, str]] = []
    for _, line in lines:
        m = HEADING.match(line)
        if m:
            headings.append((len(m[1]), m[2].strip()))

    if not any(level == 1 for level, _ in headings):
        findings.append(
            route.Finding("major", rel, 1, "docs/structure", "missing H1 title heading")
        )

    other = "README.zh-CN.md" if lang == "en" else "README.md"
    if other not in source:
        findings.append(
            route.Finding(
                "minor",
                rel,
                1,
                "docs/structure",
                f"add a language switcher link to {other} near the top",
            )
        )

    h_lower = [title.lower() for level, title in headings if level >= 2]
    missing = [
        label
        for label, keywords in SECTION_GROUPS[lang]
        if not any(any(kw in title for kw in keywords) for title in h_lower)
    ]
    if missing:
        findings.append(
            route.Finding(
                "major",
                rel,
                None,
                "docs/structure",
                f"new project README is missing required section(s): {', '.join(missing)}",
            )
        )
    return findings


def check_zh_hard_wrap(rel: str, lines: list[tuple[int, str]]) -> list[route.Finding]:
    """Flag consecutive Chinese prose lines wrapped inside a paragraph or list item."""
    findings: list[route.Finding] = []
    prev_n = -1
    prev_prose = False
    prev_has_han = False

    for n, line in lines:
        stripped = line.strip()
        is_block_start = (
            not stripped
            or stripped.startswith(("#", "|", ">", "<", "---", "***", "___"))
            or bool(TABLE_SEP.match(line))
        )
        is_list_start = bool(LIST_ITEM.match(line))
        has_han = bool(HAS_HAN.search(strip_markdown_noise(stripped)))

        if (
            prev_prose
            and n == prev_n + 1
            and not is_block_start
            and not is_list_start
            and (prev_has_han or has_han)
        ):
            findings.append(
                route.Finding(
                    "minor",
                    rel,
                    n,
                    "docs/zh-hard-wrap",
                    "Chinese prose wrapped inside a paragraph or list item renders as a space "
                    "on GitHub; keep each paragraph on one line",
                )
            )

        prev_n = n
        prev_prose = not is_block_start
        prev_has_han = has_han if prev_prose else False

    return findings


def check_page(path: Path, rel: str, *, new: bool) -> list[route.Finding]:
    """Run writing, style, CJK hard-wrap, and project-structure checks on one Markdown file."""
    lang = "zh" if rel.endswith(".zh-CN.md") else "en"
    source = path.read_text(encoding="utf-8")
    lines = unfenced_lines(source)
    findings: list[route.Finding] = []

    if new and PROJECT_README.match(rel):
        findings += check_project_structure(rel, lang, source, lines)

    if lang == "zh":
        findings += check_zh_hard_wrap(rel, lines)

    for n, line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("<") or TABLE_SEP.match(line):
            continue
        plain = strip_markdown_noise(line)
        if lang == "en":
            for match in EN_PHRASES.finditer(plain):
                findings.append(
                    route.Finding(
                        "minor",
                        rel,
                        n,
                        "docs/en-style",
                        f"cut or replace {match[0]!r} (rules/english.md)",
                    )
                )
        else:
            for pattern, advice in ZH_PATTERNS:
                if pattern.search(plain):
                    findings.append(
                        route.Finding(
                            "minor",
                            rel,
                            n,
                            "docs/zh-style",
                            f"{advice} (rules/chinese.md)",
                        )
                    )
    return findings
