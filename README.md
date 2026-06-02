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
- 已完成 `openpi_rtc` 训练入口审计和抽象 `train_step` shape smoke：确认标准 `openpi/scripts/train.py` 不能直接复用，已用短分片验证前向 loss 与反向梯度图形状闭合，见 `reports/openpi_rtc_train_entry_audit.md`。
- 已完成 `openpi_rtc` 数值权重预检：`pi05_base` 12.44GB 参数能接入 RTC 模型结构，51 个实际注入 leaf、过滤 2 个 `ShapeDtypeStruct` knob leaf；全量 grad 和小头部 `head_grad` 在 24GB 4090 当前占用下仍被 XLA/GPU 阻塞，见 `reports/openpi_rtc_numeric_weight_preflight.md`、`reports/openpi_rtc_numeric_grad_attempt.md`、`reports/openpi_rtc_numeric_head_grad.md` 和 `reports/openpi_rtc_numeric_head_grad_reduced.md`。
- 已完成 `openpi_rtc` LoRA 低显存路线审计：`gemma_2b_lora + gemma_300m_lora` 保持 `pi05=True`，`pi05_base` 权重可合并 20 个 LoRA leaf 和 2 个 knob leaf，见 `reports/openpi_rtc_lora_path_audit.md`。
- 已跑通 LoRA reduced 数值前向：`bfloat16`、1-copy、`max_token_len=64`、`action_horizon=10` 下 `forward.passed=true`，见 `reports/openpi_rtc_lora_numeric_forward_reduced.md`。
- 已跑通 LoRA reduced trainable-filter 反向与 scoped checkpoint dry-run：`lora_grad.passed=true`，远端写出 `runs/openpi_rtc_lora_grad_checkpoint/trainable_params_step1.npz`，见 `reports/openpi_rtc_lora_numeric_grad_reduced.md`。
- 已将 LoRA scoped checkpoint 物化为本地完整 policy checkpoint，`create_trained_policy` 加载 smoke 通过，并新增 LoRA `demo.py` runner 模板，见 `reports/openpi_rtc_lora_materialized_policy_smoke.md` 和 `submission/run_table30v2_aloha_lora_demo_template.sh`。
- 已新增 LoRA checkpoint 导出就绪审计，确认本地 12GB+ checkpoint 具备打包/上传前置条件，并用 tar stream smoke 验证可完整读取；真实上传和 checkpoint link 仍需要用户授权，见 `reports/lora_checkpoint_export_readiness.md`。
- 已新增 checkpoint 上传通道审计，只检查本机上传工具和凭据迹象，不读取明文、不上传，见 `reports/checkpoint_upload_channels_audit.md`。
- 已新增真实提交 readiness gate，只检查 token/submission_id/checkpoint link/runner 前置条件，不连接平台、不打印凭据，见 `reports/real_submission_readiness.md`。
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
- `reports/openpi_rtc_train_entry_audit.md`：`openpi_rtc` 训练入口、dataloader preflight 和抽象 `train_step` shape smoke 审计结果。
- `reports/openpi_rtc_numeric_weight_preflight.md`：`pi05_base` 权重接入 `openpi_rtc` 参数结构的数值预检结果。
- `reports/openpi_rtc_numeric_grad_attempt.md`：全量反向梯度尝试及 CUDA OOM blocker 记录。
- `reports/openpi_rtc_numeric_forward_bf16_1copy.md`：当前外部显存占用下，`bfloat16` 参数和 1-copy offset 前向仍 OOM 的失败日志。
- `reports/openpi_rtc_numeric_head_grad.md`：只训练 `action_in_proj/action_out_proj/knob_*` 小头部的反向尝试及 CUDA OOM blocker 记录。
- `reports/openpi_rtc_numeric_head_grad_reduced.md`：缩短 token/action horizon 后的小头部反向尝试及 XLA blocker 记录。
- `reports/openpi_rtc_lora_path_audit.md`：LoRA 低显存路线的配置、参数树和 `pi05_base` 权重合并预检结果。
- `reports/openpi_rtc_lora_numeric_weight_preflight.md`：LoRA reduced 数值 dry-run 的权重预检结果。
- `reports/openpi_rtc_lora_numeric_forward_reduced.md`：LoRA reduced 数值 forward smoke 结果。
- `reports/openpi_rtc_lora_numeric_grad_reduced.md`：LoRA reduced trainable-filter grad 与 scoped checkpoint dry-run 结果。
- `reports/openpi_rtc_lora_inference_checkpoint_materialize.md`：LoRA 完整推理 checkpoint 物化结果。
- `reports/openpi_rtc_lora_materialized_policy_smoke.md`：LoRA 完整物化 checkpoint 的 `create_trained_policy` 加载 smoke 结果。
- `reports/lora_checkpoint_export_readiness.md`：LoRA 完整物化 checkpoint 的导出/上传前置条件审计。
- `reports/checkpoint_upload_channels_audit.md`：本机 checkpoint 上传通道、工具和凭据迹象审计。
- `reports/real_submission_readiness.md`：真实提交前置条件 readiness gate。
- `reports/robochallenge_submission_package_checklist.md`：RoboChallenge 提交包清单、入口参数、凭据缺口和链接位说明。
- `runs/table30v2_aloha_dry_run_status.json`：dry-run converter 的机器可读状态。
- `runs/table30v2_aloha_dry_run_samples.jsonl`：5 帧抽样的 LeRobot-like schema 与数值摘要。
- `runs/table30v2_aloha_short_lerobot_status.json`：短 episode writer 与 dataloader smoke 的机器可读状态。
- `runs/table30v2_aloha_short_lerobot_cli_status.json`：可控分片 writer CLI smoke 的机器可读状态。
- `runs/openpi_rtc_train_entry_audit.json`：`openpi_rtc` 训练入口 shape smoke 的机器可读状态。
- `runs/openpi_rtc_numeric_weight_preflight_status.json`：`pi05_base` 权重预检机器可读状态。
- `runs/openpi_rtc_numeric_grad_attempt_status.json`：全量 grad OOM blocker 机器可读状态。
- `runs/openpi_rtc_numeric_forward_bf16_1copy_status.json`：低显存 forward OOM 尝试的机器可读状态。
- `runs/openpi_rtc_numeric_head_grad_status.json`：小头部 `head_grad` OOM blocker 机器可读状态。
- `runs/openpi_rtc_numeric_head_grad_reduced_status.json`：缩短序列 `head_grad` XLA blocker 机器可读状态。
- `runs/openpi_rtc_lora_path_audit.json`：LoRA 低显存路线审计机器可读状态。
- `runs/openpi_rtc_lora_numeric_weight_preflight_status.json`：LoRA reduced 权重预检机器可读状态。
- `runs/openpi_rtc_lora_numeric_forward_reduced_status.json`：LoRA reduced forward smoke 机器可读状态。
- `runs/openpi_rtc_lora_numeric_grad_reduced_status.json`：LoRA reduced trainable-filter grad/checkpoint smoke 机器可读状态。
- `runs/openpi_rtc_lora_inference_checkpoint_materialize_status.json`：LoRA 完整推理 checkpoint 物化机器可读状态。
- `runs/openpi_rtc_lora_materialized_policy_smoke_status.json`：LoRA 完整物化 checkpoint 加载 smoke 机器可读状态。
- `runs/lora_checkpoint_export_readiness.json`：LoRA checkpoint 导出就绪机器可读状态。
- `runs/checkpoint_upload_channels_audit.json`：checkpoint 上传通道审计机器可读状态。
- `runs/real_submission_readiness.json`：真实提交 readiness gate 机器可读状态。
- `runs/robochallenge_submission_package_audit.json`：提交包清单和启动模板的机器可读审计状态。
- `submission/submission_manifest_template.json`：不含明文凭据的提交 manifest 模板。
- `submission/run_table30v2_aloha_demo_template.sh`：Table30v2 ALOHA baseline 的 `demo.py` 启动模板。
- `submission/run_table30v2_aloha_lora_demo_template.sh`：默认指向本地 LoRA 完整物化 checkpoint 的 `demo.py` 启动模板。
- `scripts/collect_hf_manifest.py`：轻量拉取 Hugging Face repo manifest。
- `scripts/probe_pi05_base_model.sh`：探测/下载/校验 `pi05_base`，可选读取参数树。
- `scripts/audit_pi06_pi07_public_release.py`：审计 pi0.6/pi0.7 是否已有公开 OpenPI 配置或 checkpoint。
- `scripts/audit_table30v2_aloha_mapping.py`：审计 ALOHA 最小分片的视频、状态、norm stats 和 OpenPI 配置匹配。
- `scripts/dry_run_table30v2_aloha_converter.py`：抽样构造 Table30v2 ALOHA LeRobot-like 输入，并验证 OpenPI repack、ALOHA transform、delta action 和 32D padding。
- `scripts/write_table30v2_aloha_short_lerobot.py`：按 task、robot、repo_id、start_index、frame_count 写出 ALOHA 短 LeRobot 分片，并运行 OpenPI dataloader smoke。
- `scripts/audit_openpi_rtc_train_entry.py`：审计 `openpi_rtc` 训练入口并运行抽象 `train_step` 前向/反向 shape smoke。
- `scripts/run_openpi_rtc_numeric_dry_run.py`：分阶段运行 `openpi_rtc` 数值 dry-run，支持权重预检、forward、grad、head_grad 和低显存覆盖参数。
- `scripts/audit_openpi_rtc_lora_path.py`：审计 `openpi_rtc` LoRA 低显存路线并验证 `pi05_base` 权重合并。
- `scripts/audit_lora_checkpoint_export_readiness.py`：审计 LoRA 完整物化 checkpoint 是否具备导出/上传前置条件。
- `scripts/audit_checkpoint_upload_channels.py`：审计本机是否具备 checkpoint 上传工具、凭据迹象和本地打包前置条件。
- `scripts/audit_real_submission_readiness.py`：审计真实提交前 token、submission_id、checkpoint link 和 runner 条件。
- `scripts/audit_robochallenge_submission_package.py`：生成并审计提交包清单、manifest 和无凭据启动模板。
- `scripts/run_pi05_base_download_background.sh`：后台下载 `pi05_base` 的辅助脚本。
- `scripts/run_pi05_base_load_smoke_background.sh`：后台执行参数读取 smoke 的辅助脚本。
- `scripts/validate_repro_workspace.py`：检查本工作区是否具备后续迭代的最低材料。
- `work.md`：自动化迭代工作日志。

## 下一轮 P0

1. 用户选择并授权一个 RoboChallenge 评测端可访问的存储位置，把 `runs/openpi_rtc_lora_materialized_policy_checkpoint` 打包上传成 checkpoint link；仓库本身不会提交 12GB+ 权重目录。
2. 若继续走当前可运行提交路线，等待用户提供 `ROBOCHALLENGE_USER_TOKEN` 和 `ROBOCHALLENGE_SUBMISSION_ID` 后，再分别运行 baseline runner 和 LoRA runner 做真实提交入口验证。
3. 若目标改回原始 Table30，先补原始 Table30 数据/配置入口；不能把当前 Table30v2 ALOHA 证据当作 Table30 原榜单证据。

## 2026-06-02 恢复审计更新

- 已新增 `scripts/audit_openpi_rtc_lora_checkpoint_restore.py`，用于审计 `pi05_base + LoRA scoped trainable checkpoint` 的恢复/合并链路。
- 已生成 `reports/openpi_rtc_lora_checkpoint_restore_audit.md` 和 `runs/openpi_rtc_lora_checkpoint_restore_audit.json`。
- 审计结论：53 个 checkpoint key 严格匹配 `cfg.trainable_filter`；合并前 22 个 `ShapeDtypeStruct` LoRA/knob 占位，合并后剩余 0 个；参数树 shape/dtype 校验和 NNX state replace smoke 均通过。
- 该 checkpoint 仍然不是完整 policy checkpoint；推理或提交时必须同时携带相同 config、相同 LoRA variant、`pi05_base` 基础权重和 scoped trainable params。
## 2026-06-02 LoRA 推理 checkpoint 物化布局更新

- 已新增 `scripts/audit_openpi_rtc_lora_inference_checkpoint_layout.py`。
- 已生成 `reports/openpi_rtc_lora_inference_checkpoint_layout.md` 和 `runs/openpi_rtc_lora_inference_checkpoint_layout_audit.json`。
- 审计结论：`pi05_base + LoRA scoped trainable params` 可以整理为 `create_trained_policy` 需要的目录形态，关键结构是 `<checkpoint>/params` 的 Orbax PyTree checkpoint 和 `<checkpoint>/assets/cvpr_multitask_aloha/norm_stats.json`。
- 本轮默认没有写出 12GB+ 完整 checkpoint，因此 `direct_demo_checkpoint_ready=false` 仍然成立；LoRA scoped checkpoint 还不能直接作为 `demo.py --checkpoint` 参数。
- tiny Orbax save/restore smoke 已通过，说明 `{"params": ...}` 这种保存形态可以被 `openpi_rtc.models.model.restore_params` 正常读回。
- 完整物化需要显式运行：`python3 scripts/audit_openpi_rtc_lora_inference_checkpoint_layout.py --materialize --force`。生成目录位于 `runs/openpi_rtc_lora_materialized_policy_checkpoint/`，已被 `.gitignore` 排除，不能提交到 Git。

## 下一轮 P0 更新

1. 如果允许写出大文件，运行 `--materialize --force` 生成完整 LoRA 推理 checkpoint，并用 `create_trained_policy` 做加载 smoke。
2. 如果暂不写大文件，继续以官方 Table30v2 ALOHA baseline checkpoint 作为当前可运行提交模板。
3. 真实 RoboChallenge 提交仍等待 `ROBOCHALLENGE_USER_TOKEN` 和 `ROBOCHALLENGE_SUBMISSION_ID`。
## 2026-06-02 LoRA 完整 checkpoint 物化更新

- 已在 Linux 远端生成完整 LoRA 推理 checkpoint：`runs/openpi_rtc_lora_materialized_policy_checkpoint`，大小约 `12G`，该目录被 `.gitignore` 排除。
- 物化状态：`runs/openpi_rtc_lora_inference_checkpoint_materialize_status.json`，`passed=true`，`direct_demo_checkpoint_ready=true`。
- `create_trained_policy` 加载 smoke：`runs/openpi_rtc_lora_materialized_policy_smoke_status.json`，`passed=true`，policy 类型 `Policy`，模型类型 `Pi0`。
- 提交包审计已更新：LoRA checkpoint 本地已可被 `demo.py/create_trained_policy` 消费；真实网站提交仍需要 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID` 和可访问的 checkpoint link。

## 2026-06-02 LoRA 提交 runner 更新

- 已新增 `submission/run_table30v2_aloha_lora_demo_template.sh`，默认 checkpoint 为 `runs/openpi_rtc_lora_materialized_policy_checkpoint`。
- `scripts/audit_robochallenge_submission_package.py` 现在同时生成 baseline runner 和 LoRA runner，并对二者执行 `bash -n` 与无凭据 fail-fast 检查。
- `scripts/validate_repro_workspace.py` 已把 LoRA runner、manifest 双 runner 字段和无明文凭据检查纳入最低交接验证。
- 真实提交仍等待用户提供 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`，以及 LoRA checkpoint 的网站可访问链接。

## 2026-06-02 LoRA checkpoint 导出就绪更新

- 已新增 `scripts/audit_lora_checkpoint_export_readiness.py`。
- 已生成 `reports/lora_checkpoint_export_readiness.md` 和 `runs/lora_checkpoint_export_readiness.json`。
- 审计目标是本地 `runs/openpi_rtc_lora_materialized_policy_checkpoint`：检查 Orbax params metadata、manifest、norm stats、数据 shard、总大小和 Git 忽略状态。
- 已支持 `--tar-stream-smoke`：执行 `tar -C runs -cf - openpi_rtc_lora_materialized_policy_checkpoint | wc -c`，验证报告中的打包源目录可完整读取，并记录 archive stream 字节数，但不生成 12GB+ tar 文件。
- 报告给出可手动执行的本地 tar/sha256 命令；默认不自动打包 12GB+ 文件，也不上传到任何外部服务。
- 当前本地导出就绪，但网站提交仍需要真实 checkpoint link、`ROBOCHALLENGE_USER_TOKEN` 和 `ROBOCHALLENGE_SUBMISSION_ID`。
