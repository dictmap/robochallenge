# Local env runtime 权限 gate 审计

## 结论

- 审计状态：`passed=True`。
- 推荐路线：`baseline_official_aloha`。
- 覆盖 case 数量：`4`。
- 权限过宽是否拒绝：`True`。
- owner-only 权限是否放行：`True`。
- 是否在权限检查前读取内容：`False`。
- 是否启动真实 runner：`False`。
- 是否记录 synthetic 明文：`False`。

## 边界

- 本审计只使用临时 synthetic local env，不读取真实 `submission/robochallenge_env.local.sh` 内容。
- `0644` 临时 env 必须在 `source` 前失败，并提示 `chmod 600`。
- `0600` 临时 env 允许进入授权预检或 ready runner 的既有阻断边界，但不允许启动真实 runner。

## 只读边界

- `platform_contacted`：`False`。
- `uploads_performed`：`False`。
- `download_host_contacted`：`False`。
- `credentials_printed`：`False`。
- `link_values_printed`：`False`。
- `secret_values_printed`：`False`。

## 输入证据

- `bad_permissions_rejected`：`True`。
- `bad_permissions_stop_before_dry_run`：`True`。
- `bad_permissions_no_protected_values`：`True`。
- `owner_only_permissions_accepted`：`True`。
- `owner_only_no_protected_values`：`True`。
- `all_cases_expected_returncodes`：`True`。
- `all_cases_temp_env_removed`：`True`。
- `real_runner_not_started`：`True`。
- `restore_clean_state_passed`：`True`。

## Case 摘要

- `authorized_bad_permissions`：mode=`0o644`，returncode=`65`，permission_rejected=`True`，permission_accepted=`False`，passed=`True`。
- `ready_bad_permissions`：mode=`0o644`，returncode=`65`，permission_rejected=`True`，permission_accepted=`False`，passed=`True`。
- `authorized_owner_only`：mode=`0o600`，returncode=`0`，permission_rejected=`False`，permission_accepted=`True`，passed=`True`。
- `ready_owner_only`：mode=`0o600`，returncode=`1`，permission_rejected=`False`，permission_accepted=`True`，passed=`True`。

## Blocking

- local env 运行时权限 gate 已通过；权限过宽会在 source 前被拒绝，owner-only synthetic 文件可进入授权边界。
