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

"""Offline unit tests for .agents/skills/review-pr/lint_review.py."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / ".agents" / "skills" / "review-pr" / "lint_review.py"


def _load_lint_review():
    spec = importlib.util.spec_from_file_location("hub_lint_review", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_valid_review_payload_passes() -> None:
    lr = _load_lint_review()
    payload = {
        "event": "COMMENT",
        "body": (
            "**Changes requested** · 1 major, 0 minor · head `abc1234` · base `main@02ebcea`\n\n"
            "Fix the broken registration hook before merge.\n\n"
            "### Reproduction\n\n"
            "- Result: **Not run** — no GPU with RLinf 0.3.0 available on this host.\n"
            "- Setup: requires 1x NVIDIA GPU with `rlinf[embodied]==0.3.0`.\n\n"
            "### Findings\n\n"
            "| ID | Severity | Category | Location | Summary | Status | Posted |\n"
            "|---|---|---|---|---|---|---|\n"
            "| F1 | major | correctness | `models/demo/demo/adapter.py:12` | Missing register hook | confirmed | inline |\n"
            "| F2 | major | docs | `README.zh-CN.md` | Missing catalog row | confirmed | here |\n\n"
            "#### F2 · major · docs: missing Chinese catalog row\n\n"
            "Root `README.zh-CN.md` omits the new `models/demo/` row, so Chinese readers cannot discover the integration.\n\n"
            "Suggested fix: add the matching row under the Models table in `README.zh-CN.md`.\n\n"
            "Evidence: `submission/catalog` flagged missing `models/demo` link in `README.zh-CN.md`.\n"
        ),
        "comments": [
            {
                "path": "models/demo/demo/adapter.py",
                "line": 12,
                "body": (
                    "**F1 · major · correctness: missing register hook**\n\n"
                    "Ray workers load `RLINF_EXT_MODULE` and invoke `register()`, which is not defined here.\n\n"
                    "Suggested fix: export an idempotent `register()` function in `demo/__init__.py`.\n\n"
                    "Evidence: `submission/registration` found no `register()` or `register_model` call.\n"
                ),
            }
        ],
    }
    findings = lr.ReviewLinter(payload, None).run()
    assert findings == []


def test_re_review_thread_row_passes_without_section_or_comment() -> None:
    lr = _load_lint_review()
    payload = {
        "event": "COMMENT",
        "body": (
            "**Changes requested** · 1 major · head `def5678` · base `main@02ebcea`\n\n"
            "F1 remains open; earlier F2 is fixed.\n\n"
            "### Reproduction\n\n"
            "- Result: **Passed** — offline CPU tests passed (8/8).\n"
            "- Setup: CPU, `pytest -q models/demo/tests`.\n\n"
            "### Findings\n\n"
            "| ID | Severity | Category | Location | Summary | Status | Posted |\n"
            "|---|---|---|---|---|---|---|\n"
            "| F1 | major | docs-style | `models/demo/README.zh-CN.md:10` | CJK hard-wrapping still present | confirmed | thread |\n"
        ),
        "comments": [],
    }
    findings = lr.ReviewLinter(payload, None).run()
    assert findings == []


def test_invalid_payload_and_mismatched_inline_caught() -> None:
    lr = _load_lint_review()
    assert lr.ReviewLinter(["not", "a", "dict"], None).run()

    bad = {
        "event": "COMMENT",
        "body": (
            "**Ready for senior review** · no findings\n\n"
            "Looks good.\n\n"
            "### Reproduction\n\n"
            "- Result: **Not run** — docs-only PR.\n"
            "- Setup: `route.py check`.\n\n"
            "### Findings\n\n"
            "| ID | Severity | Category | Location | Summary | Status | Posted |\n"
            "|---|---|---|---|---|---|---|\n"
            "| F1 | minor | style | `models/demo/a.py:5` | Nit | confirmed | inline |\n"
        ),
        "comments": [],
    }
    findings = lr.ReviewLinter(bad, None).run()
    assert any(
        f.level == "ERROR" and "no inline comment sits there" in f.message
        for f in findings
    )
