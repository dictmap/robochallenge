# 提交对象确认 gate 审计

## 结论

- 审计状态：`passed=True`。
- 环境变量：`ROBOCHALLENGE_SUBMISSION_TARGET_CONFIRMATION`。
- 固定确认值：`CONFIRM_TABLE30V2_ALOHA_BASELINE`。
- 推荐路线：`baseline_official_aloha`。
- 覆盖 case 数量：`7`。
- 错误确认值 case 数量：`5`。
- 正确确认值 case 数量：`2`。
- 错误确认值是否被拒绝：`True`。
- 错误确认值是否停在预检前：`True`。
- 正确确认值是否被接受：`True`。
- 是否启动真实 runner：`False`。

## 边界

- 本审计只使用 synthetic token/submission id；不会读取真实 local env。
- 错误确认值会在 checkpoint link、readiness 和 dry-run 前退出。
- 正确确认值只允许流程继续到 no-contact dry-run 或真实 runner 强确认 gate，不会启动真实 runner。

## 只读边界

- `platform_contacted`：`False`。
- `uploads_performed`：`False`。
- `download_host_contacted`：`False`。
- `credentials_printed`：`False`。
- `link_values_printed`：`False`。
- `secret_values_printed`：`False`。

## 输入证据

- `bad_confirmations_rejected`：`True`。
- `bad_confirmations_stop_before_preflight`：`True`。
- `correct_confirmation_accepted`：`True`。
- `authorized_correct_reaches_dry_run`：`True`。
- `ready_correct_stops_without_real_confirm`：`True`。
- `all_cases_expected_returncodes`：`True`。
- `all_cases_no_protected_values`：`True`。
- `real_runner_not_started`：`True`。
- `restore_clean_state_passed`：`True`。

## Case 摘要

- `authorized_missing`：script=`authorized_preflight`，confirmation_present=`False`，confirmation_length=`0`，returncode=`69`，rejected=`True`，preflight_started=`False`，accepted=`False`，dry_run=`False`，passed=`True`。
- `ready_wrong`：script=`ready_runner`，confirmation_present=`True`，confirmation_length=`28`，returncode=`69`，rejected=`True`，preflight_started=`False`，accepted=`False`，dry_run=`False`，passed=`True`。
- `authorized_trailing_space`：script=`authorized_preflight`，confirmation_present=`True`，confirmation_length=`33`，returncode=`69`，rejected=`True`，preflight_started=`False`，accepted=`False`，dry_run=`False`，passed=`True`。
- `ready_lowercase`：script=`ready_runner`，confirmation_present=`True`，confirmation_length=`32`，returncode=`69`，rejected=`True`，preflight_started=`False`，accepted=`False`，dry_run=`False`，passed=`True`。
- `authorized_newline`：script=`authorized_preflight`，confirmation_present=`True`，confirmation_length=`33`，returncode=`69`，rejected=`True`，preflight_started=`False`，accepted=`False`，dry_run=`False`，passed=`True`。
- `authorized_correct`：script=`authorized_preflight`，confirmation_present=`True`，confirmation_length=`32`，returncode=`0`，rejected=`False`，preflight_started=`True`，accepted=`True`，dry_run=`True`，passed=`True`。
- `ready_correct_missing_real_confirm`：script=`ready_runner`，confirmation_present=`True`，confirmation_length=`32`，returncode=`1`，rejected=`False`，preflight_started=`True`，accepted=`True`，dry_run=`True`，passed=`True`。

## Blocking

- 提交对象确认 gate 已通过；缺失、错误或畸形确认值会在 checkpoint/readiness/dry-run 前被拒绝。
