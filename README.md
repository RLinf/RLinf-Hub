<div align="center">
  <img src="https://github.com/RLinf/misc/raw/main/pic/logo_white.svg" alt="RLinf-logo" width="480"/>
  <h1>RLinf-Hub</h1>
  <p><b>A Community Collection of Awesome Embodied &amp; Agentic AI Works Built on <a href="https://github.com/RLinf/RLinf">RLinf</a></b></p>
</div>

<div align="center">
  <a href="https://github.com/RLinf/RLinf"><img src="https://img.shields.io/badge/Core-RLinf-blue?logo=github" alt="RLinf Core"></a>
  <a href="https://github.com/RLinf/RLinf/issues/1943"><img src="https://img.shields.io/badge/Community%20Tasks-Issue%20%231943-brightgreen?logo=github" alt="Community Tasks"></a>
  <a href="https://rlinf.readthedocs.io/en/latest/"><img src="https://img.shields.io/badge/Documentation-Purple?color=8A2BE2&logo=readthedocs" alt="Docs"></a>
  <a href="https://rlinf.org/"><img src="https://img.shields.io/badge/Website-rlinf.org-00ADEF" alt="Website"></a>
  <br>
  <a href="https://github.com/RLinf/misc/blob/main/pic/wechat.jpg?raw=true"><img src="https://img.shields.io/badge/WeChat%20Group-green?logo=wechat" alt="WeChat"></a>
  <a href="https://github.com/RLinf/misc/blob/main/pic/slack.jpg?raw=true"><img src="https://badgen.net/badge/icon/Slack%20Channel?icon=slack&label&color=4A154B&labelColor=4A154B" alt="Slack"></a>
  <a href="https://github.com/RLinf/misc/blob/main/pic/discord.jpg?raw=true"><img src="https://img.shields.io/badge/Discord%20Community-5865F2?logo=discord&logoColor=white" alt="Discord"></a>
</div>

<div align="center">

[![English](https://img.shields.io/badge/lang-English-blue.svg)](README.md)
[![简体中文](https://img.shields.io/badge/语言-简体中文-red.svg)](README.zh-CN.md)

</div>

---

**RLinf-Hub** is the official community hub for awesome **Embodied AI** and **Agentic AI** works built on [RLinf](https://github.com/RLinf/RLinf). As embodied intelligence rapidly converges with multi-turn, tool-using, and reasoning agents, RLinf-Hub collects runnable implementations, reproductions, and system integrations contributed by paper authors, robotics and agent labs, and community developers across four areas:

- **Algorithms:** RL and post-training methods for VLAs, diffusion/flow policies, humanoids, reasoning/multimodal LLMs, and multi-turn agents.
- **Models:** Vision-Language-Action (VLA) policies, World Action Models (WAMs), world models, multimodal/reasoning LLMs and VLMs, and reward/value models.
- **Simulators & Benchmarks:** GPU-parallel simulators, manipulation and humanoid benchmarks, embodied-agent suites, and GUI/coding/tool-use RL environments.
- **Real-World Robots:** Robot drivers, dexterous hands, and teleoperation interfaces.

Looking for ideas or ready-to-claim tasks? Check the **[RLinf v0.5 Community & RLinf-Hub Contribution Tasks (#1943)](https://github.com/RLinf/RLinf/issues/1943)** tracker alongside the core [RLinf v0.5 Plan (#1867)](https://github.com/RLinf/RLinf/issues/1867).

---

## Why Contribute Your Work Here?

If you are the author or owner of an embodied AI or agentic AI paper, foundation model, agent workflow, simulator, benchmark, or robot platform, contributing your integration to **RLinf-Hub** gives your work immediate reach and reproducibility:

- **Visibility across the embodied & agentic RL community:** Every accepted project is featured in this catalog with full attribution to your paper, repository, and team, and highlighted across RLinf channels (GitHub, [rlinf.org](https://rlinf.org/), release notes, WeChat, Discord, and Slack).
- **Scalable training and deployment out of the box:** Plugging into RLinf connects your work to distributed FSDP/Megatron training, SGLang/vLLM high-throughput rollout, multi-simulator execution, real-world robot pipelines, and heterogeneous accelerators without building custom distributed infrastructure.
- **Fast merge with a lightweight bar:** Integrations live in self-contained folders registered via `RLINF_EXT_MODULE` against a standard RLinf environment. You keep control of your own dependencies and code layout without refactoring core `RLinf/RLinf` internals or passing heavy core end-to-end CI.
- **Path to core RLinf:** High-impact, widely used integrations can graduate into core [RLinf/RLinf](https://github.com/RLinf/RLinf) together with the maintainers.

---

## Repository Structure

```text
RLinf-Hub/
├── algorithms/   # Community RL and post-training algorithms (embodied & agentic)
├── models/       # VLA policies, WAMs, world models, LLMs/VLMs, and reward/value models
├── envs/         # Simulators, benchmarks, and embodied/agentic RL environments
└── robots/       # Real-world robots, dexterous hands, and teleop adapters
```

Each entry is self-contained inside `<category>/<project_name>/`:

```text
<category>/<project_name>/
├── README.md          # Setup, launch command, tested RLinf version, and results
├── README.zh-CN.md    # Chinese README
├── requirements.txt   # Extra dependencies beyond `rlinf`
├── configs/           # Hydra YAML configs
└── <module>/          # Python code registered via RLINF_EXT_MODULE
```

---

## Awesome Embodied & Agentic Works on RLinf

> **Be the first to feature your work!** Open a PR adding your folder under `algorithms/`, `models/`, `envs/`, or `robots/` and add a row to the matching table below.

### Algorithms ([`algorithms/`](algorithms/))

| Work | Paper / Upstream | Contributor | RLinf Version | Summary |
|---|---|---|---|---|
| *Open for contributions* | See [Issue #1943](https://github.com/RLinf/RLinf/issues/1943) | — | — | Flow/diffusion RL, offline-to-online VLA RL, humanoid RL, agentic RL |

### Models ([`models/`](models/))

| Work | Paper / Upstream | Contributor | RLinf Version | Summary |
|---|---|---|---|---|
| [SmolVLA (450M)](models/smolvla/) | [lerobot/smolvla_base](https://huggingface.co/lerobot/smolvla_base) ([LeRobot](https://github.com/huggingface/lerobot)) | [@AsakaTigar](https://github.com/AsakaTigar) | `0.3.0` | Inference-only LeRobot SmolVLA (450M) policy adapter via `RLINF_EXT_MODULE` |

### Simulators & Benchmarks ([`envs/`](envs/))

| Work | Paper / Upstream | Contributor | RLinf Version | Summary |
|---|---|---|---|---|
| *Open for contributions* | See [Issue #1943](https://github.com/RLinf/RLinf/issues/1943) | — | — | GPU-parallel simulators, manipulation/humanoid benchmarks, embodied & agentic RL envs |

### Real-World Robots ([`robots/`](robots/))

| Work | Hardware / SDK | Contributor | RLinf Version | Summary |
|---|---|---|---|---|
| *Open for contributions* | See [Issue #1943](https://github.com/RLinf/RLinf/issues/1943) | — | — | Humanoids, bimanual/industrial arms, dexterous hands, teleop devices |

---

## How to Contribute

1. **Pick or propose a work:** Claim an open item on [RLinf/RLinf#1943](https://github.com/RLinf/RLinf/issues/1943), or comment there (or open an issue here) to introduce your own paper, model, simulator, environment, or robot.
2. **Set up RLinf:** Follow the [RLinf Installation Guide](https://rlinf.readthedocs.io/en/latest/rst_source/start/installation.html) using `requirements/install.sh` or an official RLinf Docker image. Register custom algorithms, models, or real-world robots via `RLINF_EXT_MODULE` (see the [RLinf Extending Guides](https://rlinf.readthedocs.io/en/latest/rst_source/extending/index.html)), or supply a custom `EnvWorker` / entry script for simulators and agentic environments (see [`envs/README.md`](envs/README.md)).
3. **Add your project folder:** Place all code, configs, dependency notes, `README.md`, and `README.zh-CN.md` under `algorithms/<name>/`, `models/<name>/`, `envs/<name>/`, or `robots/<name>/`, and add an entry to the catalog table in `README.md` and `README.zh-CN.md`.
4. **Open a Pull Request:** Include the minimal checklist below:
   - [ ] Self-contained code, Hydra config, and `requirements.txt` (pinning the tested `rlinf` release or commit)
   - [ ] `README.md` and `README.zh-CN.md` with install steps, launch command, and expected metrics or behavior
   - [ ] Proof that it runs: training/evaluation logs, reward or success curve, or a short real-robot demo video
   - [ ] Apache-2.0 license header on source files and DCO sign-off on commits (`git commit -s`)

---

## Links & Community

- **Core Framework:** [RLinf/RLinf](https://github.com/RLinf/RLinf)
- **Community Contribution Tasks:** [RLinf/RLinf#1943](https://github.com/RLinf/RLinf/issues/1943)
- **RLinf v0.5 Core Plan:** [RLinf/RLinf#1867](https://github.com/RLinf/RLinf/issues/1867)
- **Documentation:** [rlinf.readthedocs.io](https://rlinf.readthedocs.io/en/latest/)
- **Website & Blog:** [rlinf.org](https://rlinf.org/)
