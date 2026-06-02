# Checkpoint 归档生成 dry-run

## 结论

- 审计状态：`passed=True`。
- 是否 dry-run：`True`。
- 是否请求执行：`False`。
- 是否通过显式执行门槛：`False`。
- 是否缺少执行确认：`False`。
- 是否生成 tar：`False`。
- 是否生成 sha256：`False`。
- 是否上传：`False`。
- 是否读取凭据：`False`。
- 是否连接平台：`False`。
- 预期 tar 大小：`11.064` GB。
- runs 剩余空间 10GB 桶：`460` GB。

## 路径状态

- checkpoint 目录存在：`True`。
- tar 生成前不存在：`True`。
- sha256 生成前不存在：`True`。
- tar 生成后不存在：`True`。
- sha256 生成后不存在：`True`。
- tar 路径被 Git 忽略：`True`。
- sha256 路径被 Git 忽略：`True`。

## 命令

- `dry_run`：`python3 scripts/create_checkpoint_archive.py`。
- `execute`：`python3 scripts/create_checkpoint_archive.py --execute --confirm-create-large-archive`。
- `tar_invocation`：`tar -C runs -cf runs/openpi_rtc_lora_materialized_policy_checkpoint.tar openpi_rtc_lora_materialized_policy_checkpoint`。
- `sha256_method`：`python hashlib.sha256 -> runs/openpi_rtc_lora_materialized_policy_checkpoint.tar.sha256`。
- `uses_shell`：`False`。
- `destructive_commands`：`False`。

## Blocking

- 默认 dry-run 不生成 tar；真正生成约 12GB 归档必须显式使用 --execute --confirm-create-large-archive。
- 本脚本不上传 checkpoint、不读取凭据、不连接 RoboChallenge 平台。
- 真实提交仍需要用户提供 token、submission id 和可访问 checkpoint link。
