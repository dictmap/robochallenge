# RoboChallenge 网页表单字段包

## 结论

- 审计状态：`passed=True`。
- Web 表单当前是否就绪：`False`。
- 字段数：`12`，已就绪 `7`，待用户补齐 `5`。

## 字段清单

- `Benchmark`：ready=`True`，value=`Table30v2`。
  来源：`runs/robochallenge_submission_package_audit.json`。当前可复现链路是 Table30v2；原始 Table30 仍需单独补齐。
- `Robot Type`：ready=`True`，value=`aloha`。
  来源：`runs/table30v2_aloha_mapping_audit.json`。当前 runner 和数据映射均为 ALOHA。
- `Task Name`：ready=`True`，value=`pack_the_toothbrush_holder`。
  来源：`runs/table30v2_aloha_mapping_audit.json`。已验证任务链为 pack_the_toothbrush_holder。
- `Prompt`：ready=`True`，value=`Put the toothbrush and toothpaste into the toiletries case in sequence, close the case, and then place it into the basket.`。
  来源：`submission/submission_manifest_template.json`。runner 默认 prompt 与任务说明一致。
- `Inference Code Link`：ready=`True`，value=`https://github.com/dictmap/robochallenge/tree/main`。
  来源：`submission/submission_manifest_template.json`。建议填写当前 GitHub 主分支；不要在链接里携带凭据。
- `Fine-tuning / Restore Evidence`：ready=`True`，value=`https://github.com/dictmap/robochallenge/tree/main`。
  来源：`reports/robochallenge_submission_package_checklist.md`。同仓库包含 scripts、notebooks、reports 和 LoRA 恢复/物化证据。
- `Checkpoint Link`：ready=`False`，value=``。
  来源：`runs/checkpoint_link_intake.json`。需要用户授权上传后填入真实可访问 HTTPS 链接；当前不打印链接明文。
- `RoboChallenge User Token`：ready=`False`，value=``。
  来源：`runs/real_submission_readiness.json`。只能写入本地 env 或 shell，不能写入 tracked 文件。
- `RoboChallenge Submission ID`：ready=`False`，value=``。
  来源：`runs/real_submission_readiness.json`。必须来自 RoboChallenge 页面，不能伪造。
- `Submission Variant`：ready=`False`，value=`baseline 或 lora_materialized`。
  来源：`runs/next_user_action_packet.json`。需要用户确认提交官方 ALOHA baseline 还是 LoRA 物化 checkpoint。
- `Checkpoint Upload / Archive`：ready=`False`，value=`pending_user_authorization`。
  来源：`runs/checkpoint_upload_channels_audit.json`。LoRA 版本需要用户授权生成 tar、选择上传通道并得到 checkpoint link。
- `Authorized Notebook Entry`：ready=`True`，value=`Notebook 第 44/45 节`。
  来源：`reports/next_user_action_packet.md`。推荐先通过 Jupyter 写入 local env，再跑授权预检。

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
- `current_web_form_not_ready`：`True`。
- `link_intake_passed`：`True`。
- `link_download_default_no_contact`：`True`。
- `upload_channels_audited`：`True`。
- `action_packet_passed`：`True`。
- `secret_scan_clean`：`True`。

## Blocking

- 字段 `Checkpoint Link` 仍未就绪：需要用户授权上传后填入真实可访问 HTTPS 链接；当前不打印链接明文。
- 字段 `RoboChallenge User Token` 仍未就绪：只能写入本地 env 或 shell，不能写入 tracked 文件。
- 字段 `RoboChallenge Submission ID` 仍未就绪：必须来自 RoboChallenge 页面，不能伪造。
