# 提交 variant gate 审计

## 结论

- 审计状态：`passed=True`。
- 推荐路线：`baseline_official_aloha`。
- 覆盖 case 数量：`8`。
- 错误 variant case 数量：`4`。
- 合法 variant case 数量：`4`。
- 错误 variant 是否被拒绝：`True`。
- 错误 variant 是否停在预检前：`True`。
- 合法 variant 是否被接受：`True`。
- 是否启动真实 runner：`False`。

## 边界

- 本审计只设置 synthetic variant，不读取真实 token、submission id、checkpoint link 或 local env 内容。
- 支持的 variant 只有 `baseline` 与 `lora`；当前推荐提交路线仍是 `baseline`。
- 错误 variant 会在 checkpoint link、readiness 和 dry-run 前退出，避免拼写错误被后续缺凭据提示掩盖。

## 只读边界

- `platform_contacted`：`False`。
- `uploads_performed`：`False`。
- `download_host_contacted`：`False`。
- `credentials_printed`：`False`。
- `link_values_printed`：`False`。
- `secret_values_printed`：`False`。

## 输入证据

- `bad_variants_rejected`：`True`。
- `bad_variants_stop_before_preflight`：`True`。
- `valid_variants_accepted`：`True`。
- `all_cases_expected_returncodes`：`True`。
- `all_cases_no_protected_values`：`True`。
- `real_runner_not_started`：`True`。
- `restore_clean_state_passed`：`True`。

## Case 摘要

- `authorized_typo_basleine`：script=`authorized_preflight`，variant_length=`8`，returncode=`67`，rejected=`True`，preflight_started=`False`，accepted=`False`，passed=`True`。
- `ready_lora_trailing_space`：script=`ready_runner`，variant_length=`5`，returncode=`67`，rejected=`True`，preflight_started=`False`，accepted=`False`，passed=`True`。
- `authorized_uppercase`：script=`authorized_preflight`，variant_length=`8`，returncode=`67`，rejected=`True`，preflight_started=`False`，accepted=`False`，passed=`True`。
- `ready_baseline_newline`：script=`ready_runner`，variant_length=`9`，returncode=`67`，rejected=`True`，preflight_started=`False`，accepted=`False`，passed=`True`。
- `authorized_baseline`：script=`authorized_preflight`，variant_length=`8`，returncode=`0`，rejected=`False`，preflight_started=`True`，accepted=`True`，passed=`True`。
- `ready_baseline`：script=`ready_runner`，variant_length=`8`，returncode=`1`，rejected=`False`，preflight_started=`True`，accepted=`True`，passed=`True`。
- `authorized_lora`：script=`authorized_preflight`，variant_length=`4`，returncode=`0`，rejected=`False`，preflight_started=`True`，accepted=`True`，passed=`True`。
- `ready_lora`：script=`ready_runner`，variant_length=`4`，returncode=`1`，rejected=`False`，preflight_started=`True`，accepted=`True`，passed=`True`。

## Blocking

- 提交 variant gate 已通过；拼写错误、大小写错误或空白字符会在授权预检前被拒绝。
