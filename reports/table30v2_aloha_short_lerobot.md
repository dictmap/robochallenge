# Table30v2 ALOHA 短 episode LeRobot writer

## 结论

- 写出状态：`passed=True`。
- LeRobot repo_id：`robochallenge_table30v2_aloha_short`。
- 本地路径：`/home/yjl/.cache/huggingface/lerobot/robochallenge_table30v2_aloha_short`。
- 写入帧数：`64`，fps=`30`。
- 写入字段：三路图像、14D `observation.state`、14D `action`、任务 prompt。

## dataloader smoke

- OpenPI config：`cvpr_multitask_aloha_rtc`。
- state shape：`[1, 5, 32]`。
- actions shape：`[1, 5, 50, 32]`。
- image keys：`['base_0_rgb', 'left_wrist_0_rgb', 'right_wrist_0_rgb']`。
- tokenized prompt shape：`[1, 5, 200]`。

## 下一步

- 将短 episode writer 扩展为可控分片 writer，再接小步数微调 dry-run。
- 真实提交仍需要 RoboChallenge `user_token` 和 `submission_id`。
