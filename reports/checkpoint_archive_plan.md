# Checkpoint 归档计划审计

## 结论

- 审计状态：`passed=True`。
- 是否生成 tar：`False`。
- 是否执行上传：`False`。
- 是否读取凭据：`False`。
- 预计 tar 大小：`11.064` GB。
- runs 剩余空间十 GB 桶：`460` GB。
- 空间余量是否满足 2 倍预计 tar：`True`。

## 路径与 Git 忽略

- `archive_ignored`：`True`。
- `sha256_ignored`：`True`。
- `split_part_ignored`：`True`。

## 建议命令

- `create_archive`：`tar -C runs -cf runs/openpi_rtc_lora_materialized_policy_checkpoint.tar openpi_rtc_lora_materialized_policy_checkpoint`。
- `write_sha256`：`sha256sum runs/openpi_rtc_lora_materialized_policy_checkpoint.tar > runs/openpi_rtc_lora_materialized_policy_checkpoint.tar.sha256`。
- `optional_split_4g`：`split -b 4G -d -a 3 runs/openpi_rtc_lora_materialized_policy_checkpoint.tar runs/openpi_rtc_lora_materialized_policy_checkpoint.tar.part-`。
- `commands_safe`：`True`。

## 输入证据

- `export_audit_local_ready`：`True`。
- `tar_stream_smoke_passed`：`True`。
- `upload_audit_passed`：`True`。
- `checkpoint_dir_exists`：`True`。
- `archive_absent`：`True`。
- `sha256_absent`：`True`。
- `uploads_not_performed`：`True`。

## Blocking

- 本审计不生成 tar、不计算真实 sha256、不上传 checkpoint。
- 真实上传仍需要用户选择并授权存储位置，再提供可访问 checkpoint link。
