# Baseline 凭据卫生证据包

## 结论

- 审计状态：`passed=True`。
- 推荐路线：`baseline_official_aloha`。
- 建议本地凭据文件：`submission/robochallenge_env.local.sh`。
- 本地凭据文件是否存在：`False`。
- 是否读取本地凭据文件内容：`False`。
- 本地凭据文件是否被 Git 忽略：`True`。
- 本地凭据文件是否被 Git 跟踪：`False`。
- baseline 是否需要 checkpoint upload：`False`。
- baseline 是否需要 checkpoint link：`False`。

## 凭据到位后的安全顺序

1. 只读授权预检：`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_authorized_preflight_template.sh`
2. baseline dry-run gate：`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_ready_real_submission_template.sh`

## 边界

- 真实 token 和 submission id 只能写入 Git 忽略的 local env 或当前 shell。
- 本证据包只检查路径和上游审计结果，不读取 local env 内容。
- LoRA/web checkpoint 的归档、上传和 checkpoint link 仍保留在单独分支，不属于 baseline 前置条件。

## 只读边界

- `platform_contacted`：`False`。
- `uploads_performed`：`False`。
- `download_host_contacted`：`False`。
- `credentials_printed`：`False`。
- `link_values_printed`：`False`。
- `secret_values_printed`：`False`。

## 输入证据

- `env_template_passed`：`True`。
- `template_uses_placeholders_for_secrets`：`True`。
- `template_default_variant_baseline`：`True`。
- `local_env_gitignored_by_template_audit`：`True`。
- `local_env_gitignored_now`：`True`。
- `local_env_not_tracked`：`True`。
- `plaintext_scan_passed`：`True`。
- `plaintext_scan_hit_count_zero`：`True`。
- `authorized_preflight_passed`：`True`。
- `authorized_preflight_no_credentials_smoke`：`True`。
- `baseline_dry_run_gate_passed`：`True`。
- `baseline_dry_run_gate_command_exact`：`True`。
- `baseline_dry_run_stops_before_real_runner`：`True`。
- `baseline_required_ids_complete`：`True`。
- `baseline_required_ids_do_not_include_lora_only`：`True`。
- `lora_branch_keeps_upload_and_link_ids`：`True`。

## Blocking

- baseline 凭据卫生边界已固化；真实 token/submission id 只应写入 Git 忽略的 local env，然后先跑只读预检和 baseline dry-run gate。
