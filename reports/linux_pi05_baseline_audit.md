# Linux pi0.5 baseline 审计

## 已发现资源

- 主 baseline 目录：`/home/yjl/yjl/RoboChallenge/baseline_pi05_multitask`
- baseline 大小：约 8GB，主要来自 `.venv`
- 样例数据目录：`/home/yjl/yjl/RoboChallenge/baseline_pi05_multitask/20260413`
- 已有 checkpoint：`/home/yjl/yjl/RoboChallenge/checkpoints/table30v2_multitask_baseline_aloha`
- checkpoint 大小：约 12GB
- 目标仓库目录：`/home/yjl/robochallenge/repo`

## baseline 入口

- `demo.py`：RoboChallenge 官方评测入口，需要 `user_token` 和 `submission_id`。
- `test.py`：本地 mock 调试入口，连接 `mock_server/mock_robot_server.py`。
- `mock_server/mock_settings.py`：选择 `ROBOT_TAG` 和 `RECORD_DATA_DIR`。
- `openpi/`：RoboChallenge 使用的 openpi runtime 代码。
- `.venv/`：已有 Python 3.11 运行环境，包含 `openpi`、`openpi_rtc`、`jax`、`torch`、`cv2`、`jupyterlab`、`ipykernel`、`nbformat`。

## 平台配置

| robot_type | ROBOT_TAG | 样例任务 | action_type | image_size | checkpoint 状态 |
| --- | --- | --- | --- | --- | --- |
| `aloha` | `aloha` | `pack_the_toothbrush_holder` | `joint` | `640x480` | 已存在 |
| `dosw` | `w1` | `sweep_the_trash` | `joint` | `640x480` | 未确认 |
| `arx5` | `arx5` | `hang_the_cup` | `leftjoint` | `1280x720` | 未确认 |
| `ur5` | `ur5` | `arrange_fruits` | `leftjoint` | `640x480` | 未确认 |

## Notebook 验证

- Notebook：`/home/yjl/robochallenge/repo/notebooks/robochallenge_pi05_submit_cn.ipynb`
- 执行产物：`/home/yjl/robochallenge/repo/notebooks/robochallenge_pi05_submit_cn.executed.ipynb`
- 预检状态：`/home/yjl/robochallenge/repo/runs/notebook_preflight_status.json`
- 数据体检：`/home/yjl/robochallenge/repo/runs/data_audit_aloha.json`

ALOHA 样例数据体检结果：

- `left_states.jsonl`：1100 帧
- `right_states.jsonl`：1100 帧
- `cam_high_rgb.mp4`：1100 帧
- `cam_left_wrist_rgb.mp4`：1100 帧
- `cam_right_wrist_rgb.mp4`：1100 帧

## 下一步判断

- 可以直接进入 ALOHA mock smoke test。
- 不应把 `.venv`、checkpoint、样例视频、日志或 token 放入 Git。
- 真实提交前必须由用户提供或授权读取 RoboChallenge `user_token` 和 `submission_id`。
