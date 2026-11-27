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

"""Check RLinf-Hub component submissions: layout, requirements, registration, catalog, artifacts.

Usage::

    python3 .agents/skills/submission/check.py            # submissions changed against main
    python3 .agents/skills/submission/check.py FILE ...
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import route

CATEGORIES = ("algorithms", "models", "envs", "robots")
PROJECT_SLUG = re.compile(r"^[a-z0-9][a-z0-9_-]*$")

# Artifact rules
ARTIFACT_DIRS = frozenset({"outputs", "logs", "wandb", "checkpoints", "__pycache__"})
BINARY_EXTS = frozenset(
    {
        ".pt",
        ".pth",
        ".safetensors",
        ".ckpt",
        ".onnx",
        ".bin",
        ".h5",
        ".hdf5",
        ".pkl",
        ".pickle",
        ".whl",
        ".tar",
        ".gz",
        ".zip",
    }
)
MAX_FILE_BYTES = 5 * 1024 * 1024  # 5 MB

# Requirements rules
LOCAL_REQ = re.compile(
    r"(?:file://|(?<![A-Za-z0-9_])(?:/home/|/Users/|[A-Za-z]:\\)|\.\./)"
)
GIT_URL = re.compile(r"git\+(?:https?|ssh)://\S+")
RAY_PIN = re.compile(r"^\s*ray(?:\[[^\]]+\])?\s*(?:[=<>!~]|@|$)", re.IGNORECASE)
LOCAL_WHEEL_TAG = re.compile(r"\+(?:cu\d+|rocm[\d.]+)", re.IGNORECASE)
RLINF_REF = re.compile(r"\brlinf\b", re.IGNORECASE)

# Registration patterns
EXT_HOOK = re.compile(
    r"\b(?:def\s+register\s*\(|register_model\s*\(|SupportedModel\.register\s*\(|"
    r"register_advantage\s*\(|register_policy_loss\s*\(|register_reward\s*\(|"
    r"register_robot\s*\(|register_part\s*\(|RLINF_EXT_MODULE\b)"
)
ENV_HOOK = re.compile(
    r"\b(?:EnvWorker\b|BaseEnv\b|gymnasium\b|gym\.Env\b|def\s+register\s*\(|"
    r"def\s+main\s*\(|if\s+__name__\s*==\s*['\"]__main__['\"])"
)

# Markdown relative link pattern
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def touched_projects(
    changes: list[route.Change] | tuple[route.Change, ...],
    root: Path | None = None,
) -> list[tuple[str, str]]:
    """Return sorted ``(category, project_name)`` pairs touched by ``changes``."""
    base = root or route.REPO_ROOT
    found: set[tuple[str, str]] = set()
    for change in changes:
        parts = Path(change.path).parts
        if (
            len(parts) >= 3
            and parts[0] in CATEGORIES
            and (base / parts[0] / parts[1]).is_dir()
        ):
            found.add((parts[0], parts[1]))
    return sorted(found)


def _project_py_files(proj_dir: Path) -> list[Path]:
    """Non-test Python files inside a project directory."""
    files = []
    for path in sorted(proj_dir.rglob("*.py")):
        rel = path.relative_to(proj_dir)
        if "tests" in rel.parts or rel.name.startswith("test_"):
            continue
        files.append(path)
    return files


def check_layout(
    category: str, project: str, root: Path | None = None
) -> list[route.Finding]:
    """Check required structure of ``<category>/<project>/``."""
    base = root or route.REPO_ROOT
    rel_proj = f"{category}/{project}"
    proj_dir = base / rel_proj
    findings: list[route.Finding] = []

    if not PROJECT_SLUG.match(project):
        findings.append(
            route.Finding(
                "major",
                rel_proj,
                None,
                "submission/layout",
                f"project folder {project!r} must match lowercase [a-z0-9][a-z0-9_-]*",
            )
        )

    for required in ("README.md", "README.zh-CN.md", "requirements.txt"):
        if not (proj_dir / required).is_file():
            findings.append(
                route.Finding(
                    "major",
                    f"{rel_proj}/{required}",
                    None,
                    "submission/layout",
                    f"missing required project file {required}",
                )
            )

    configs_dir = proj_dir / "configs"
    has_yaml = configs_dir.is_dir() and any(
        p.suffix in (".yaml", ".yml") for p in configs_dir.rglob("*") if p.is_file()
    )
    if not has_yaml:
        findings.append(
            route.Finding(
                "major",
                f"{rel_proj}/configs",
                None,
                "submission/layout",
                "missing configs/ directory with at least one Hydra YAML file",
            )
        )

    if not _project_py_files(proj_dir):
        findings.append(
            route.Finding(
                "major",
                rel_proj,
                None,
                "submission/layout",
                "project has no Python module or entry script outside tests/",
            )
        )
    return findings


def check_requirements(
    category: str, project: str, root: Path | None = None
) -> list[route.Finding]:
    """Check ``requirements.txt`` for portability, git pins, core pins, and RLinf version."""
    base = root or route.REPO_ROOT
    rel = f"{category}/{project}/requirements.txt"
    req_path = base / rel
    if not req_path.is_file():
        return []

    text = req_path.read_text(encoding="utf-8", errors="ignore")
    findings: list[route.Finding] = []
    has_rlinf_ref = bool(RLINF_REF.search(text))

    for idx, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        code = line.split("#", 1)[0].strip()
        if not code:
            continue
        if LOCAL_REQ.search(code):
            findings.append(
                route.Finding(
                    "major",
                    rel,
                    idx,
                    "submission/requirements",
                    "local filesystem path in requirements.txt; use published packages or pinned git URLs",
                )
            )
        for match in GIT_URL.finditer(code):
            url = match.group(0)
            # Strip egg fragment before checking for @<rev>
            without_frag = url.split("#", 1)[0]
            after_proto = without_frag.split("://", 1)[1]
            # Require @<rev> after the repo path (not user@host)
            repo_part = after_proto.split("/", 1)[1] if "/" in after_proto else ""
            if "@" not in repo_part:
                findings.append(
                    route.Finding(
                        "major",
                        rel,
                        idx,
                        "submission/requirements",
                        "unpinned git dependency; pin a commit hash, tag, or branch with @<rev>",
                    )
                )
        if RAY_PIN.match(code):
            findings.append(
                route.Finding(
                    "major",
                    rel,
                    idx,
                    "submission/requirements",
                    "do not pin ray in project requirements.txt; use RLinf's installed Ray version",
                )
            )
        if LOCAL_WHEEL_TAG.search(code):
            findings.append(
                route.Finding(
                    "major",
                    rel,
                    idx,
                    "submission/requirements",
                    "platform-specific wheel suffix (+cu/+rocm) breaks cross-platform install; "
                    "document PyTorch/CUDA setup in README.md instead",
                )
            )

    if not has_rlinf_ref:
        readme_path = base / category / project / "README.md"
        readme_has_rlinf = readme_path.is_file() and bool(
            RLINF_REF.search(readme_path.read_text(encoding="utf-8", errors="ignore"))
        )
        findings.append(
            route.Finding(
                "minor" if readme_has_rlinf else "major",
                rel,
                1,
                "submission/requirements",
                "record the tested rlinf version or commit in a header comment "
                "(e.g. '# Tested with rlinf[embodied]==0.3.0')",
            )
        )
    return findings


def check_registration(
    category: str, project: str, root: Path | None = None
) -> list[route.Finding]:
    """Verify the project exposes an RLinf registration hook or EnvWorker/entry point."""
    base = root or route.REPO_ROOT
    rel_proj = f"{category}/{project}"
    py_files = _project_py_files(base / rel_proj)
    if not py_files:
        return []

    combined = "\n".join(
        p.read_text(encoding="utf-8", errors="ignore") for p in py_files
    )
    if category == "envs":
        if not ENV_HOOK.search(combined):
            return [
                route.Finding(
                    "major",
                    rel_proj,
                    None,
                    "submission/registration",
                    "envs project should provide a custom EnvWorker, env adapter, or launch entry script",
                )
            ]
        return []

    if not EXT_HOOK.search(combined):
        return [
            route.Finding(
                "major",
                rel_proj,
                None,
                "submission/registration",
                f"{category} project must expose an RLINF_EXT_MODULE registration entry point "
                "(def register() or RLinf register_* / SupportedModel.register hook)",
            )
        ]
    return []


def check_catalog(
    projects: list[tuple[str, str]],
    changes: list[route.Change] | tuple[route.Change, ...],
    root: Path | None = None,
) -> list[route.Finding]:
    """Check that touched projects are linked in root README.md and README.zh-CN.md."""
    base = root or route.REPO_ROOT
    findings: list[route.Finding] = []
    root_readmes = ("README.md", "README.zh-CN.md")

    for readme in root_readmes:
        readme_path = base / readme
        if not readme_path.is_file():
            continue
        content = readme_path.read_text(encoding="utf-8", errors="ignore")
        for category, project in projects:
            prefix = f"{category}/{project}"
            pattern = re.compile(rf"\(/?{re.escape(prefix)}(?:/[^)\s]*)?\)")
            if not pattern.search(content):
                findings.append(
                    route.Finding(
                        "major",
                        readme,
                        None,
                        "submission/catalog",
                        f"missing catalog row linking to {prefix}/",
                    )
                )

        # Also validate relative links inside changed root READMEs
        if any(c.path == readme and c.status != "D" for c in changes):
            for idx, line in enumerate(content.splitlines(), 1):
                if not line.lstrip().startswith("|"):
                    continue
                for match in MD_LINK.finditer(line):
                    target = match.group(1).split("#", 1)[0]
                    if not target or target.startswith(
                        ("http://", "https://", "mailto:")
                    ):
                        continue
                    if not (base / target.lstrip("/")).exists():
                        findings.append(
                            route.Finding(
                                "major",
                                readme,
                                idx,
                                "submission/catalog",
                                f"broken catalog link {target!r}",
                            )
                        )
    return findings


def check_artifacts(
    changes: list[route.Change] | tuple[route.Change, ...],
    root: Path | None = None,
) -> list[route.Finding]:
    """Reject committed checkpoints, run outputs, logs, or oversized binaries."""
    base = root or route.REPO_ROOT
    findings: list[route.Finding] = []
    for change in changes:
        if change.status == "D":
            continue
        rel = change.path
        full = base / rel
        if not full.is_file():
            continue
        parts = Path(rel).parts
        if any(part in ARTIFACT_DIRS for part in parts):
            findings.append(
                route.Finding(
                    "major",
                    rel,
                    None,
                    "submission/artifacts",
                    "committed run output or cache directory; keep logs/outputs/wandb outside git",
                )
            )
            continue
        suffix = full.suffix.lower()
        if suffix in BINARY_EXTS:
            findings.append(
                route.Finding(
                    "critical",
                    rel,
                    None,
                    "submission/artifacts",
                    f"committed binary/checkpoint file ({suffix}); host weights on Hugging Face or Releases",
                )
            )
            continue
        size = full.stat().st_size
        if size > MAX_FILE_BYTES:
            mb = size / (1024 * 1024)
            findings.append(
                route.Finding(
                    "major",
                    rel,
                    None,
                    "submission/artifacts",
                    f"file is {mb:.1f} MB (limit 5.0 MB); host large media or data outside git",
                )
            )
    return findings


def main() -> int:
    args = route.check_parser(__doc__.splitlines()[0]).parse_args()
    selection = route.select("submission", args)
    changes = selection.changes
    projects = touched_projects(changes)

    findings: list[route.Finding] = []
    findings += check_artifacts(changes)
    for category, project in projects:
        findings += check_layout(category, project)
        findings += check_requirements(category, project)
        findings += check_registration(category, project)
    findings += check_catalog(projects, changes)

    return route.report("submission", findings)


if __name__ == "__main__":
    raise SystemExit(main())
