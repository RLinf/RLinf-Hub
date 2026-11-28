<div align="center">
  <img src="https://github.com/RLinf/misc/raw/main/pic/logo_white.svg" alt="RLinf-logo" width="480"/>
  <h1>RLinf-Hub</h1>
  <p><b>基于 <a href="https://github.com/RLinf/RLinf">RLinf</a> 的具身智能与智能体开源作品社区集合</b></p>
</div>

<div align="center">
  <a href="https://github.com/RLinf/RLinf"><img src="https://img.shields.io/badge/核心框架-RLinf-blue?logo=github" alt="RLinf 核心框架"></a>
  <a href="https://github.com/RLinf/RLinf/issues/1943"><img src="https://img.shields.io/badge/社区任务-Issue%20%231943-brightgreen?logo=github" alt="社区任务"></a>
  <a href="https://rlinf.readthedocs.io/zh-cn/latest/"><img src="https://img.shields.io/badge/中文文档-red?logo=readthedocs" alt="中文文档"></a>
  <a href="https://rlinf.org/zh/"><img src="https://img.shields.io/badge/官网-rlinf.org-00ADEF" alt="官网"></a>
  <br>
  <a href="https://github.com/RLinf/misc/blob/main/pic/wechat.jpg?raw=true"><img src="https://img.shields.io/badge/微信交流群-green?logo=wechat" alt="微信交流群"></a>
  <a href="https://github.com/RLinf/misc/blob/main/pic/slack.jpg?raw=true"><img src="https://badgen.net/badge/icon/Slack%20%E9%A2%91%E9%81%93?icon=slack&label&color=4A154B&labelColor=4A154B" alt="Slack 频道"></a>
  <a href="https://github.com/RLinf/misc/blob/main/pic/discord.jpg?raw=true"><img src="https://img.shields.io/badge/Discord%20社区-5865F2?logo=discord&logoColor=white" alt="Discord 社区"></a>
</div>

<div align="center">

[![English](https://img.shields.io/badge/lang-English-blue.svg)](README.md)
[![简体中文](https://img.shields.io/badge/语言-简体中文-red.svg)](README.zh-CN.md)

</div>

---

**RLinf-Hub** 是 [RLinf](https://github.com/RLinf/RLinf) 官方维护的社区作品集，收录基于 RLinf 构建的优秀 **具身智能（Embodied AI）** 与 **智能体（Agentic AI）** 开源工作。随着具身智能加速与多轮推理、工具调用和自主规划智能体融合，RLinf-Hub 面向论文作者、机器人与智能体实验室及社区开发者征集可运行实现、复现方案与系统接入，覆盖四个方向：

- **算法（Algorithms）**：面向 VLA、diffusion/flow policy、人形机器人、推理与多模态大模型以及多轮智能体的强化学习与后训练算法。
- **模型（Models）**：VLA policy、世界动作模型（WAM）、世界模型、推理与多模态 LLM/VLM，以及 reward/value 模型。
- **仿真器与基准（Simulators & Benchmarks）**：GPU 并行仿真器、操作与人形基准测试、具身智能体评测套件，以及 GUI/代码/工具调用强化学习环境。
- **真机机器人（Real-World Robots）**：真机驱动、灵巧手接口与遥操作设备接入。

如果想找现成方向或认领任务，可以查看 **[RLinf v0.5 社区与 RLinf-Hub 任务列表（#1943）](https://github.com/RLinf/RLinf/issues/1943)**，以及核心维护团队负责的 [RLinf v0.5 计划（#1867）](https://github.com/RLinf/RLinf/issues/1867)。

---

## 为什么把你的工作提交到 RLinf-Hub

如果你是具身智能或智能体方向的论文作者、开源模型、Agent 工作流、仿真基准维护者，或是机器人硬件团队，将项目接入 **RLinf-Hub** 可以带来以下收益：

- **面向具身与智能体 RL 社区曝光**：所有合入项目都会展示在下方目录中，完整标注论文、上游仓库与作者团队，并通过 RLinf 社区渠道（GitHub、[rlinf.org](https://rlinf.org/zh/)、版本发布说明、微信群、Discord 与 Slack）推荐。
- **开箱获得大规模训练与部署能力**：接入 RLinf 后，用户可以直接调用分布式 FSDP/Megatron 训练、SGLang/vLLM 高吞吐 rollout、多仿真器并行执行、真机训练部署流程以及多类异构加速器，无需重复搭建分布式底层设施。
- **轻量化评审，快速合入**：每个项目独立存放在对应目录下，在标准 RLinf 环境中通过 `RLINF_EXT_MODULE` 注册接入。你可以自由管理自己的依赖与代码组织方式，无需改动 `RLinf/RLinf` 核心代码，也不必通过主仓耗时的端到端 CI。
- **向核心仓库演进的通道**：社区使用广泛、影响力突出的作品，后续可与维护团队合作合入核心仓库 [RLinf/RLinf](https://github.com/RLinf/RLinf)。

---

## 仓库目录结构

```text
RLinf-Hub/
├── algorithms/   # 社区强化学习与后训练算法（具身与智能体）
├── models/       # VLA policy、世界动作模型、世界模型、LLM/VLM 与 reward/value 模型
├── envs/         # 仿真器、评测基准与具身/智能体强化学习环境
└── robots/       # 真机机器人、灵巧手与遥操作适配
```

每个提交在 `<category>/<project_name>/` 下保持独立：

```text
<category>/<project_name>/
├── README.md          # 英文说明：安装步骤、启动命令、验证过的 RLinf 版本与运行结果
├── README.zh-CN.md    # 中文说明：安装步骤、启动命令、验证过的 RLinf 版本与运行结果
├── requirements.txt   # 除 `rlinf` 之外的额外依赖
├── configs/           # Hydra YAML 配置文件
└── <module>/          # 通过 RLINF_EXT_MODULE 注册的 Python 模块
```

---

## 优秀具身与智能体作品目录

> **欢迎提交你的工作！** 发起 PR 将代码放到 `algorithms/`、`models/`、`envs/` 或 `robots/` 对应目录，并在下表补上一行索引即可。

### 算法（[`algorithms/`](algorithms/)）

| 作品 | 论文 / 上游仓库 | 贡献者 | RLinf 版本 | 简介 |
|---|---|---|---|---|
| *欢迎贡献* | 见 [Issue #1943](https://github.com/RLinf/RLinf/issues/1943) | — | — | Flow/diffusion RL、离线到在线 VLA RL、人形控制 RL、agentic RL |

### 模型（[`models/`](models/)）

| 作品 | 论文 / 上游仓库 | 贡献者 | RLinf 版本 | 简介 |
|---|---|---|---|---|
| [SmolVLA (450M)](models/smolvla/README.zh-CN.md) | [lerobot/smolvla_base](https://huggingface.co/lerobot/smolvla_base)（[LeRobot](https://github.com/huggingface/lerobot)） | [@AsakaTigar](https://github.com/AsakaTigar) | `0.3.0` | 基于 `RLINF_EXT_MODULE` 接入的上游 LeRobot SmolVLA (450M) 推理适配器 |

### 仿真器与基准（[`envs/`](envs/)）

| 作品 | 论文 / 上游仓库 | 贡献者 | RLinf 版本 | 简介 |
|---|---|---|---|---|
| *欢迎贡献* | 见 [Issue #1943](https://github.com/RLinf/RLinf/issues/1943) | — | — | GPU 并行仿真器、操作与人形基准、具身与智能体 RL 环境 |

### 真机机器人（[`robots/`](robots/)）

| 作品 | 硬件 / SDK | 贡献者 | RLinf 版本 | 简介 |
|---|---|---|---|---|
| *欢迎贡献* | 见 [Issue #1943](https://github.com/RLinf/RLinf/issues/1943) | — | — | 人形机器人、双臂与工业机械臂、灵巧手、遥操作设备 |

---

## 如何贡献

1. **认领任务或提交自有工作**：在 [RLinf/RLinf#1943](https://github.com/RLinf/RLinf/issues/1943) 留言认领任务，或直接在该 issue（或本仓库新建 issue）介绍你要接入的论文、模型、仿真器、环境或机器人。
2. **准备 RLinf 环境**：按 [RLinf 安装文档](https://rlinf.readthedocs.io/zh-cn/latest/rst_source/start/installation.html) 使用 `requirements/install.sh` 或官方 Docker 镜像搭建环境。自定义算法、模型和真机机器人通过 `RLINF_EXT_MODULE` 注册（写法见 [RLinf 扩展指南](https://rlinf.readthedocs.io/zh-cn/latest/rst_source/extending/index.html)），仿真器与智能体环境可提供自定义 `EnvWorker` 或启动脚本（见 [`envs/README.zh-CN.md`](envs/README.zh-CN.md)）。
3. **整理独立目录**：将代码、配置、依赖说明、`README.md` 与 `README.zh-CN.md` 放入 `algorithms/<name>/`、`models/<name>/`、`envs/<name>/` 或 `robots/<name>/`，并在根目录 `README.md` 和 `README.zh-CN.md` 的对应目录表中添加一条记录。
4. **提交 Pull Request**：合入前请确认满足以下最简清单：
   - [ ] 独立完整的代码、Hydra 配置文件与 `requirements.txt`（注明验证过的 `rlinf` 版本或 commit）
   - [ ] 包含安装步骤、启动命令和预期结果的 `README.md` 与 `README.zh-CN.md`
   - [ ] 可复现验证材料：训练/评测日志、reward 或成功率曲线，或真机演示短视频
   - [ ] 源码文件带 Apache-2.0 协议头，commit 带 DCO 签名（`git commit -s`）

---

## 相关链接

- **核心框架**：[RLinf/RLinf](https://github.com/RLinf/RLinf)
- **社区任务列表**：[RLinf/RLinf#1943](https://github.com/RLinf/RLinf/issues/1943)
- **RLinf v0.5 核心计划**：[RLinf/RLinf#1867](https://github.com/RLinf/RLinf/issues/1867)
- **中文文档**：[rlinf.readthedocs.io/zh-cn](https://rlinf.readthedocs.io/zh-cn/latest/)
- **官网与博客**：[rlinf.org/zh](https://rlinf.org/zh/)
