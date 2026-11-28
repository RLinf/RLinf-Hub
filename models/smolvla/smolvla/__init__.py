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

"""RLinf extension entry point for the LeRobot SmolVLA policy."""

from rlinf.config import SupportedModel
from rlinf.models import register_model

from .adapter import build_smolvla

__all__ = ["build_smolvla", "register"]


def register() -> None:
    """Register SmolVLA through both RLinf hooks in each process."""
    try:
        SupportedModel.get("smolvla")
        return
    except NotImplementedError:
        pass
    register_model("smolvla", build_smolvla, category="embodied")
    # register_model also updates the enum; keep the explicit hub hook idempotent.
    SupportedModel.register("smolvla", force=True)
