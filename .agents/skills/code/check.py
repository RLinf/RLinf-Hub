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

"""Check changed RLinf-Hub code: syntax, YAML, Ruff, package layout, headers, portability.

Usage::

    python3 .agents/skills/code/check.py            # files changed against main
    python3 .agents/skills/code/check.py FILE ...
"""

from __future__ import annotations

import ast
import datetime
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import route

CATEGORIES = ("algorithms", "models", "envs", "robots")
NON_PACKAGE_DIRS = frozenset(
    {"tests", "test", "scripts", "configs", "config", "examples", "assets", "docs"}
)
HEADER = re.compile(r"# Copyright (\d{4}) The RLinf Authors\.")
HARDCODED_PATH = re.compile(
    r"(?<![A-Za-z0-9_])(?:/home/[A-Za-z0-9._-]+/|/Users/[A-Za-z0-9._-]+/|[A-Za-z]:\\Users\\)"
)
CUDA_CALL = re.compile(r"\btorch\.cuda\b|\.cuda\s*\(")


def check_py_syntax(path: str, root: Path | None = None) -> list[route.Finding]:
    """Parse a Python file with ``ast.parse`` to catch syntax errors."""
    base = root or route.REPO_ROOT
    try:
        source = (base / path).read_text(encoding="utf-8")
        ast.parse(source, filename=path)
    except SyntaxError as exc:
        return [
            route.Finding(
                "critical",
                path,
                exc.lineno or 1,
                "code/syntax",
                f"Python syntax error: {exc.msg}",
            )
        ]
    return []


def check_shell_syntax(path: str, root: Path | None = None) -> list[route.Finding]:
    """Check a shell script with ``bash -n``."""
    base = root or route.REPO_ROOT
    result = subprocess.run(
        ["bash", "-n", str(base / path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return []
    msg = (result.stderr or result.stdout).strip().splitlines()[0]
    return [route.Finding("critical", path, None, "code/shell-syntax", msg)]


def check_yaml_syntax(path: str, root: Path | None = None) -> list[route.Finding]:
    """Validate YAML syntax when PyYAML is available."""
    try:
        import yaml
    except ImportError:
        return []
    base = root or route.REPO_ROOT
    try:
        list(yaml.safe_load_all((base / path).read_text(encoding="utf-8")))
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        line = mark.line + 1 if mark is not None else None
        msg = str(getattr(exc, "problem", exc)).splitlines()[0]
        return [
            route.Finding("critical", path, line, "code/yaml", f"invalid YAML: {msg}")
        ]
    return []


def check_ruff(paths: list[str], root: Path | None = None) -> list[route.Finding]:
    """Run pre-commit (if configured) or ruff lint/format on changed Python files."""
    base = root or route.REPO_ROOT
    if (base / ".pre-commit-config.yaml").is_file() and shutil.which("pre-commit"):
        result = subprocess.run(
            ["pre-commit", "run", "--files", *paths],
            cwd=base,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return []
        print(result.stdout + result.stderr)
        return [
            route.Finding(
                "major",
                ".pre-commit-config.yaml",
                None,
                "code/ruff",
                "pre-commit failed on changed files (output above)",
            )
        ]

    py_paths = [p for p in paths if p.endswith(".py")]
    if not py_paths:
        return []
    if not shutil.which("ruff"):
        print("skipped: ruff is not installed (pip install ruff)")
        return []

    findings: list[route.Finding] = []
    check_res = subprocess.run(
        ["ruff", "check", *py_paths],
        cwd=base,
        check=False,
        capture_output=True,
        text=True,
    )
    if check_res.returncode != 0:
        print(check_res.stdout + check_res.stderr)
        findings.append(
            route.Finding(
                "major",
                py_paths[0],
                None,
                "code/ruff",
                "ruff check failed on changed Python files (output above)",
            )
        )
    fmt_res = subprocess.run(
        ["ruff", "format", "--check", *py_paths],
        cwd=base,
        check=False,
        capture_output=True,
        text=True,
    )
    if fmt_res.returncode != 0:
        print(fmt_res.stdout + fmt_res.stderr)
        findings.append(
            route.Finding(
                "major",
                py_paths[0],
                None,
                "code/ruff",
                "ruff format --check failed on changed Python files (output above)",
            )
        )
    return findings


def check_header(path: str, root: Path | None = None) -> list[route.Finding]:
    """Check Apache-2.0 RLinf copyright header on a new Python file."""
    base = root or route.REPO_ROOT
    head = (base / path).read_text(encoding="utf-8").splitlines()[:5]
    years = [m[1] for line in head if (m := HEADER.match(line))]
    if not years:
        return [
            route.Finding(
                "major",
                path,
                1,
                "code/license",
                "new file without '# Copyright <year> The RLinf Authors.'; "
                "a vendored file keeps its upstream header",
            )
        ]
    year = str(datetime.date.today().year)
    if years[0] != year:
        return [
            route.Finding(
                "minor",
                path,
                1,
                "code/license",
                f"new file carries {years[0]}; use {year} unless it moved from another path",
            )
        ]
    return []


def check_init(
    changes: list[route.Change] | tuple[route.Change, ...],
    root: Path | None = None,
) -> list[route.Finding]:
    """Every package directory inside ``<category>/<project>/<pkg>/`` needs ``__init__.py``."""
    base = root or route.REPO_ROOT
    projects: set[Path] = set()
    for change in changes:
        parts = Path(change.path).parts
        if len(parts) >= 2 and parts[0] in CATEGORIES:
            proj = base / parts[0] / parts[1]
            if proj.is_dir():
                projects.add(proj)

    findings: list[route.Finding] = []
    for proj in sorted(projects):
        for entry in sorted(proj.iterdir()):
            if (
                not entry.is_dir()
                or entry.name in NON_PACKAGE_DIRS
                or entry.name.startswith(".")
                or entry.name == "__pycache__"
            ):
                continue
            for directory in sorted(
                [entry, *(p for p in entry.rglob("*") if p.is_dir())]
            ):
                if "__pycache__" in directory.parts or any(
                    part.startswith(".") for part in directory.parts
                ):
                    continue
                if (
                    any(directory.glob("*.py"))
                    and not (directory / "__init__.py").is_file()
                ):
                    findings.append(
                        route.Finding(
                            "major",
                            directory.relative_to(base).as_posix(),
                            None,
                            "code/init",
                            "has Python files but no __init__.py",
                        )
                    )
    return findings


def _is_test_or_skill(path: str) -> bool:
    parts = Path(path).parts
    return (
        parts[0] in ("tests", ".agents")
        or "tests" in parts
        or Path(path).name.startswith("test_")
    )


def check_line_rules(path: str, root: Path | None = None) -> list[route.Finding]:
    """Check added lines for hardcoded local home paths and direct CUDA calls."""
    if _is_test_or_skill(path):
        return []
    base = root or route.REPO_ROOT
    lines = (base / path).read_text(encoding="utf-8", errors="ignore").splitlines()
    findings: list[route.Finding] = []
    is_py = path.endswith(".py")
    for idx, line in enumerate(lines, 1):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        if HARDCODED_PATH.search(line):
            findings.append(
                route.Finding(
                    "major",
                    path,
                    idx,
                    "code/hardcoded-path",
                    "hardcoded local home path; take paths from Hydra config or environment variables",
                )
            )
        if is_py and CUDA_CALL.search(line):
            findings.append(
                route.Finding(
                    "minor",
                    path,
                    idx,
                    "code/cuda",
                    "direct torch.cuda/.cuda() call; prefer Worker.torch_platform or tensor.device for portability",
                )
            )
    return findings


def main() -> int:
    args = route.check_parser(__doc__.splitlines()[0]).parse_args()
    selection = route.select("code", args)
    present = [c for c in selection.changes if c.status != "D"]
    findings: list[route.Finding] = []
    yaml_skipped = False

    if present:
        findings += check_ruff([c.path for c in present])
    findings += check_init(selection.changes)

    for change in present:
        path = change.path
        if path.endswith(".py"):
            findings += check_py_syntax(path)
            if change.status == "A":
                findings += check_header(path)
        elif path.endswith(".sh"):
            findings += check_shell_syntax(path)
        elif path.endswith((".yaml", ".yml")):
            try:
                import yaml  # noqa: F401
            except ImportError:
                yaml_skipped = True
            else:
                findings += check_yaml_syntax(path)

        if path.endswith((".py", ".yaml", ".yml", ".sh")):
            findings += selection.relevant(check_line_rules(path))

    if yaml_skipped:
        print("skipped: YAML syntax check needs PyYAML (pip install pyyaml)")

    return route.report("code", findings)


if __name__ == "__main__":
    raise SystemExit(main())
