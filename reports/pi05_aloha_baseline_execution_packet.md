# pi0.5 ALOHA baseline 离线执行证据包

## 结论

- 审计状态：`passed=True`。
- 推荐路线：`baseline_official_aloha`。
- 目标：`Table30v2 / aloha / pack_the_toothbrush_holder`。
- pi0.5 本地缓存：`/home/yjl/.cache/openpi/openpi-assets/checkpoints/pi05_base`。
- pi0.5 GCS 对象数：`29`。
- pi0.5 本地匹配字节：`12441749581` / `12441749581`。
- 参数叶子数：`51`。
- 参数元素数：`3353433872`。
- ALOHA 数据目录：`/home/yjl/yjl/RoboChallenge/baseline_pi05_multitask/20260413/aloha/pack_the_toothbrush_holder`。
- state/video 帧数：`1100` / `1100`。
- ALOHA checkpoint：`/home/yjl/yjl/RoboChallenge/checkpoints/table30v2_multitask_baseline_aloha`。
- checkpoint 是否存在：`True`。

## 转换与 smoke

- dry-run 抽样数：`5`。
- padding 后 state shape：`[5, 32]`。
- padding 后 actions shape：`[5, 50, 32]`。
- 短 LeRobot episode 帧数：`64`。
- CLI 短 LeRobot episode 帧数：`80`。
- mock policy smoke exit_code：`0`。
- mock policy inference 命中数：`162`。
- policy log：`runs/policy_smoke_aloha.log`。
- mock server log：`runs/mock_server_aloha.log`。

## 边界

- 本审计只读取已有 JSON 和日志，不启动真实 runner。
- 不读取 RoboChallenge token/submission id/local env。
- 不连接 RoboChallenge 平台、不上传、不下载 checkpoint。

## 证据

- `pi05_local_cache_complete`：`True`。
- `pi05_remote_object_count`：`True`。
- `pi05_bytes_match`：`True`。
- `pi05_params_load_smoke_preserved`：`True`。
- `pi05_params_loaded`：`True`。
- `pi05_params_leaf_count_positive`：`True`。
- `pi05_params_total_elements_positive`：`True`。
- `selected_robot_aloha`：`True`。
- `selected_task_pack_toothbrush`：`True`。
- `selected_checkpoint_exists`：`True`。
- `data_record_exists`：`True`。
- `data_state_frame_counts_match`：`True`。
- `data_video_frame_counts_match`：`True`。
- `mapping_task_name`：`True`。
- `mapping_episode_frames`：`True`。
- `dry_run_passed`：`True`。
- `dry_run_sample_count`：`True`。
- `dry_run_state_32`：`True`。
- `dry_run_actions_50x32`：`True`。
- `short_lerobot_passed`：`True`。
- `short_lerobot_frame_count`：`True`。
- `short_lerobot_state_shape`：`True`。
- `short_lerobot_actions_shape`：`True`。
- `short_lerobot_cli_passed`：`True`。
- `short_lerobot_cli_frame_count`：`True`。
- `short_lerobot_cli_state_shape`：`True`。
- `short_lerobot_cli_actions_shape`：`True`。
- `policy_smoke_passed`：`True`。
- `policy_smoke_inference_seen`：`True`。
- `mock_server_started`：`True`。
- `secret_scan_clean`：`True`。

## Blocking

- pi0.5 基模缓存、Table30v2 ALOHA 数据转换和本地 mock policy smoke 均已形成离线执行证据。
