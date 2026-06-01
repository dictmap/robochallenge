# RoboChallenge pi0.5 复现提交工作区

本工作区用于推进 RoboChallenge 比赛/榜单的 pi0.5 复现、优化和提交准备。当前优先目标按用户提供的页面 `https://robochallenge.ai/benchmark_detail` 处理，即 Table30 基准；同时保留 Table30 V2 / ICRA WBC 的数据与 baseline 入口，避免比赛入口切换时重复建链。

## 最新状态

- OpenPI `pi05_base` 基模已经在 Linux 上复现：29 个 GCS 对象下载到 `/home/yjl/.cache/openpi/openpi-assets/checkpoints/pi05_base`，大小校验通过。
- `pi05_base` 参数读取 smoke 已通过：51 个参数 leaf，约 3.353B 参数元素，见 `runs/pi05_base_probe_status.json` 和 `reports/pi05_base_repro.md`。
- 已审计 `pi0.6 / pi0.7` 公开可复现性：当前 OpenPI 公开代码和 `openpi-assets` bucket 未发现可下载 checkpoint/config，见 `reports/pi06_pi07_public_release_audit.md`。
- 已完成 Table30v2 ALOHA 最小分片字段映射：`pack_the_toothbrush_holder` 可进入 dry-run converter，见 `reports/table30v2_aloha_mapping.md`。
- 已完成 Table30v2 ALOHA dry-run converter：5 帧抽样、50 步 action window、`random_action_offset=True` 的 5 份样本、14D 到 pi0.5 32D padding 全部通过，见 `reports/table30v2_aloha_dry_run_converter.md`。
- 已完成 Table30v2 ALOHA 短 episode LeRobot writer：写出 64 帧本地 repo `robochallenge_table30v2_aloha_short`，并用 OpenPI dataloader 读通一批，见 `reports/table30v2_aloha_short_lerobot.md`。
- 已将短 episode writer 扩展为可控分片 CLI：已验证 `start_index=10`、`frame_count=80`、独立 repo `robochallenge_table30v2_aloha_short_offset10`，见 `reports/table30v2_aloha_short_lerobot_cli.md`。
- Linux 上已有 RoboChallenge pi0.5 多任务 baseline：`/home/yjl/yjl/RoboChallenge/baseline_pi05_multitask`。
- 已有 ALOHA checkpoint：`/home/yjl/yjl/RoboChallenge/checkpoints/table30v2_multitask_baseline_aloha`。
- 核心操作已经写入中文 Jupyter：`notebooks/robochallenge_pi05_submit_cn.ipynb`。
- Notebook 轻量执行产物：`notebooks/robochallenge_pi05_submit_cn.executed.ipynb`。
- 预检脚本：`scripts/run_notebook_preflight.sh`。
- ALOHA mock smoke 已跑通：`scripts/run_aloha_mock_smoke.sh`，结果见 `runs/policy_smoke_aloha_status.json`。

## 当前结论

- 已创建 5 分钟一次的线程 heartbeat 自动化：`RoboChallenge pi0.5 复现提交迭代`。
- Windows 本机只能做资料整理和轻量脚本验证，GPU 为 MX550 2GB，不满足 openpi pi0.5 推理或 LoRA 微调。
- Linux 机器 `y12` 可用，环境为 Ubuntu 22.04 + RTX 4090 24GB，后续训练、推理、baseline smoke test 优先放到 Linux 上。
- GitHub 仓库 `dictmap/robochallenge` 已配置 deploy key，当前代码已可从 Linux 推送。
- RoboChallenge 官方 Hugging Face 数据规模很大：Table30v2 约 1.46TB，ICRA WBC 约 1.61TB；不能盲目全量下载，先按任务/机器人形态做分片抽样和转换验证。
- `pi05_base` 是 Fine-Tuning 基模，不是 RoboChallenge 可直接提交的任务 policy；提交仍应走 Table30/Table30v2 任务数据、机器人配置和官方评测入口。

## 目录

- `baseline/official_table30v2_convert_to_lerobot.py`：RoboChallenge Table30v2 官方转换脚本备份。
- `baseline/official_table30v2_readme.md`：RoboChallenge Table30v2 官方数据卡备份。
- `sources/hf_table30v2_api.json`：Table30v2 Hugging Face API 快照。
- `sources/hf_icra_wbc_api.json`：ICRA WBC Hugging Face API 快照。
- `sources/source_manifest.json`：本轮使用的来源清单。
- `configs/repro_targets.json`：复现目标和执行环境约束。
- `reports/initial_repro_assessment.md`：第一轮复现评估。
- `reports/pi05_base_repro.md`：pi0.5 基模下载、配置核对和参数读取 smoke 结果。
- `reports/pi06_pi07_public_release_audit.md`：pi0.6/pi0.7 是否能公开复现的审计结果。
- `reports/table30v2_aloha_mapping.md`：Table30v2 ALOHA 最小分片到 LeRobot/OpenPI 的字段映射。
- `reports/table30v2_aloha_dry_run_converter.md`：Table30v2 ALOHA 最小分片 dry-run converter 与 OpenPI transform smoke 结果。
- `reports/table30v2_aloha_short_lerobot.md`：Table30v2 ALOHA 短 episode LeRobot writer 与 dataloader smoke 结果。
- `reports/table30v2_aloha_short_lerobot_cli.md`：可控分片 writer CLI 变体验证结果。
- `runs/table30v2_aloha_dry_run_status.json`：dry-run converter 的机器可读状态。
- `runs/table30v2_aloha_dry_run_samples.jsonl`：5 帧抽样的 LeRobot-like schema 与数值摘要。
- `runs/table30v2_aloha_short_lerobot_status.json`：短 episode writer 与 dataloader smoke 的机器可读状态。
- `runs/table30v2_aloha_short_lerobot_cli_status.json`：可控分片 writer CLI smoke 的机器可读状态。
- `scripts/collect_hf_manifest.py`：轻量拉取 Hugging Face repo manifest。
- `scripts/probe_pi05_base_model.sh`：探测/下载/校验 `pi05_base`，可选读取参数树。
- `scripts/audit_pi06_pi07_public_release.py`：审计 pi0.6/pi0.7 是否已有公开 OpenPI 配置或 checkpoint。
- `scripts/audit_table30v2_aloha_mapping.py`：审计 ALOHA 最小分片的视频、状态、norm stats 和 OpenPI 配置匹配。
- `scripts/dry_run_table30v2_aloha_converter.py`：抽样构造 Table30v2 ALOHA LeRobot-like 输入，并验证 OpenPI repack、ALOHA transform、delta action 和 32D padding。
- `scripts/write_table30v2_aloha_short_lerobot.py`：按 task、robot、repo_id、start_index、frame_count 写出 ALOHA 短 LeRobot 分片，并运行 OpenPI dataloader smoke。
- `scripts/run_pi05_base_download_background.sh`：后台下载 `pi05_base` 的辅助脚本。
- `scripts/run_pi05_base_load_smoke_background.sh`：后台执行参数读取 smoke 的辅助脚本。
- `scripts/validate_repro_workspace.py`：检查本工作区是否具备后续迭代的最低材料。
- `work.md`：自动化迭代工作日志。

## 下一轮 P0

1. 定位并适配 `openpi_rtc` 训练入口，避免误用只导入 `openpi.training.config` 的标准 `openpi/scripts/train.py`。
2. 用本地短分片跑小步数训练 dry-run，先验证训练入口、loss 前向和 checkpoint 写出，不做长训。
3. 明确 RoboChallenge 提交流程需要的账号/API token/模型包格式；涉及登录和提交动作必须等用户凭据或授权。
