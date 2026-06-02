# 真实提交阻塞项摘要

## 结论

- 审计状态：`passed=True`。
- go/no-go：`blocked`。
- 真实提交就绪：`False`。
- Web 表单就绪：`False`。
- checkpoint link 形态就绪：`False`。
- 下载已验证：`False`。
- 阻塞项数量：`11`。
- 推荐路线：`baseline_official_aloha`。
- baseline 是否需要 checkpoint link：`False`。
- baseline 是否需要 checkpoint upload：`False`。
- LoRA/web 是否需要 checkpoint link：`True`。
- LoRA/web 是否需要 checkpoint upload：`True`。
- 是否连接平台：`False`。
- 是否上传：`False`。
- 是否读取真实凭据：`False`。

## 本地材料状态

- `submission_package_ready`：`True`。
- `artifact_manifest_ready`：`True`。
- `env_template_ready`：`True`。
- `notebook_structure_ready`：`True`。
- `jupyter_input_template_ready`：`True`。
- `jupyter_authorized_preflight_template_ready`：`True`。
- `authorized_preflight_template_ready`：`True`。
- `ready_real_runner_template_ready`：`True`。
- `authorized_checkpoint_archive_template_ready`：`True`。
- `authorized_execution_checklist_ready`：`True`。
- `route_aware_submission_blockers_ready`：`True`。
- `upload_channels_audited`：`True`。
- `preflight_bundle_ready`：`True`。
- `secret_scan_clean`：`True`。

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

## 需要用户提供或授权

- `ROBOCHALLENGE_USER_TOKEN`：用户登录 RoboChallenge 后提供；只能放入本地 shell 或被 Git 忽略的 local env 文件。
- `ROBOCHALLENGE_SUBMISSION_ID`：用户在 RoboChallenge My Submission/Detail 页面确认；不能伪造。
- `CHECKPOINT_UPLOAD_AUTHORIZATION`：如果提交 LoRA 物化 checkpoint，用户需要确认是否生成 12GB+ tar 并选择上传通道。
- `ROBOCHALLENGE_CHECKPOINT_LINK`：由用户授权上传后得到；只做脱敏形态检查，默认不联网验证。

## 当前阻塞项

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

## 拿到用户输入后的下一步

- 先运行 `python3 scripts/audit_real_submission_readiness.py`。
- 如果 readiness 仍为 false，停止，不启动真实 runner。
- 如果需要联网验证 checkpoint link，必须由用户显式授权后再运行 `python3 scripts/audit_checkpoint_link_download_verification.py --verify-download`。
