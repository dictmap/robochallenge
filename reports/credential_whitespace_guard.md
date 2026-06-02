# 凭据空白字符 gate 审计

## 结论

- 审计状态：`passed=True`。
- 推荐路线：`baseline_official_aloha`。
- 覆盖 case 数量：`6`。
- 坏输入 case 数量：`4`。
- 干净输入 case 数量：`2`。
- 带空白字符凭据是否被拒绝：`True`。
- 干净凭据 dry-run 是否通过：`True`。
- 是否启动真实 runner：`False`。
- 是否记录 synthetic 明文：`False`。

## 边界

- 本审计只使用 synthetic token/submission id，不读取真实凭据。
- 拒绝范围只覆盖空格、tab、换行等空白字符，避免用户复制粘贴时把不可见字符带入真实提交。
- 干净 synthetic 值只允许 dry-run 输出长度字段，不允许输出 synthetic 明文。

## 只读边界

- `platform_contacted`：`False`。
- `uploads_performed`：`False`。
- `download_host_contacted`：`False`。
- `credentials_printed`：`False`。
- `link_values_printed`：`False`。
- `secret_values_printed`：`False`。

## 输入证据

- `bad_credentials_rejected`：`True`。
- `bad_credentials_stop_before_dry_run`：`True`。
- `clean_credentials_dry_run_passed`：`True`。
- `clean_credentials_lengths_only`：`True`。
- `all_cases_expected_returncodes`：`True`。
- `all_cases_no_protected_values`：`True`。
- `real_runner_not_started`：`True`。

## Case 摘要

- `baseline_token_leading_space`：route=`baseline`，field=`user_token`，returncode=`66`，whitespace_rejected=`True`，clean_dry_run_passed=`False`，passed=`True`。
- `baseline_submission_trailing_space`：route=`baseline`，field=`submission_id`，returncode=`66`，whitespace_rejected=`True`，clean_dry_run_passed=`False`，passed=`True`。
- `lora_token_tab`：route=`lora`，field=`user_token`，returncode=`66`，whitespace_rejected=`True`，clean_dry_run_passed=`False`，passed=`True`。
- `lora_submission_newline`：route=`lora`，field=`submission_id`，returncode=`66`，whitespace_rejected=`True`，clean_dry_run_passed=`False`，passed=`True`。
- `baseline_clean_credentials`：route=`baseline`，field=`none`，returncode=`0`，whitespace_rejected=`False`，clean_dry_run_passed=`True`，passed=`True`。
- `lora_clean_credentials`：route=`lora`，field=`none`，returncode=`0`，whitespace_rejected=`False`，clean_dry_run_passed=`True`，passed=`True`。

## Blocking

- 凭据空白字符 gate 已通过；token/submission id 带空格、tab 或换行时会在 dry-run 前被拒绝。
