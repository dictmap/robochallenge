# RoboChallenge pi0.5 复现提交工作区

本工作区用于推进 RoboChallenge 比赛/榜单的 pi0.5 复现、优化和提交准备。当前优先目标按用户提供的页面 `https://robochallenge.ai/benchmark_detail` 处理，即 Table30 基准；同时保留 Table30 V2 / ICRA WBC 的数据与 baseline 入口，避免比赛入口切换时重复建链。

## 最新状态

- Linux 上已有 RoboChallenge pi0.5 多任务 baseline：`/home/yjl/yjl/RoboChallenge/baseline_pi05_multitask`。
- 已有 ALOHA checkpoint：`/home/yjl/yjl/RoboChallenge/checkpoints/table30v2_multitask_baseline_aloha`。
- 核心操作已经写入中文 Jupyter：`notebooks/robochallenge_pi05_submit_cn.ipynb`。
- Notebook 轻量执行产物：`notebooks/robochallenge_pi05_submit_cn.executed.ipynb`。
- 预检脚本：`scripts/run_notebook_preflight.sh`。

## 当前结论

- 已创建 5 分钟一次的线程 heartbeat 自动化：`RoboChallenge pi0.5 复现提交迭代`。
- Windows 本机只能做资料整理和轻量脚本验证，GPU 为 MX550 2GB，不满足 openpi pi0.5 推理或 LoRA 微调。
- Linux 机器 `y12` 可用，环境为 Ubuntu 22.04 + RTX 4090 24GB，后续训练、推理、baseline smoke test 优先放到 Linux 上。
- GitHub 仓库 `dictmap/robochallenge` 目前为空；已生成 deploy key，等待用户在 GitHub 页面添加后即可拉取/推送。
- RoboChallenge 官方 Hugging Face 数据规模很大：Table30v2 约 1.46TB，ICRA WBC 约 1.61TB；不能盲目全量下载，先按任务/机器人形态做分片抽样和转换验证。

## 目录

- `baseline/official_table30v2_convert_to_lerobot.py`：RoboChallenge Table30v2 官方转换脚本备份。
- `baseline/official_table30v2_readme.md`：RoboChallenge Table30v2 官方数据卡备份。
- `sources/hf_table30v2_api.json`：Table30v2 Hugging Face API 快照。
- `sources/hf_icra_wbc_api.json`：ICRA WBC Hugging Face API 快照。
- `sources/source_manifest.json`：本轮使用的来源清单。
- `configs/repro_targets.json`：复现目标和执行环境约束。
- `reports/initial_repro_assessment.md`：第一轮复现评估。
- `scripts/collect_hf_manifest.py`：轻量拉取 Hugging Face repo manifest。
- `scripts/validate_repro_workspace.py`：检查本工作区是否具备后续迭代的最低材料。
- `work.md`：自动化迭代工作日志。

## 下一轮 P0

1. 等 deploy key 加到 `dictmap/robochallenge` 后，在 Linux 4090 上 clone 空仓库并同步本工作区骨架。
2. 在 Linux 上 clone `Physical-Intelligence/openpi`，只做依赖/配置 smoke test，不先下载大 checkpoint。
3. 选择一个最小 Table30v2 任务分片，验证官方 `convert_to_lerobot.py` 与 openpi 数据配置的字段匹配。
4. 明确 RoboChallenge 提交流程需要的账号/API token/模型包格式；涉及登录和提交动作必须等用户凭据或授权。
