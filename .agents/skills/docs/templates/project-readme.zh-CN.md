# <项目名称>（RLinf 接入）

[English](README.md) | [简体中文](README.zh-CN.md)

<用一两句自然中文说明本目录接入的内容、上游论文或仓库链接，以及当前支持范围（如训练与评测、仅推理评估或仿真环境封装）。>

## 支持范围

- **RLinf 版本**：`<版本或 commit>`（例如 `rlinf[embodied]==0.3.0`）
- **上游依赖**：[<上游名称>](<上游链接>) `<锁定版本或权重 revision>`
- **支持能力**：<当前支持的功能：训练 / 评测 / 推理 / 真机控制>
- **使用限制**：<尚未支持的能力或硬件前提>

## 目录结构

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

## 安装

先通过官方 Docker 镜像或在 RLinf 仓库中安装基础环境：

```bash
bash requirements/install.sh embodied --env dummy
```

随后在 RLinf-Hub 根目录安装本项目额外依赖：

```bash
python -m pip install -r <category>/<project_name>/requirements.txt
```

<如需安装系统库或下载权重，在此补充简洁的命令块。>

## 使用方式

在 RLinf-Hub 根目录设置环境变量，使驱动进程和每个 Ray worker 自动注册本模块：

```bash
export PYTHONPATH="$PWD/<category>/<project_name>${PYTHONPATH:+:$PYTHONPATH}"
export RLINF_EXT_MODULE=<module>
```

<给出最简 Hydra 配置组合或启动命令，并只说明用户需要修改的关键配置项。>

## 验证与结果

在 RLinf-Hub 根目录运行离线 CPU 契约测试：

```bash
PYTHONPATH="$PWD/<category>/<project_name>" pytest -q <category>/<project_name>/tests
```

<按需补充 GPU 冒烟测试、多 worker 或真机验证命令、预期输出以及评测指标或曲线。请明确区分 CPU 契约测试、GPU 冒烟测试与任务级基准结果。>
