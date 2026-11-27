# <Project Name> for RLinf

[English](README.md) | [简体中文](README.zh-CN.md)

<One or two sentences stating what this integration provides, linking to the upstream paper/repo/checkpoint, and naming its scope (for example, SFT + RL training, inference-only evaluation, or simulator wrapper).>

## Supported Scope

- **RLinf version:** `<version or commit>` (for example, `rlinf[embodied]==0.3.0`)
- **Upstream:** [<upstream-name>](<upstream-url>) `<pinned version or checkpoint revision>`
- **Capabilities:** <what works today: training / evaluation / inference / robot hardware>
- **Limitations:** <what is out of scope, if any>

## Directory Layout

```text
<category>/<project_name>/
├── README.md
├── README.zh-CN.md
├── requirements.txt
├── configs/
│   └── <config>.yaml
├── <module>/
│   └── ...
└── tests/
    └── test_<project_name>.py
```

## Install

Install RLinf first using an official Docker image or from an RLinf checkout:

```bash
bash requirements/install.sh embodied --env dummy
```

Then install this project's extra dependencies from the RLinf-Hub root:

```bash
python -m pip install -r <category>/<project_name>/requirements.txt
```

<If system libraries or checkpoint downloads are needed, add one concise command block here.>

## Usage

Export the project module so RLinf registers it in the driver and every Ray worker:

```bash
export PYTHONPATH="$PWD/<category>/<project_name>${PYTHONPATH:+:$PYTHONPATH}"
export RLINF_EXT_MODULE=<module>
```

<Show the minimal Hydra config composition or launch command, and explain only the keys the user needs to set.>

## Verification and Results

Run the offline CPU contract tests from the RLinf-Hub root:

```bash
PYTHONPATH="$PWD/<category>/<project_name>" pytest -q <category>/<project_name>/tests
```

<Show optional GPU / multi-worker / real-robot verification commands, expected output, and benchmark metrics or curves. Keep CPU contract tests, GPU smoke tests, and task-level benchmarks distinct.>
