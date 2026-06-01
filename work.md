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
