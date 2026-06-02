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

## 2026-06-02 第十五轮：openpi_rtc LoRA trainable-filter grad/checkpoint dry-run

### 已完成

- 将 `scripts/run_openpi_rtc_numeric_dry_run.py` 扩展为 `lora_grad` 模式，使用 `config.trainable_filter` 求梯度，区别于旧的全量 `grad` 模式。
- 将运行时 checkpoint 目录加入 `.gitignore`：`runs/*checkpoint*/`，避免误提交大文件。
- 运行 LoRA reduced `lora_grad`：`compute_param_dtype=bfloat16`、`random_action_offset_copies=1`、`max_token_len=64`、`action_horizon=10`。
- 写出远端 scoped checkpoint：`runs/openpi_rtc_lora_grad_checkpoint/trainable_params_step1.npz` 和 `runs/openpi_rtc_lora_grad_checkpoint/metadata.json`。
- 生成 `reports/openpi_rtc_lora_numeric_grad_reduced.md` 和 `runs/openpi_rtc_lora_numeric_grad_reduced_status.json`。
- 已将 LoRA trainable-filter grad/checkpoint smoke 纳入 `scripts/validate_repro_workspace.py`。
- 中文 Notebook 第 18 节新增可选 `RUN_OPENPI_RTC_LORA_NUMERIC_GRAD`，默认关闭，避免预检反复写约 1GB checkpoint。

### 验证结果

- LoRA reduced `lora_grad`：`passed=true`。
- dataloader shape：state=`[1, 32]`、actions=`[1, 10, 32]`、tokenized prompt=`[1, 64]`。
- 权重结构：loaded leaf=`73`、partial params leaf=`51`、过滤 `ShapeDtypeStruct` leaf=`22`。
- `lora_grad` loss=`0.0`，grad_norm=`0.0`，耗时约 `59.893` 秒。
- scoped trainable 参数摘要：leaf=`53`，元素数=`466,958,097`。
- 远端 checkpoint 目录大小约 `987MB`；该目录已被 `.gitignore` 排除，不会进入 Git。
- 本地 `python scripts/validate_repro_workspace.py` 已通过。

### 当前边界

- 这是 LoRA reduced 的单步反向与 scoped checkpoint 写出链路，不是完整训练，也不是可直接提交的完整 policy checkpoint。
- scoped checkpoint 只包含 `config.trainable_filter` 选中的 trainable params；下一步必须审计它如何与 `pi05_base` base params 合并恢复。
- loss 与 grad_norm 都是 `0.0`，只能说明链路可跑通，不能说明策略质量。
- 真实 RoboChallenge 提交仍需要用户提供网站 `user_token` 与 `submission_id`。

### 下一步

- P0：补齐 LoRA scoped checkpoint restore/merge 审计，明确提交或推理时如何加载 `pi05_base + scoped trainable params`。
- P1：准备 RoboChallenge 提交包清单和 token/submission_id 缺口说明。

## 2026-06-02 第十六轮：LoRA scoped checkpoint 恢复/合并审计

### 已完成

- 新增 `scripts/audit_openpi_rtc_lora_checkpoint_restore.py`，专门审计 `pi05_base + LoRA scoped trainable checkpoint` 的恢复/合并链路。
- 修复 scoped checkpoint 读取时的 bfloat16 兼容点：`np.savez` 写出的 bfloat16 在 `np.load` 中显示为 `|V2`，恢复时需要先按 `ml_dtypes.bfloat16` 复原视图，再转换为目标 dtype。
- 生成 `reports/openpi_rtc_lora_checkpoint_restore_audit.md` 和 `runs/openpi_rtc_lora_checkpoint_restore_audit.json`。
- 已将 restore/merge 审计纳入 `scripts/validate_repro_workspace.py`。
- 更新 `README.md` 的当前 P0，避免继续把 restore 审计列为未完成事项。

### 验证结果

- restore 审计：`passed=true`。
- LoRA 模型 leaf：`73`；`pi05_base` 合并后 leaf：`73`。
- `cfg.trainable_filter` key：`53`；checkpoint key：`53`；二者严格匹配，没有缺失 key、额外 key 或非 trainable key。
- checkpoint 中 LoRA key：`20`；`knob_*` key：`2`。
- 合并前 `ShapeDtypeStruct` 占位：`22`；scoped 覆盖 leaf：`53`；合并后剩余占位：`0`。
- 参数树 shape/dtype 校验通过；NNX state replace smoke 通过。
- 远端 `python3 scripts/validate_repro_workspace.py` 已通过。

### 当前边界

- scoped checkpoint 不是完整 policy checkpoint；恢复时必须同时使用相同 config、相同 LoRA variant、`pi05_base` 基础权重和 scoped trainable params。
- 本轮只验证恢复/合并链路，不代表策略质量提升，也没有完成 RoboChallenge 真实提交。
- 真实 RoboChallenge 提交仍需要用户提供网站 `user_token` 与 `submission_id`。

### 下一步

- P0：准备 RoboChallenge 提交包清单和最小提交模板，明确入口脚本、依赖、模型恢复材料、Table30/Table30v2 目标说明与 token/submission_id 缺口。
- P1：把 `pi05_base + LoRA scoped trainable params` 的恢复步骤整理成最小推理模板，供后续真实提交入口复用。

## 2026-06-02 第十七轮：RoboChallenge 提交包清单和最小启动模板

### 已完成

- 新增 `scripts/audit_robochallenge_submission_package.py`，生成并审计提交包清单、机器可读 manifest 和无明文凭据启动模板。
- 生成 `reports/robochallenge_submission_package_checklist.md`。
- 生成 `runs/robochallenge_submission_package_audit.json`。
- 生成 `submission/README.md`、`submission/submission_manifest_template.json` 和 `submission/run_table30v2_aloha_demo_template.sh`。
- 中文 Notebook 新增第 20 节“RoboChallenge 提交包清单与最小启动模板”。
- 已将提交包清单/模板审计纳入 `scripts/validate_repro_workspace.py`。

### 验证结果

- 提交包审计：`passed=true`。
- 当前可运行目标：`Table30v2 / aloha / pack_the_toothbrush_holder`。
- `demo.py` 必需参数检查通过：`user_token`、`submission_id`、`checkpoint`、`prompt`、`action_type`、`duration`、`valid_action_num`、`image_size`、`robot_type`。
- mock smoke、Table30v2 ALOHA 映射、LoRA restore 审计均被提交包审计引用并通过。
- `submission/run_table30v2_aloha_demo_template.sh` 通过 `bash -n`。
- 无凭据运行模板会立即要求 `ROBOCHALLENGE_USER_TOKEN`，不会误连真实平台。
- 远端 `python3 scripts/validate_repro_workspace.py` 已通过。

### 当前边界

- 当前提交模板默认走官方 pi0.5 Table30v2 ALOHA baseline checkpoint。
- LoRA scoped checkpoint 已通过恢复/合并审计，但仍不是 `demo.py --checkpoint` 可直接消费的完整 policy checkpoint。
- 真实提交仍需要用户提供 `ROBOCHALLENGE_USER_TOKEN` 和 `ROBOCHALLENGE_SUBMISSION_ID`。
- 如果目标是原始 Table30，而不是 Table30v2 ALOHA，需要另补原始 Table30 数据、任务和机器人配置入口。

### 下一步

- P0：把 `pi05_base + LoRA scoped trainable params` 整理成 `demo.py` 可复用的最小推理入口或完整 checkpoint 包，缩小 LoRA 路线与真实提交入口之间的差距。
- P1：等待用户提供真实 token/submission_id 后，才运行 `submission/run_table30v2_aloha_demo_template.sh` 进入真实评测。
## 2026-06-02 第十八轮：LoRA 推理 checkpoint 物化布局审计

### 已完成

- 新增 `scripts/audit_openpi_rtc_lora_inference_checkpoint_layout.py`，用于审计 `pi05_base + LoRA scoped trainable params` 如何整理成 `create_trained_policy` / `demo.py` 可读取的完整推理 checkpoint 目录。
- 默认只做布局审计和 tiny Orbax checkpoint save/restore smoke，不自动写出 12GB+ 完整权重目录。
- 明确推理目录形态：`<checkpoint>/params` 必须是 Orbax PyTree checkpoint，顶层 item 为 `{"params": full_params}`；norm stats 需要放在 `<checkpoint>/assets/cvpr_multitask_aloha/norm_stats.json`。
- 确认完整物化目标目录 `runs/openpi_rtc_lora_materialized_policy_checkpoint/` 的内容会被 `.gitignore` 的 `runs/*checkpoint*/` 规则排除。
- 生成 `reports/openpi_rtc_lora_inference_checkpoint_layout.md` 和 `runs/openpi_rtc_lora_inference_checkpoint_layout_audit.json`。
- 已将该审计纳入 `scripts/validate_repro_workspace.py`。

### 验证结果

- layout audit：`passed=true`。
- LoRA 模型 leaf：`73`；`cfg.trainable_filter` key：`53`。
- scoped checkpoint leaf：`53`，metadata 为 `scoped_trainable_checkpoint / cfg.trainable_filter`。
- restore/merge 审计引用通过：合并后 `ShapeDtypeStruct` 占位 leaf 为 `0`。
- 官方 ALOHA norm stats 存在：`/home/yjl/yjl/RoboChallenge/checkpoints/table30v2_multitask_baseline_aloha/assets/cvpr_multitask_aloha/norm_stats.json`。
- tiny Orbax save/restore smoke 通过：写入 `runs/openpi_rtc_lora_checkpoint_layout_smoke/params` 后可由 `openpi_rtc.models.model.restore_params` 读回。
- 远端 `python3 scripts/validate_repro_workspace.py` 已通过。

### 当前边界

- `direct_demo_checkpoint_ready=false`：本轮没有自动物化完整 12GB+ checkpoint，因此 LoRA scoped checkpoint 仍不能直接传给 `demo.py --checkpoint`。
- 如需写出完整 checkpoint，需要显式运行：`python3 scripts/audit_openpi_rtc_lora_inference_checkpoint_layout.py --materialize --force`。
- 真实 RoboChallenge 提交仍需要用户提供 `ROBOCHALLENGE_USER_TOKEN` 和 `ROBOCHALLENGE_SUBMISSION_ID`，不能伪造。

### 下一步

- P0：在用户确认允许写出大文件后，运行 `--materialize --force` 生成完整 LoRA 推理 checkpoint，并用 `create_trained_policy` 做恢复 smoke。
- P1：如果不走 LoRA 物化路线，继续使用官方 Table30v2 ALOHA baseline checkpoint 作为当前可运行提交模板。
## 2026-06-02 第十九轮：LoRA 完整 checkpoint 物化与 policy 加载 smoke

### 已完成

- 运行 `scripts/audit_openpi_rtc_lora_inference_checkpoint_layout.py --materialize --force`，把 `pi05_base + LoRA scoped trainable params` 物化为完整推理 checkpoint。
- 完整 checkpoint 目录：`runs/openpi_rtc_lora_materialized_policy_checkpoint`，远端大小约 `12G`，仍被 `.gitignore` 的 `runs/*checkpoint*/` 排除。
- 新增 `scripts/smoke_openpi_rtc_materialized_policy.py`，用 `openpi_rtc.policies.policy_config.create_trained_policy` 直接加载完整物化 checkpoint。
- 更新提交包审计：`direct_demo_checkpoint_ready=true`，但真实网站提交仍需要 token/submission_id 和可访问 checkpoint link。
- 生成 `reports/openpi_rtc_lora_inference_checkpoint_materialize.md`、`runs/openpi_rtc_lora_inference_checkpoint_materialize_status.json`、`reports/openpi_rtc_lora_materialized_policy_smoke.md` 和 `runs/openpi_rtc_lora_materialized_policy_smoke_status.json`。

### 验证结果

- checkpoint 物化：`passed=true`，`direct_demo_checkpoint_ready=true`。
- 物化耗时：约 `20.842` 秒。
- 物化后恢复 leaf：`73`。
- `assets/cvpr_multitask_aloha/norm_stats.json` 存在。
- `create_trained_policy` smoke：`passed=true`，policy 类型 `Policy`，模型类型 `Pi0`，加载耗时约 `4.831` 秒。

### 当前边界

- 本地 LoRA checkpoint 已经可以被 `create_trained_policy` 加载，但还没有上传为 RoboChallenge 网站可访问的 checkpoint link。
- 真实提交仍需要用户提供 `ROBOCHALLENGE_USER_TOKEN` 和 `ROBOCHALLENGE_SUBMISSION_ID`。
- 当前可运行链路仍是 Table30v2 ALOHA；如果目标切回原始 Table30，需要另补数据和配置入口。

### 下一步

- P0：准备 LoRA checkpoint 的上传/链接方案，或在用户给出凭据后用官方 baseline/LoRA 本地 checkpoint 分别跑真实提交入口。
- P1：补一个不联网的 `demo.py --checkpoint runs/openpi_rtc_lora_materialized_policy_checkpoint` 参数模板，避免提交时手工改路径。

## 2026-06-02 第二十轮：LoRA 提交 runner 模板与审计闭环

### 已完成

- 扩展 `scripts/audit_robochallenge_submission_package.py`，同时生成 baseline runner 和 LoRA runner。
- 新增 `submission/run_table30v2_aloha_lora_demo_template.sh`，默认 checkpoint 为 `runs/openpi_rtc_lora_materialized_policy_checkpoint`。
- 提交包审计新增两类检查：`bash -n` 语法检查、无凭据 fail-fast 检查；不会在缺少 `ROBOCHALLENGE_USER_TOKEN` 时误连真实平台。
- 更新 `submission/submission_manifest_template.json`，记录 baseline 与 LoRA 两个 runner 模板。
- 更新 `scripts/validate_repro_workspace.py`，把 LoRA runner、manifest 双 runner 字段、无明文 secret 检查纳入最低交接验证。
- 中文 Notebook 新增第 23 节，记录 LoRA runner 的生成、审计和验证命令。

### 验证结果

- baseline runner：通过 `bash -n`，无凭据运行会立即要求 `ROBOCHALLENGE_USER_TOKEN`。
- LoRA runner：通过 `bash -n`，无凭据运行会立即要求 `ROBOCHALLENGE_USER_TOKEN`。
- LoRA runner 默认路径包含 `runs/openpi_rtc_lora_materialized_policy_checkpoint`，不写入明文 token、submission_id 或外部密钥。
- 远端 `python3 scripts/validate_repro_workspace.py` 需要在同步并重跑提交包审计后验证。

### 当前边界

- LoRA checkpoint 本地可被 policy 加载，但还没有上传成 RoboChallenge 网站可访问的 checkpoint link。
- 真实提交仍需要用户提供 `ROBOCHALLENGE_USER_TOKEN` 和 `ROBOCHALLENGE_SUBMISSION_ID`。
- 当前可运行链路仍是 Table30v2 ALOHA；如果目标切回原始 Table30，需要另补数据和配置入口。

### 下一步

- P0：同步到 Linux 后重跑提交包审计、workspace validator、notebook preflight 和 secret scan，并提交推送。
- P1：用户提供凭据和 checkpoint link 后，再运行 baseline/LoRA runner 进入真实评测入口。

## 2026-06-02 第二十一轮：LoRA checkpoint 导出就绪审计

### 已完成

- 新增 `scripts/audit_lora_checkpoint_export_readiness.py`，用于审计本地 LoRA 完整物化 checkpoint 是否具备上传/导出前置条件。
- 审计对象为 `runs/openpi_rtc_lora_materialized_policy_checkpoint`。
- 检查必需文件：`params/_METADATA`、`params/_CHECKPOINT_METADATA`、`params/manifest.ocdbt`、`params/ocdbt.process_0/manifest.ocdbt` 和 `assets/cvpr_multitask_aloha/norm_stats.json`。
- 检查 checkpoint 总大小、参数数据 shard 数量、最大文件抽样和 `.gitignore` 排除状态。
- 报告给出手动 tar 与 sha256 命令；默认不打包 12GB+ 文件，不上传外部服务，不写入任何 token。
- 新增 `--tar-stream-smoke`，用 `tar -C runs -cf - openpi_rtc_lora_materialized_policy_checkpoint | wc -c` 验证完整 checkpoint 可被 tar 读取，并记录 archive stream 字节数，但不生成大文件。
- 已将导出就绪审计纳入 `scripts/validate_repro_workspace.py`。

### 验证结果

- 导出就绪审计：`passed=true`，`local_export_ready=true`，`web_submission_ready=false`。
- checkpoint 文件数量：`18`；目录数量：`6`；总大小：`11.06 GB`。
- 参数数据 shard 数量：`13`。
- 必需文件全部存在：`params/_METADATA`、`params/_CHECKPOINT_METADATA`、`params/manifest.ocdbt`、`params/ocdbt.process_0/manifest.ocdbt`、`assets/cvpr_multitask_aloha/norm_stats.json`。
- `.gitignore` 命中 `runs/*checkpoint*/`，完整 checkpoint 不会进入 Git。
- tar stream smoke：`passed=true`，耗时 `19.666` 秒，archive stream bytes=`11879987200`，expected min bytes=`11879949503`。
- 远端 `python3 scripts/validate_repro_workspace.py` 已通过。

### 当前边界

- 本地 checkpoint 可以被 policy 加载，也具备导出前置结构，但还没有真实可访问 checkpoint link。
- 真实上传需要用户选择并授权存储位置。
- 真实提交仍需要 `ROBOCHALLENGE_USER_TOKEN` 和 `ROBOCHALLENGE_SUBMISSION_ID`。

### 下一步

- P0：运行 notebook preflight、secret scan 和 diff check 后提交推送。
- P1：用户授权存储位置后，按报告命令打包、上传并回填 checkpoint link。

## 2026-06-02 第二十二轮：checkpoint 上传通道审计

### 已完成

- 新增 `scripts/audit_checkpoint_upload_channels.py`，审计当前 Linux 机器是否已有可用上传工具和凭据迹象。
- 审计范围包括 `hf` / `huggingface-cli`、`gh`、`git-lfs`、`rclone`、`ossutil`、`aws`、`gsutil`、`gcloud`、`azcopy` 和 `curl`。
- 只检查命令是否存在、版本信息、环境变量是否存在、配置文件是否存在；不读取明文 token，不调用上传接口。
- 检查 `runs/openpi_rtc_lora_materialized_policy_checkpoint.tar` 是否尚未生成，并确认该 tar 路径会被 `.gitignore` 排除。
- 已将上传通道审计纳入 `scripts/validate_repro_workspace.py`。

### 验证结果

- 上传通道审计：`passed=true`，`uploads_performed=false`，`plaintext_credentials_read=false`。
- 本机可用上传相关工具：`git-lfs` 和 `curl`。
- 未发现 Hugging Face、GitHub CLI、rclone、OSS、AWS、GCS、Azure 的环境变量或配置文件凭据迹象。
- `runs/openpi_rtc_lora_materialized_policy_checkpoint.tar` 尚未生成；该 tar 路径会被 `.gitignore` 排除。
- 本审计不会上传 checkpoint，不会生成 12GB+ tar，不会伪造 checkpoint link。

### 当前边界

- 本地 checkpoint 已具备打包前置条件，但上传通道仍必须由用户选择并授权。
- 真实提交仍需要 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID` 和真实 checkpoint link。

### 下一步

- P0：运行 workspace validator、notebook preflight、secret scan 和 diff check 后提交推送。
- P1：用户确认上传通道后，按对应工具执行打包/上传，并把真实 checkpoint link 回填到 RoboChallenge。

## 2026-06-02 第二十三轮：真实提交 readiness gate

### 已完成

- 新增 `scripts/audit_real_submission_readiness.py`，汇总真实提交前置条件。
- 检查 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、`ROBOCHALLENGE_CHECKPOINT_LINK` 和 `ROBOCHALLENGE_LORA_CHECKPOINT_LINK` 是否存在，但不打印具体值。
- 检查 baseline/LoRA runner 是否存在并通过 `bash -n`。
- 引用提交包审计、LoRA checkpoint 导出审计和上传通道审计，区分“本地 runner 准备好”和“真实 Web 提交准备好”。
- 已将 readiness gate 纳入 `scripts/validate_repro_workspace.py`。

### 验证结果

- readiness gate：`passed=true`，`ready_for_real_submission=false`。
- Web 表单就绪：`false`；本地 baseline runner 就绪：`false`；本地 LoRA runner 就绪：`false`。
- `platform_contacted=false`，`credentials_printed=false`。
- baseline/LoRA runner 均存在并通过 `bash -n`。
- 输入证据已就绪：提交包审计、LoRA 导出审计、上传通道审计均通过；baseline checkpoint 与 LoRA checkpoint 均存在。
- 阻塞项准确记录：缺少 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、真实 checkpoint link，且尚未执行 checkpoint 上传。

### 当前边界

- readiness gate 只做本地前置检查，不连接 RoboChallenge 平台，不提交任务。
- 真实提交仍需要用户授权上传通道、真实 checkpoint link、`ROBOCHALLENGE_USER_TOKEN` 和 `ROBOCHALLENGE_SUBMISSION_ID`。

### 下一步

- P0：运行 workspace validator、notebook preflight、secret scan 和 diff check 后提交推送。
- P1：用户提供真实凭据和 checkpoint link 后，再运行 readiness gate；通过后才能执行 baseline/LoRA runner。

## 2026-06-02 第二十四轮：真实提交交接文档审计

### 已完成

- 新增 `submission/REAL_SUBMISSION_HANDOFF.md`，把用户拿到 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID` 和真实 checkpoint link 后的最短命令链固化下来。
- 新增 `scripts/audit_submission_handoff_docs.py`，检查交接文档是否包含必需环境变量、runner 路径、tar/sha256/readiness 命令和安全边界。
- 审计明确不会连接 RoboChallenge 平台、不会上传 checkpoint、不会打印凭据。
- 已将交接文档审计纳入 `scripts/validate_repro_workspace.py`。

### 验证结果

- 交接文档审计：`passed=true`，`platform_contacted=false`，`uploads_performed=false`，`credentials_printed=false`。
- 必需环境变量、路径、命令和安全边界全部命中；`secret_patterns_found=[]`。
- `python3 scripts/validate_repro_workspace.py` 已通过，并新增输出“真实提交交接文档审计已通过”。
- Notebook preflight 已通过，第 27 节可执行交接文档审计。
- `python3 -m py_compile`、`git diff --check` 和凭据扫描已通过。

### 当前边界

- 本轮只补齐无凭据状态下的真实提交交接证据，不会伪造 token、submission id 或 checkpoint link。
- 真实提交仍需要用户授权上传通道，并提供真实可访问 checkpoint link。

### 下一步

- P0：用户提供真实 token、submission id 和 checkpoint link 后，重新运行 readiness gate。
- P1：用户授权上传通道后，再生成 tar、sha256 并上传物化 LoRA checkpoint。

## 2026-06-02 第二十五轮：runner 占位符凭据防误跑

### 已完成

- baseline/LoRA runner 新增 `reject_placeholder`，在调用 `demo.py` 前拒绝 `<真实 ...>`、`example`、`replace_me` 这类占位符凭据。
- `scripts/audit_robochallenge_submission_package.py` 新增 `placeholder_credentials_failfast` 审计，用占位符环境变量运行 runner 并要求 fail-fast。
- `scripts/validate_repro_workspace.py` 已将 `mentions_placeholder_guard` 和 `placeholder_credentials_failfast` 纳入最低交接验证。
- Notebook 第 23 节输出新增 `placeholder` 字段，方便在 Jupyter 中直接查看 runner 占位符拦截状态。

### 验证结果

- 提交包审计：`passed=true`，baseline/LoRA runner 的 `placeholder_credentials_failfast.passed=true`。
- 占位符凭据运行返回码为 `64`，stderr 为“`ROBOCHALLENGE_USER_TOKEN 看起来仍是占位符，请设置真实值。`”。
- `python3 scripts/validate_repro_workspace.py` 已通过。
- Notebook preflight 已通过；无关耗时和磁盘字段漂移已恢复。
- 待运行：最终 secret scan、diff check 和提交推送。

### 当前边界

- 本轮只增强本地 runner 防误跑逻辑，不连接 RoboChallenge 平台，不上传 checkpoint，不伪造凭据。

### 下一步

- P0：最终 secret scan、diff check 后提交推送。

## 2026-06-02 第三十九轮：提交准备材料 manifest 审计

### 已完成

- 新增 `scripts/audit_submission_artifact_manifest.py`，生成提交准备材料 manifest，不读取凭据、不上传、不连接 RoboChallenge 平台。
- manifest 覆盖 README、work.md、核心 Notebook、submission runner/template、handoff 文档、关键复现报告、checkpoint/link/readiness/preflight 报告和 GUI HTML，并为小文件计算 sha256。
- 审计显式检查 `submission/robochallenge_env.local.sh`、`.env`、`.env.local`、物化 checkpoint 目录、tar、sha256 和分片路径不会被 Git 跟踪。
- `scripts/audit_submission_preflight_bundle.py` 已把 `submission_artifact_manifest` 纳入一键预检子命令。
- `scripts/validate_repro_workspace.py` 已纳入 manifest JSON/报告/脚本和通过条件。
- `submission/REAL_SUBMISSION_HANDOFF.md`、`submission/AUTHORIZED_SUBMISSION_SEQUENCE.md` 和相关审计脚本已补充 manifest 命令。
- Notebook 新增第 39 节“提交准备材料 manifest 审计”。

### 验证结果

- 本地语法检查已通过：`audit_submission_artifact_manifest.py`、preflight、handoff、authorized sequence 和 validator 均可编译。
- Notebook 第 39 节已修复 PowerShell 中文写入导致的问号乱码，当前问号计数为 `0`。
- Linux 端 manifest 审计已通过：`passed=true`，材料数量大于 30，缺失材料和禁止跟踪路径均为 `0`。
- Linux 端 `bash scripts/run_notebook_preflight.sh` 已通过，第 39 节可在 Notebook 流程中复跑。
- Linux 端 `python3 scripts/validate_repro_workspace.py` 已通过，新增输出“提交准备材料 manifest 审计已通过”。
- Linux 端明文凭据扫描已通过：`hit_count=0`。
- Linux 端 `git diff --check` 已通过；Notebook 和 work.md 行尾已规范为 LF。

### 当前边界

- 本轮只审计小文件材料清单和 Git 忽略边界，不生成 tar、不上传 checkpoint、不读取或伪造真实 token、submission id、checkpoint link。
- 真实提交仍缺 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID` 和真实可访问 checkpoint link。

### 下一步

- P0：提交并推送本轮提交准备材料 manifest 审计产物。

## 2026-06-02 第三十八轮：真实提交环境变量模板审计

### 已完成

- 新增 `submission/robochallenge_env_template.sh`，只保存 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、`ROBOCHALLENGE_LORA_CHECKPOINT_LINK` 和 `ROBOCHALLENGE_CHECKPOINT_LINK` 的占位符。
- `.gitignore` 新增 `.env.local`、`*.env.local`、`submission/robochallenge_env.local.sh` 和 `submission/*.local.sh`，避免真实提交凭据副本进入 Git。
- 新增 `scripts/audit_submission_env_template.py`，只审计 tracked 模板和 Git 忽略规则，不读取、不打印真实凭据。
- `scripts/audit_submission_preflight_bundle.py`、`scripts/audit_submission_handoff_docs.py`、`scripts/audit_authorized_submission_sequence.py` 和 `scripts/validate_repro_workspace.py` 已纳入环境模板审计。
- `submission/REAL_SUBMISSION_HANDOFF.md` 和 `submission/AUTHORIZED_SUBMISSION_SEQUENCE.md` 已改为先复制模板到本地忽略副本，再编辑并 `source` 本地副本。
- Notebook 新增第 38 节“真实提交环境变量模板审计”，可在 Jupyter 中复跑该检查。

### 验证结果

- 本地 `python scripts/audit_submission_env_template.py` 已通过：`passed=true`，四个必需变量均存在且保持占位符。
- 本地真实副本路径 `submission/robochallenge_env.local.sh`、`.env` 和 `.env.local` 均已被 Git 忽略。
- `secret_pattern_hits=[]`，`credentials_read=false`，`credentials_printed=false`，`secret_values_printed=false`。
- 本地交接文档审计和授权后提交顺序审计已通过；总预检包已通过并保持 `go_no_go=blocked`。
- Linux 端 `bash scripts/run_notebook_preflight.sh` 已通过，第 38 节可在 Notebook 流程中复跑。
- Linux 端 `python3 scripts/validate_repro_workspace.py` 已通过，新增输出“真实提交环境变量模板审计已通过”。
- Linux 端 `git diff --check` 已通过；Notebook 行尾已规范为 LF。

### 当前边界

- 本轮不写入真实 token、submission id 或 checkpoint link，不生成 tar，不上传 checkpoint，不连接 RoboChallenge 平台。
- 真实提交仍缺 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID` 和真实可访问 checkpoint link。

### 下一步

- P0：提交并推送本轮环境变量模板审计产物。
## 2026-06-02 第三十七轮：GUI 面板纳入提交前预检汇总

### 已完成
- 更新 `scripts/render_submission_status_dashboard.py`，把 `runs/submission_preflight_bundle.json` 纳入 GUI 数据源。
- `reports/submission_status_dashboard.html` 新增“提交前预检汇总”卡片，展示 `go/no-go=blocked`、`no-contact=是` 和 `no-leak=是`。
- `runs/submission_status_dashboard.json` 新增 `preflight_passed`、`preflight_go_no_go`、`preflight_no_contact`、`preflight_no_secret_leak` 等机器可读字段。
- 更新 `scripts/validate_repro_workspace.py`，强制要求 GUI 至少 11 张卡片、至少 4 个阻塞卡片，并检查预检汇总卡片和 no-contact/no-leak 字段。
- 更新 Notebook 第 34 节 GUI 单元：重新生成面板后会断言“提交前预检汇总”卡片、`go/no-go=blocked` 和 no-contact/no-leak 状态。

### 验证结果
- 本地 `python scripts\render_submission_status_dashboard.py` 已通过，`card_count=11`、`blocked_count=4`、`source_count=11`。
- 本地 `python scripts\validate_repro_workspace.py` 已通过。
- Linux 已重跑 dashboard 渲染、`validate_repro_workspace.py`、`run_notebook_preflight.sh`、`audit_plaintext_secrets.py` 和 `git diff --check`，均已通过。
- 新增/更新的 Notebook、dashboard JSON 和 dashboard HTML 已检查：无问号乱码、无替换字符、无常见 mojibake。
- 浏览器插件拒绝直接打开本地 `file://` HTML；本轮未绕过该安全策略，改用静态 HTML/JSON 校验。

### 当前边界
- GUI 只展示状态，不连接 RoboChallenge 平台、不上传 checkpoint、不读取或显示真实 token/link。
- 当前真实提交仍缺 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID` 和真实可访问 checkpoint link，因此 GUI 中预检汇总正确显示 `go/no-go=blocked`。

### 下一步
- P0：提交并推送本轮 GUI 面板预检汇总卡片产物。
## 2026-06-02 第三十六轮：真实提交前预检汇总

### 已完成
- 新增 `scripts/audit_submission_preflight_bundle.py`，一键串联 checkpoint link 回填审计、默认下载校验协议、真实提交 readiness gate、handoff 文档审计和明文凭据扫描。
- 修复 `scripts/audit_checkpoint_link_intake.py` 的场景 smoke：内部子进程改用当前 Python 解释器，并固定 UTF-8 输出，避免 Windows 本地 `python3` 缺失或默认编码导致误失败。
- 修复 `scripts/audit_real_submission_readiness.py` 的本地兼容性：`bash -n` 改为通过 stdin 检查脚本文本，并收敛 WSL relay 的不可打印 stderr，不污染 JSON/Markdown。
- `submission/REAL_SUBMISSION_HANDOFF.md` 新增一键预检命令，`scripts/audit_submission_handoff_docs.py` 已强制检查该命令和脚本路径。
- `scripts/validate_repro_workspace.py` 新增真实提交前预检汇总 gate，要求 no-contact、no-upload、no-secret-leak 且当前 go/no-go 仍准确为 `blocked`。
- Notebook `notebooks/robochallenge_pi05_submit_cn.ipynb` 新增第 37 节“真实提交前预检汇总”，可在 Jupyter 中复现该 bundle。

### 验证结果
- 本地 `python scripts\audit_submission_preflight_bundle.py` 已通过：`passed=true`，`go_no_go=blocked`，五个子审计 returncode 均为 `0`。
- 本地 bundle 关键边界均为 false：`platform_contacted=false`、`uploads_performed=false`、`download_host_contacted=false`、`credentials_printed=false`、`link_values_printed=false`、`secret_values_printed=false`。
- 本地 handoff 审计已通过，并确认 `submission_preflight_bundle` 命令和 `scripts/audit_submission_preflight_bundle.py` 路径均已被文档覆盖。
- Linux 已重跑 `audit_submission_preflight_bundle.py`、`validate_repro_workspace.py`、`run_notebook_preflight.sh`、`audit_plaintext_secrets.py` 和 `git diff --check`，均已通过。
- 新增/更新的 handoff 文档、bundle 报告、bundle JSON、Notebook 第 37 节均已检查：无问号乱码、无替换字符、无常见 mojibake。

### 当前边界
- 本轮仍不生成 tar、不上传 checkpoint、不连接 RoboChallenge 平台、不接触 checkpoint 下载 host、不读取或保存真实 token/link。
- 当前真实提交仍缺 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID` 和真实可访问 checkpoint link，因此 bundle 的正确结论是 `blocked`，不是 ready。

### 下一步
- P0：提交并推送本轮真实提交前预检汇总产物。

## 2026-06-02 第二十九轮：明文凭据扫描审计

### 已完成

- 新增 `scripts/audit_plaintext_secrets.py`，扫描 Git 跟踪文件和未忽略的未跟踪文件，检查 OpenAI、Hugging Face、GitHub、AWS、private key 和 RoboChallenge 凭据赋值形态。
- 审计只输出命中文件、行号和规则名，不输出任何疑似凭据值。
- 生成 `reports/plaintext_secret_scan.md` 和 `runs/plaintext_secret_scan.json`，并纳入 `scripts/validate_repro_workspace.py` 总体验证。
- Notebook 新增第 30 节“明文凭据扫描”，可在 Jupyter 中直接复跑该审计。

### 验证结果

- `python3 -m py_compile scripts/audit_plaintext_secrets.py scripts/validate_repro_workspace.py` 已通过。
- 明文凭据扫描：`passed=true`，`hit_count=0`，`secret_values_printed=false`，`platform_contacted=false`，`uploads_performed=false`。
- `python3 scripts/validate_repro_workspace.py` 已通过，并新增输出“明文凭据扫描已通过”。
- Notebook preflight 已通过，第 30 节可执行；本轮新增 Notebook 文本未出现问号替换乱码。

### 当前边界

- 本轮不生成 checkpoint tar，不上传 checkpoint，不连接 RoboChallenge 平台，也不读取或伪造真实 token。
- 真实提交仍需要用户提供 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID` 和可访问的 checkpoint link。

### 下一步

- P0：提交前运行最终 `git diff --check`、总体验证和明文凭据扫描；通过后提交推送。

## 2026-06-02 第三十轮：checkpoint 归档生成 dry-run

### 已完成

- 新增 `scripts/create_checkpoint_archive.py`，把 LoRA 物化 checkpoint 的 tar/sha256 生成流程从手工命令变成受控脚本。
- 脚本默认只执行 dry-run，检查 checkpoint 目录、Git 忽略规则、tar 工具、磁盘空间和执行命令形态。
- 真正生成约 12GB tar 必须显式传入 `--execute --confirm-create-large-archive`；本轮没有使用该执行门槛。
- 如果只传 `--execute` 但缺少二次确认，脚本会返回失败并保持 dry-run，不会让用户误以为已经生成归档。
- 生成 `reports/checkpoint_archive_dry_run.md` 和 `runs/checkpoint_archive_dry_run.json`，并纳入 `scripts/validate_repro_workspace.py`。
- Notebook 新增第 31 节“checkpoint 归档生成 dry-run”，可在 Jupyter 中复跑该检查。

### 验证结果

- dry-run：`passed=true`，`dry_run=true`，`archive_created=false`，`sha256_created=false`。
- 安全边界：`upload_performed=false`，`credentials_read=false`，`platform_contacted=false`。
- 执行门槛：`execute_requested=false`，`explicit_execute_gate=false`；脚本报告中保留真实执行命令供用户授权后使用。
- `python3 -m py_compile scripts/create_checkpoint_archive.py scripts/validate_repro_workspace.py` 已在 Linux 上通过。
- Notebook preflight 已通过，第 31 节可执行；新增 Notebook 文本未出现问号替换乱码。
- `python3 scripts/validate_repro_workspace.py`、`python3 scripts/audit_plaintext_secrets.py` 和 `git diff --check` 已通过。

### 当前边界

- 本轮不生成 tar、不计算真实 sha256、不上传 checkpoint、不连接 RoboChallenge 平台。
- 真实提交仍需要用户提供 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID` 和可访问 checkpoint link。

### 下一步

- P0：同步到 Linux 后运行 dry-run、总体验证、Notebook preflight、明文凭据扫描和 `git diff --check`；通过后提交推送。

## 2026-06-02 第三十一轮：checkpoint link 回填审计

### 已完成

- 新增 `scripts/audit_checkpoint_link_intake.py`，离线检查 `ROBOCHALLENGE_CHECKPOINT_LINK` 和 `ROBOCHALLENGE_LORA_CHECKPOINT_LINK` 的回填形态。
- 审计只输出是否存在、长度、HTTPS 形态、archive/checkpoint 提示、占位符判定和布尔结论，不打印 checkpoint link 明文。
- 场景 smoke 覆盖三种情况：缺失链接应 blocked、占位符链接应 rejected、synthetic HTTPS 形态应 accepted。
- `submission/REAL_SUBMISSION_HANDOFF.md` 新增 checkpoint link 回填前检查步骤。
- `scripts/audit_submission_handoff_docs.py` 和 `scripts/validate_repro_workspace.py` 已纳入 link intake 审计要求。
- Notebook 新增第 32 节“checkpoint link 回填审计”，可在 Jupyter 中复跑该检查。

### 验证结果

- checkpoint link 回填审计：`passed=true`，当前环境 `link_shape_ready=false`，符合“真实链接缺失仍 blocked”的预期。
- 场景 smoke：缺失链接 blocked、占位符链接 rejected、synthetic HTTPS 形态 accepted，且 `link_values_printed=false`。
- 交接文档审计：`passed=true`，已要求包含 `python3 scripts/audit_checkpoint_link_intake.py` 和“不打印链接明文”边界。
- `python3 scripts/validate_repro_workspace.py` 已通过，并新增输出“Checkpoint link 回填审计已通过”。
- Notebook preflight 已通过，第 32 节可执行；新增 Notebook 文本未出现问号替换乱码。
- 明文凭据扫描已通过：`hit_count=0`，`secret_values_printed=false`。
- `git diff --check` 已通过。

### 当前边界

- 本轮不联网验证 checkpoint link 是否可下载，不生成 tar，不上传 checkpoint，不连接 RoboChallenge 平台。
- 当前真实提交仍缺 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID` 和真实可访问 checkpoint link。

### 下一步

- P0：同步到 Linux 后完成最终验证并提交推送。

## 2026-06-02 第三十二轮：用户授权后提交顺序审计

### 已完成

- 新增 `submission/AUTHORIZED_SUBMISSION_SEQUENCE.md`，固化用户授权后从离线自检、归档生成、上传、环境变量设置、link intake、readiness gate、runner dry-run 到真实 runner 的执行顺序。
- 新增 `scripts/audit_authorized_submission_sequence.py`，审计清单是否包含关键命令、环境变量、停止条件、安全护栏和当前输入证据。
- `submission/REAL_SUBMISSION_HANDOFF.md` 新增清单入口和审计命令。
- `scripts/audit_submission_handoff_docs.py` 和 `scripts/validate_repro_workspace.py` 已纳入授权后提交顺序审计。
- Notebook 新增第 33 节“用户授权后提交顺序审计”，可在 Jupyter 中复跑该检查。

### 验证结果

- 用户授权后提交顺序审计：`passed=true`，关键顺序 `link intake -> readiness -> dry-run -> real runner` 已通过。
- 清单覆盖命令：离线自检、归档 dry-run、显式归档生成、link intake、readiness gate、LoRA runner dry-run、LoRA 真实 runner 和 baseline runner。
- 安全边界：`platform_contacted=false`，`uploads_performed=false`，`archive_created=false`，`credentials_printed=false`，`link_values_printed=false`。
- 交接文档审计：`passed=true`，已要求包含 `submission/AUTHORIZED_SUBMISSION_SEQUENCE.md` 和 `python3 scripts/audit_authorized_submission_sequence.py`。
- `python3 scripts/validate_repro_workspace.py` 已通过，并新增输出“用户授权后提交顺序审计已通过”。
- Notebook preflight 已通过，第 33 节可执行；新增 Notebook 文本未出现问号替换乱码。
- 明文凭据扫描已通过：`hit_count=0`，`secret_values_printed=false`。
- `git diff --check` 已通过。

### 当前边界

- 本轮不执行真实 runner，不生成 tar，不上传 checkpoint，不读取或伪造真实 token，不连接 RoboChallenge 平台。
- 真实提交仍缺 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID` 和真实可访问 checkpoint link。

### 下一步

- P0：同步到 Linux 后完成最终验证并提交推送。

## 2026-06-02 第三十三轮：提交状态 GUI 面板

### 已完成

- 新增 `scripts/render_submission_status_dashboard.py`，从现有 JSON 审计结果生成静态 HTML 状态面板。
- 新增 `reports/submission_status_dashboard.html`，汇总 pi0.5 基模、pi0.6/pi0.7 release gap、Table30v2 ALOHA、LoRA policy、checkpoint 导出、归档生成、上传/link、readiness gate、授权后顺序和明文凭据扫描。
- 新增 `runs/submission_status_dashboard.json`，记录面板来源数量、卡片数量、已完成/待授权/需关注统计和当前阻塞。
- `scripts/validate_repro_workspace.py` 已纳入提交状态 GUI 面板检查。
- Notebook 新增第 34 节“提交状态 GUI 面板”，可在 Jupyter 中重新生成 HTML。

### 验证结果

- Linux 渲染已通过：`card_count=10`，`done_count=6`，`blocked_count=3`，`watch_count=1`。
- 面板不读取或显示真实凭据，状态中 `credentials_printed=false`，`link_values_printed=false`，`platform_contacted=false`。
- `python3 scripts/validate_repro_workspace.py` 已通过，并新增输出“提交状态 GUI 面板已通过”。
- Notebook preflight 已通过；第 34 节中文检查无问号乱码、无替换字符、无拉丁化 mojibake。
- 最终明文凭据扫描已通过：`hit_count=0`，`scanned_files=138`。
- `git diff --check` 已通过。

### 当前边界

- 本轮只生成静态 HTML GUI，不启动 Web 服务，不连接 RoboChallenge 平台，不上传 checkpoint。
- 真实提交仍缺 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID` 和真实可访问 checkpoint link。

### 下一步

- P0：提交推送本轮 GUI 面板产物。

## 2026-06-02 第三十四轮：checkpoint 分片上传计划审计

### 已完成

- 新增 `scripts/audit_checkpoint_split_plan.py`，离线计算 LoRA checkpoint tar 的 4GiB 分片上传计划。
- 生成 `reports/checkpoint_split_plan.md` 和 `runs/checkpoint_split_plan.json`，记录预计分片数量、每片大小、Git 忽略状态和授权后 split/cat/sha256 命令。
- `scripts/validate_repro_workspace.py` 已纳入分片计划检查。
- Notebook 新增第 35 节“checkpoint 分片上传计划审计”，可在 Jupyter 中重放该审计。

### 验证结果

- 分片计划审计：`passed=true`，预计 tar `11.064 GiB`，预计分片 `3` 个。
- 分片大小：前两片各 `4.0 GiB`，第三片 `3.064 GiB`。
- `archive_created=false`，`parts_created=false`，`upload_performed=false`，`credentials_read=false`，`platform_contacted=false`。
- 分片路径均被 Git 忽略；当前实际存在分片数量为 `0`。
- Linux 总体验证已通过，并新增输出“Checkpoint 分片上传计划审计已通过”。
- Notebook preflight 已通过；第 35 节中文检查无问号乱码、无替换字符、无拉丁化 mojibake。
- 最终明文凭据扫描已通过：`hit_count=0`，`scanned_files=141`。
- `git diff --check` 已通过。

### 当前边界

- 本轮不生成真实 tar、不生成分片、不上传 checkpoint、不读取或保存任何凭据。
- 真实分片上传仍需要用户明确授权生成 tar/sha256，并选择可由 RoboChallenge 评测端访问的存储通道。

### 下一步

- P0：提交推送本轮分片计划产物。

## 2026-06-02 第三十五轮：checkpoint link 下载校验审计

### 已完成

- 新增 `scripts/audit_checkpoint_link_download_verification.py`，默认离线审计 checkpoint link 下载校验协议。
- 生成 `reports/checkpoint_link_download_verification.md` 和 `runs/checkpoint_link_download_verification.json`，记录 curl 可用性、脱敏 HEAD/Range 命令、当前链接状态和阻塞项。
- `submission/REAL_SUBMISSION_HANDOFF.md` 已补充 link 下载校验步骤：默认不联网；用户明确授权后才运行 `--verify-download`。
- `scripts/audit_submission_handoff_docs.py` 已把下载校验步骤纳入交接文档审计。
- `scripts/validate_repro_workspace.py` 已纳入 checkpoint link 下载校验检查。
- Notebook 新增第 36 节“checkpoint link 下载校验审计”，可在 Jupyter 中重放默认离线审计。

### 验证结果

- 默认下载校验审计：`passed=true`，`verify_download_requested=false`。
- 当前仍缺真实 checkpoint link：`link_shape_ready=false`，因此 `download_verified=false`。
- 默认模式未接触下载 host：`download_host_contacted=false`，未连接 RoboChallenge 平台，未上传，未读取凭据，未打印链接明文。
- 授权后校验命令使用 `[REDACTED_CHECKPOINT_LINK]` 脱敏占位符，避免把真实链接写入报告。
- handoff 审计已通过，并新增 link download 四项输入证据。
- Linux 总体验证已通过，并新增输出“Checkpoint link 下载校验审计已通过”。
- Notebook preflight 已通过；第 36 节中文检查无问号乱码、无替换字符、无拉丁化 mojibake。
- 最终明文凭据扫描已通过：`hit_count=0`，`scanned_files=144`。
- `git diff --check` 已通过。

### 当前边界

- 本轮不联网验证真实下载，不生成 tar，不上传 checkpoint，不读取或保存真实链接。
- 真实下载校验必须等用户提供真实 checkpoint link 并明确授权 `--verify-download`。

### 下一步

- P0：提交推送本轮 checkpoint link 下载校验产物。

## 2026-06-02 第二十七轮：readiness gate 场景 smoke 与 Notebook 乱码修复

### 已完成

- 新增 `scripts/audit_real_submission_readiness_scenarios.py`，离线验证 readiness gate 在“缺少凭据”和“synthetic 凭据/链接齐全”两种场景下的布尔逻辑。
- 生成 `reports/real_submission_readiness_scenarios.md` 和 `runs/real_submission_readiness_scenarios.json`。
- 修复 Notebook 第 27 节的中文问号乱码，并新增第 28 节 readiness 场景 smoke。
- 已将 readiness 场景 smoke 纳入 `scripts/validate_repro_workspace.py`。

### 验证结果

- readiness 场景 smoke：`passed=true`，`platform_contacted=false`，`credentials_printed=false`，`synthetic_values_recorded=false`。
- 缺凭据场景：`ready_for_real_submission=false`，`web_form_ready=false`。
- synthetic 齐全场景：`ready_for_real_submission=true`，`web_form_ready=true`，baseline/LoRA runner ready 均为 `true`；该结果只验证 gate 逻辑翻转。
- Notebook 第 27-28 节问号计数为 `0`，preflight 已通过。
- `python3 scripts/validate_repro_workspace.py` 已通过，并新增输出“真实提交 readiness 场景 smoke 已通过”。
- 待运行：最终 secret scan、diff check 和提交推送。

### 当前边界

- synthetic ready 只验证本地 gate 逻辑，不代表真实提交完成。
- 真实提交仍需要用户提供真实 token、submission id 和可访问 checkpoint link。

### 下一步

- P0：最终 secret scan、diff check 后提交推送。
- P1：用户提供真实凭据和 checkpoint link 后，重新运行 readiness gate。

## 2026-06-02 第二十八轮：checkpoint 归档计划审计

### 已完成

- 新增 `scripts/audit_checkpoint_archive_plan.py`，审计 LoRA 完整物化 checkpoint 的 tar/sha256 归档计划。
- 检查 tar、sha256 和 split part 路径是否会被 Git 忽略，并验证磁盘空间是否满足预计 tar 的 2 倍余量。
- `.gitignore` 新增 `*.tar.sha256`，避免用户生成 sha256 文件后误加入 Git。
- Notebook 新增第 29 节 `checkpoint 归档计划审计`。
- 已将归档计划审计纳入 `scripts/validate_repro_workspace.py`。

### 验证结果

- 归档计划审计：`passed=true`，`archive_created=false`，`upload_performed=false`，`credentials_read=false`。
- 预计 tar 大小：`11.064 GB`；runs 剩余空间十 GB 桶：`480 GB`；2 倍空间余量检查通过。
- `archive_ignored=true`，`sha256_ignored=true`，`split_part_ignored=true`。
- 建议命令已审计：`tar -C runs -cf ...`、`sha256sum ... > ...tar.sha256` 和可选 `split -b 4G ...`。
- `python3 scripts/validate_repro_workspace.py` 已通过，并新增输出“Checkpoint 归档计划审计已通过”。
- Notebook preflight 已通过；无关耗时和磁盘字段漂移已恢复。
- 待运行：最终 secret scan、diff check 和提交推送。

### 当前边界

- 本轮不生成 tar、不计算真实 sha256、不上传 checkpoint。
- 真实上传仍需要用户选择并授权存储位置，再提供可访问 checkpoint link。

### 下一步

- P0：最终 secret scan、diff check 后提交推送。

## 2026-06-02 第二十六轮：runner dry-run 不连接平台检查

### 已完成

- baseline/LoRA runner 新增 `ROBOCHALLENGE_DRY_RUN=1`，用于只打印安全命令摘要，不调用 `demo.py`。
- 提交包审计新增 `dry_run_no_contact`，验证 dry-run 不打印 token/submission id 明文。
- 真实提交交接文档补充 LoRA runner dry-run 命令：`ROBOCHALLENGE_DRY_RUN=1 bash submission/run_table30v2_aloha_lora_demo_template.sh`。
- `scripts/audit_submission_handoff_docs.py` 已将 dry-run 命令和“不打印凭据”边界纳入审计。

### 验证结果

- 提交包审计：`passed=true`，baseline/LoRA `dry_run_no_contact.passed=true`，`printed_secret=false`。
- dry-run 输出只包含 `dry_run=true`、checkpoint、prompt 长度、token 长度、submission id 长度和 robot type。
- 交接文档审计：`passed=true`，新增 `lora_runner_dry_run=true` 和 `says_dry_run_no_credentials=true`。
- `python3 scripts/validate_repro_workspace.py` 已通过。
- Notebook preflight 已通过；无关耗时和磁盘字段漂移已恢复。
- 待运行：最终 secret scan、diff check 和提交推送。

### 当前边界

- dry-run 只验证 runner 命令形态和凭据不泄露，不代表 RoboChallenge 平台提交成功。
- 真实提交仍需要用户提供真实 token、submission id、checkpoint link，并在 readiness gate 通过后执行。

### 下一步

- P0：最终 secret scan、diff check 后提交推送。
## 2026-06-02 第四十轮：runner dry-run checkpoint/link 明文脱敏

### 已完成

- 修复 `submission/run_table30v2_aloha_demo_template.sh` 和 `submission/run_table30v2_aloha_lora_demo_template.sh` 的 dry-run 输出：不再打印 `checkpoint=$CHECKPOINT`，改为只打印 `checkpoint_length`。
- 更新 `scripts/audit_robochallenge_submission_package.py`，使用 synthetic checkpoint URL 执行 baseline/LoRA dry-run，并验证 token、submission id、checkpoint/link 明文均未出现在输出中。
- `scripts/validate_repro_workspace.py` 新增 `printed_checkpoint=false` 和 `has_checkpoint_length=true` 检查。
- `submission/REAL_SUBMISSION_HANDOFF.md` 和 `submission/AUTHORIZED_SUBMISSION_SEQUENCE.md` 已明确 dry-run 只打印 checkpoint 长度，不打印 checkpoint/link 明文。
- `scripts/audit_submission_handoff_docs.py` 和 `scripts/audit_authorized_submission_sequence.py` 已纳入对应安全边界。

### 验证结果

- Linux 端 submission package 审计已通过：baseline/LoRA `dry_run_no_contact.passed=true`，`printed_secret=false`，`printed_checkpoint=false`，`has_checkpoint_length=true`。
- baseline/LoRA dry-run 输出只包含 `dry_run=true`、`checkpoint_length=64`、`prompt_length=122`、token 长度、submission id 长度和 `robot_type=aloha`。
- Linux 端 Notebook preflight 已通过；现有提交包审计 cell 可复跑该检查。
- Linux 端 `python3 scripts/validate_repro_workspace.py` 已通过。
- Linux 端 `git diff --check` 已通过。

### 当前边界

- 本轮只修复 dry-run 脱敏，不生成 tar，不上传 checkpoint，不读取或伪造真实 token、submission id、checkpoint link。
- 真实提交仍缺 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID` 和真实可访问 checkpoint link。

### 下一步

- P0：提交并推送本轮 runner dry-run 脱敏产物。

## 2026-06-02 第四十一轮：真实提交阻塞项摘要审计

### 已完成

- 新增 `scripts/audit_submission_blockers_summary.py`，汇总 readiness、checkpoint link、上传通道、manifest、preflight、提交包和明文凭据扫描结果。
- 新增机器可读产物 `runs/submission_blockers_summary.json` 和中文报告 `reports/submission_blockers_summary.md`。
- Notebook `notebooks/robochallenge_pi05_submit_cn.ipynb` 新增第 40 节，Jupyter 内可直接复跑阻塞项摘要审计。
- `submission/REAL_SUBMISSION_HANDOFF.md` 和 `submission/AUTHORIZED_SUBMISSION_SEQUENCE.md` 已加入阻塞项摘要命令。
- `scripts/audit_submission_handoff_docs.py`、`scripts/audit_authorized_submission_sequence.py` 和 `scripts/validate_repro_workspace.py` 已纳入该摘要审计。

### 验证结果

- Linux 端 `python3 scripts/audit_submission_blockers_summary.py` 已通过：`passed=true`，`go_no_go=blocked`，`ready_for_real_submission=false`，`blocking_count=11`。
- 阻塞摘要确认未连接平台、未上传、未读取凭据、未打印 token/submission id/checkpoint link 明文。
- Linux 端 Notebook preflight 已通过；第 40 节可执行。现存 nbformat `MissingIDFieldWarning` 来自历史 cell，不影响执行。
- Linux 端 `python3 scripts/validate_repro_workspace.py` 已通过，并新增输出“真实提交阻塞项摘要已通过”。
- Linux 端 `git diff --check` 和 UTF-8/乱码哨兵检查已通过。

### 当前边界

- 本轮只补齐真实提交前的阻塞项证据汇总，不生成 tar、不上传 checkpoint、不连接 RoboChallenge 平台、不伪造 token 或 submission id。
- 当前真实提交仍缺 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、真实可访问 checkpoint link，以及用户对 12GB+ checkpoint 归档/上传的明确授权。

### 下一步

- P0：提交并推送本轮阻塞项摘要审计产物。
- P1：用户提供真实凭据和 checkpoint link 后，先运行 `python3 scripts/audit_real_submission_readiness.py`，再决定是否进入真实 runner。

## 2026-06-02 第四十二轮：Notebook 结构与编码审计

### 已完成

- 修复 `notebooks/robochallenge_pi05_submit_cn.ipynb` 中第 38、39 节 4 个历史 cell 缺失 `id` 的问题。
- 新增 `scripts/audit_notebook_structure.py`，静态审计 Notebook cell id、输出状态、execution_count、LF 行尾、乱码哨兵和第 40 节阻塞摘要标记。
- 新增 `runs/notebook_structure_audit.json` 和 `reports/notebook_structure_audit.md`。
- `scripts/audit_submission_preflight_bundle.py` 已将 `notebook_structure` 纳入一键预检。
- `scripts/audit_submission_artifact_manifest.py`、`scripts/audit_submission_blockers_summary.py` 和 `scripts/validate_repro_workspace.py` 已纳入 Notebook 结构审计证据。

### 验证结果

- Linux 端 Notebook 结构审计已通过：`cell_count=83`，`missing_id_indexes=[]`，`duplicate_ids=[]`，`crlf_count=0`，`bad_marker_hits=[]`。
- Linux 端 Notebook preflight 已通过，并且不再出现 `MissingIDFieldWarning`。
- Linux 端总体验证 `python3 scripts/validate_repro_workspace.py` 已通过，新增输出“Notebook 结构与编码审计已通过”。
- Linux 端 `git diff --check` 已通过；本轮新增脚本和报告没有乱码哨兵命中。

### 当前边界

- 本轮只修复和审计 Notebook 结构，不连接 RoboChallenge 平台、不读取凭据、不上传 checkpoint、不生成大 tar。
- 真实提交仍需要用户提供 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、真实可访问 checkpoint link，并明确授权 checkpoint 归档/上传。

### 下一步

- P0：提交并推送本轮 Notebook 结构审计产物。

## 2026-06-02 第四十三轮：授权后安全预检模板审计

### 已完成

- 新增 `submission/run_authorized_preflight_template.sh`，用于用户补齐 token、submission id、checkpoint link 后先做安全预检；默认不联网、不上传、不运行真实 runner。
- 新增 `scripts/audit_authorized_preflight_template.py`，审计模板片段、`bash -n`、明文凭据模式和无凭据 smoke。
- 修复模板中的自引用审计问题：`audit_submission_blockers_summary.py` 的返回码会延后处理，未 ready 时仍能安全停在 dry-run 前。
- `submission/REAL_SUBMISSION_HANDOFF.md` 和 `submission/AUTHORIZED_SUBMISSION_SEQUENCE.md` 已加入授权后安全预检命令。
- `scripts/audit_submission_preflight_bundle.py`、`scripts/audit_submission_artifact_manifest.py`、`scripts/audit_submission_blockers_summary.py`、`scripts/audit_submission_handoff_docs.py`、`scripts/audit_authorized_submission_sequence.py` 和 `scripts/validate_repro_workspace.py` 已纳入该模板审计证据。

### 验证结果

- Linux 端 `python3 scripts/audit_authorized_preflight_template.py` 已通过：`passed=true`，`bash_n.passed=true`。
- 无凭据 smoke 已通过：`env_file_present_false=true`，`verify_download_disabled=true`，`ready_false=true`，`stops_before_runner=true`，`real_runner_not_called=true`。
- Linux 端提交材料审计链已通过：authorized sequence、handoff docs、Notebook structure、plaintext secrets、preflight bundle、artifact manifest、blockers summary 均为通过状态。
- Linux 端 `python3 scripts/validate_repro_workspace.py` 已通过，并新增输出“授权后安全预检模板审计已通过”。
- Linux 端 `git diff --check` 已通过。

### 当前边界

- 本轮只压缩并审计“用户授权后”的安全预检入口，不接触 RoboChallenge 平台，不上传 checkpoint，不生成大 tar，不读取或伪造真实凭据。
- 真实提交仍需要 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、真实可访问 checkpoint link，以及用户对 12GB+ checkpoint 归档/上传的明确授权。

### 下一步

- P0：提交并推送本轮授权后安全预检模板产物。
- P1：用户提供真实凭据和 checkpoint link 后，先运行 `bash submission/run_authorized_preflight_template.sh`；只有 readiness 为 true 且 dry-run 通过后，才进入真实 runner。

## 2026-06-02 第四十四轮：强确认真实 runner 入口审计

### 已完成

- 新增 `submission/run_ready_real_submission_template.sh`，作为真实 runner 的强确认入口；它会先复跑 link/download/readiness，再执行 dry-run，最后只有在确认短语匹配时才启动真实 runner。
- 新增 `scripts/audit_ready_real_runner_template.py`，离线审计强确认入口的语法、必要片段、禁止上传片段、无凭据 smoke 和 synthetic 无确认 smoke。
- Notebook `notebooks/robochallenge_pi05_submit_cn.ipynb` 新增第 41 节“强确认真实 runner 模板审计”，核心操作可在 Jupyter 中复跑。
- 修复 manifest/preflight 的自引用问题：`audit_submission_artifact_manifest.py` 不再要求当前 preflight 已通过，只要求 preflight 状态存在且 go/no-go 为 blocked。
- `submission/REAL_SUBMISSION_HANDOFF.md` 和 `submission/AUTHORIZED_SUBMISSION_SEQUENCE.md` 已改为推荐通过强确认入口执行真实 runner。
- `scripts/audit_submission_handoff_docs.py`、`scripts/audit_authorized_submission_sequence.py`、`scripts/audit_submission_preflight_bundle.py`、`scripts/audit_submission_blockers_summary.py`、`scripts/audit_notebook_structure.py` 和 `scripts/validate_repro_workspace.py` 已纳入该入口审计。

### 验证结果

- Linux 端 `python3 scripts/audit_ready_real_runner_template.py` 已通过：`passed=true`，`bash_n.passed=true`。
- 无凭据 smoke 已通过：返回非零、`ready_false=true`、未 dry-run、未启动真实 runner、未提及 `demo.py`。
- synthetic 无确认 smoke 已通过：只执行 dry-run，随后因缺少 `ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION` 停在真实 runner 前。
- Notebook 结构审计已通过：`cell_count=85`，第 41 节标记、`RUN_READY_REAL_RUNNER_TEMPLATE_AUDIT` 和 `scripts/audit_ready_real_runner_template.py` 均存在。
- Linux 端提交材料审计链已通过：handoff docs、authorized sequence、plaintext secrets、preflight bundle、artifact manifest、blockers summary 和总体验证均通过。
- Linux 端 `git diff --check` 已通过。

### 当前边界

- 本轮不连接 RoboChallenge 平台、不上传 checkpoint、不生成大 tar、不读取或伪造真实 token/submission id/checkpoint link。
- 强确认入口只有在用户补齐真实凭据、checkpoint link，并设置确认短语后才会调用真实 runner；当前仍处于 `go_no_go=blocked`。

### 下一步

- P0：提交并推送本轮强确认真实 runner 入口产物。
- P1：用户提供真实凭据后，先运行 `bash submission/run_authorized_preflight_template.sh`，再用 `ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION bash submission/run_ready_real_submission_template.sh` 进入真实 runner。

## 2026-06-02 第四十五轮：授权后 checkpoint 归档强确认入口审计

### 已完成

- 新增 `submission/run_authorized_checkpoint_archive_template.sh`，作为 12GB+ LoRA 物化 checkpoint 归档的强确认入口。
- 新增 `scripts/audit_authorized_checkpoint_archive_template.py`，离线审计该入口的 bash 语法、必要片段、禁止上传/runner 片段、无确认 smoke 和归档未生成状态。
- Notebook `notebooks/robochallenge_pi05_submit_cn.ipynb` 新增第 42 节“授权后 checkpoint 归档模板审计”，核心操作可在 Jupyter 中复跑。
- `submission/AUTHORIZED_SUBMISSION_SEQUENCE.md` 和 `submission/REAL_SUBMISSION_HANDOFF.md` 已从裸 `tar/sha256sum` 最短流程改为受控入口：先运行 `bash submission/run_authorized_checkpoint_archive_template.sh` dry-run；只有用户明确授权后才使用 `ROBOCHALLENGE_ARCHIVE_CONFIRM=CREATE_ROBOCHALLENGE_CHECKPOINT_ARCHIVE bash submission/run_authorized_checkpoint_archive_template.sh`。
- `scripts/audit_submission_preflight_bundle.py`、`scripts/audit_submission_artifact_manifest.py`、`scripts/audit_submission_blockers_summary.py`、`scripts/audit_authorized_submission_sequence.py`、`scripts/audit_submission_handoff_docs.py`、`scripts/audit_notebook_structure.py` 和 `scripts/validate_repro_workspace.py` 已纳入该归档入口审计。

### 验证结果

- Linux 端 `python3 scripts/audit_authorized_checkpoint_archive_template.py` 已通过：`passed=true`，`bash_n.passed=true`。
- 无确认 smoke 已通过：返回非零、命中 `missing explicit archive confirmation` 和 `stop before creating tar`，`archive_created=false`，`sha256_created=false`，`upload_performed=false`，`credentials_read=false`，`platform_contacted=false`。
- Notebook 结构审计已通过：`cell_count=87`，第 42 节标记、`RUN_AUTHORIZED_CHECKPOINT_ARCHIVE_TEMPLATE_AUDIT` 和 `scripts/audit_authorized_checkpoint_archive_template.py` 均存在，且无乱码哨兵命中。
- Linux 端提交材料审计链已通过：handoff docs、authorized sequence、plaintext secrets、preflight bundle、artifact manifest、blockers summary 和总体验证均通过。
- Linux 端 `git diff --check` 已通过。

### 当前边界

- 本轮不生成 tar、不计算真实 sha256、不上传 checkpoint、不连接 RoboChallenge 平台、不读取或伪造真实 token/submission id/checkpoint link。
- 真实提交仍处于 `go_no_go=blocked`：还缺 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、真实可访问 checkpoint link，以及用户对 checkpoint 归档/上传和真实 runner 的明确授权。

### 下一步

- P0：提交并推送本轮授权后 checkpoint 归档强确认入口产物。
- P1：用户提供真实凭据、checkpoint link 和归档/上传授权后，先运行 `bash submission/run_authorized_preflight_template.sh`；如果要生成 LoRA checkpoint tar，再设置 `ROBOCHALLENGE_ARCHIVE_CONFIRM=CREATE_ROBOCHALLENGE_CHECKPOINT_ARCHIVE` 执行归档入口。

## 2026-06-02 第四十六轮：提交状态 GUI 面板归档门禁展示

### 已完成

- 更新 `scripts/render_submission_status_dashboard.py`，把 `runs/authorized_checkpoint_archive_template_audit.json` 纳入提交状态 GUI 的数据源。
- GUI 面板新增“归档强确认入口”卡片，明确展示 `ROBOCHALLENGE_ARCHIVE_CONFIRM=CREATE_ROBOCHALLENGE_CHECKPOINT_ARCHIVE` 是生成 checkpoint tar 的必要确认短语。
- “归档生成”卡片已改为说明默认不生成 tar，真实生成必须先通过归档强确认入口。
- 面板状态 JSON 新增 `archive_confirm_gate_passed`、`archive_confirm_phrase` 和 `archive_no_confirm_blocks`，便于后续自动化审计直接读取。
- 更新 `scripts/validate_repro_workspace.py`，把 GUI 面板中的归档门禁卡片、确认短语和无确认阻断状态纳入总体验证。
- 本地生成 `reports/submission_status_dashboard_preview.png` 做 GUI 视觉检查，确认新增卡片可见，长确认短语能换行显示。

### 验证结果

- 本地 `python -m py_compile scripts\render_submission_status_dashboard.py scripts\validate_repro_workspace.py` 已通过。
- 本地 `python scripts\render_submission_status_dashboard.py` 已生成新版 `reports/submission_status_dashboard.html` 和 `runs/submission_status_dashboard.json`。
- 本地 Chrome headless 截图已通过人工检查：新增“归档强确认入口”卡片正常显示，确认短语没有被截断。
- Linux 端最终审计链已复跑通过：`python3 scripts/audit_plaintext_secrets.py`、`python3 scripts/audit_submission_artifact_manifest.py`、`python3 scripts/audit_submission_preflight_bundle.py`、`python3 scripts/audit_submission_blockers_summary.py`、`python3 scripts/validate_repro_workspace.py` 和 `git diff --check` 均通过。

### 当前边界

- 本轮只补 GUI 展示和静态审计，不生成 checkpoint tar、不上传 checkpoint、不连接 RoboChallenge 平台、不读取或伪造真实凭据。
- 真实提交仍处于 `go_no_go=blocked`：还缺 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、真实可访问 checkpoint link，以及用户对 checkpoint 归档/上传和真实 runner 的明确授权。

### 下一步

- P0：同步到 Linux 端，复跑提交材料审计链和总体验证后提交推送。
- P1：用户补齐真实凭据和 checkpoint link 后，先运行 `bash submission/run_authorized_preflight_template.sh`；需要生成 checkpoint tar 时再显式设置 `ROBOCHALLENGE_ARCHIVE_CONFIRM=CREATE_ROBOCHALLENGE_CHECKPOINT_ARCHIVE`。

## 2026-06-02 第四十七轮：授权执行清单与 Notebook 第 43 节

### 已完成

- 新增 `scripts/audit_authorized_execution_checklist.py`，把真实提交前需要用户确认或提供的内容整理成一份只读清单：提交对象确认、`ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、真实 checkpoint link、checkpoint 归档授权和真实 runner 强确认。
- 新增机器可读产物 `runs/authorized_execution_checklist.json` 和中文报告 `reports/authorized_execution_checklist.md`。
- Notebook `notebooks/robochallenge_pi05_submit_cn.ipynb` 新增第 43 节“授权执行清单审计”，可在 Jupyter 内直接复跑该清单审计。
- `scripts/audit_submission_preflight_bundle.py`、`scripts/audit_submission_artifact_manifest.py`、`scripts/audit_submission_blockers_summary.py`、`scripts/audit_notebook_structure.py`、`scripts/render_submission_status_dashboard.py` 和 `scripts/validate_repro_workspace.py` 已纳入该清单。
- GUI 面板新增“授权执行清单”卡片，显示当前清单已准备好，但仍等待用户输入。

### 验证结果

- Linux 端 `python3 scripts/audit_authorized_execution_checklist.py` 已通过：`passed=true`，`go_no_go=blocked_by_user_inputs`，`current_runnable_target=Table30v2 ALOHA`。
- Notebook 结构审计已通过：`cell_count=89`，第 43 节标记、`RUN_AUTHORIZED_EXECUTION_CHECKLIST` 和 `scripts/audit_authorized_execution_checklist.py` 均存在，且无乱码哨兵命中。
- Linux 端提交状态 GUI 已通过：`source_count=13`，`card_count=13`，`authorized_execution_checklist_passed=true`。
- Linux 端最终审计链已通过：明文凭据扫描、Notebook 结构、授权执行清单、artifact manifest、preflight bundle、blockers summary、GUI 渲染、总体验证和 `git diff --check` 均通过。

### 当前边界

- 本轮仍不读取真实 token、不连接 RoboChallenge 平台、不上传 checkpoint、不生成 checkpoint tar、不启动真实 runner。
- 真实提交仍处于阻塞状态：还缺用户确认提交对象、`ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、真实 checkpoint link，以及 checkpoint 归档/上传和真实 runner 的明确授权。

### 下一步

- P0：提交并推送本轮授权执行清单与 Notebook 第 43 节产物。
- P1：用户补齐真实凭据和 checkpoint link 后，先在 Jupyter 第 43 节复跑授权执行清单，再运行 `bash submission/run_authorized_preflight_template.sh`。

## 2026-06-03 第四十八轮：Jupyter 安全填空本地 env 入口审计

### 已完成
- 新增 `scripts/audit_jupyter_input_template.py`，静态审计 Notebook 第 44 节的本地 env 填空入口；审计不执行 Notebook、不读取凭据、不联网、不上传。
- Notebook `notebooks/robochallenge_pi05_submit_cn.ipynb` 新增第 44 节“安全填空本地 env 入口”，默认 `RUN_SAFE_LOCAL_ENV_INPUT_TEMPLATE=False`，只有用户手动改成 `True` 后才会通过 `getpass`/`input` 写入本地 env。
- 第 44 节只写入 `submission/robochallenge_env.local.sh`，该路径已被 `.gitignore` 覆盖；写入时使用 `shlex.quote`，并拒绝空值、占位符和值中换行。
- `scripts/audit_notebook_structure.py`、`scripts/audit_submission_preflight_bundle.py`、`scripts/audit_submission_artifact_manifest.py`、`scripts/audit_submission_blockers_summary.py`、`scripts/audit_authorized_execution_checklist.py`、`scripts/render_submission_status_dashboard.py` 和 `scripts/validate_repro_workspace.py` 已纳入该入口审计。
- GUI 面板新增“Jupyter 安全填空”卡片，显示 local env 入口已就绪、默认关闭、等待用户输入。

### 验证结果

- Linux 端 `python3 scripts/audit_jupyter_input_template.py` 已通过：`passed=true`，`section_index=89`，`run_flag_default_false=true`，`code_cell_clean=true`，`local_env_ignored=true`，`secret_pattern_hits=[]`。
- Linux 端 `python3 scripts/audit_notebook_structure.py` 已通过：`cell_count=91`，无缺失/重复 cell id，无输出，无 `execution_count`，第 44 节关键标记齐全。
- Linux 端完整 no-contact 预检链已通过：`python3 scripts/audit_plaintext_secrets.py`、`python3 scripts/audit_submission_preflight_bundle.py`、`python3 scripts/audit_submission_artifact_manifest.py`、`python3 scripts/audit_submission_blockers_summary.py`、`python3 scripts/render_submission_status_dashboard.py` 和 `python3 scripts/validate_repro_workspace.py` 均通过。
- GUI 状态 JSON 已更新：`source_count=14`，`card_count=14`，`done_count=9`，`blocked_count=4`，`jupyter_input_template_passed=true`，`jupyter_input_default_off=true`，`jupyter_local_env_ignored=true`。
- Linux 端 `git diff --check` 已通过；明文凭据扫描 `hit_count=0`。

### 当前边界

- 本轮没有读取真实 token、submission id 或 checkpoint link，没有接触 RoboChallenge 平台，没有上传 checkpoint，没有生成 checkpoint tar，也没有启动真实 runner。
- 真实提交仍处于 `go_no_go=blocked`：还缺 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、真实可访问 checkpoint link，以及用户对 checkpoint 归档/上传和真实 runner 的明确授权。

### 下一步
- P0：提交并推送本轮 Jupyter 安全填空入口、审计脚本、GUI 和总体验证更新。
- P1：用户拿到真实凭据和 checkpoint link 后，在 Notebook 第 44 节手动设置 `RUN_SAFE_LOCAL_ENV_INPUT_TEMPLATE=True` 写入 `submission/robochallenge_env.local.sh`，然后运行 `python3 scripts/audit_real_submission_readiness.py` 和 `bash submission/run_authorized_preflight_template.sh`。

## 2026-06-03 第四十九轮：授权后 Jupyter 预检入口审计

### 已完成
- 新增 `scripts/audit_jupyter_authorized_preflight_template.py`，静态审计 Notebook 第 45 节“授权后 Jupyter 预检入口”；审计不执行 Notebook、不读取 `submission/robochallenge_env.local.sh`、不联网、不上传、不启动真实 runner。
- Notebook `notebooks/robochallenge_pi05_submit_cn.ipynb` 新增第 45 节；默认 `RUN_JUPYTER_AUTHORIZED_PREFLIGHT_TEMPLATE_AUDIT=True` 只跑静态审计，`RUN_JUPYTER_AUTHORIZED_PREFLIGHT=False` 不读取 local env。
- 第 45 节的真实执行路径只在用户手动改开关后运行 `source submission/robochallenge_env.local.sh; bash submission/run_authorized_preflight_template.sh`，并且只打印 returncode 和报告路径，不打印 token、submission id 或 checkpoint link。
- `scripts/audit_notebook_structure.py`、`scripts/audit_submission_preflight_bundle.py`、`scripts/audit_submission_artifact_manifest.py`、`scripts/audit_submission_blockers_summary.py`、`scripts/audit_authorized_execution_checklist.py`、`scripts/render_submission_status_dashboard.py` 和 `scripts/validate_repro_workspace.py` 已纳入该入口审计。
- GUI 面板新增“Jupyter 授权预检”卡片，显示第 45 节已就绪、默认只审计、等待用户完成 local env 后手动开启。

### 验证结果

- Linux 端 `python3 scripts/audit_jupyter_authorized_preflight_template.py` 已通过：`passed=true`，`section_index=91`，`audit_default_true=true`，`execution_default_false=true`，`code_cell_clean=true`，`runner_started=false`，`secret_pattern_hits=[]`。
- Linux 端 `python3 scripts/audit_notebook_structure.py` 已通过：`cell_count=93`，无缺失/重复 cell id，无输出，无 `execution_count`，第 45 节关键标记齐全。
- Linux 端完整 no-contact 预检链已通过：明文凭据扫描、授权顺序、handoff docs、preflight bundle、artifact manifest、blockers summary、GUI 渲染、总体验证和 `git diff --check` 均通过。
- GUI 状态 JSON 已更新：`source_count=15`，`card_count=15`，`done_count=10`，`blocked_count=4`，`jupyter_authorized_preflight_template_passed=true`，`jupyter_authorized_preflight_default_off=true`，`jupyter_authorized_preflight_audit_on=true`。
- 明文凭据扫描仍为 `hit_count=0`；本轮没有读取、打印或保存真实凭据。

### 当前边界

- 本轮没有读取真实 token、submission id 或 checkpoint link，没有接触 RoboChallenge 平台，没有上传 checkpoint，没有生成 checkpoint tar，也没有启动真实 runner。
- 真实提交仍处于 `go_no_go=blocked`：还缺 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、真实可访问 checkpoint link，以及用户对 checkpoint 归档/上传和真实 runner 的明确授权。

### 下一步
- P0：提交并推送本轮授权后 Jupyter 预检入口、审计脚本、GUI 和总体验证更新。
- P1：用户拿到真实凭据和 checkpoint link 后，先运行 Notebook 第 44 节写入 local env，再手动开启第 45 节 `RUN_JUPYTER_AUTHORIZED_PREFLIGHT=True` 复跑授权预检；只有预检显示 ready 后，才进入归档/上传或真实 runner 强确认入口。

## 2026-06-03 第五十轮：Jupyter 真实提交交接路径固化

### 已完成
- 更新 `submission/REAL_SUBMISSION_HANDOFF.md`，把 `notebooks/robochallenge_pi05_submit_cn.ipynb` 第 44 节和第 45 节写成推荐的真实提交前安全入口，并保留 shell 命令作为 fallback。
- 更新 `submission/AUTHORIZED_SUBMISSION_SEQUENCE.md`，在用户授权后的执行顺序里加入 `python3 scripts/audit_jupyter_input_template.py` 和 `python3 scripts/audit_jupyter_authorized_preflight_template.py`，并明确第 44 节只写入被 Git 忽略的 `submission/robochallenge_env.local.sh`。
- 扩展 `scripts/audit_submission_handoff_docs.py`：现在会检查 Notebook 路径、两个 Jupyter 审计脚本、`RUN_SAFE_LOCAL_ENV_INPUT_TEMPLATE=True`、`RUN_JUPYTER_AUTHORIZED_PREFLIGHT=True` 以及第 44/45 节默认关闭证据。
- 扩展 `scripts/audit_authorized_submission_sequence.py`：现在会把 Notebook 路径覆盖、Jupyter 默认关闭、local env 被忽略、授权预检不启动 runner 纳入 `passed` 判定。
- 更新 `scripts/validate_repro_workspace.py`，总验证会硬性检查 handoff/sequence 两份文档中的新增 Jupyter 证据。

### 验证结果

- Linux 端语法检查已通过：`python3 -m py_compile scripts/audit_submission_handoff_docs.py scripts/audit_authorized_submission_sequence.py scripts/validate_repro_workspace.py`。
- Linux 端新增审计链已通过：`python3 scripts/audit_jupyter_input_template.py`、`python3 scripts/audit_jupyter_authorized_preflight_template.py`、`python3 scripts/audit_submission_handoff_docs.py`、`python3 scripts/audit_authorized_submission_sequence.py` 和 `python3 scripts/validate_repro_workspace.py` 均通过。
- 刷新后的 `runs/submission_handoff_docs_audit.json` 中，`jupyter_input_template_passed=true`、`jupyter_input_default_false=true`、`jupyter_input_local_env_ignored=true`、`jupyter_authorized_preflight_execution_default_false=true`、`jupyter_authorized_preflight_runner_not_started=true`。
- 刷新后的 `runs/authorized_submission_sequence_audit.json` 中，`path_mentions` 已覆盖 Notebook、第 44 节审计脚本、第 45 节审计脚本和 local env；所有 Jupyter 输入证据均为 `true`。
- 完整 no-contact 链仍通过：明文凭据扫描、真实提交前预检汇总、artifact manifest、blockers summary、GUI 渲染、总体验证和 `git diff --check` 均通过。
- 派生归档审计只更新了磁盘剩余空间桶 `470GB -> 460GB`；`archive_created=false`、`upload_performed=false`、`platform_contacted=false` 保持不变。

### 当前边界

- 本轮没有读取真实 token、submission id 或 checkpoint link，没有接触 RoboChallenge 平台，没有上传 checkpoint，没有生成 checkpoint tar，也没有启动真实 runner。
- 真实提交仍处于 `go_no_go=blocked`：还缺 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、真实可访问 checkpoint link，以及用户对 checkpoint 归档/上传和真实 runner 的明确授权。

### 下一步
- P0：提交并推送本轮 Jupyter handoff/sequence 固化、审计脚本和派生报告。
- P1：用户拿到真实凭据后，优先按 Notebook 第 44 节写入 local env，再手动开启第 45 节做授权预检；预检 ready 之后再进入 checkpoint 归档/上传或真实 runner 强确认入口。

## 2026-06-03 第五十一轮：下一步用户动作包与 GUI 卡片

### 已完成
- 新增 `scripts/render_next_user_action_packet.py`，从 readiness、blockers、授权执行清单、Jupyter 第 44/45 节审计和 handoff/sequence 审计生成一页式下一步动作包。
- 新增机器可读产物 `runs/next_user_action_packet.json` 和中文报告 `reports/next_user_action_packet.md`。
- 动作包明确列出 6 个需要用户补齐或授权的项目：提交对象确认、`ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、真实 checkpoint link、checkpoint 归档授权、真实 runner 强确认。
- 更新 `scripts/audit_submission_preflight_bundle.py`，把 `next_user_action_packet` 加入只读预检子审计。
- 更新 `scripts/audit_submission_artifact_manifest.py`，把动作包报告、脚本和 no-contact/no-leak 证据纳入提交准备材料 manifest。
- 更新 `scripts/render_submission_status_dashboard.py`，GUI 新增“下一步动作包”卡片，链接到 `reports/next_user_action_packet.md`。
- 更新 `scripts/validate_repro_workspace.py`，总体验证会检查动作包报告、JSON、脚本、6 个用户决策项、Notebook 第 44/45 节入口和 no-contact/no-leak 边界。

### 验证结果

- 本地和 Linux 端语法检查已通过：`python3 -m py_compile scripts/render_next_user_action_packet.py scripts/audit_submission_preflight_bundle.py scripts/audit_submission_artifact_manifest.py scripts/render_submission_status_dashboard.py scripts/validate_repro_workspace.py`。
- Linux 端 `python3 scripts/render_next_user_action_packet.py` 已通过：`passed=true`，`go_no_go=blocked_by_user_inputs`，`local_env_ignored=true`，6 个 `required_decision_ids` 齐全，`first_notebook_steps` 覆盖 Notebook 第 44/45 节。
- Linux 端完整 no-contact 链已通过：动作包、preflight bundle、artifact manifest、blockers summary、GUI 渲染、总体验证和 `git diff --check` 均通过。
- GUI 状态已升级为 16 个数据源和 16 张卡片，新增“下一步动作包”卡片；真实提交仍显示 `ready=false`、`go/no-go=blocked`。
- 明文凭据扫描仍为无命中；本轮没有读取、打印或保存真实 token、submission id、checkpoint link。

### 当前边界

- 本轮没有接触 RoboChallenge 平台，没有上传 checkpoint，没有生成 checkpoint tar，没有启动真实 runner，也没有联网验证 checkpoint link。
- 真实提交仍处于 `go_no_go=blocked`：还缺 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、真实可访问 checkpoint link，以及用户对 checkpoint 归档/上传和真实 runner 的明确授权。

### 下一步
- P0：提交并推送本轮下一步动作包、GUI 卡片和审计链更新。
- P1：用户拿到凭据后，直接打开 `reports/next_user_action_packet.md` 或 GUI“下一步动作包”卡片，按 Notebook 第 44/45 节路线写入 local env 并跑授权预检。

## 2026-06-03 第五十二轮：网页表单字段包与 GUI 卡片

### 已完成
- 新增 `scripts/render_web_form_field_packet.py`，把 RoboChallenge 网页提交/运行会用到的字段整理成只读字段包。
- 新增机器可读产物 `runs/web_form_field_packet.json` 和中文报告 `reports/web_form_field_packet.md`。
- 字段包覆盖 12 个字段：Benchmark、Robot Type、Task Name、Prompt、Inference Code Link、Fine-tuning/Restore Evidence、Checkpoint Link、RoboChallenge User Token、RoboChallenge Submission ID、Submission Variant、Checkpoint Upload/Archive、Authorized Notebook Entry。
- 更新 `scripts/audit_submission_preflight_bundle.py`，把 `web_form_field_packet` 加入只读预检子审计。
- 更新 `scripts/audit_submission_artifact_manifest.py`，把网页字段包报告、脚本和 no-contact/no-leak 证据纳入提交准备材料 manifest。
- 更新 `scripts/render_submission_status_dashboard.py`，GUI 新增“网页表单字段”卡片，链接到 `reports/web_form_field_packet.md`。
- 更新 `scripts/validate_repro_workspace.py`，总体验证会检查字段数、字段名、当前 `web_form_ready=false`、no-contact/no-leak 边界和 preflight 子命令覆盖。

### 验证结果

- 本地和 Linux 端语法检查已通过：`python3 -m py_compile scripts/render_web_form_field_packet.py scripts/audit_submission_preflight_bundle.py scripts/audit_submission_artifact_manifest.py scripts/render_submission_status_dashboard.py scripts/validate_repro_workspace.py`。
- Linux 端 `python3 scripts/render_web_form_field_packet.py` 已通过：`passed=true`，`field_count=12`，`ready_field_count=7`，`missing_field_count=5`，`web_form_ready=false`。
- Linux 端完整 no-contact 链已通过：网页字段包、preflight bundle、artifact manifest、blockers summary、GUI 渲染、总体验证和 `git diff --check` 均通过。
- 字段包明确显示已准备好的字段包括 Table30v2、aloha、pack_the_toothbrush_holder、prompt、GitHub 代码链接和 Notebook 授权入口；仍缺 checkpoint link、user token、submission id、提交 variant 确认和 checkpoint 归档/上传授权。
- 明文凭据扫描仍为无命中；本轮没有读取、打印或保存真实 token、submission id、checkpoint link。

### 当前边界

- 本轮没有接触 RoboChallenge 平台，没有上传 checkpoint，没有生成 checkpoint tar，没有启动真实 runner，也没有联网验证 checkpoint link。
- 真实提交仍处于 `go_no_go=blocked`：还缺 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、真实可访问 checkpoint link，以及用户对 checkpoint 归档/上传和真实 runner 的明确授权。

### 下一步
- P0：提交并推送本轮网页表单字段包、GUI 卡片和审计链更新。
- P1：用户拿到凭据后，先看 `reports/web_form_field_packet.md` 确认表单字段，再按 Notebook 第 44/45 节写入 local env 并跑授权预检。

## 2026-06-03 第五十三轮：提交路线拆分包与 GUI 卡片

### 已完成
- 新增 `scripts/render_submission_variant_route_packet.py`，把官方 Table30v2 ALOHA baseline 路线和 LoRA 物化 checkpoint 路线拆开审计。
- 新增机器可读产物 `runs/submission_variant_route_packet.json` 和中文报告 `reports/submission_variant_route_packet.md`。
- 路线包明确默认建议先走 `baseline_official_aloha`：本地 runner 使用 Linux 上已存在的官方 ALOHA checkpoint，不需要生成 LoRA tar，也不需要 checkpoint link。
- 路线包同时保留 `lora_materialized`：本地 checkpoint 和 policy smoke 已就绪；如作为网页可访问 checkpoint 提交，仍需要用户授权归档/上传并回填真实 HTTPS link。
- 更新 `scripts/audit_submission_preflight_bundle.py`、`scripts/audit_submission_artifact_manifest.py`、`scripts/render_submission_status_dashboard.py` 和 `scripts/validate_repro_workspace.py`，把路线拆分包纳入预检、manifest、GUI 和总体验证。
- GUI 面板新增“提交路线拆分”卡片，避免把 LoRA checkpoint link/upload 阻塞误读为官方 baseline 本地 runner 的硬前置。

### 验证结果

- 本地 `python -X utf8 -m py_compile scripts\render_submission_variant_route_packet.py scripts\audit_submission_preflight_bundle.py scripts\audit_submission_artifact_manifest.py scripts\render_submission_status_dashboard.py scripts\validate_repro_workspace.py` 已通过。
- 本地 `python -X utf8 scripts\render_submission_variant_route_packet.py` 已通过：`passed=true`，`recommended_default=baseline_official_aloha`，`route_count=2`。
- baseline 路线证据：`local_runner_ready_without_credentials=true`、`local_checkpoint_ready=true`、`requires_checkpoint_upload=false`、`requires_checkpoint_link_for_local_runner=false`。
- LoRA 路线证据：`local_runner_ready_without_credentials=true`、`local_checkpoint_ready=true`、`requires_checkpoint_upload_for_public_link=true`。

### 当前边界

- 本轮没有读取真实 token、submission id 或 checkpoint link，没有接触 RoboChallenge 平台，没有上传 checkpoint，没有生成 checkpoint tar，也没有启动真实 runner。
- 真实提交仍需要用户提供 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`，并确认提交 variant 和真实 runner 强确认；LoRA 网页 checkpoint 路线还需要归档/上传授权和真实 checkpoint link。

### 下一步

- P0：同步到 Linux 端，复跑路线包、预检汇总、manifest、GUI、总体验证和 `git diff --check`，然后提交推送。
- P1：用户拿到凭据后，默认先按 baseline 官方 ALOHA 路线跑授权预检；只有明确选择 LoRA 网页 checkpoint 路线时，再进入归档/上传/link 流程。

## 2026-06-03 第五十四轮：baseline 官方路线最短提交路径

### 已完成

- 修正 `submission/run_ready_real_submission_template.sh`：默认 `ROBOCHALLENGE_SUBMISSION_VARIANT` 从 `lora` 改为 `baseline`。
- 修正同一 wrapper 的读取顺序：先加载被 Git 忽略的 `submission/robochallenge_env.local.sh`，再读取 `ROBOCHALLENGE_SUBMISSION_VARIANT`、`ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD` 和 `ROBOCHALLENGE_REAL_RUN_CONFIRM`，避免 local env 中的 variant 被忽略。
- 更新 `submission/robochallenge_env_template.sh`，加入安全默认值 `ROBOCHALLENGE_SUBMISSION_VARIANT=baseline`。
- 更新 `scripts/audit_ready_real_runner_template.py`：现在会检查默认路线是 baseline，并用 synthetic token/submission id 验证“没有 checkpoint link 时也能进入 baseline dry-run，然后因缺少真实确认短语停在真实 runner 前”。
- 新增 `scripts/render_baseline_submission_quickstart.py`，生成官方 ALOHA baseline 最短提交路径包。
- 新增机器可读产物 `runs/baseline_submission_quickstart.json` 和中文报告 `reports/baseline_submission_quickstart.md`。
- 已把 baseline 最短路径包纳入 preflight、artifact manifest、GUI dashboard 和总体验证。

### 验证目标

- baseline 路线必须显示 `requires_checkpoint_upload=false`、`requires_checkpoint_link=false`。
- wrapper 默认路线必须是 `baseline`。
- synthetic 无确认 smoke 必须显示 `variant=baseline`、`dry_run_called=true`、`missing_confirmation=true`、`real_runner_started=false`。
- 本轮仍不读取真实 token，不连接 RoboChallenge 平台，不上传 checkpoint，不生成 checkpoint tar，不启动真实 runner。

### 当前边界

- baseline 官方路线离真实 runner 只剩用户侧输入和强确认：`ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、提交对象确认、`ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION`。
- LoRA 网页 checkpoint 路线仍需要额外的归档/上传授权和真实 checkpoint link。

### 下一步

- P0：同步到 Linux 端并复跑完整 no-contact 审计链；通过后提交推送。
- P1：如果用户提供 token/submission id，先用 baseline quickstart 的第 2/3 步做授权预检和 dry-run gate，不进入 LoRA 上传流程。
## 2026-06-03 第五十五轮：路线感知阻塞摘要与 GUI 卡片

### 已完成

- 新增 `scripts/render_route_aware_submission_blockers.py`，把 baseline 官方 ALOHA 最短路线和 LoRA/web checkpoint 路线的阻塞项拆开输出。
- 新增机器可读产物 `runs/route_aware_submission_blockers.json` 和中文报告 `reports/route_aware_submission_blockers.md`。
- 明确 baseline 路线当前只差 5 项：提交对象确认、`ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline`、真实 runner 强确认；不需要 checkpoint link，不需要 checkpoint upload，不需要归档授权。
- 明确 LoRA/web checkpoint 路线仍需要 checkpoint 归档授权、上传和真实 `ROBOCHALLENGE_CHECKPOINT_LINK`。
- 更新 `scripts/audit_submission_preflight_bundle.py`、`scripts/audit_submission_artifact_manifest.py`、`scripts/audit_submission_blockers_summary.py`、`scripts/render_submission_status_dashboard.py` 和 `scripts/validate_repro_workspace.py`，把路线感知摘要纳入预检、manifest、阻塞摘要、GUI 和总体验证。
- GUI 面板新增“路线感知阻塞”卡片，并把底部“当前阻塞”切换为 baseline 最短路线阻塞，避免把 LoRA/web 的 checkpoint link 误读为 baseline 前置条件。

### 验证结果

- Linux 端 `python3 -m py_compile` 已通过，覆盖新增脚本和所有改动脚本。
- Linux 端 `python3 scripts/render_route_aware_submission_blockers.py` 已通过：`passed=true`，`recommended_route=baseline_official_aloha`，`baseline_requires_checkpoint_link=false`，`baseline_requires_checkpoint_upload=false`，`lora_web_requires_checkpoint_link=true`，`lora_web_requires_checkpoint_upload=true`。
- Linux 端完整 no-contact 链已通过：动作包、网页字段包、路线拆分包、baseline quickstart、路线感知阻塞摘要、阻塞摘要、manifest、preflight、GUI、总体验证和 `git diff --check` 均通过。
- GUI 状态 JSON 已升级为 `source_count=20`、`card_count=20`、`done_count=15`，底部 baseline 当前阻塞列表不含 `ROBOCHALLENGE_CHECKPOINT_LINK`。
- 本轮没有读取真实 token、submission id 或 checkpoint link，没有接触 RoboChallenge 平台，没有上传 checkpoint，没有生成 checkpoint tar，也没有启动真实 runner。

### 当前边界

- baseline 官方路线离真实 runner 只剩用户侧输入和强确认：提交对象确认、`ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline`、`ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION`。
- LoRA/web checkpoint 路线仍需额外的归档/上传授权和真实可访问 checkpoint link。

### 下一步

- P0：提交并推送本轮 route-aware 阻塞摘要、GUI 卡片、manifest 和验证链更新。
- P1：用户拿到 token/submission id 后，先按 baseline quickstart 跑授权预检和 dry-run gate，不进入 LoRA 上传流程。

## 2026-06-03 第五十六轮：交接文档路线感知固化

### 已完成

- 更新 `submission/REAL_SUBMISSION_HANDOFF.md`：明确 baseline 官方路线不需要 checkpoint link、checkpoint upload 或归档授权；LoRA/web checkpoint 路线才需要上传和真实 checkpoint link。
- 更新 `submission/AUTHORIZED_SUBMISSION_SEQUENCE.md`：把“选择提交路线”前置，默认先跑 `render_route_aware_submission_blockers.py` 和 `render_baseline_submission_quickstart.py`；归档、上传、link 回填只作为 LoRA/web 分支。
- 更新 `submission/README.md` 和根 `README.md`，把 baseline quickstart 写成当前推荐路线，LoRA/web checkpoint 上传保留为可选分支。
- 扩展 `scripts/audit_submission_handoff_docs.py` 和 `scripts/audit_authorized_submission_sequence.py`，现在会强制检查 route-aware 文档证据：baseline 不需要 link/upload，LoRA/web 需要 link/upload。
- 修正两个审计脚本的成功提示，避免仍用旧的“所有真实执行都等待 checkpoint link”表达。

### 验证结果

- Linux 端 `python3 -m py_compile scripts/audit_submission_handoff_docs.py scripts/audit_authorized_submission_sequence.py` 已通过。
- Linux 端 `python3 scripts/audit_submission_handoff_docs.py` 已通过：route-aware guardrails 全为 true，`passed=true`。
- Linux 端 `python3 scripts/audit_authorized_submission_sequence.py` 已通过：route-aware guardrails 全为 true，`passed=true`。
- 完整 no-contact 链已通过：明文凭据扫描、handoff/sequence 审计、preflight、blockers summary、manifest、GUI、总体验证和 `git diff --check` 均通过。
- 明文扫描仍为 `hit_count=0`；本轮没有读取 token、submission id 或 checkpoint link，没有连接 RoboChallenge 平台，没有上传 checkpoint，没有生成 tar，没有启动真实 runner。

### 当前边界

- baseline 官方路线仍只等待用户确认目标、`ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline` 和真实 runner 强确认。
- LoRA/web checkpoint 路线额外等待用户授权归档/上传并提供真实 checkpoint link。

### 下一步

- P0：提交并推送本轮交接文档和文档审计规则更新。
- P1：用户拿到 token/submission id 后，从 `reports/baseline_submission_quickstart.md` 或 Notebook 第 44/45 节开始跑 baseline 授权预检。

## 2026-06-03 第五十七轮：下一步动作包 baseline 化

### 已完成

- 更新 `scripts/render_next_user_action_packet.py`：动作包现在直接读取 `submission_variant_route_packet` 和 `baseline_submission_quickstart`，默认展示 baseline 官方路线当前只差 5 项。
- 动作包新增字段：`recommended_route=baseline_official_aloha`、`baseline_requires_checkpoint_link=false`、`baseline_requires_checkpoint_upload=false`、`lora_web_requires_checkpoint_link=true`、`lora_web_requires_checkpoint_upload=true`。
- 动作包报告 `reports/next_user_action_packet.md` 新增 “Baseline 最短路线当前只差” 和 “LoRA / 网页 checkpoint 路线当前只差” 两节；旧的 readiness/web/LoRA 全局阻塞保留在兼容区，不再作为默认当前阻塞。
- 调整 `scripts/audit_submission_preflight_bundle.py` 的子审计顺序：先刷新路线拆分包和 baseline quickstart，再生成动作包，避免动作包读到旧路线状态。
- 更新 `scripts/audit_submission_artifact_manifest.py`、`scripts/render_submission_status_dashboard.py` 和 `scripts/validate_repro_workspace.py`，把动作包的 route-aware 字段纳入 manifest、GUI 和总体验证。
- 更新 `scripts/render_route_aware_submission_blockers.py`，反向检查动作包已经具备 baseline no-link / LoRA-web needs-link 语义，防止回退。

### 验证结果

- Linux 端动作包 smoke 已通过：`passed=true`，`recommended_route=baseline_official_aloha`，`baseline_requires_checkpoint_link=false`，`current_blocking` 只包含 baseline 5 项。
- 完整 no-contact 链已通过：明文凭据扫描、preflight、blockers summary、manifest、GUI、总体验证和 `git diff --check` 均通过。
- GUI 状态仍为 `source_count=20`、`card_count=20`、`done_count=15`；“下一步动作包”卡片现在显示 `baseline 优先`。
- 明文扫描仍为 `hit_count=0`；本轮没有读取真实 token、submission id 或 checkpoint link，没有连接 RoboChallenge 平台，没有上传 checkpoint，没有生成 tar，没有启动真实 runner。

### 当前边界

- baseline 官方路线的默认动作包现在只等待：提交对象确认、`ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline`、真实 runner 强确认。
- LoRA/web checkpoint 路线仍单独等待归档/上传授权和真实 checkpoint link。

### 下一步

- P0：提交并推送本轮动作包 baseline 化、GUI 和验证链更新。
- P1：继续检查 Notebook 第 44/45 节中的用户提示文字，确保它们也默认引导 baseline 而不是 LoRA/web link。

## 2026-06-03 第五十八轮：Jupyter baseline 引导固化

### 已完成

- 更新 Notebook 第 44 节“安全填空本地 env 入口”：默认推荐 `baseline` / `baseline_official_aloha`，明确 baseline 只要求 token 和 submission id，不要求 checkpoint link；checkpoint link 留空不会进入 LoRA 上传流程。
- 更新 Notebook 第 45 节“授权后 Jupyter 预检入口”：默认按 `baseline_official_aloha` 做授权预检；baseline 不需要 checkpoint link，也不需要 checkpoint upload；LoRA/web checkpoint 的归档、上传和 link 回填保留为手动选择分支。
- 扩展 `scripts/audit_jupyter_input_template.py`：新增 `recommended_route`、`baseline_requires_checkpoint_link`、`baseline_requires_checkpoint_upload`、`lora_web_requires_checkpoint_link`、`lora_web_requires_checkpoint_upload` 和 `route_guidance` 字段。
- 扩展 `scripts/audit_jupyter_authorized_preflight_template.py`：把 baseline 预检与 LoRA/web checkpoint 上传路线的分离变成硬性审计项。
- 更新 `scripts/audit_submission_artifact_manifest.py`、`scripts/render_submission_status_dashboard.py` 和 `scripts/validate_repro_workspace.py`：manifest、GUI 和总体验证现在都会检查 Jupyter 入口的 baseline no-link / LoRA-web needs-link 语义。

### 验证结果

- Linux 端语法检查已通过：`python3 -m py_compile` 覆盖两个 Jupyter 审计脚本、manifest、dashboard 和总验证脚本。
- Linux 端 `python3 scripts/audit_jupyter_input_template.py` 已通过：`passed=true`，`recommended_route=baseline_official_aloha`，`baseline_requires_checkpoint_link=false`，`baseline_requires_checkpoint_upload=false`。
- Linux 端 `python3 scripts/audit_jupyter_authorized_preflight_template.py` 已通过：`passed=true`，baseline 预检和 LoRA/web checkpoint 上传路线已分离。
- 完整 no-contact 链已通过：明文凭据扫描、preflight、blockers summary、manifest、GUI、总体验证和 `git diff --check` 均通过。
- GUI 状态仍为 `source_count=20`、`card_count=20`、`done_count=15`；“Jupyter 安全填空”卡片显示 `baseline 默认`，“Jupyter 授权预检”卡片显示 `baseline 预检`。

### 当前边界

- 本轮没有读取真实 token、submission id 或 checkpoint link，没有连接 RoboChallenge 平台，没有上传 checkpoint，没有生成 checkpoint tar，没有启动真实 runner。
- baseline 官方路线当前只等待：提交对象确认、`ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline`、真实 runner 强确认。
- LoRA/web checkpoint 路线仍单独等待归档/上传授权和真实 checkpoint link。

### 下一步

- P0：重新同步 `work.md` 到 Linux，刷新 manifest/dashboard/总验证后提交并推送本轮 Jupyter baseline 引导固化。
- P1：下一轮继续从 GUI 和 `reports/baseline_submission_quickstart.md` 检查真实授权入口的人机操作顺序，确保用户拿到 token 后先复现 baseline 基模。

## 2026-06-03 第五十九轮：授权执行清单 baseline 主路径化

### 已完成

- 更新 `scripts/audit_authorized_execution_checklist.py`：`required_user_decisions` 现在是 baseline 主路径 5 项，分别是提交对象确认、`ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline`、真实 runner 强确认。
- 同一清单新增 `lora_web_user_decisions`，单独保留 LoRA/web checkpoint 路线需要的 `CHECKPOINT_ARCHIVE_AUTHORIZATION` 和 `ROBOCHALLENGE_CHECKPOINT_LINK`。
- 更新 `scripts/render_next_user_action_packet.py`：动作包不再把 checkpoint link/归档授权当成 baseline 必需项，同时会检查 LoRA/web 分支仍包含这些项。
- 更新 `scripts/render_submission_variant_route_packet.py`：路线拆分包不再依赖 action/web 下游产物，打破 preflight 子审计循环依赖。
- 更新 `scripts/audit_submission_preflight_bundle.py`：子审计顺序改为 route packet -> baseline quickstart -> 授权清单 -> 动作包 -> web form -> route-aware -> handoff -> manifest；preflight 主 blocking 改为 baseline 5 项，旧全局 readiness/link 阻塞只作为兼容字段保留。
- 更新 `scripts/render_submission_status_dashboard.py` 和 `scripts/validate_repro_workspace.py`：GUI 的真实提交 gate、授权执行清单、网页表单字段卡片都改成 route-aware 文案，并强制验证 baseline no-link / LoRA-web needs-link。

### 验证结果

- Linux 端语法检查已通过，覆盖 route packet、baseline quickstart、授权清单、动作包、web form、route-aware、preflight、manifest、dashboard、总验证脚本。
- Linux 端完整 no-contact 链已通过：明文凭据扫描、preflight bundle、blockers summary、artifact manifest、GUI dashboard、总体验证和 `git diff --check` 均通过。
- `runs/authorized_execution_checklist.json`：`passed=true`，`recommended_route=baseline_official_aloha`，baseline 主决策数为 5，不含 `ROBOCHALLENGE_CHECKPOINT_LINK` 和 `CHECKPOINT_ARCHIVE_AUTHORIZATION`。
- `runs/next_user_action_packet.json`：`passed=true`，`next_user_action_packet_decision_count=5`，`baseline_current_blocking` 只含 baseline 5 项；`lora_web_current_blocking` 单独包含 checkpoint link 和归档授权。
- GUI dashboard 仍为 `source_count=20`、`card_count=20`、`done_count=15`；“授权执行清单”卡片显示 `baseline 输入`，底部当前阻塞不含 checkpoint link。

### 当前边界

- 本轮没有读取真实 token、submission id 或 checkpoint link，没有连接 RoboChallenge 平台，没有上传 checkpoint，没有生成 checkpoint tar，没有启动真实 runner。
- baseline 官方路线仍只等待：提交对象确认、`ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline`、真实 runner 强确认。
- LoRA/web checkpoint 路线仍单独等待归档/上传授权和真实 checkpoint link。

### 下一步

- P0：同步 `work.md` 后刷新 manifest/dashboard/总验证，提交并推送本轮授权执行清单 baseline 主路径化。
- P1：下一轮继续检查真实 token 到位后的 dry-run gate 命令，保证第一条可执行授权路径就是 baseline 基模复现。

## 2026-06-03 第六十轮：baseline dry-run gate 独立证据包

### 已完成
- 新增 `scripts/render_baseline_dry_run_gate.py`，把用户拿到 `ROBOCHALLENGE_USER_TOKEN` 和 `ROBOCHALLENGE_SUBMISSION_ID` 后的 baseline dry-run gate 单独固化为机器可读证据包。
- 新增 `runs/baseline_dry_run_gate.json` 和中文报告 `reports/baseline_dry_run_gate.md`。
- 明确 baseline 官方 ALOHA 路线不需要 checkpoint link、checkpoint upload 或 checkpoint 归档授权；LoRA/web checkpoint 路线仍单独保留上传和真实 link 回填要求。
- 明确授权后两条安全入口：先跑 `ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_authorized_preflight_template.sh`，再跑 `ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_ready_real_submission_template.sh` 作为 dry-run gate。
- dry-run gate 证据来自 `ready_real_runner_template_audit` 的 synthetic no-confirm smoke：`variant=baseline`、`dry_run_called=true`、`missing_confirmation=true`、`stops_before_real_runner=true`、`real_runner_started=false`、`printed_protected_values=false`。
- 更新 `scripts/audit_submission_preflight_bundle.py`、`scripts/audit_submission_artifact_manifest.py`、`scripts/render_submission_status_dashboard.py` 和 `scripts/validate_repro_workspace.py`，把 dry-run gate 纳入 preflight、manifest、GUI 和总验证。

### 验证结果

- Linux 端 `python3 -m py_compile` 已通过，覆盖新增脚本和所有改动脚本。
- Linux 端 `python3 scripts/render_baseline_dry_run_gate.py` 已通过：`passed=true`，`recommended_route=baseline_official_aloha`，`requires_checkpoint_link=false`，`requires_checkpoint_upload=false`，`stops_before_real_runner_without_confirmation=true`。
- Linux 端完整 no-contact 链已通过：明文凭据扫描、preflight bundle、blockers summary、artifact manifest、GUI dashboard、总体验证和 `git diff --check` 均通过。
- `runs/submission_preflight_bundle.json` 现在包含 `baseline_dry_run_gate_passed=true`、`baseline_dry_run_gate_command=ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_ready_real_submission_template.sh`、`baseline_dry_run_gate_stops_before_real_runner=true`。
- GUI dashboard 升级为 `source_count=21`、`card_count=21`、`done_count=16`、`blocked_count=4`，新增 “Baseline dry-run gate” 卡片。
- 本轮没有读取真实 token、submission id 或 checkpoint link，没有连接 RoboChallenge 平台，没有上传 checkpoint，没有生成 checkpoint tar，也没有启动真实 runner。

### 当前边界

- baseline 官方路线仍只等待：提交对象确认、`ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline`、真实 runner 强确认。
- LoRA/web checkpoint 路线仍单独等待归档/上传授权和真实 checkpoint link。

### 下一步

- P0：提交并推送本轮 baseline dry-run gate 证据包、GUI 卡片、manifest 和验证链更新。
- P1：用户拿到 token/submission id 后，先按 `reports/baseline_dry_run_gate.md` 跑 baseline 授权前只读预检和 dry-run gate，再决定是否进入真实 runner 强确认。

## 2026-06-03 第六十一轮：baseline 凭据卫生证据包

### 已完成

- 新增 `scripts/render_baseline_credential_hygiene.py`，把凭据到位后的本地卫生边界单独固化为机器可读证据包。
- 新增 `runs/baseline_credential_hygiene.json` 和中文报告 `reports/baseline_credential_hygiene.md`。
- 明确真实 `ROBOCHALLENGE_USER_TOKEN` 和 `ROBOCHALLENGE_SUBMISSION_ID` 只能写入 Git 忽略的 `submission/robochallenge_env.local.sh` 或当前 shell。
- 凭据卫生脚本只检查路径、Git 忽略状态、是否未跟踪，以及上游审计结果；不会读取 `submission/robochallenge_env.local.sh` 内容。
- 凭据卫生包串联了 `submission_env_template_audit`、`plaintext_secret_scan`、`authorized_preflight_template_audit`、`baseline_dry_run_gate`、`next_user_action_packet` 和 `route_aware_submission_blockers`。
- 更新 `scripts/audit_submission_preflight_bundle.py`、`scripts/audit_submission_artifact_manifest.py`、`scripts/render_submission_status_dashboard.py` 和 `scripts/validate_repro_workspace.py`，把凭据卫生包纳入 preflight、manifest、GUI 和总验证。

### 验证结果

- Linux 端 `python3 -m py_compile` 已通过，覆盖新增脚本和所有改动脚本。
- Linux 端 `python3 scripts/render_baseline_credential_hygiene.py` 已通过：`passed=true`，`recommended_route=baseline_official_aloha`，`local_env_gitignored=true`，`local_env_tracked=false`，`local_env_content_read=false`。
- Linux 端完整 no-contact 链已通过：明文凭据扫描、preflight bundle、blockers summary、artifact manifest、GUI dashboard、总体验证和 `git diff --check` 均通过。
- `runs/submission_preflight_bundle.json` 现在包含 `baseline_credential_hygiene_passed=true`、`baseline_credential_hygiene_local_env_gitignored=true`、`baseline_credential_hygiene_local_env_content_read=false`。
- GUI dashboard 升级为 `source_count=22`、`card_count=22`、`done_count=17`、`blocked_count=4`，新增 “Baseline 凭据卫生” 卡片。
- 本轮没有读取真实 token、submission id 或 checkpoint link，没有读取 local env 内容，没有连接 RoboChallenge 平台，没有上传 checkpoint，没有生成 checkpoint tar，也没有启动真实 runner。

### 当前边界

- baseline 官方路线仍只等待：提交对象确认、`ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline`、真实 runner 强确认。
- LoRA/web checkpoint 路线仍单独等待归档/上传授权和真实 checkpoint link。

### 下一步

- P0：提交并推送本轮 baseline 凭据卫生证据包、GUI 卡片、manifest 和验证链更新。
- P1：用户拿到 token/submission id 后，先写入被 Git 忽略的 local env，再跑 `reports/baseline_credential_hygiene.md` 对应的卫生检查和 baseline dry-run gate。

## 2026-06-03 第六十二轮：baseline local env synthetic smoke

### 已完成

- 修正 `submission/run_authorized_preflight_template.sh`：现在先 source `submission/robochallenge_env.local.sh`，再读取 `ROBOCHALLENGE_SUBMISSION_VARIANT`，默认路线改为 `baseline`。
- 同一脚本在 readiness 已通过时，即使 route-aware blockers summary 仍提示人工决策项，也只作为 warning 记录并继续执行 dry-run；真实 runner 仍由 `ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION` 单独强确认保护。
- 扩展 `scripts/audit_authorized_preflight_template.py`：硬性检查 variant 在 source local env 之后读取、默认值是 baseline、blockers warning 只能继续 dry-run。
- 新增 `scripts/render_baseline_local_env_smoke.py`，用临时 synthetic local env 验证授权预检和 ready runner gate。
- 新增 `runs/baseline_local_env_smoke.json` 和中文报告 `reports/baseline_local_env_smoke.md`。
- synthetic local env smoke 会创建临时 fake env，运行完后删除，并恢复被 wrapper 刷新的 readiness/link/blockers 状态文件；报告只记录长度和布尔证据，不记录 synthetic 明文值。
- 更新 `scripts/audit_submission_preflight_bundle.py`、`scripts/audit_submission_artifact_manifest.py`、`scripts/render_submission_status_dashboard.py` 和 `scripts/validate_repro_workspace.py`，把 local env smoke 纳入 preflight、manifest、GUI 和总验证。

### 验证结果

- Linux 端 `python3 -m py_compile` 已通过，覆盖新增脚本和所有改动脚本。
- Linux 端 `bash -n submission/run_authorized_preflight_template.sh` 已通过。
- Linux 端 `python3 scripts/audit_authorized_preflight_template.py` 已通过：`reads_variant_after_local_env_source=true`，`default_variant_baseline=true`，`blockers_warning_continues_dry_run_only=true`。
- Linux 端 `python3 scripts/render_baseline_local_env_smoke.py` 已通过：authorized preflight `returncode=0`、`variant_baseline=true`、`dry_run_called=true`；ready runner `variant_baseline=true`、`stops_before_real_runner=true`；临时 env 文件已删除。
- Linux 端完整 no-contact 链已通过：明文凭据扫描、preflight bundle、blockers summary、artifact manifest、GUI dashboard、总体验证和 `git diff --check` 均通过。
- GUI dashboard 升级为 `source_count=23`、`card_count=23`、`done_count=18`、`blocked_count=4`，新增 “Baseline local env smoke” 卡片。
- 本轮没有读取真实 token、submission id 或 checkpoint link，没有连接 RoboChallenge 平台，没有上传 checkpoint，没有生成 checkpoint tar，也没有启动真实 runner。

### 当前边界

- baseline 官方路线仍只等待：提交对象确认、`ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline`、真实 runner 强确认。
- LoRA/web checkpoint 路线仍单独等待归档/上传授权和真实 checkpoint link。

### 下一步

- P0：提交并推送本轮 authorized preflight local env 读取顺序修复、synthetic local env smoke、GUI 卡片、manifest 和验证链更新。
- P1：用户拿到 token/submission id 后，可直接把它们写入 `submission/robochallenge_env.local.sh`，再跑 baseline local env smoke、授权预检和 dry-run gate。

## 2026-06-03 第六十三轮：baseline final handoff packet

### 已完成

- 新增 `scripts/render_baseline_final_handoff_packet.py`，把 baseline 凭据后执行顺序固化为最终交接证据包。
- 新增 `runs/baseline_final_handoff_packet.json` 和中文报告 `reports/baseline_final_handoff_packet.md`。
- final handoff 明确 4 条命令顺序：
  1. `python3 scripts/render_baseline_credential_hygiene.py`
  2. `ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_authorized_preflight_template.sh`
  3. `ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_ready_real_submission_template.sh`
  4. `ROBOCHALLENGE_SUBMISSION_VARIANT=baseline ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION bash submission/run_ready_real_submission_template.sh`
- 前三条命令被标记为 no-contact；第四条只作为真实 runner 强确认入口保留，不会在本轮执行。
- 交接包硬性检查 baseline 当前只差 5 项：`SUBMISSION_TARGET_CONFIRMATION`、`ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline`、`ROBOCHALLENGE_REAL_RUN_CONFIRM`。
- 交接包硬性检查 baseline 不需要 `ROBOCHALLENGE_CHECKPOINT_LINK`、`CHECKPOINT_ARCHIVE_AUTHORIZATION`、checkpoint upload 或 checkpoint 归档授权；这些仍只属于 LoRA/web checkpoint 路线。
- 更新 `scripts/audit_submission_preflight_bundle.py`、`scripts/audit_submission_artifact_manifest.py`、`scripts/render_submission_status_dashboard.py` 和 `scripts/validate_repro_workspace.py`，把 final handoff 纳入 preflight、manifest、GUI 和总验证。

### 验证结果

- Linux 端 `python3 -m py_compile` 已通过，覆盖新增脚本和所有改动脚本。
- Linux 端 `python3 scripts/render_baseline_final_handoff_packet.py` 已通过：`passed=true`，`command_count=4`，`no_contact_command_count=3`，`real_runner_requires_confirmation=true`，`local_env_content_read=false`。
- Linux 端完整 no-contact 链已通过：明文凭据扫描、preflight bundle、blockers summary、artifact manifest、GUI dashboard、总体验证和 `git diff --check` 均通过。
- `runs/submission_preflight_bundle.json` 现在包含 `baseline_final_handoff_passed=true`、`baseline_final_handoff_command_count=4`、`baseline_final_handoff_no_contact_command_count=3`、`baseline_final_handoff_real_runner_requires_confirmation=true`。
- GUI dashboard 升级为 `source_count=24`、`card_count=24`、`done_count=19`、`blocked_count=4`，新增 “Baseline final handoff” 卡片。
- 本轮没有读取真实 token、submission id 或 checkpoint link，没有读取 local env 内容，没有连接 RoboChallenge 平台，没有上传 checkpoint，没有生成 checkpoint tar，也没有启动真实 runner。

### 当前边界

- baseline 官方路线仍只等待：提交对象确认、`ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline`、真实 runner 强确认。
- LoRA/web checkpoint 路线仍单独等待归档/上传授权和真实 checkpoint link。

### 下一步

- P0：提交并推送本轮 baseline final handoff 证据包、GUI 卡片、manifest 和验证链更新。
- P1：用户提供 token/submission id 并明确授权后，先跑 final handoff 的前三条 no-contact 命令；第四条真实 runner 强确认命令只能在用户明确允许真实提交时执行。

## 2026-06-03 第六十四轮：Jupyter 第 46 节 final handoff 接入

### 已完成

- 在 `notebooks/robochallenge_pi05_submit_cn.ipynb` 追加第 46 节：`baseline final handoff 交接包`。
- 第 46 节默认 `RUN_JUPYTER_BASELINE_FINAL_HANDOFF_TEMPLATE_AUDIT=True`，会静态审计本节结构。
- 第 46 节默认 `RUN_JUPYTER_BASELINE_FINAL_HANDOFF_PACKET=True`，会生成/刷新 `runs/baseline_final_handoff_packet.json` 和 `reports/baseline_final_handoff_packet.md`。
- 第 46 节默认 `RUN_JUPYTER_BASELINE_REAL_RUNNER=False`，不会从 Notebook 自动启动真实 runner。
- 新增 `scripts/audit_jupyter_final_handoff_template.py`，硬性检查第 46 节包含 4 条 final handoff 命令、前三步 no-contact、第四条真实 runner 强确认短语，以及 baseline 不需要 checkpoint link/upload。
- 更新 `scripts/audit_notebook_structure.py`，把第 46 节纳入 Notebook 结构和编码审计。
- 更新 `scripts/audit_submission_preflight_bundle.py`、`scripts/audit_submission_artifact_manifest.py`、`scripts/render_submission_status_dashboard.py` 和 `scripts/validate_repro_workspace.py`，把 Jupyter final handoff 纳入 preflight、manifest、GUI 和总验证。

### 验证结果

- Linux 端 `python3 -m py_compile` 已通过，覆盖新增脚本和所有改动脚本。
- Linux 端 `python3 scripts/audit_jupyter_final_handoff_template.py` 已通过：`passed=true`，`section_index=93`，`packet_default_true=true`，`real_runner_default_false=true`，`command_count=4`，`no_contact_command_count=3`，`real_runner_requires_confirmation=true`。
- Linux 端 `python3 scripts/audit_notebook_structure.py` 已通过：`cell_count=95`，第 46 节关键标记全部存在，未发现乱码哨兵、输出单元或 execution_count。
- Linux 端完整 no-contact 链已通过：明文凭据扫描、preflight bundle、blockers summary、artifact manifest、GUI dashboard、总体验证和 `git diff --check` 均通过。
- `runs/submission_preflight_bundle.json` 现在包含 `jupyter_final_handoff_passed=true`、`jupyter_final_handoff_packet_default_true=true`、`jupyter_final_handoff_real_runner_default_false=true`、`jupyter_final_handoff_no_contact_command_count=3`。
- GUI dashboard 升级为 `source_count=25`、`card_count=25`、`done_count=20`、`blocked_count=4`，新增 “Jupyter final handoff” 卡片。
- 本轮没有读取真实 token、submission id 或 checkpoint link，没有读取 local env 内容，没有连接 RoboChallenge 平台，没有上传 checkpoint，没有生成 checkpoint tar，也没有启动真实 runner。

### 当前边界

- baseline 官方路线仍只等待：提交对象确认、`ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline`、真实 runner 强确认。
- LoRA/web checkpoint 路线仍单独等待归档/上传授权和真实 checkpoint link。

### 下一步

- P0：提交并推送本轮 Notebook 第 46 节、Jupyter final handoff 审计、GUI 卡片、manifest 和验证链更新。
- P1：下一轮可继续做凭据到位后的只读执行演练说明，但真实 runner 仍必须等用户明确提供凭据和授权。
