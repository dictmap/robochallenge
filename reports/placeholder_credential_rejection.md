# 占位符凭据拒绝审计

## 结论

- 审计状态：`passed=True`。
- 推荐路线：`baseline_official_aloha`。
- baseline 占位符是否被拒绝：`True`。
- LoRA 占位符是否被拒绝：`True`。
- baseline 是否停在 dry-run 前：`True`。
- LoRA 是否停在 dry-run 前：`True`。
- baseline 是否未启动真实 runner：`True`。
- LoRA 是否未启动真实 runner：`True`。
- 是否记录占位符明文：`False`。
- 是否记录安全假值明文：`False`。

## 覆盖的场景

- `submission/run_table30v2_aloha_demo_template.sh` / `user_token`：returncode=`64`，rejected=`True`，stops_before_dry_run=`True`。
- `submission/run_table30v2_aloha_demo_template.sh` / `submission_id`：returncode=`64`，rejected=`True`，stops_before_dry_run=`True`。
- `submission/run_table30v2_aloha_lora_demo_template.sh` / `user_token`：returncode=`64`，rejected=`True`，stops_before_dry_run=`True`。
- `submission/run_table30v2_aloha_lora_demo_template.sh` / `submission_id`：returncode=`64`，rejected=`True`，stops_before_dry_run=`True`。

## 只读边界

- `platform_contacted`：`False`。
- `uploads_performed`：`False`。
- `download_host_contacted`：`False`。
- `credentials_printed`：`False`。
- `link_values_printed`：`False`。
- `secret_values_printed`：`False`。

## 输入证据

- `baseline_token_placeholder_rejected`：`True`。
- `baseline_submission_id_placeholder_rejected`：`True`。
- `lora_token_placeholder_rejected`：`True`。
- `lora_submission_id_placeholder_rejected`：`True`。
- `baseline_token_stops_before_dry_run`：`True`。
- `baseline_submission_id_stops_before_dry_run`：`True`。
- `lora_token_stops_before_dry_run`：`True`。
- `lora_submission_id_stops_before_dry_run`：`True`。
- `baseline_real_runner_not_started`：`True`。
- `lora_real_runner_not_started`：`True`。
- `no_protected_values_printed`：`True`。

## Blocking

- 占位符 token/submission id 已验证会在 dry-run 和真实 runner 前被拒绝。
