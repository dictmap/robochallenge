# Baseline dry-run gate 证据包

## 结论

- 审计状态：`passed=True`。
- 推荐路线：`baseline_official_aloha`。
- baseline 是否需要 checkpoint upload：`False`。
- baseline 是否需要 checkpoint link：`False`。
- 无真实确认短语时是否停在 runner 前：`True`。
- 错误确认短语时是否停在 runner 前：`True`。
- 畸形确认短语时是否停在 runner 前：`True`。

## 目标确认、token、submission id、variant 到位后先跑

1. 授权前只读预检：`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_authorized_preflight_template.sh`
2. baseline wrapper dry-run gate：`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_ready_real_submission_template.sh`
3. 真实 runner 强确认命令：`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION bash submission/run_ready_real_submission_template.sh`

第 2 条用于验证 wrapper 和 baseline runner 入口；缺少真实 runner 强确认短语时只会 dry-run，然后停在真实 runner 前。
第 3 条只有用户明确授权真实提交时才运行，会连接 RoboChallenge 并启动真实 runner。

## 路线边界

- baseline 官方 ALOHA 路线不需要 checkpoint link、checkpoint upload 或归档授权。
- LoRA / 网页 checkpoint 路线仍单独保留 checkpoint 归档、上传和真实 link 回填要求。

## 只读边界

- `platform_contacted`：`False`。
- `uploads_performed`：`False`。
- `download_host_contacted`：`False`。
- `credentials_printed`：`False`。
- `link_values_printed`：`False`。
- `secret_values_printed`：`False`。

## 输入证据

- `route_packet_passed`：`True`。
- `recommended_route_baseline`：`True`。
- `quickstart_passed`：`True`。
- `quickstart_no_checkpoint_upload`：`True`。
- `quickstart_no_checkpoint_link`：`True`。
- `authorized_preflight_command_exact`：`True`。
- `dry_run_gate_command_exact`：`True`。
- `real_runner_command_exact`：`True`。
- `ready_runner_template_passed`：`True`。
- `ready_runner_default_baseline`：`True`。
- `synthetic_dry_run_called`：`True`。
- `synthetic_variant_baseline`：`True`。
- `synthetic_missing_confirmation`：`True`。
- `synthetic_stops_before_real_runner`：`True`。
- `synthetic_real_runner_not_started`：`True`。
- `synthetic_no_protected_values_printed`：`True`。
- `wrong_confirm_dry_run_called`：`True`。
- `wrong_confirm_confirmation_present`：`True`。
- `wrong_confirm_stops_before_real_runner`：`True`。
- `wrong_confirm_real_runner_not_started`：`True`。
- `wrong_confirm_no_protected_values_printed`：`True`。
- `malformed_confirm_cases_rejected`：`True`。
- `malformed_confirm_case_count`：`True`。
- `malformed_confirm_real_runner_not_started`：`True`。
- `authorized_execution_passed`：`True`。
- `authorized_execution_baseline_required_ids`：`True`。
- `authorized_execution_baseline_no_lora_ids`：`True`。
- `action_packet_passed`：`True`。
- `action_packet_baseline_required_ids`：`True`。
- `action_packet_baseline_no_lora_ids`：`True`。
- `route_aware_passed`：`True`。
- `route_aware_baseline_no_checkpoint_upload`：`True`。
- `route_aware_baseline_no_checkpoint_link`：`True`。
- `route_aware_baseline_required_ids`：`True`。
- `route_aware_baseline_no_lora_ids`：`True`。
- `route_aware_lora_keeps_link_branch`：`True`。
- `secret_scan_clean`：`True`。
- `previous_preflight_passed_or_absent`：`True`。

## Blocking

- baseline dry-run gate 已固化；目标确认、token、submission id 和 variant=baseline 到位后先跑只读预检，再跑 dry-run gate，缺少真实 runner 强确认短语时不会启动 runner。
