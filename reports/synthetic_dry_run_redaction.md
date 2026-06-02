# Synthetic dry-run 脱敏审计

## 结论

- 审计状态：`passed=True`。
- 推荐路线：`baseline_official_aloha`。
- baseline dry-run 是否通过：`True`。
- LoRA dry-run 是否通过：`True`。
- baseline 是否只输出长度：`True`。
- LoRA 是否只输出长度：`True`。
- baseline 是否未启动真实 runner：`True`。
- LoRA 是否未启动真实 runner：`True`。
- 是否记录 synthetic 明文：`False`。

## 覆盖的命令

- `submission/run_table30v2_aloha_demo_template.sh`：returncode=`0`，dry_run_passed=`True`，outputs_lengths_only=`True`。
- `submission/run_table30v2_aloha_lora_demo_template.sh`：returncode=`0`，dry_run_passed=`True`，outputs_lengths_only=`True`。

## 只读边界

- `platform_contacted`：`False`。
- `uploads_performed`：`False`。
- `download_host_contacted`：`False`。
- `credentials_printed`：`False`。
- `link_values_printed`：`False`。
- `secret_values_printed`：`False`。

## 输入证据

- `baseline_dry_run_passed`：`True`。
- `lora_dry_run_passed`：`True`。
- `baseline_outputs_lengths_only`：`True`。
- `lora_outputs_lengths_only`：`True`。
- `baseline_real_runner_not_started`：`True`。
- `lora_real_runner_not_started`：`True`。
- `no_protected_values_printed`：`True`。

## Blocking

- synthetic dry-run 已验证只输出长度字段，不打印 token/submission id 明文。
