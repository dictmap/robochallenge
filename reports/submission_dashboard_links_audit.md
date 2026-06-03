# GUI dashboard 链接审计

## 结论

- 审计状态：`passed=True`。
- Dashboard JSON：`runs/submission_status_dashboard.json`。
- Dashboard HTML：`reports/submission_status_dashboard.html`。
- 卡片数量：`42`。
- 已完成 / 阻塞 / 关注：`36` / `5` / `1`。
- 真实提交就绪：`False`。
- 缺失报告链接数：`0`。
- 非本地报告链接数：`0`。
- HTML 未渲染 href 数：`0`。
- 重复标题数：`0`。

## 证据

- `dashboard_json_exists`：`True`。
- `dashboard_html_exists`：`True`。
- `dashboard_passed`：`True`。
- `card_count_matches`：`True`。
- `done_count_matches`：`True`。
- `blocked_count_matches`：`True`。
- `watch_count_matches`：`True`。
- `all_reports_local`：`True`。
- `all_reports_exist`：`True`。
- `all_report_hrefs_rendered`：`True`。
- `no_duplicate_titles`：`True`。
- `html_declares_utf8`：`True`。
- `html_is_chinese`：`True`。
- `html_has_no_external_links`：`True`。
- `html_has_blocking_section`：`True`。

## Blocking

- GUI dashboard 链接审计通过；所有卡片报告链接均为本地已存在文件。
