# Baseline 最终交接包

## 结论

- 审计状态：`passed=True`。
- 推荐路线：`baseline_official_aloha`。
- 建议本地凭据文件：`submission/robochallenge_env.local.sh`。
- 是否读取 local env 内容：`False`。
- baseline 是否需要 checkpoint upload：`False`。
- baseline 是否需要 checkpoint link：`False`。
- baseline 是否需要 checkpoint 归档授权：`False`。
- 前三步 no-contact 命令数量：`3`。
- 真实 runner 是否需要强确认：`True`。

## 凭据后执行顺序

1. 凭据卫生检查：`python3 scripts/render_baseline_credential_hygiene.py`
   - no_contact=`True`；requires_user_credentials=`False`；starts_real_runner=`False`。
2. baseline 授权前只读预检：`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_authorized_preflight_template.sh`
   - no_contact=`True`；requires_user_credentials=`True`；starts_real_runner=`False`。
3. baseline dry-run gate：`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_ready_real_submission_template.sh`
   - no_contact=`True`；requires_user_credentials=`True`；starts_real_runner=`False`。
4. 真实 runner 强确认入口：`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION bash submission/run_ready_real_submission_template.sh`
   - no_contact=`False`；requires_user_credentials=`True`；starts_real_runner=`True`。

## 当前 baseline 只差

- `ROBOCHALLENGE_REAL_RUN_CONFIRM`
- `ROBOCHALLENGE_SUBMISSION_ID`
- `ROBOCHALLENGE_SUBMISSION_VARIANT=baseline`
- `ROBOCHALLENGE_USER_TOKEN`
- `SUBMISSION_TARGET_CONFIRMATION`

## 边界

- 本包没有读取真实 token、submission id 或 checkpoint link。
- 前三条命令只用于卫生检查、只读预检和 dry-run gate；第四条命令会启动真实 runner，只能在用户明确授权后运行。
- checkpoint 归档、上传和 checkpoint link 仍属于 LoRA/web checkpoint 路线，不是 baseline 官方 ALOHA 路线的前置条件。

## 只读边界

- `platform_contacted`：`False`。
- `uploads_performed`：`False`。
- `download_host_contacted`：`False`。
- `credentials_printed`：`False`。
- `link_values_printed`：`False`。
- `secret_values_printed`：`False`。

## 输入证据

- `route_packet_passed`：`True`。
- `route_packet_recommends_baseline`：`True`。
- `quickstart_passed`：`True`。
- `quickstart_command_2_exact`：`True`。
- `quickstart_command_3_exact`：`True`。
- `quickstart_command_4_exact`：`True`。
- `dry_run_gate_passed`：`True`。
- `dry_run_gate_command_exact`：`True`。
- `dry_run_gate_real_command_exact`：`True`。
- `dry_run_gate_stops_before_real_runner`：`True`。
- `credential_hygiene_passed`：`True`。
- `credential_hygiene_local_env_gitignored`：`True`。
- `credential_hygiene_local_env_not_tracked`：`True`。
- `credential_hygiene_does_not_read_local_env`：`True`。
- `local_env_smoke_passed`：`True`。
- `local_env_smoke_values_not_recorded`：`True`。
- `local_env_smoke_temp_env_removed`：`True`。
- `local_env_smoke_authorized_preflight_baseline`：`True`。
- `local_env_smoke_ready_runner_stops`：`True`。
- `authorized_execution_passed`：`True`。
- `authorized_execution_required_ids_complete`：`True`。
- `action_packet_passed`：`True`。
- `action_packet_required_ids_complete`：`True`。
- `route_aware_passed`：`True`。
- `route_aware_recommends_baseline`：`True`。
- `route_aware_baseline_no_checkpoint_upload`：`True`。
- `route_aware_baseline_no_checkpoint_link`：`True`。
- `route_aware_baseline_blocking_exact`：`True`。
- `route_aware_baseline_no_lora_ids`：`True`。
- `route_aware_lora_keeps_checkpoint_requirements`：`True`。
- `credential_hygiene_required_ids_complete`：`True`。
- `dry_run_gate_required_ids_complete`：`True`。
- `secret_scan_clean`：`True`。
- `handoff_command_count`：`True`。
- `handoff_command_order_exact`：`True`。
- `handoff_first_three_no_contact`：`True`。
- `handoff_real_runner_requires_confirmation`：`True`。

## Blocking

- baseline 最终交接包已固化；拿到用户凭据后先跑前三个 no-contact 步骤，只有用户明确授权时才运行第四个真实 runner 强确认命令。
