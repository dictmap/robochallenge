# 授权后安全预检模板审计

## 结论

- 审计状态：`passed=True`。
- 模板路径：`submission/run_authorized_preflight_template.sh`。
- bash 语法检查：`True`。
- 无凭据 smoke：`True`。
- 是否连接平台：`False`。
- 是否上传：`False`。
- 是否读取或打印凭据：`False`。

## 必要片段

- `sources_local_env_file`：`True`。
- `reads_variant_after_local_env_source`：`True`。
- `default_variant_baseline`：`True`。
- `requires_target_confirmation`：`True`。
- `runs_link_intake`：`True`。
- `runs_link_download_default`：`True`。
- `download_verify_guarded`：`True`。
- `runs_readiness`：`True`。
- `runs_blockers_summary`：`True`。
- `reads_readiness_json`：`True`。
- `lora_dry_run_only`：`True`。
- `baseline_dry_run_only`：`True`。
- `blockers_warning_continues_dry_run_only`：`True`。
- `requires_explicit_real_authorization`：`True`。

## 禁止片段

- `calls_lora_real_runner`：`False`。
- `calls_baseline_real_runner`：`False`。

## 无凭据 smoke

- `returncode`：`0`。
- `passed`：`True`。
- `env_file_present_false`：`True`。
- `verify_download_disabled`：`True`。
- `target_confirmation_present`：`True`。
- `stops_before_runner`：`True`。
- `ready_false`：`True`。
- `real_runner_not_called`：`True`。

## Blocking

- 授权后安全预检模板已通过；默认不联网、不上传、不运行真实 runner。
