# 关键交接报告一致性审计

## 结论

- 审计状态：`passed=True`。
- 检查报告数量：`10`。
- Markdown/JSON 状态不一致数量：`0`。
- 缺少审计状态行数量：`0`。
- 中文乱码哨兵命中数量：`0`。
- 明文凭据模式命中数量：`0`。

## 检查项

### baseline_submission_quickstart

- JSON：`runs/baseline_submission_quickstart.json`。
- 报告：`reports/baseline_submission_quickstart.md`。
- JSON passed：`True`。
- Markdown passed：`True`。
- 状态一致：`True`。
- 乱码哨兵命中：`0`。

### baseline_readonly_preflight_entry

- JSON：`runs/baseline_readonly_preflight_entry.json`。
- 报告：`reports/baseline_readonly_preflight_entry.md`。
- JSON passed：`True`。
- Markdown passed：`True`。
- 状态一致：`True`。
- 乱码哨兵命中：`0`。

### authorized_execution_checklist

- JSON：`runs/authorized_execution_checklist.json`。
- 报告：`reports/authorized_execution_checklist.md`。
- JSON passed：`True`。
- Markdown passed：`True`。
- 状态一致：`True`。
- 乱码哨兵命中：`0`。

### authorized_checkpoint_archive_template

- JSON：`runs/authorized_checkpoint_archive_template_audit.json`。
- 报告：`reports/authorized_checkpoint_archive_template_audit.md`。
- JSON passed：`True`。
- Markdown passed：`True`。
- 状态一致：`True`。
- 乱码哨兵命中：`0`。

### ready_real_runner_template

- JSON：`runs/ready_real_runner_template_audit.json`。
- 报告：`reports/ready_real_runner_template_audit.md`。
- JSON passed：`True`。
- Markdown passed：`True`。
- 状态一致：`True`。
- 乱码哨兵命中：`0`。

### notebook_dashboard_gui_section

- JSON：`runs/notebook_dashboard_gui_section_audit.json`。
- 报告：`reports/notebook_dashboard_gui_section_audit.md`。
- JSON passed：`True`。
- Markdown passed：`True`。
- 状态一致：`True`。
- 乱码哨兵命中：`0`。

### submission_preflight_bundle

- JSON：`runs/submission_preflight_bundle.json`。
- 报告：`reports/submission_preflight_bundle.md`。
- JSON passed：`True`。
- Markdown passed：`True`。
- 状态一致：`True`。
- 乱码哨兵命中：`0`。

### submission_artifact_manifest

- JSON：`runs/submission_artifact_manifest.json`。
- 报告：`reports/submission_artifact_manifest.md`。
- JSON passed：`True`。
- Markdown passed：`True`。
- 状态一致：`True`。
- 乱码哨兵命中：`0`。

### chinese_utf8_artifacts

- JSON：`runs/chinese_utf8_artifact_audit.json`。
- 报告：`reports/chinese_utf8_artifact_audit.md`。
- JSON passed：`True`。
- Markdown passed：`True`。
- 状态一致：`True`。
- 乱码哨兵命中：`0`。

### plaintext_secret_scan

- JSON：`runs/plaintext_secret_scan.json`。
- 报告：`reports/plaintext_secret_scan.md`。
- JSON passed：`True`。
- Markdown passed：`True`。
- 状态一致：`True`。
- 乱码哨兵命中：`0`。

## Blocking

- 关键交接 Markdown 报告与 JSON 状态一致，未发现本地镜像滞后迹象。
