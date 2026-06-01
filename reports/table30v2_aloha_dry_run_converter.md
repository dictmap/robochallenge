# Table30v2 ALOHA Dry-Run Converter

## 结论

- dry-run 状态：`passed=True`。
- 抽样帧数：`5`，输出 JSONL：`/home/yjl/robochallenge/repo/runs/table30v2_aloha_dry_run_samples.jsonl`。
- 未写入全量 LeRobot 数据，未复制视频帧，只保存 schema 与数值摘要。
- raw ALOHA 双臂 14 维 state/action 已能通过 OpenPI ALOHA repack、50 步窗口、delta action 和 pi0.5 32 维 padding smoke。

## 关键形状

- raw state sequence：`[50, 14]`。
- raw action sequence：`[50, 14]`。
- after data transforms state shape：`[5, 14]`，14D 校验：`True`。
- after data transforms actions shape：`[5, 50, 14]`，50x14 校验：`True`。
- after padding state shape：`[5, 32]`，32D 校验：`True`。
- after padding actions shape：`[5, 50, 32]`，50x32 校验：`True`。
- random action offset prefill：shape=`[5]`，values=`[12, 15, 5, 0, 3]`。
- image keys：`['base_0_rgb', 'left_wrist_0_rgb', 'right_wrist_0_rgb']`。

## 下一步

- 将 dry-run 逻辑扩展为可选小 episode LeRobot writer，先只写一个短 episode。
- 小 episode 通过后，再用 `LeRobotW1DualDataConfig(repo_id='cvpr_multitask_aloha')` 做 dataloader smoke。
