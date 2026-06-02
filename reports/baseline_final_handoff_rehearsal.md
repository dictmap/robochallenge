# Baseline final handoff 前三步演练

## 结论

- 审计状态：`passed=True`。
- 推荐路线：`baseline_official_aloha`。
- 演练命令数：`3`。
- synthetic token 长度：`53`。
- synthetic submission id 长度：`56`。
- 是否记录 synthetic 明文值：`False`。
- 临时 env 文件是否已删除：`True`。
- 工作区状态是否已恢复：`True`。

## 已演练命令

1. `python3 scripts/render_baseline_credential_hygiene.py`，返回码：`0`。
2. `ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_authorized_preflight_template.sh`，返回码：`0`。
3. `ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_ready_real_submission_template.sh`，返回码：`1`。

## 边界

- 本演练只使用临时 synthetic local env，不读取真实 token、submission id 或 checkpoint link。
- 本演练会恢复 wrapper 刷新的 readiness/link/blockers 状态文件，只保留本 rehearsal 产物。
- 第四条真实 runner 确认命令没有执行，仍必须等待用户明确授权。

## 只读边界

- `platform_contacted`：`False`。
- `uploads_performed`：`False`。
- `download_host_contacted`：`False`。
- `credentials_printed`：`False`。
- `link_values_printed`：`False`。
- `secret_values_printed`：`False`。

## 输入证据

- `handoff_packet_passed`：`True`。
- `handoff_first_three_commands_exact`：`True`。
- `handoff_first_three_declared_no_contact`：`True`。
- `rehearsal_command_count`：`True`。
- `synthetic_env_file_existed_during_run`：`True`。
- `synthetic_env_file_removed_after_run`：`True`。
- `workspace_state_restored_after_rehearsal`：`True`。
- `step1_returncode_zero`：`True`。
- `step1_credential_hygiene_passed`：`True`。
- `step1_no_protected_values_printed`：`True`。
- `step2_returncode_zero`：`True`。
- `step2_loaded_env_file`：`True`。
- `step2_variant_baseline`：`True`。
- `step2_dry_run_called`：`True`。
- `step2_robot_type_aloha`：`True`。
- `step2_no_protected_values_printed`：`True`。
- `step3_returncode_missing_confirmation`：`True`。
- `step3_loaded_env_file`：`True`。
- `step3_variant_baseline`：`True`。
- `step3_dry_run_called`：`True`。
- `step3_missing_confirmation`：`True`。
- `step3_stops_before_real_runner`：`True`。
- `step3_real_runner_not_started`：`True`。
- `step3_no_protected_values_printed`：`True`。

## Blocking

- baseline final handoff 前三条命令已用 synthetic local env 按顺序演练；前三步不会启动真实 runner，第四步仍必须等待用户明确授权。
