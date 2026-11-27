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

"""Offline unit tests for .agents/skills/code/check.py."""

from __future__ import annotations

import datetime
import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / ".agents" / "skills"


def _load_code_check():
    if str(SKILLS_DIR) not in sys.path:
        sys.path.insert(0, str(SKILLS_DIR))
    spec = importlib.util.spec_from_file_location(
        "hub_code_check", SKILLS_DIR / "code" / "check.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_syntax_and_header_checks(tmp_path: Path) -> None:
    check = _load_code_check()
    year = datetime.date.today().year

    good = tmp_path / "good.py"
    good.write_text(f"# Copyright {year} The RLinf Authors.\nx = 1\n", encoding="utf-8")
    assert check.check_py_syntax("good.py", root=tmp_path) == []
    assert check.check_header("good.py", root=tmp_path) == []

    bad_syn = tmp_path / "bad.py"
    bad_syn.write_text("def broken(:\n", encoding="utf-8")
    findings = check.check_py_syntax("bad.py", root=tmp_path)
    assert len(findings) == 1
    assert findings[0].severity == "critical"
    assert findings[0].rule == "code/syntax"

    no_hdr = tmp_path / "no_hdr.py"
    no_hdr.write_text("x = 1\n", encoding="utf-8")
    hdr_findings = check.check_header("no_hdr.py", root=tmp_path)
    assert len(hdr_findings) == 1
    assert hdr_findings[0].severity == "major"
    assert hdr_findings[0].rule == "code/license"

    old_hdr = tmp_path / "old_hdr.py"
    old_hdr.write_text("# Copyright 2020 The RLinf Authors.\nx = 1\n", encoding="utf-8")
    old_findings = check.check_header("old_hdr.py", root=tmp_path)
    assert len(old_findings) == 1
    assert old_findings[0].severity == "minor"


def test_init_check_catches_missing_package_init_only(tmp_path: Path) -> None:
    check = _load_code_check()
    route = sys.modules["route"]

    pkg = tmp_path / "models" / "demo" / "demo"
    pkg.mkdir(parents=True)
    (pkg / "adapter.py").write_text("x = 1\n", encoding="utf-8")

    # tests/ is exempt from __init__.py requirement
    tests_dir = tmp_path / "models" / "demo" / "tests"
    tests_dir.mkdir(parents=True)
    (tests_dir / "test_demo.py").write_text("def test_ok(): pass\n", encoding="utf-8")

    changes = [route.Change("A", "models/demo/demo/adapter.py")]
    findings = check.check_init(changes, root=tmp_path)
    assert len(findings) == 1
    assert findings[0].path == "models/demo/demo"
    assert findings[0].rule == "code/init"

    (pkg / "__init__.py").write_text("", encoding="utf-8")
    assert check.check_init(changes, root=tmp_path) == []


def test_line_rules_catch_hardcoded_paths_and_cuda(tmp_path: Path) -> None:
    check = _load_code_check()

    adapter = tmp_path / "models" / "demo" / "demo" / "adapter.py"
    adapter.parent.mkdir(parents=True)
    adapter.write_text(
        "# /home/alice/comment_ignored.pt\n"
        'CKPT = "/home/alice/weights.pt"\n'
        "x = x.cuda()\n",
        encoding="utf-8",
    )
    findings = check.check_line_rules("models/demo/demo/adapter.py", root=tmp_path)
    rules = {(f.line, f.rule, f.severity) for f in findings}
    assert (2, "code/hardcoded-path", "major") in rules
    assert (3, "code/cuda", "minor") in rules

    # Test files are excluded from hardcoded-path and cuda line heuristics
    test_file = tmp_path / "models" / "demo" / "tests" / "test_demo.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text(
        'p = "/home/alice/x"\ny = torch.cuda.is_available()\n', encoding="utf-8"
    )
    assert check.check_line_rules("models/demo/tests/test_demo.py", root=tmp_path) == []


def test_shell_and_yaml_syntax_checks(tmp_path: Path) -> None:
    check = _load_code_check()

    bad_sh = tmp_path / "bad.sh"
    bad_sh.write_text("if true; then\n  echo hi\n", encoding="utf-8")
    sh_findings = check.check_shell_syntax("bad.sh", root=tmp_path)
    assert len(sh_findings) == 1
    assert sh_findings[0].rule == "code/shell-syntax"

    good_sh = tmp_path / "good.sh"
    good_sh.write_text("#!/usr/bin/env bash\necho ok\n", encoding="utf-8")
    assert check.check_shell_syntax("good.sh", root=tmp_path) == []

    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("a: [1, 2\n", encoding="utf-8")
    try:
        import yaml  # noqa: F401
    except ImportError:
        assert check.check_yaml_syntax("bad.yaml", root=tmp_path) == []
    else:
        y_findings = check.check_yaml_syntax("bad.yaml", root=tmp_path)
        assert len(y_findings) == 1
        assert y_findings[0].rule == "code/yaml"
