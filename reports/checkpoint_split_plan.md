# Checkpoint 分片上传计划审计

## 结论

- 审计状态：`passed=True`。
- 是否生成 tar：`False`。
- 是否生成分片：`False`。
- 是否上传：`False`。
- 是否读取凭据：`False`。
- 预计 tar 大小：`11.064` GiB。
- 建议分片大小：`4` GiB。
- 预计分片数量：`3`。
- 当前已存在分片数量：`0`。

## 预计分片

- `runs/openpi_rtc_lora_materialized_policy_checkpoint.tar.part-000`：预计 `4.0` GiB，exists=`False`，git_ignored=`True`。
- `runs/openpi_rtc_lora_materialized_policy_checkpoint.tar.part-001`：预计 `4.0` GiB，exists=`False`，git_ignored=`True`。
- `runs/openpi_rtc_lora_materialized_policy_checkpoint.tar.part-002`：预计 `3.064` GiB，exists=`False`，git_ignored=`True`。

## 授权后命令

- `split_archive`：`split -b 4G -d -a 3 runs/openpi_rtc_lora_materialized_policy_checkpoint.tar runs/openpi_rtc_lora_materialized_policy_checkpoint.tar.part-`。
- `list_parts`：`ls -lh runs/openpi_rtc_lora_materialized_policy_checkpoint.tar.part-*`。
- `verify_reassembled_archive`：`sha256sum -c runs/openpi_rtc_lora_materialized_policy_checkpoint.tar.sha256`。
- `reassemble_archive`：`cat runs/openpi_rtc_lora_materialized_policy_checkpoint.tar.part-* > runs/openpi_rtc_lora_materialized_policy_checkpoint.tar`。
- `commands_safe`：`True`。

## Blocking

- 本审计不生成 tar、不生成分片、不上传 checkpoint。
- 真实分片上传仍需要用户先授权生成 tar/sha256，并选择存储通道。
- 拿到真实可访问 checkpoint link 后，仍需运行 checkpoint link intake 和 readiness gate。
