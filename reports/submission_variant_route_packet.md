# 提交路线拆分包

## 结论

- 审计状态：`passed=True`。
- 推荐默认路线：`baseline_official_aloha`。
- 路线数量：`2`。

## 路线

### 官方 Table30v2 ALOHA baseline

- route id：`baseline_official_aloha`。
- 是否推荐默认：`True`。
- 本地 runner 在未填凭据前是否已就绪：`True`。
- 本地 checkpoint 是否就绪：`True`。
- 本地 runner 是否需要 checkpoint upload：`False`。
- 本地 runner 是否需要 checkpoint link：`False`。
- 生成公网 checkpoint link 是否仍需上传：`False`。
- 说明：本地 runner 路线使用 Linux 上已存在的官方 ALOHA checkpoint，不需要先生成 LoRA tar，也不需要 checkpoint link。仍需要用户 token、submission id、提交对象确认和真实 runner 强确认。
- 当前阻塞：
  - `SUBMISSION_TARGET_CONFIRMATION`
  - `ROBOCHALLENGE_USER_TOKEN`
  - `ROBOCHALLENGE_SUBMISSION_ID`
  - `ROBOCHALLENGE_SUBMISSION_VARIANT=baseline`
  - `ROBOCHALLENGE_REAL_RUN_CONFIRM`
- 证据：
  - `package_audit_passed`：`True`。
  - `mapping_ready`：`True`。
  - `official_checkpoint_exists`：`True`。
  - `runner_template_ready_without_credentials`：`True`。
  - `token_present`：`False`。
  - `submission_id_present`：`False`。

### LoRA 物化 checkpoint

- route id：`lora_materialized`。
- 是否推荐默认：`False`。
- 本地 runner 在未填凭据前是否已就绪：`True`。
- 本地 checkpoint 是否就绪：`True`。
- 本地 runner 是否需要 checkpoint upload：`False`。
- 本地 runner 是否需要 checkpoint link：`False`。
- 生成公网 checkpoint link 是否仍需上传：`True`。
- 说明：本地 LoRA 物化 checkpoint 已能被 policy 加载；如果作为网页可访问 checkpoint 提交，仍需要用户授权归档/上传并回填真实 HTTPS checkpoint link。
- 当前阻塞：
  - `SUBMISSION_TARGET_CONFIRMATION`
  - `ROBOCHALLENGE_USER_TOKEN`
  - `ROBOCHALLENGE_SUBMISSION_ID`
  - `ROBOCHALLENGE_SUBMISSION_VARIANT=lora`
  - `CHECKPOINT_ARCHIVE_AUTHORIZATION`
  - `ROBOCHALLENGE_CHECKPOINT_LINK`
  - `ROBOCHALLENGE_REAL_RUN_CONFIRM`
- 证据：
  - `package_audit_passed`：`True`。
  - `mapping_ready`：`True`。
  - `materialized_checkpoint_exists`：`True`。
  - `lora_export_ready`：`True`。
  - `policy_smoke_passed`：`True`。
  - `runner_template_ready_without_credentials`：`True`。
  - `upload_channels_audited`：`True`。
  - `uploads_performed`：`False`。
  - `checkpoint_link_present`：`False`。

## 只读边界

- `platform_contacted`：`False`。
- `uploads_performed`：`False`。
- `download_host_contacted`：`False`。
- `credentials_printed`：`False`。
- `link_values_printed`：`False`。
- `secret_values_printed`：`False`。

## 输入证据

- `package_audit_passed`：`True`。
- `readiness_gate_passed`：`True`。
- `baseline_local_route_ready_without_credentials`：`True`。
- `baseline_does_not_need_upload_or_link`：`True`。
- `lora_local_checkpoint_ready`：`True`。
- `lora_public_link_still_needs_upload`：`True`。
- `secret_scan_clean`：`True`。

## Blocking

- 提交路线已拆分；默认建议先走官方 ALOHA baseline 本地 runner 路线。
