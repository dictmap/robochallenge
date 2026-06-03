# Baseline 只读预检入口

## 结论

- 审计状态：`passed=True`。
- 推荐路线：`baseline_official_aloha`。
- 目标确认值：`CONFIRM_TABLE30V2_ALOHA_BASELINE`。
- 当前是否替用户确认：`False`。
- baseline 是否需要 checkpoint 上传：`False`。
- baseline 是否需要 checkpoint link：`False`。
- 只读预检是否需要真实 runner 强确认：`False`。

## 用户确认后最短入口

1. `Notebook 第 44 节：RUN_SAFE_LOCAL_ENV_INPUT_TEMPLATE=True`，只把真实 token、submission id 和确认值写入被 Git 忽略的 local env。
2. `Notebook 第 45 节：RUN_AUTHORIZED_PREFLIGHT_TEMPLATE=True`，或在 shell 运行 `ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_authorized_preflight_template.sh`。
3. 只读预检通过后，才进入 baseline dry-run gate；真实 runner 强确认不属于只读预检。

## 只读预检需要的用户输入

- `SUBMISSION_TARGET_CONFIRMATION`
- `ROBOCHALLENGE_USER_TOKEN`
- `ROBOCHALLENGE_SUBMISSION_ID`
- `ROBOCHALLENGE_SUBMISSION_VARIANT=baseline`

## 不属于只读预检的项

- `ROBOCHALLENGE_REAL_RUN_CONFIRM`
- `CHECKPOINT_ARCHIVE_AUTHORIZATION`
- `ROBOCHALLENGE_CHECKPOINT_LINK`

## 证据

- `quickstart_passed`：`True`。
- `quickstart_command_2_exact`：`True`。
- `quickstart_recommends_baseline`：`True`。
- `quickstart_no_upload`：`True`。
- `quickstart_no_link`：`True`。
- `action_packet_passed`：`True`。
- `action_packet_recommends_baseline`：`True`。
- `action_packet_target_confirmation_value_exact`：`True`。
- `action_packet_target_not_confirmed`：`True`。
- `final_handoff_passed`：`True`。
- `final_handoff_second_command_exact`：`True`。
- `final_handoff_first_three_no_contact`：`True`。
- `final_handoff_real_runner_requires_confirmation`：`True`。
- `final_handoff_target_confirmation_value_exact`：`True`。
- `final_handoff_target_not_confirmed`：`True`。
- `jupyter_input_passed`：`True`。
- `jupyter_input_manual_target_confirmation`：`True`。
- `jupyter_input_exact_target_confirmation`：`True`。
- `jupyter_authorized_preflight_passed`：`True`。
- `target_confirmation_packet_passed`：`True`。
- `target_confirmation_value_exact`：`True`。
- `target_not_confirmed_for_user`：`True`。
- `target_does_not_confirm_for_user`：`True`。
- `target_table30v2_aloha_task_exact`：`True`。
- `route_aware_passed`：`True`。
- `route_aware_recommends_baseline`：`True`。
- `route_aware_baseline_no_upload`：`True`。
- `route_aware_baseline_no_link`：`True`。
- `route_aware_lora_web_keeps_upload`：`True`。
- `route_aware_lora_web_keeps_link`：`True`。
- `readonly_required_ids_subset_current_blocking`：`True`。
- `readonly_excluded_ids_not_required`：`True`。
- `real_runner_confirm_excluded_from_readonly_preflight`：`True`。
- `checkpoint_archive_auth_excluded_from_readonly_preflight`：`True`。
- `checkpoint_link_excluded_from_readonly_preflight`：`True`。
- `secret_scan_clean`：`True`。

## Blocking

- baseline 只读预检入口已固化；用户确认目标并填写 token/submission id 后，先运行第 45 节或 shell 只读预检，仍不要设置真实 runner 强确认。
