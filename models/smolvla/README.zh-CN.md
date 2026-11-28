# 面向 RLinf 的 SmolVLA (450M)

[English](README.md) | [简体中文](README.zh-CN.md)

这是面向官方 [`lerobot/smolvla_base`](https://huggingface.co/lerobot/smolvla_base) checkpoint 的自包含 RLinf-Hub 适配器，仅用于推理。适配器直接调用上游 LeRobot 实现，不复制模型代码，也不修改 RLinf。训练、actor replay 和 PPO/GRPO logprob 尚未实现，相关路径会抛出 `NotImplementedError`。

## 支持范围

- RLinf `0.3.0`，启用 `embodied` extra（tag `v0.3`，commit `0505431899574619da86f551bad70b71e0ea2177`；PyPI 0.3.0 sdist 与该 tag 一致）。
- LeRobot `0.4.4`，启用 `smolvla` extra，搭配 Transformers `4.57.1`。
- 已在 CUDA 12.8 构建的 Torch `2.10.0` 与 TorchVision `0.25.0` 上验证。
- Checkpoint revision 为 `5e8d12a6e2975b0e5e5fce7c8caf47c371d257b6`。
- 适配器只移除 checkpoint 中的 `type` 注册标记，供 LeRobot 0.4.4 解析配置，模型字段与权重不变。
- 输入为三路 `observation.images.camera*`、6 维 state；输出为长度 50 的 6 维 action chunk。
- `precision=fp32` 使用 FP32；`precision=fp16` 启用 FP16 autocast；`precision=bf16` 启用 BF16 autocast。三种模式都保留 FP32 模型参数，并返回 CPU FP32 动作。
- `model_path` 可以是 Hugging Face repo ID，也可以是本地 checkpoint 目录。

## 目录结构

```text
models/smolvla/
├── README.md
├── README.zh-CN.md
├── requirements.txt
├── configs/
│   └── smolvla.yaml
├── smolvla/
│   ├── __init__.py
│   └── adapter.py
└── tests/
    ├── test_smolvla.py
    └── ray_smoke.py
```

## 安装

### 1. 安装 RLinf 0.3.0

在 RLinf 源码目录中安装 embodied 环境：

```bash
cd /path/to/RLinf
git checkout 0505431899574619da86f551bad70b71e0ea2177  # v0.3
bash requirements/install.sh embodied --env dummy
source .venv/bin/activate
```

安装脚本只在自身进程中激活虚拟环境，因此安装完成后还要在当前 shell 执行 `source .venv/bin/activate`。如果使用官方 RLinf Docker 镜像，则直接使用容器内已激活的环境。

### 2. 回到 RLinf-Hub 根目录安装模型依赖

```bash
cd /path/to/RLinf-Hub
export PYTHONPATH="$PWD/models/smolvla${PYTHONPATH:+:$PYTHONPATH}"
uv pip install -r models/smolvla/requirements.txt
```

`requirements.txt` 只包含 RLinf 之外的依赖，文件头记录了验证过的 RLinf 版本。这里刻意不使用 LeRobot `0.7.0`：它的 SmolVLA extra 需要 Transformers 5.x，而 RLinf `0.3.0[embodied]` 将 Transformers 限制在 `4.57.6`。锁定文件使用 `datasets==4.8.0`，因为 `datasets 5.2` 需要 Hugging Face Hub 1.x，与 Transformers 4.57 的 `<1.0` 要求冲突；`torchcodec==0.10.0` 满足 LeRobot 0.4.4 的 `<0.11.0` 上限。

极简 Linux 镜像还需要系统 FFmpeg 共享库。如果导入 LeRobot 时提示缺少 `libavcodec` 或 `libavformat`，请安装 FFmpeg，例如执行 `apt-get install -y ffmpeg`。

适配器会在首次使用时下载固定 revision 的 checkpoint。也可以用已安装的 `huggingface-hub` 提前下载：

```bash
python -c "from huggingface_hub import snapshot_download; snapshot_download('lerobot/smolvla_base', revision='5e8d12a6e2975b0e5e5fce7c8caf47c371d257b6')"
```

### 本地 checkpoint

将 `model_path` 指向同时包含 `config.json` 和 `model.safetensors` 的本地目录即可。适配器会直接读取本地配置，并把同一目录传给 `SmolVLAPolicy.from_pretrained`；`model_revision` 仍保留在调用中，但 LeRobot 加载本地目录时会忽略它。如果路径是已存在但没有 `config.json` 的目录，适配器会抛出 `FileNotFoundError`，而不会把该目录误判为 Hugging Face repo ID；非目录路径仍走原来的 Hugging Face repo ID 下载逻辑。

## 向 RLinf 注册

在 Hub 根目录执行：

```bash
export PYTHONPATH="$PWD/models/smolvla${PYTHONPATH:+:$PYTHONPATH}"
export RLINF_EXT_MODULE=smolvla
python -c "from smolvla import register; register(); print('smolvla registered')"
```

`RLINF_EXT_MODULE` 会在每个 Ray worker 中自动注册。外部驱动脚本在调用 `validate_cfg()` 前也需要先注册：

```python
from smolvla import register

register()
cfg = validate_cfg(cfg)
```

## Hydra 模型片段

`models/smolvla/configs/smolvla.yaml` 是模型组片段。构建完整 RLinf recipe 时，将配置目录加入 Hydra search path，并在 actor 与 rollout 两侧 include：

```yaml
hydra:
  searchpath:
    - file://${oc.env:SMOLVLA_CONFIG_DIR}
```

```bash
export SMOLVLA_CONFIG_DIR="$PWD/models/smolvla/configs"
```

```yaml
defaults:
  - smolvla@actor.model
  - smolvla@rollout.model
```

片段使用 `num_action_chunks: 50`，因为适配器返回完整的 `predict_action_chunk()` 结果；它不调用 `select_action()`，也不维护第二条 action 队列。

## 输入与归一化

| RLinf 输入 | Shape | LeRobot 目标 |
|---|---|---|
| `main_images` | `[B,H,W,C]` 或 `[B,1,H,W,C]` | `observation.images.camera1` |
| `extra_view_images` | `[B,2,H,W,C]` 或两个 `[B,H,W,C]` 张量 | `observation.images.camera2`、`camera3` |
| `states` | `[B,6]` | `observation.state` |
| `task_descriptions` | 长度为 `B` 的 `list[str]` | `task` |

整数图像会除以 255，浮点图像按已归一化到 `[0,1]` 处理；HWC 输入会转换为 CHW。上游 processor 负责 tokenization、图像归一化和可选的 state/action 归一化。由于 RLinf 观测已经带 batch 维，适配器会移除 LeRobot 的自动 add-batch 步骤。

适配器根据 checkpoint 配置重建 processor，而不是加载 base checkpoint 中过期的已保存 pipeline。base checkpoint 只包含含义不明确的旧版逐机器人 action 统计量，因此 `stats_path: null` 使用单位 mean/std，仅用于 shape 冒烟测试。若需要具有物理意义的 action 值，请把 `stats_path` 指向使用当前 feature key 的 JSON 文件：

```json
{
  "observation.state": {"mean": [0, 0, 0, 0, 0, 0], "std": [1, 1, 1, 1, 1, 1]},
  "action": {"mean": [0, 0, 0, 0, 0, 0], "std": [1, 1, 1, 1, 1, 1]}
}
```

## 验证

以下命令均在 RLinf-Hub 根目录执行。CPU 契约测试不下载权重；更新后的测试套件预期为 `13 passed, 5 deselected`。

```bash
PYTHONPATH="$PWD/models/smolvla${PYTHONPATH:+:$PYTHONPATH}" \
  python -m pytest -q models/smolvla/tests/test_smolvla.py -k 'not gpu and not network'
```

解析真实 Hugging Face repo ID 与两个 checkpoint 文件：

```bash
PYTHONPATH="$PWD/models/smolvla${PYTHONPATH:+:$PYTHONPATH}" \
SMOLVLA_NETWORK_SMOKE=1 \
  python -m pytest -q models/smolvla/tests/test_smolvla.py -k 'network_remote_checkpoint'
```

真实 checkpoint 的 GPU 冒烟测试。第一条命令通过本地 checkpoint 目录加载同一份官方权重，其余三条使用远程 repo ID：

```bash
PYTHONPATH="$PWD/models/smolvla${PYTHONPATH:+:$PYTHONPATH}" \
CUDA_VISIBLE_DEVICES=0 SMOLVLA_GPU_SMOKE=1 \
  python -m pytest -q --log-cli-level=INFO models/smolvla/tests/test_smolvla.py -k 'gpu_local_checkpoint'

PYTHONPATH="$PWD/models/smolvla${PYTHONPATH:+:$PYTHONPATH}" \
CUDA_VISIBLE_DEVICES=0 SMOLVLA_GPU_SMOKE=1 \
  python -m pytest -q --log-cli-level=INFO models/smolvla/tests/test_smolvla.py -k 'gpu_checkpoint_smoke and fp32'

PYTHONPATH="$PWD/models/smolvla${PYTHONPATH:+:$PYTHONPATH}" \
CUDA_VISIBLE_DEVICES=0 SMOLVLA_GPU_SMOKE=1 \
  python -m pytest -q --log-cli-level=INFO models/smolvla/tests/test_smolvla.py -k 'gpu_checkpoint_smoke and fp16'

PYTHONPATH="$PWD/models/smolvla${PYTHONPATH:+:$PYTHONPATH}" \
CUDA_VISIBLE_DEVICES=0 SMOLVLA_GPU_SMOKE=1 \
  python -m pytest -q --log-cli-level=INFO models/smolvla/tests/test_smolvla.py -k 'gpu_checkpoint_smoke and bf16'
```

每个 GPU 测试都会返回一个有限的 CPU FP32 `[1, 50, 6]` 张量，并记录 checkpoint 来源、延迟、GPU 名称和峰值 CUDA 显存。

Ray 双 worker 注册与推理冒烟测试需要两张可见且支持 BF16 的 GPU：

```bash
PYTHONPATH="$PWD/models/smolvla${PYTHONPATH:+:$PYTHONPATH}" \
RLINF_EXT_MODULE=smolvla CUDA_VISIBLE_DEVICES=0,1 \
  python models/smolvla/tests/ray_smoke.py
```

预期输出为每个 worker 一条 JSON 记录，最后打印 `RAY_SMOKE_OK`。只有一张 GPU 时，可改为 `SMOLVLA_RAY_WORKERS=1 CUDA_VISIBLE_DEVICES=0`。脚本沿用当前 shell 的 Hugging Face 缓存和网络配置；如有需要，可设置 `HF_HOME` 或 `HF_ENDPOINT`。

## 验证结果

### Linux A100 主结果

验证环境为 Ubuntu 26.04.1 LTS、2× NVIDIA A100-SXM4-80GB（驱动 595.99.02，功耗上限 400 W）、Python 3.12.16、PyTorch 2.10.0+cu128（CUDA 12.8）、Ray 2.60.1、RLinf 0.3.0（tag `v0.3`，commit `0505431899574619da86f551bad70b71e0ea2177`）、LeRobot 0.4.4、Transformers 4.57.1 与 torchcodec 0.10.0。Checkpoint 大小为 906,712,520 字节，SHA256 为 `7cd549ac2351fb069c0ddb3c34ad2d09cfc92b56a15dccdfc2e41467aaca01eb`，revision 为 `5e8d12a6e2975b0e5e5fce7c8caf47c371d257b6`，加载耗时 32.0 秒。

基线 `e41c39a` 套件为 11/11 通过，耗时 112.77 秒，其中包含 8 项 CPU 契约测试和 3 项真实 checkpoint GPU 测试；这些数字仅作为历史基线证据保留。

F1–F6 补丁已在这台 A100 上重新验证：

- CPU 契约套件：**13 passed, 5 deselected**，耗时 27.13 秒。
- 真实 Hugging Face repo ID 解析：**1 passed**，耗时 5.64 秒。
- 真实 checkpoint GPU 套件：**4 passed**，耗时 114.35 秒——包含一次本地目录 FP32 加载，以及远程 FP32/FP16/BF16 加载；全部返回有限的 CPU FP32 `[1, 50, 6]` 动作。
- Ray 双 worker：两个 worker 仅通过 `RLINF_EXT_MODULE=smolvla` 自动注册，加载官方 checkpoint，执行 BF16 autocast 前向，并返回有限的 `[1, 50, 6]` 动作，单次耗时分别为 281.12 ms 和 275.99 ms；驱动进程以 `RAY_SMOKE_OK` 和退出码 0 结束。
- Ruff check 与 Ruff format check 均通过。

已安装 RLinf Python 树哈希
`ab9d8de97599ea82de91e0e70d39b49079b517bdbb10cafac69833fc8ec15a2d` 与 tag
`v0.3`（`0505431899574619da86f551bad70b71e0ea2177`）完全一致；PyPI 0.3.0
sdist 包含相同的 583 个 Python 文件。

### A100 稳态延迟（基线 e41c39a）

Batch size 为 1。每种精度执行三轮，每轮两次 warmup 加 30 次正式调用，共 90 个正式样本。计时覆盖完整的 `adapter.predict_action_batch`，包括预处理、tokenization、flow-matching 推理和后处理；每次正式调用前后都执行 `torch.cuda.synchronize()`，计时期间不调用 `empty_cache()`。测试前 GPU 为 P0、34.53 W，测试后为 P0、50.11 W、利用率 32%。

| 精度 | 首次 forward | P50 | P95 | 均值 | 标准差 | 最小值 | 最大值 |
|---|---:|---:|---:|---:|---:|---:|---:|
| FP32 | 946.82 | 251.80 | 261.82 | 253.49 | 5.85 | 248.71 | 297.88 |
| FP16 autocast | 3,995.21 | 275.47 | 285.15 | 276.39 | 4.61 | 270.67 | 295.17 |
| BF16 autocast | 294.11 | 269.32 | 278.06 | 270.54 | 3.91 | 265.68 | 284.41 |

表中单位为毫秒。每次切换精度后的首次调用单独列出，不计入稳态统计。

### Windows RTX 5070 Ti 跨平台补充

F1–F6 补丁也在 Windows 11（Python 3.12.16、Torch 2.10.0+cu128、RTX 5070 Ti sm_120、驱动 621.14、功耗上限 300 W）上通过了 13 项 CPU、1 项真实远程解析与 4 项真实 checkpoint GPU 测试。补丁未重新测量延迟。下表属于基线 `e41c39a` 证据：11/11 测试通过，模型加载耗时 45.4 秒，使用相同的 90 样本协议得到以下共享桌面数据：

| 精度 | P50 | P95 | 均值 | 标准差 | 最小值 | 最大值 |
|---|---:|---:|---:|---:|---:|---:|
| FP32 | 525.33 | 6,329.80 | 1,553.76 | 4,019.25 | 481.26 | 25,322.57 |
| FP16 autocast | 657.75 | 680.02 | 722.40 | 433.60 | 616.39 | 4,220.54 |
| BF16 autocast | 648.54 | 668.99 | 648.24 | 15.85 | 582.13 | 686.48 |

各轮 P50 稳定。共享桌面上的 FP32 与 FP16 存在长尾离群点，数据予以保留而非剔除。这些是初步端到端测量，不是受控基准，也不宣称 FP16/BF16 已经带来加速。

### 权重存储、计算与输出 dtype

精度开关只启用 CUDA autocast，不会量化或重新存储权重。Linux 审计复现了与 Windows 完全一致的 dtype 直方图。

| 阶段 | FP32 模式 | FP16 模式 | BF16 模式 |
|---|---|---|---|
| Checkpoint 张量存储（磁盘上） | 混合：474 个 BF16 张量（446,772,624 个元素）+ 26 个 F32 张量（3,273,552 个元素） | 同一 checkpoint | 同一 checkpoint |
| 适配器加载后的参数 | 500 个 `torch.float32` 张量（450,046,176 个元素）+ 2 个 FP32 buffer（64 个元素） | 同样的 FP32 模型参数 | 同样的 FP32 模型参数 |
| 推理时 autocast 状态 | 关闭（`actual_autocast_dtype=None`） | 开启，`torch.float16` | 开启，`torch.bfloat16` |
| 探针 `nn.Linear` 输出 dtype | `torch.float32` | `torch.float16` | `torch.bfloat16` |
| 适配器输出 | CPU `torch.float32` `[B,50,6]` | CPU `torch.float32` `[B,50,6]` | CPU `torch.float32` `[B,50,6]` |

现有证据覆盖契约测试、严格 checkpoint 加载和分布式注册/推理，不包含任务级 benchmark rollout 或成功率测量。
