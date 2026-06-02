# 提交对象确认包

## 结论

- 审计状态：`passed=True`。
- 确认项：`SUBMISSION_TARGET_CONFIRMATION`。
- 推荐路线：`baseline_official_aloha`。
- 推荐 variant：`baseline`。
- 推荐确认值：`CONFIRM_TABLE30V2_ALOHA_BASELINE`。
- 是否已经替用户确认：`False`。

## 需要用户确认的目标

- Benchmark：`Table30v2`。
- Robot Type：`aloha`。
- Task Name：`pack_the_toothbrush_holder`。
- Prompt：`Put the toothbrush and toothpaste into the toiletries case in sequence, close the case, and then place it into the basket.`。
- 本地 checkpoint：`/home/yjl/yjl/RoboChallenge/checkpoints/table30v2_multitask_baseline_aloha`。
- checkpoint 是否存在：`True`。

## 边界

- 本包只把当前可复现目标整理成可核对字段，不替用户做参赛目标确认。
- 本包不读取 token、submission id、checkpoint link 或 local env 内容。
- 本包不连接 RoboChallenge 平台，不上传 checkpoint，不生成 tar，也不启动真实 runner。

## 输入证据

- `package_audit_passed`：`True`。
- `selected_benchmark_matches`：`True`。
- `selected_robot_type_matches`：`True`。
- `selected_task_name_matches`：`True`。
- `selected_prompt_matches`：`True`。
- `selected_checkpoint_exists`：`True`。
- `mapping_task_name_matches`：`True`。
- `mapping_prompt_matches`：`True`。
- `mapping_ready_for_converter`：`True`。
- `mapping_lengths_match`：`True`。
- `dry_run_transform_smoke_present`：`True`。
- `quickstart_recommends_baseline`：`True`。
- `quickstart_baseline_needs_no_link`：`True`。
- `route_aware_recommends_baseline`：`True`。
- `route_aware_baseline_keeps_target_confirmation_blocking`：`True`。
- `web_form_recommends_baseline`：`True`。
- `web_form_keeps_target_confirmation_out_of_field_blocking`：`True`。
- `secret_scan_clean`：`True`。

## 只读边界

- `platform_contacted`：`False`。
- `uploads_performed`：`False`。
- `download_host_contacted`：`False`。
- `credentials_printed`：`False`。
- `link_values_printed`：`False`。
- `secret_values_printed`：`False`。

## Blocking

- 确认包已生成；仍需用户明确确认提交 Table30v2 ALOHA baseline 后，才可视为满足 SUBMISSION_TARGET_CONFIRMATION。
