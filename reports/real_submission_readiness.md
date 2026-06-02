# 真实提交 readiness gate

## 结论

- 审计状态：`passed=True`。
- 可进入真实提交：`False`。
- Web 表单就绪：`False`。
- 本地 baseline runner 就绪：`False`。
- 本地 LoRA runner 就绪：`False`。
- 是否连接 RoboChallenge 平台：`False`。
- 是否打印凭据：`False`。

## 环境变量状态

- `ROBOCHALLENGE_USER_TOKEN`：present=`False`，length=`0`，looks_like_url=`False`。
- `ROBOCHALLENGE_SUBMISSION_ID`：present=`False`，length=`0`，looks_like_url=`False`。
- `ROBOCHALLENGE_CHECKPOINT_LINK`：present=`False`，length=`0`，looks_like_url=`False`。
- `ROBOCHALLENGE_LORA_CHECKPOINT_LINK`：present=`False`，length=`0`，looks_like_url=`False`。

## 输入证据

- `submission_audit_passed`：`True`。
- `export_audit_local_ready`：`True`。
- `upload_audit_passed`：`True`。
- `uploads_performed`：`False`。
- `manifest_status`：`template_pending_credentials`。
- `baseline_checkpoint_exists`：`True`。
- `lora_checkpoint_exists`：`True`。

## Blocking

- 缺少 ROBOCHALLENGE_USER_TOKEN。
- 缺少 ROBOCHALLENGE_SUBMISSION_ID。
- 缺少真实可访问 checkpoint link；可使用 ROBOCHALLENGE_CHECKPOINT_LINK 或 ROBOCHALLENGE_LORA_CHECKPOINT_LINK 记录。
- 尚未执行 checkpoint 上传，本地 tar 文件也未生成。
