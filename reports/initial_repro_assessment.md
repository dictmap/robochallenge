# 第一轮复现评估

## 目标判断

用户给出的页面是 `https://robochallenge.ai/benchmark_detail`。当前按 Table30 基准处理，因为公开搜索结果中该页面对应 30 个桌面操作任务，并显示 `pi0.5/rc_baseline` 成绩。RoboChallenge 同时有 Table30 V2 / CVPR Competition Benchmark 和 ICRA WBC 入口，因此后续提交前必须确认最终报名入口。

## 官方材料

- RoboChallenge Hugging Face 组织包含 5 个模型和 63 个数据集。
- `RoboChallenge/Table30v2` 数据卡说明包含 30 个任务、4 类机器人形态：ARX5、UR5、ALOHA、DOS-W1。
- Table30v2 官方建议将数据转换为 LeRobot 格式，并提供 `convert_to_lerobot.py`，但该脚本示例偏 ARX5 单臂数据，其他 embodiment 需要适配。
- `RoboChallenge/icra_wbc` 数据集是 Agibot G2 全身移动操作数据，含 2800 个遥操作 episode，结构与 Table30v2 不同。
- openpi 官方 README 说明 pi0.5 支持训练和推理，但环境要求是 Ubuntu 22.04；推理需至少 8GB 显存，LoRA 微调需 22.5GB 以上显存。

## 本地与 Linux 环境

- Windows：Python 3.10.9、git 2.40.1、uv 0.11.16，可做轻量处理。
- Windows GPU：NVIDIA GeForce MX550 2048 MiB，不适合 pi0.5 推理或训练。
- Linux：`y12`，Ubuntu 22.04，Python 3.10.12，RTX 4090 24564 MiB，可作为主执行环境。
- Linux 根分区可用约 530GB，不够全量下载 1.46TB Table30v2 或 1.61TB ICRA WBC，但够做任务分片、checkpoint、LoRA 试跑。

## 复现路线

1. 仓库准备：等待 deploy key 加入 `dictmap/robochallenge`，然后在 Linux 初始化代码仓库。
2. openpi 准备：clone `Physical-Intelligence/openpi`，先执行 `uv sync` / import smoke test，暂不下载大权重。
3. 数据准备：从 Table30v2 选择一个最小任务分片，优先单臂 UR5 或 ARX5；只下载对应 `.tar.part-*`，不全量同步。
4. 数据转换：先复用官方 `convert_to_lerobot.py` 验证 ARX5；再抽象出 UR5/ALOHA/DOS-W1 的 adapter。
5. pi0.5 配置：基于 openpi 的 pi05 fine-tuning config 增加 RoboChallenge 数据映射、norm stats 和 action/state transform。
6. 最小训练或推理：4090 上先做小步数 LoRA 或 checkpoint 加载 smoke test；通过后再扩大任务。
7. 提交准备：整理 checkpoint、policy server 启动方式、依赖版本、模型说明和 RoboChallenge 平台需要的提交材料。

## 当前风险

- 比赛入口未最终确认：Table30、Table30v2 CVPR 和 ICRA WBC 的数据结构、模型和提交要求不同。
- 网站提交动作需要用户账号或 token，不能由脚本绕过。
- 官方 baseline 模型体积约 44GB/个；Linux 剩余空间允许少量 checkpoint，但不适合多模型全量缓存。
- Table30v2 官方转换脚本只覆盖单臂示例，双臂/全身任务需要额外适配。
