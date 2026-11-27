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

"""Offline unit tests for .agents/skills/create-pr/lint_pr.py."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / ".agents" / "skills" / "create-pr" / "lint_pr.py"


def _load_lint_pr():
    spec = importlib.util.spec_from_file_location("hub_lint_pr", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_title_checks_valid_and_invalid() -> None:
    lp = _load_lint_pr()
    assert lp.check_title("feat(models): add smolvla inference adapter") == []
    assert lp.check_title("docs: update catalog table") == []

    bad_cap = lp.check_title("feat(models): Add SmolVLA.")
    codes = {f.code for f in bad_cap}
    assert "title-capital" in codes
    assert "title-period" in codes

    bad_mood = lp.check_title("fix(envs): fixed reset leak")
    assert any(f.code == "title-mood" and f.level == "ERROR" for f in bad_mood)

    bad_len = lp.check_title("feat(models): " + "a" * 73)
    assert any(f.code == "title-desc-long" and f.level == "ERROR" for f in bad_len)

    vague = lp.check_title("feat(new): add model")
    assert any(f.code == "title-scope-vague" and f.level == "WARN" for f in vague)


def test_body_checks_template_valid_and_errors() -> None:
    lp = _load_lint_pr()

    # Raw template fails because Checklist is unticked
    tpl_findings = lp.check_body(lp.TEMPLATE)
    assert any(
        f.code == "checkbox-unticked" and f.level == "ERROR" for f in tpl_findings
    )

    valid_body = (
        "## Description\n\n"
        "Add SmolVLA inference adapter under `models/smolvla/`.\n\n"
        "## Verification Evidence\n\n"
        "Ran `pytest -q models/smolvla/tests` on CPU (8/8 passed).\n\n"
        "## Scope and Limitations\n\n"
        "Inference-only adapter; training is out of scope.\n\n"
        "## Checklist\n\n"
        "- [x] Self-contained code, Hydra config, and `requirements.txt`\n"
        "- [x] `README.md` and `README.zh-CN.md`\n"
    )
    assert lp.check_body(valid_body) == []


def test_body_fixes_uniform_indent_and_preserves_fences() -> None:
    lp = _load_lint_pr()
    mangled = (
        "  ## Description\n\n"
        "  Add adapter for SmolVLA\n"
        "  with clean registration.\n\n"
        "  ## Verification Evidence\n\n"
        "  ```bash\n"
        "  pytest -q\n"
        "  ```\n\n"
        "  ## Scope and Limitations\n\n"
        "  Inference only.\n\n"
        "  ## Checklist\n\n"
        "  - [x] Verified\n"
    )
    err_codes = {f.code for f in lp.check_body(mangled)}
    assert "body-indented-heading" in err_codes

    fixed = lp.fix_body(mangled, unwrap=True)
    assert lp.check_body(fixed) == []
    assert "Add adapter for SmolVLA with clean registration." in fixed
