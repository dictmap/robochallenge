# 工作日志

## 2026-06-02 第一轮

### 已完成

- 创建本地独立工作区 `robochallenge_pi05_repro`。
- 创建 5 分钟 heartbeat 自动化：`robochallenge-pi0-5`。
- 下载官方 Table30v2 数据卡和 `convert_to_lerobot.py` 作为本地参考。
- 保存 Hugging Face API 快照：`hf_table30v2_api.json`、`hf_icra_wbc_api.json`。
- 检查本地 Windows 环境：Python 3.10.9、git 2.40.1、uv 0.11.16、MX550 2GB。
- 检查 Linux 环境：Ubuntu 22.04、Python 3.10.12、RTX 4090 24GB、根分区可用约 530GB。
- 为 `dictmap/robochallenge` 创建 deploy key，并同步到 Linux 机器。

### 当前阻塞

- GitHub deploy key 还未添加到仓库，`ssh -T github.com-dictmap-robochallenge` 当前返回 `Permission denied (publickey)`。
- RoboChallenge 真实提交需要网站账号、比赛入口确认、提交格式或 API token；这些不能伪造。
- 全量数据和 checkpoint 体积很大，必须先确定最小任务分片和训练策略。

### 下一步

- deploy key 生效后，在 Linux 上初始化/clone `dictmap/robochallenge`。
- 在 Linux 上准备 openpi 环境 smoke test。
- 基于 Table30v2 官方 README 自动生成任务/形态矩阵，先挑 UR5 或 ARX5 单臂任务做最小转换链。

## 2026-06-02 第二轮

### 已完成

- 用户确认可以使用 Linux，并提供 `dictmap/robochallenge` 仓库。
- deploy key 已添加并验证成功：GitHub 返回 `Hi dictmap/robochallenge!`。
- Linux 上确认已有 pi0.5 baseline：`/home/yjl/yjl/RoboChallenge/baseline_pi05_multitask`。
- 该 baseline 包含 `demo.py` 官方评测入口、`test.py` mock 入口、`mock_server`、`robot`、`utils`、OpenPI runtime 和 4 个机器人平台配置。
- Linux 上确认已有 ALOHA checkpoint：`/home/yjl/yjl/RoboChallenge/checkpoints/table30v2_multitask_baseline_aloha`，大小约 12GB。
- 已将轻量代码入口复制到 `/home/yjl/robochallenge/repo`，并排除 `.venv`、checkpoint、样例视频、日志等大文件。
- 已创建中文 Jupyter：`notebooks/robochallenge_pi05_submit_cn.ipynb`。
- 已用 baseline `.venv` 执行 Notebook 轻量预检，生成 `notebooks/robochallenge_pi05_submit_cn.executed.ipynb`。
- Notebook 修正了 `RECORD_DATA_DIR` 相对路径解析：官方 mock server 路径是相对 `mock_server/`，不是 repo 根目录。

### 验证结果

- Notebook JSON 校验通过。
- nbformat cell id 已规范化，重新执行无 MissingID 警告。
- ALOHA 样例数据体检通过：`left_states.jsonl=1100`、`right_states.jsonl=1100`，三路视频均为 `1100` 帧。
- Notebook 预检状态写入 `runs/notebook_preflight_status.json`。

### 当前阻塞

- 尚未跑重型 policy smoke test；需要启动 mock server 并加载 12GB ALOHA checkpoint，占用 GPU。
- 官方 `demo.py` 真实提交需要 RoboChallenge 网站的 `user_token` 和 `submission_id`。

### 下一步

- P0：在 Linux 上用 Notebook 开关或命令行启动 ALOHA mock server，再跑一次短时 `test.py` smoke。
- P1：把仓库提交并推送到 `dictmap/robochallenge`。
- P2：根据网站提交页确认真实评测时间窗口和命令参数。

## 2026-06-02 第三轮

### 已完成

- 修复 ALOHA mock server 启动目录：`mock_robot_server.py` 必须从 `baseline_pi05_multitask/mock_server` 目录启动，否则 `../20260413/...` 样例路径解析失败。
- 修复 mock 客户端 URL：`robot/interface_client.py` 的 mock 地址去掉尾部 `/`，避免请求 `//clock-sync` 返回 404。
- 修复 smoke 运行路径：`scripts/run_aloha_mock_smoke.sh` 改为启动 baseline mock server，但执行仓库内的 `test.py`，确保使用仓库内已修复的客户端。
- 为 `test.py` 增加 `--max_wait` 参数，smoke 不再依赖外部 `timeout` 杀进程。
- 确认 Linux LeRobot 可用：通过 `PYTHONPATH` 引入 `/home/yjl/yjl/RoboChallenge/third_party/lerobot` 后，`openpi_rtc`、`openpi_client`、`lerobot`、`jax`、`torch`、`cv2` 全部 import 通过。

### 验证结果

- `scripts/probe_linux_pi05_env.sh` 通过。
- `scripts/run_aloha_mock_smoke.sh` 通过。
- smoke 状态：`runs/policy_smoke_aloha_status.json` 显示 `exit_code=0`、`smoke=passed`。
- 日志 `runs/policy_smoke_aloha.log` 出现多条 `Inference result`，证明 ALOHA 样例数据、mock server、pi0.5 checkpoint、openpi 推理链路已经打通。

### 当前阻塞

- 真实 RoboChallenge 提交仍需要用户申请并提供 `user_token` 和 `submission_id`。
- 仍需最终确认参赛目标是 `Table30` 还是 `Table30v2`；当前跑通的是 `Table30v2` ALOHA baseline。

### 下一步

- P0：把本轮修复和 smoke 结果提交并推送到 `dictmap/robochallenge`。
- P1：根据用户选择的目标榜单，补对应的数据/模型映射；如果是 Table30 原榜，需要补 Table30 专用数据和配置。

## 2026-06-02 第四轮：先复现基模

### 已完成

- 按“基模”优先复现 OpenPI 官方 `pi05_base` checkpoint。
- 新增 `scripts/probe_pi05_base_model.sh`：解析官方 `pi05_*` 训练配置、列出公共 GCS 对象、可选下载、校验本地缓存大小、可选读取 JAX 参数树。
- 新增 `scripts/run_pi05_base_download_background.sh` 和 `scripts/run_pi05_base_load_smoke_background.sh`，方便后台下载和后台 smoke。
- 中文 Jupyter `notebooks/robochallenge_pi05_submit_cn.ipynb` 已加入“pi0.5 基模复现”小节；默认不下载，显式打开开关才会拉取 11.6GiB checkpoint。
- 已在 Linux 下载 `gs://openpi-assets/checkpoints/pi05_base` 到 `/home/yjl/.cache/openpi/openpi-assets/checkpoints/pi05_base`。
- 下载中发现一个对象因为旧进程并发写入导致本地大小超过远端大小；已定位只有这一个对象异常，删除后断点重拉，最终校验通过。
- 生成报告 `reports/pi05_base_repro.md`，生成状态 `runs/pi05_base_probe_status.json` 和 manifest `runs/pi05_base_manifest.json`。

### 验证结果

- `pi05_base` 公共 GCS 对象数：29。
- 远端总大小：12,441,749,581 bytes，约 11.587 GiB。
- 本地匹配大小：12,441,749,581 bytes，`local_complete=true`。
- `LOAD_PI05_PARAMS=1` 参数读取 smoke 通过：`loaded=true`，51 个参数 leaf，`total_elements=3353433872`，dtype 为 `bfloat16`。
- 已核对 `pi05_libero`、`pi05_aloha_pen_uncap`、`pi05_full_droid_finetune` 等配置均使用 `pi05_base/params` 作为基模权重来源。

### 当前阻塞

- `pi05_base` 是 Fine-Tuning 基模，不是可直接提交 RoboChallenge 的任务 policy。
- 真实 RoboChallenge 提交仍需要用户申请并提供 `user_token` 和 `submission_id`。
- 原始 `Table30` 和 `Table30v2` 必须继续分开处理；当前已跑通的是 `Table30v2` ALOHA baseline，基模复现不等于完成 Table30 原榜提交。

### 下一步

- P0：基于 `pi05_base` 和现有 Table30v2 数据，补最小任务分片的数据字段、norm stats、动作维度和 prompt 映射。
- P1：优先把 ALOHA 或 UR5 的一个 Table30v2 分片接到 OpenPI finetune/eval 配置。

## 2026-06-02 第五轮：补查 pi0.6 / pi0.7

### 已完成

- 按用户提醒补查 `pi0.6`、`pi0.7`。
- 新增 `scripts/audit_pi06_pi07_public_release.py`：扫描本地 OpenPI 配置、查询 `openpi-assets` 公共 checkpoint 前缀，并生成审计报告。
- 官方 OpenPI 当前公开仓库只列 `pi0`、`pi0-FAST`、`pi0.5` 三类模型；本地代码未命中可用 `pi06/pi07/pi0.6/pi0.7` config。
- 已查询 `checkpoints/pi06`、`checkpoints/pi07`、`checkpoints/pi0_6`、`checkpoints/pi0_7`、`checkpoints/pi06_base`、`checkpoints/pi07_base`、`checkpoints/pi0.6`、`checkpoints/pi0.7`、`checkpoints/pistar06`、`checkpoints/pi_star06` 等公共 GCS 前缀，当前对象数均为 0。
- 生成 `reports/pi06_pi07_public_release_audit.md` 和 `runs/pi06_pi07_public_audit.json`。

### 结论

- `pi*0.6` 和 `pi0.7` 有公开论文/博客，可作为方法参考，但没有发现可像 `pi05_base` 一样下载并加载的公开 OpenPI checkpoint。
- 当前不能声称“复现 pi0.6/pi0.7 模型本体”；可执行路线仍是先用 `pi05_base` 和 RoboChallenge/Table30v2 baseline。

### 下一步

- P0：把 `pi*0.6` 的 RECAP 思路拆成可在 RoboChallenge 上落地的后续优化项：成功/失败标签、失败轨迹、reward bin/value function、优势加权再训练。
- P1：把 `pi0.7` 的 steerable prompt/subtask/visual subgoal/metadata conditioning 思路记录为后续 prompt 与分层策略优化方向。

## 2026-06-02 第六轮：Table30v2 ALOHA 最小分片映射

### 已完成

- 新增 `scripts/audit_table30v2_aloha_mapping.py`，审计 `pack_the_toothbrush_holder` ALOHA 分片的视频、状态字段、任务描述、OpenPI 配置和 checkpoint norm stats。
- 确认官方 `convert_to_lerobot.py` 是单臂模板，不能直接用于当前 ALOHA 双臂分片。
- 确认当前样例分片实际结构是 `left_states.jsonl`、`right_states.jsonl` 和三路视频：`cam_high_rgb.mp4`、`cam_left_wrist_rgb.mp4`、`cam_right_wrist_rgb.mp4`。
- 确认 `cvpr_multitask_aloha_rtc` 使用 `LeRobotW1DualDataConfig(repo_id='cvpr_multitask_aloha')`，pi0.5 模型 `action_dim=32`、`action_horizon=50`。
- 确认 checkpoint `cvpr_multitask_aloha` 的 `state/actions` norm stats 都是 14 维，和双臂 ALOHA 数据一致。
- 生成 `reports/table30v2_aloha_mapping.md` 和 `runs/table30v2_aloha_mapping_audit.json`。

### 验证结果

- 左臂状态帧数：1100，右臂状态帧数：1100。
- 三路视频均为 1100 帧、30fps、640x480。
- 推荐数据映射：`state=concat(left.master_qpos, right.master_qpos)`，`action=下一帧 concat(left.master_qpos, right.master_qpos)`，均为 14 维。
- OpenPI 桥接方式：训练时 14 维 state/action pad 到 pi0.5 的 32 维；推理输出用 `AlohaDualOutputs` 截取前 14 维。
- `ready_for_dry_run_converter=true`。

### 下一步

- P0：写 ALOHA 最小分片 dry-run converter，先只抽样 2-5 帧生成 LeRobot-like feature schema 并校验，不写全量数据。
- P1：dry-run 通过后，再扩展到可选小 episode 输出和 OpenPI dataloader smoke。

## 2026-06-02 第七轮：Table30v2 ALOHA dry-run converter

### 已完成

- 新增 `scripts/dry_run_table30v2_aloha_converter.py`，默认抽样 `pack_the_toothbrush_holder` 的 5 帧，并构造一个 50 步 action window。
- dry-run 输入已按 baseline 的 `LeRobotW1DualDataConfig` 使用扁平 LeRobot 键：`observation.images.front_image`、`observation.images.left_image`、`observation.images.right_image`、`observation.state`、`action`。
- 已验证 `cvpr_multitask_aloha_rtc` 的真实训练配置：`random_action_offset=True`、`random_action_offset_copies=5`、`action_horizon=50`、`model.action_dim=32`。
- 已生成 `runs/table30v2_aloha_dry_run_samples.jsonl`，只保存 schema 和数值摘要，不复制全量图片或视频。
- 已生成 `reports/table30v2_aloha_dry_run_converter.md` 和 `runs/table30v2_aloha_dry_run_status.json`。
- 已将 dry-run converter 纳入 `scripts/validate_repro_workspace.py` 的最低交接检查。

### 验证结果

- raw state sequence：`[50, 14]`。
- raw action sequence：`[50, 14]`。
- OpenPI data transforms 后 state：`[5, 14]`。
- OpenPI data transforms 后 actions：`[5, 50, 14]`。
- pi0.5 padding 后 state：`[5, 32]`。
- pi0.5 padding 后 actions：`[5, 50, 32]`。
- 三路图像键已匹配：`base_0_rgb`、`left_wrist_0_rgb`、`right_wrist_0_rgb`，mask 全为 true。
- `passed=true`。

### 当前阻塞

- 仍不能进行真实 RoboChallenge 提交：需要用户申请并提供网站 `user_token` 与 `submission_id`，不能伪造。
- 仍未写全量 LeRobot 数据集；目前只完成最小 dry-run schema 与 transform smoke。
- 当前可提交 policy 仍是 Table30v2 ALOHA baseline 方向；原始 `Table30` 若作为正式目标，需要另行补齐对应数据入口和评测配置。

### 下一步

- P0：把 dry-run converter 扩展为可选小 episode LeRobot writer，先只写一个短 episode 并运行 dataloader smoke。
- P1：小 episode 成功后，再准备微调/评测命令模板和提交打包清单。

## 2026-06-02 第八轮：短 episode LeRobot writer 与 dataloader smoke

### 已完成

- 新增 `scripts/write_table30v2_aloha_short_lerobot.py`，从 `pack_the_toothbrush_holder` ALOHA 样例写出 64 帧本地 LeRobot repo。
- 输出 repo_id：`robochallenge_table30v2_aloha_short`。
- 输出路径：`/home/yjl/.cache/huggingface/lerobot/robochallenge_table30v2_aloha_short`。
- 写入字段：`observation.images.front_image`、`observation.images.left_image`、`observation.images.right_image`、`observation.state`、`action` 和 task prompt。
- 使用 `cvpr_multitask_aloha_rtc` 的 `LeRobotW1DualDataConfig` 读取本地 repo，完成 OpenPI dataloader smoke。
- 已生成 `reports/table30v2_aloha_short_lerobot.md` 和 `runs/table30v2_aloha_short_lerobot_status.json`。
- 已将短 episode writer 和 dataloader smoke 纳入 `scripts/validate_repro_workspace.py`。

### 验证结果

- LeRobot 写出帧数：64，fps：30。
- dataloader 后 state shape：`[1, 5, 32]`。
- dataloader 后 actions shape：`[1, 5, 50, 32]`。
- dataloader 后 image keys：`base_0_rgb`、`left_wrist_0_rgb`、`right_wrist_0_rgb`。
- prompt tokenizer shape：`[1, 5, 200]`。
- `passed=true`。

### 当前阻塞

- 真实 RoboChallenge 提交仍需要用户申请并提供 `user_token` 与 `submission_id`。
- 当前只写了一个短 episode，本轮没有做全量 Table30v2 转换，也没有做长时间训练。
- 原始 `Table30` 仍未等同于当前 Table30v2 ALOHA 分片；若正式入口要求原始 Table30，需要补对应数据与配置。

### 下一步

- P0：把短 episode writer 扩展为可控分片 writer，支持指定 task、robot 和 frame_count，并保留本地 repo 不覆盖选项。
- P1：跑小步数训练 dry-run，验证训练入口、loss 前向和 checkpoint 写出。

## 2026-06-02 第九轮：可控分片 writer CLI

### 已完成

- 将 `scripts/write_table30v2_aloha_short_lerobot.py` 扩展为显式 CLI。
- 新增可控参数：`--task`、`--robot`、`--episode-dir`、`--task-info`、`--config-name`、`--repo-id`、`--frame-count`、`--start-index`、`--overwrite/--no-overwrite`、`--status-path`、`--report-path`。
- 保留安全删除限制：只允许删除 Hugging Face LeRobot cache 下、且 repo_id 以 `robochallenge_` 开头的本项目 repo。
- 用默认参数重跑 64 帧短分片，保持标准状态文件不变。
- 用非默认参数跑通可控分片：`repo_id=robochallenge_table30v2_aloha_short_offset10`、`start_index=10`、`frame_count=80`。
- 生成 CLI 证据：`reports/table30v2_aloha_short_lerobot_cli.md` 和 `runs/table30v2_aloha_short_lerobot_cli_status.json`。
- 已将默认 writer smoke 和 CLI writer smoke 都纳入 `scripts/validate_repro_workspace.py`。

### 验证结果

- 默认 writer：`start_index=0`、`frame_count=64`，dataloader smoke 通过。
- CLI writer：`start_index=10`、`frame_count=80`，dataloader smoke 通过。
- 两条 smoke 的关键形状一致：state=`[1, 5, 32]`，actions=`[1, 5, 50, 32]`，tokenized prompt=`[1, 5, 200]`。

### 当前阻塞

- `openpi/scripts/train.py` 导入的是标准 `openpi.training.config`，而 RoboChallenge 已验证配置在 `openpi_rtc.training.config`；不能直接误用标准训练入口声称完成训练 dry-run。
- 真实 RoboChallenge 提交仍需要用户申请并提供 `user_token` 与 `submission_id`。

### 下一步

- P0：定位或搭建 `openpi_rtc` 训练 dry-run 入口，使用本地短分片做 1-step loss 前向/反向验证。
- P1：若训练入口需要较大显存或权重加载许可，明确记录阻塞和可替代的 lightweight forward smoke。

## 2026-06-02 第十轮：openpi_rtc 训练入口 shape smoke

### 已完成

- 新增 `scripts/audit_openpi_rtc_train_entry.py`，不改 baseline 源码，专门审计 `openpi_rtc` 训练入口和本地短分片训练形状。
- 确认 baseline 现有训练候选脚本只有 `train.py`、`train_pytorch.py`、`train_test.py`，没有现成 `train_rtc.py`。
- 确认标准 `openpi/scripts/train.py` 绑定 `openpi.training.*`，没有导入 `openpi_rtc.training.*`，不能直接用于当前 RoboChallenge RTC 配置。
- 确认 `openpi_rtc.models.pi0.compute_loss` 已有 `actions.ndim == 4` 的 multi-offset 分支，能够接收当前 dataloader 产生的 `[batch, 5, 50, 32]` actions。
- 用本地短分片 `robochallenge_table30v2_aloha_short` 和 `cvpr_multitask_aloha_rtc` 完成 dataloader preflight。
- 用 `jax.eval_shape` 完成抽象 `train_step` 前向 loss 与反向梯度 shape smoke，不加载 `pi05_base` 大权重，不写真实 checkpoint。
- 生成 `reports/openpi_rtc_train_entry_audit.md` 和 `runs/openpi_rtc_train_entry_audit.json`。
- 已将该审计纳入 `scripts/validate_repro_workspace.py` 的最低交接检查。

### 验证结果

- dataloader state shape：`[1, 5, 32]`。
- dataloader actions shape：`[1, 5, 50, 32]`。
- tokenized prompt shape：`[1, 5, 200]`。
- image keys：`base_0_rgb`、`left_wrist_0_rgb`、`right_wrist_0_rgb`。
- 抽象 `train_step` shape smoke：`passed=true`。
- `info_shape.loss`、`info_shape.grad_norm`、`info_shape.param_norm` 均为标量。
- 本地 `python scripts/validate_repro_workspace.py` 已通过。

### 当前边界

- 本轮验证的是训练图和维度闭合，不是数值训练；尚未加载 `pi05_base` 权重跑真实 loss。
- `openpi_rtc.training.weight_loaders.py` 仍引用标准 `openpi.models.model` 和 `openpi.shared.download`，真实权重加载前需要继续核对是否会造成 namespace 风险。
- 真实 RoboChallenge 提交仍需要用户申请并提供网站 `user_token` 与 `submission_id`。

### 下一步

- P0：固化最小 `openpi_rtc` 数值训练脚本，在 Linux GPU 上加载 `pi05_base` 权重跑真实 1-step loss/grad/checkpoint dry-run。
- P1：如果真实 1-step 因显存或权重 namespace 失败，先修复 `openpi_rtc` weight loader 的 namespace 风险，再重跑。

## 2026-06-02 第十一轮：openpi_rtc 数值权重预检与 grad OOM blocker

### 已完成

- 新增 `scripts/run_openpi_rtc_numeric_dry_run.py`，支持 `weight_preflight`、`forward`、`grad` 三种模式。
- 默认使用 `cvpr_multitask_aloha_rtc` 和本地短分片 `robochallenge_table30v2_aloha_short`。
- 将 `pi05_base` 权重路径改为本地已验证缓存：`/home/yjl/.cache/openpi/openpi-assets/checkpoints/pi05_base/params`。
- 修复 `openpi_rtc` weight loader partial params 问题：按官方训练入口逻辑过滤 `ShapeDtypeStruct`，让 `knob_dir`、`knob_scale` 保留模型初始化值。
- 生成 `reports/openpi_rtc_numeric_weight_preflight.md` 和 `runs/openpi_rtc_numeric_weight_preflight_status.json`。
- 尝试全量 `grad` 并生成 `reports/openpi_rtc_numeric_grad_attempt.md` 和 `runs/openpi_rtc_numeric_grad_attempt_status.json`。
- 已将数值权重预检与 grad OOM blocker 纳入 `scripts/validate_repro_workspace.py`。

### 验证结果

- 权重预检：`passed=true`。
- `pi05_base` params 大小：`12,441,721,931` bytes。
- dataloader state shape：`[1, 5, 32]`。
- dataloader actions shape：`[1, 5, 50, 32]`。
- tokenized prompt shape：`[1, 5, 200]`。
- 权重结构：expected 53 leaf / loaded 53 leaf / actual partial params 51 leaf。
- 已过滤 `ShapeDtypeStruct` leaf：2 个，分别为 `knob_dir`、`knob_scale`。
- 全量 `grad`：失败，`XlaRuntimeError: CUDA_ERROR_OUT_OF_MEMORY`。

### 当前边界

- 当前 4090 上有非本轮 RoboChallenge 进程占用显存：`lerobot_sim` 约 3GB，长期 `policy-provider` 约 2.2GB；本轮没有直接杀这些非当前任务进程。
- 在当前外部显存占用下，`forward` 与全量 `grad` 都会 OOM；此前空闲显存更高时曾观察到一次 forward loss 通过，但本轮只把可复现到文件的结果作为交接证据。
- 全量 pi0.5 反向在单张 24GB 4090 上不适合作为默认路线，需要改 LoRA、冻结层、FSDP/多卡或更小训练目标。

### 下一步

- P0：做 LoRA/冻结层 `openpi_rtc` 1-step grad/checkpoint dry-run，避免全量参数反向 OOM。
- P1：在用户确认可释放 GPU 进程后，重跑官方 5-copy forward 并保存通过状态文件。

## 2026-06-02 第十二轮：openpi_rtc 小头部反向 blocker 固化

### 已完成

- 将 `scripts/run_openpi_rtc_numeric_dry_run.py` 扩展为支持 `head_grad` 模式，只对 `action_in_proj`、`action_out_proj`、`knob_*` 小头部参数求梯度并计划写 scoped checkpoint。
- 新增低显存覆盖参数：`--max-token-len` 和 `--action-horizon`，用于缩短 prompt token 和 action horizon 做 smoke。
- 运行完整小头部反向：`random_action_offset_copies=1`、`bfloat16` 参数、默认 token/action 设置。
- 运行缩短版小头部反向：`random_action_offset_copies=1`、`max_token_len=64`、`action_horizon=10`。
- 生成 `reports/openpi_rtc_numeric_head_grad.md`、`runs/openpi_rtc_numeric_head_grad_status.json`、`reports/openpi_rtc_numeric_head_grad_reduced.md` 和 `runs/openpi_rtc_numeric_head_grad_reduced_status.json`。
- 已将两份小头部反向失败证据纳入 `scripts/validate_repro_workspace.py`，并增加检查：当前状态没有成功写出 `runs/openpi_rtc_head_grad_checkpoint/metadata.json`。

### 验证结果

- 小头部完整反向的权重预检通过，dataloader shape 为 state=`[1, 32]`、actions=`[1, 50, 32]`、tokenized prompt=`[1, 200]`。
- 小头部完整反向失败：`XlaRuntimeError: CUDA_ERROR_OUT_OF_MEMORY`。
- 小头部缩短版权重预检通过，dataloader shape 为 state=`[1, 32]`、actions=`[1, 10, 32]`、tokenized prompt=`[1, 64]`。
- 小头部缩短版失败：`XlaRuntimeError: INTERNAL: an internal operation failed`。
- 本地 `python scripts/validate_repro_workspace.py` 已通过。

### 当前阻塞

- 当前 GPU 上仍有非本轮 RoboChallenge 进程占用显存；在未获用户授权前不停止这些进程。
- 本轮没有成功写出 head-grad checkpoint，因此不能声称完成 1-step 数值训练。
- 真实 RoboChallenge 提交仍需要用户申请并提供网站 `user_token` 与 `submission_id`。

### 下一步

- P0：同步更新中文 Notebook 的可选 `head_grad` 入口并运行 notebook preflight，确保默认只跑安全的 `weight_preflight`。
- P1：若用户授权释放 GPU，重跑 `forward` 和 `head_grad`；若不能释放 GPU，则改为 LoRA/FSDP/offload 或更小模型状态。

## 2026-06-02 第十三轮：openpi_rtc LoRA 低显存路线审计

### 已完成

- 新增 `scripts/audit_openpi_rtc_lora_path.py`，专门审计 `cvpr_multitask_aloha_rtc` 是否能切到 pi0.5 LoRA 低显存路线。
- 使用 LoRA 变体 `paligemma_variant=gemma_2b_lora` 与 `action_expert_variant=gemma_300m_lora`，并确认 `pi05=True` 保持不变。
- 用 `model.get_freeze_filter()` 设置 LoRA 冻结规则，并关闭 EMA：`ema_decay=None`。
- 用 `pi05_base` 本地权重 `/home/yjl/.cache/openpi/openpi-assets/checkpoints/pi05_base/params` 运行权重合并预检。
- 生成 `reports/openpi_rtc_lora_path_audit.md` 和 `runs/openpi_rtc_lora_path_audit.json`。
- 已将 LoRA 审计纳入 `scripts/validate_repro_workspace.py`。

### 验证结果

- LoRA 总参数 leaf：`73`，元素数：`3,403,422,481`。
- LoRA 参数 leaf：`20`，元素数：`49,987,584`。
- 冻结参数 leaf：`20`，元素数：`2,936,464,384`。
- 可训练参数 leaf：`53`，元素数：`466,958,097`。
- `pi05_base` 权重合并通过：合并后 leaf=`73`，补入 LoRA leaf=`20`，补入 knob leaf=`2`。
- 本地 `python scripts/validate_repro_workspace.py` 已通过。

### 当前边界

- 本轮只验证 LoRA 配置、参数树和权重合并，不代表已经完成 LoRA 数值 forward/grad。
- 当前 GPU 上仍有非本轮 RoboChallenge 进程占用显存；在未获用户授权前不停止这些进程。
- LoRA 可训练元素数仍约 4.67 亿，是否能在当前 4090 占用下完成数值 forward/grad 需要下一轮实测。

### 下一步

- P0：将 LoRA 变体参数接入 `scripts/run_openpi_rtc_numeric_dry_run.py`，先跑 LoRA 版 `weight_preflight`，再尝试低显存 `forward`。
- P1：若 LoRA `forward` 仍失败，记录为新的数值 blocker，并转向 FSDP/offload 或等待用户授权释放 GPU。

## 2026-06-02 第十四轮：openpi_rtc LoRA reduced 数值 forward smoke

### 已完成

- 将 `scripts/run_openpi_rtc_numeric_dry_run.py` 扩展为支持 `--paligemma-variant` 和 `--action-expert-variant`，可直接指定 `gemma_2b_lora` 与 `gemma_300m_lora`。
- 修复 LoRA 场景下 `expected_param_shape` 对 `ShapeDtypeStruct` 占位 leaf 直接 `.astype` 的兼容问题。
- 运行 LoRA reduced `weight_preflight`：`random_action_offset_copies=1`、`max_token_len=64`、`action_horizon=10`。
- 运行 LoRA reduced `forward`：`compute_param_dtype=bfloat16`、`random_action_offset_copies=1`、`max_token_len=64`、`action_horizon=10`。
- 生成 `reports/openpi_rtc_lora_numeric_weight_preflight.md`、`runs/openpi_rtc_lora_numeric_weight_preflight_status.json`、`reports/openpi_rtc_lora_numeric_forward_reduced.md` 和 `runs/openpi_rtc_lora_numeric_forward_reduced_status.json`。
- 已将 LoRA numeric preflight 与 reduced forward smoke 纳入 `scripts/validate_repro_workspace.py`。

### 验证结果

- LoRA reduced 权重预检：`passed=true`。
- LoRA reduced dataloader shape：state=`[1, 32]`、actions=`[1, 10, 32]`、tokenized prompt=`[1, 64]`。
- LoRA 权重结构：loaded leaf=`73`、partial params leaf=`51`、过滤 `ShapeDtypeStruct` leaf=`22`。
- LoRA reduced forward：`passed=true`，loss=`0.0`，耗时约 `17.519` 秒。
- 本地 `python scripts/validate_repro_workspace.py` 已通过。

### 当前边界

- 本轮只证明 LoRA reduced 数值前向链路能跑通，不代表已经完成 LoRA 训练或 checkpoint。
- 现有 `grad` 模式仍会对完整 state 求梯度，不能冒充 LoRA trainable-filter grad。
- LoRA forward 运行中 GPU 占用接近 21GB，后续 LoRA grad 仍可能触发显存或 XLA blocker。

### 下一步

- P0：新增 LoRA trainable-filter `lora_grad` 或等价 scoped grad/checkpoint dry-run，只更新 LoRA/非冻结参数并写 scoped checkpoint。
- P1：若 LoRA grad 失败，保存 blocker 报告并转向 FSDP/offload 或等待用户授权释放 GPU。
