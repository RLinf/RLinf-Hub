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

"""Offline unit tests for .agents/skills/submission/check.py."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / ".agents" / "skills"


def _load_submission_check():
    if str(SKILLS_DIR) not in sys.path:
        sys.path.insert(0, str(SKILLS_DIR))
    spec = importlib.util.spec_from_file_location(
        "hub_submission_check", SKILLS_DIR / "submission" / "check.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _make_valid_model(root: Path, name: str = "demo_vla") -> None:
    proj = root / "models" / name
    (proj / "configs").mkdir(parents=True)
    (proj / name).mkdir(parents=True)
    (proj / "README.md").write_text(
        "# Demo VLA\nTested with rlinf 0.3.0.\n", encoding="utf-8"
    )
    (proj / "README.zh-CN.md").write_text(
        "# Demo VLA\n已测试 rlinf 0.3.0。\n", encoding="utf-8"
    )
    (proj / "requirements.txt").write_text(
        "# Tested with rlinf[embodied]==0.3.0\nlerobot==0.4.4\n",
        encoding="utf-8",
    )
    (proj / "configs" / f"{name}.yaml").write_text(
        "model_type: demo_vla\n", encoding="utf-8"
    )
    (proj / name / "__init__.py").write_text(
        "def register() -> None:\n    pass\n", encoding="utf-8"
    )
    (root / "README.md").write_text(
        f"| [Demo VLA](models/{name}/) | upstream | @dev | `0.3.0` | Summary |\n",
        encoding="utf-8",
    )
    (root / "README.zh-CN.md").write_text(
        f"| [Demo VLA](models/{name}/README.zh-CN.md) | upstream | @dev | `0.3.0` | 简介 |\n",
        encoding="utf-8",
    )


def test_valid_submission_passes_all_checks(tmp_path: Path) -> None:
    check = _load_submission_check()
    route = sys.modules["route"]
    _make_valid_model(tmp_path)

    changes = [
        route.Change("M", "README.md"),
        route.Change("M", "README.zh-CN.md"),
        route.Change("A", "models/demo_vla/README.md"),
        route.Change("A", "models/demo_vla/requirements.txt"),
        route.Change("A", "models/demo_vla/demo_vla/__init__.py"),
    ]
    projects = check.touched_projects(changes, root=tmp_path)
    assert projects == [("models", "demo_vla")]
    assert check.check_layout("models", "demo_vla", root=tmp_path) == []
    assert check.check_requirements("models", "demo_vla", root=tmp_path) == []
    assert check.check_registration("models", "demo_vla", root=tmp_path) == []
    assert check.check_catalog(projects, changes, root=tmp_path) == []
    assert check.check_artifacts(changes, root=tmp_path) == []


def test_layout_and_registration_catch_missing_items(tmp_path: Path) -> None:
    check = _load_submission_check()
    proj = tmp_path / "models" / "BadName"
    (proj / "pkg").mkdir(parents=True)
    (proj / "pkg" / "model.py").write_text("class M: pass\n", encoding="utf-8")

    layout_findings = check.check_layout("models", "BadName", root=tmp_path)
    messages = "\n".join(f.message for f in layout_findings)
    assert "lowercase" in messages
    assert "README.md" in messages
    assert "README.zh-CN.md" in messages
    assert "requirements.txt" in messages
    assert "configs/" in messages

    reg_findings = check.check_registration("models", "BadName", root=tmp_path)
    assert len(reg_findings) == 1
    assert reg_findings[0].rule == "submission/registration"


def test_requirements_catches_unpinned_git_local_path_ray_and_cuda_wheel(
    tmp_path: Path,
) -> None:
    check = _load_submission_check()
    proj = tmp_path / "models" / "bad_req"
    proj.mkdir(parents=True)
    (proj / "requirements.txt").write_text(
        "ray==2.40.0\n"
        "torch==2.6.0+cu124\n"
        "git+https://github.com/org/repo.git\n"
        "pkg @ file:///home/user/pkg\n",
        encoding="utf-8",
    )
    findings = check.check_requirements("models", "bad_req", root=tmp_path)
    messages = [f.message for f in findings]
    assert any("ray" in m for m in messages)
    assert any("+cu" in m for m in messages)
    assert any("unpinned git" in m for m in messages)
    assert any("local filesystem path" in m for m in messages)
    assert any("tested rlinf version" in m for m in messages)


def test_catalog_and_artifacts_checks(tmp_path: Path) -> None:
    check = _load_submission_check()
    route = sys.modules["route"]
    _make_valid_model(tmp_path, "smolvla")

    # Break root README.zh-CN.md by dropping the catalog entry and adding a dead link
    (tmp_path / "README.zh-CN.md").write_text(
        "| [Missing](models/nonexistent/README.zh-CN.md) | — | — | — | — |\n",
        encoding="utf-8",
    )
    changes = [
        route.Change("M", "README.zh-CN.md"),
        route.Change("A", "models/smolvla/README.md"),
    ]
    cat_findings = check.check_catalog([("models", "smolvla")], changes, root=tmp_path)
    assert len(cat_findings) == 2
    assert all(f.rule == "submission/catalog" for f in cat_findings)

    # Committed checkpoint and logs
    ckpt = tmp_path / "models" / "smolvla" / "model.safetensors"
    ckpt.write_bytes(b"fake")
    log = tmp_path / "models" / "smolvla" / "outputs" / "run.log"
    log.parent.mkdir(parents=True)
    log.write_text("log", encoding="utf-8")

    art_findings = check.check_artifacts(
        [
            route.Change("A", "models/smolvla/model.safetensors"),
            route.Change("A", "models/smolvla/outputs/run.log"),
        ],
        root=tmp_path,
    )
    by_path = {f.path: f.severity for f in art_findings}
    assert by_path["models/smolvla/model.safetensors"] == "critical"
    assert by_path["models/smolvla/outputs/run.log"] == "major"


def test_catalog_enforces_path_boundary_for_shared_prefixes(tmp_path: Path) -> None:
    check = _load_submission_check()
    route = sys.modules["route"]
    _make_valid_model(tmp_path, "pi05")

    # Root READMEs list models/pi05/, not models/pi0/
    changes = [route.Change("A", "models/pi0/README.md")]
    findings = check.check_catalog([("models", "pi0")], changes, root=tmp_path)
    assert len(findings) == 2
    assert {f.path for f in findings} == {"README.md", "README.zh-CN.md"}
    assert all(f.rule == "submission/catalog" for f in findings)
