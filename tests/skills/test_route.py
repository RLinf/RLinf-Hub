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

"""Offline unit tests for .agents/skills/route.py."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / ".agents" / "skills"


def _load_route():
    spec = importlib.util.spec_from_file_location("hub_route", SKILLS_DIR / "route.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_load_areas_discovers_all_area_skills() -> None:
    route = _load_route()
    areas = {a.name: a for a in route.load_areas()}
    assert set(areas) == {"code", "docs", "submission"}
    for area in areas.values():
        assert area.skill.is_file()
        assert area.check.is_file()


def test_area_ownership_routing() -> None:
    route = _load_route()
    areas = {a.name: a for a in route.load_areas()}

    assert areas["code"].owns("models/smolvla/smolvla/adapter.py")
    assert areas["code"].owns("models/smolvla/configs/smolvla.yaml")
    assert areas["code"].owns("tests/skills/test_route.py")
    assert not areas["code"].owns("README.md")

    assert areas["submission"].owns("models/smolvla/requirements.txt")
    assert areas["submission"].owns("algorithms/my_algo/README.md")
    assert areas["submission"].owns("README.md")
    assert not areas["submission"].owns("AGENTS.md")

    assert areas["docs"].owns("README.md")
    assert areas["docs"].owns("README.zh-CN.md")
    assert areas["docs"].owns("models/smolvla/README.zh-CN.md")
    assert not areas["docs"].owns("models/smolvla/smolvla/adapter.py")


def test_glob_regex_star_vs_doublestar() -> None:
    route = _load_route()
    single = route.glob_regex("models/*.md")
    assert single.match("models/README.md")
    assert not single.match("models/smolvla/README.md")

    deep = route.glob_regex("models/**/*.md")
    assert deep.match("models/README.md")
    assert deep.match("models/smolvla/README.md")


def test_finding_validation_and_report_exit_code(
    capsys: pytest.CaptureFixture[str],
) -> None:
    route = _load_route()
    with pytest.raises(ValueError):
        route.Finding("warn", "a.py", 1, "code/x", "bad severity")

    rc_minor = route.report(
        "demo", [route.Finding("minor", "a.py", 3, "demo/m", "nit")]
    )
    assert rc_minor == 0
    out = capsys.readouterr().out
    assert "minor a.py:3 demo/m: nit" in out
    assert "demo: 1 minor" in out

    rc_major = route.report(
        "demo", [route.Finding("major", "a.py", None, "demo/M", "blocker")]
    )
    assert rc_major == 1


def test_claude_and_gemini_symlinks_exist() -> None:
    claude_md = REPO_ROOT / "CLAUDE.md"
    assert claude_md.is_symlink()
    assert claude_md.resolve() == (REPO_ROOT / "AGENTS.md").resolve()

    claude_skills = REPO_ROOT / ".claude" / "skills"
    assert claude_skills.is_symlink()
    assert claude_skills.resolve() == SKILLS_DIR.resolve()

    gemini_settings = REPO_ROOT / ".gemini" / "settings.json"
    assert gemini_settings.is_file()
    assert "AGENTS.md" in gemini_settings.read_text(encoding="utf-8")
