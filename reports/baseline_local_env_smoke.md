# Baseline synthetic local env smoke

## 结论

- 审计状态：`passed=True`。
- 推荐路线：`baseline_official_aloha`。
- synthetic token 长度：`45`。
- synthetic submission id 长度：`48`。
- 是否记录 synthetic 明文值：`False`。
- 是否注入父环境确认短语污染：`True`。
- 是否记录确认短语明文值：`False`。
- 临时 env 文件是否已删除：`True`。

## 覆盖的命令

- 授权预检：`bash submission/run_authorized_preflight_template.sh`。
- ready runner gate：`bash submission/run_ready_real_submission_template.sh`。

## 只读边界

- `platform_contacted`：`False`。
- `uploads_performed`：`False`。
- `download_host_contacted`：`False`。
- `credentials_printed`：`False`。
- `link_values_printed`：`False`。
- `secret_values_printed`：`False`。

## 输入证据

- `synthetic_env_file_existed_during_run`：`True`。
- `synthetic_env_file_removed_after_run`：`True`。
- `workspace_state_restored_after_smoke`：`True`。
- `authorized_preflight_returncode_zero`：`True`。
- `authorized_preflight_loaded_env_file`：`True`。
- `authorized_preflight_variant_baseline`：`True`。
- `authorized_preflight_dry_run_called`：`True`。
- `authorized_preflight_robot_type_aloha`：`True`。
- `authorized_preflight_no_protected_values_printed`：`True`。
- `ready_runner_returncode_missing_confirmation`：`True`。
- `ready_runner_loaded_env_file`：`True`。
- `ready_runner_variant_baseline`：`True`。
- `ready_runner_dry_run_called`：`True`。
- `ready_runner_parent_real_confirm_injected_before_scrub`：`True`。
- `ready_runner_parent_real_confirm_scrubbed`：`True`。
- `ready_runner_confirmation_absent_after_scrub`：`True`。
- `ready_runner_missing_confirmation`：`True`。
- `ready_runner_stops_before_real_runner`：`True`。
- `ready_runner_real_runner_not_started`：`True`。
- `ready_runner_no_protected_values_printed`：`True`。

## Blocking

- synthetic local env 已验证：baseline 预检和 dry-run gate 均会读取 local env，且不会打印值。
