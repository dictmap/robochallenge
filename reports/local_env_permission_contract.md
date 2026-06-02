# Local env 权限契约审计

## 结论

- 审计状态：`passed=True`。
- 推荐路线：`baseline_official_aloha`。
- 建议本地凭据文件：`submission/robochallenge_env.local.sh`。
- 建议权限命令：`chmod 600 submission/robochallenge_env.local.sh`。
- 本地凭据文件是否存在：`False`。
- 本地凭据文件权限：``。
- 本地凭据文件是否仅 owner 有权限：`True`。
- 是否读取本地凭据文件内容：`False`。

## 边界

- 本审计只读取文件元数据和模板文本，不读取真实 local env 内容。
- 如果真实 local env 文件存在，建议权限必须收敛到 `chmod 600`。
- Windows/PowerShell 侧权限语义不同；最终提交前以 Linux 端审计结果为准。

## 只读边界

- `platform_contacted`：`False`。
- `uploads_performed`：`False`。
- `download_host_contacted`：`False`。
- `credentials_printed`：`False`。
- `link_values_printed`：`False`。
- `secret_values_printed`：`False`。

## 输入证据

- `env_template_exists`：`True`。
- `env_template_mentions_local_copy`：`True`。
- `env_template_recommends_chmod_600`：`True`。
- `local_env_gitignored`：`True`。
- `local_env_not_tracked`：`True`。
- `local_env_content_not_read`：`True`。
- `local_env_absent_or_owner_only`：`True`。
- `synthetic_chmod_600_owner_only`：`True`。
- `synthetic_chmod_600_owner_readable`：`True`。
- `synthetic_file_removed_after_run`：`True`。

## Blocking

- local env 权限契约已通过；真实凭据文件应保持 Git 忽略、未跟踪且 chmod 600。
