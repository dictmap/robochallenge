# 路线感知阻塞摘要

## 结论

- 审计状态：`passed=True`。
- 推荐路线：`baseline_official_aloha`。
- baseline 是否需要 checkpoint upload：`False`。
- baseline 是否需要 checkpoint link：`False`。
- LoRA/web 是否需要 checkpoint upload：`True`。
- LoRA/web 是否需要 checkpoint link：`True`。

## Baseline 最短路线当前只差

- `SUBMISSION_TARGET_CONFIRMATION`
- `ROBOCHALLENGE_USER_TOKEN`
- `ROBOCHALLENGE_SUBMISSION_ID`
- `ROBOCHALLENGE_SUBMISSION_VARIANT=baseline`
- `ROBOCHALLENGE_REAL_RUN_CONFIRM`

## LoRA / 网页 checkpoint 路线当前只差

- `SUBMISSION_TARGET_CONFIRMATION`
- `ROBOCHALLENGE_USER_TOKEN`
- `ROBOCHALLENGE_SUBMISSION_ID`
- `ROBOCHALLENGE_SUBMISSION_VARIANT=lora`
- `CHECKPOINT_ARCHIVE_AUTHORIZATION`
- `ROBOCHALLENGE_CHECKPOINT_LINK`
- `ROBOCHALLENGE_REAL_RUN_CONFIRM`

## 说明

- 如果先复现并提交官方 ALOHA baseline，本地 runner 不需要 checkpoint link，也不需要生成或上传 LoRA tar。
- 只有选择 LoRA 物化 checkpoint 或网页 checkpoint 链接路线时，才进入归档、上传和 checkpoint link 回填流程。
- 旧的全局 readiness 阻塞仍会列出 checkpoint link，因为它同时覆盖网页表单和 LoRA checkpoint 路线。

## 旧全局阻塞（保留兼容）

- 缺少 ROBOCHALLENGE_USER_TOKEN。
- 缺少 ROBOCHALLENGE_SUBMISSION_ID。
- 缺少真实可访问 checkpoint link；可使用 ROBOCHALLENGE_CHECKPOINT_LINK 或 ROBOCHALLENGE_LORA_CHECKPOINT_LINK 记录。
- 尚未执行 checkpoint 上传，本地 tar 文件也未生成。
- 缺少 checkpoint link；请设置 ROBOCHALLENGE_CHECKPOINT_LINK 或 ROBOCHALLENGE_LORA_CHECKPOINT_LINK。
- 缺少真实 checkpoint link；当前只能审计下载校验协议，不能联网验证。
- 未请求 --verify-download；本轮不联网、不下载、不接触 checkpoint link host。
- 需要用户提供真实 ROBOCHALLENGE_USER_TOKEN。
- 需要用户提供真实 ROBOCHALLENGE_SUBMISSION_ID。
- 需要确认本次要提交的是 Table30v2 ALOHA 还是原始 Table30；当前可运行链路是 Table30v2 ALOHA。
- 若要提交 LoRA 版本，还需要把本地 12GB+ checkpoint 放到网站可访问的 checkpoint link。

## 只读边界

- `platform_contacted`：`False`。
- `uploads_performed`：`False`。
- `download_host_contacted`：`False`。
- `credentials_printed`：`False`。
- `link_values_printed`：`False`。
- `secret_values_printed`：`False`。

## 输入证据

- `route_packet_passed`：`True`。
- `recommended_default_is_baseline`：`True`。
- `baseline_quickstart_passed`：`True`。
- `baseline_quickstart_no_upload`：`True`。
- `baseline_quickstart_no_link`：`True`。
- `baseline_route_local_runner_ready_without_credentials`：`True`。
- `baseline_route_no_upload`：`True`。
- `baseline_route_no_local_link`：`True`。
- `baseline_blocking_has_no_checkpoint_link`：`True`。
- `baseline_blocking_has_no_archive_authorization`：`True`。
- `baseline_required_ids_complete`：`True`。
- `lora_web_requires_checkpoint_link`：`True`。
- `lora_web_requires_archive_authorization`：`True`。
- `lora_web_required_ids_complete`：`True`。
- `readiness_gate_passed`：`True`。
- `readiness_currently_false`：`True`。
- `web_form_packet_passed`：`True`。
- `action_packet_passed`：`True`。
- `secret_scan_clean`：`True`。

## Blocking

- 路线感知阻塞摘要已生成；baseline 最短路线不需要 checkpoint link 或归档上传。
