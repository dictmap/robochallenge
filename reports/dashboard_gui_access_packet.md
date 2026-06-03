# GUI dashboard 展示入口

## 结论

- 审计状态：`passed=True`。
- HTML 路径：`reports/submission_status_dashboard.html`。
- 本机绝对路径：`/home/yjl/robochallenge/repo/reports/submission_status_dashboard.html`。
- 卡片数量：`40`。
- 来源数量：`40`。
- 已完成/待授权/关注：`34 / 5 / 1`。
- 是否已满足真实提交：`False`。

## 浏览器边界

- 本轮是否尝试 GUI 预览：`True`。
- 是否被浏览器策略阻止：`True`。
- 是否生成截图：`False`。
- 边界说明：`in-app browser blocked local file URL preview; this packet does not bypass it`。

## 证据

- `dashboard_status_passed`：`True`。
- `dashboard_html_path_exact`：`True`。
- `dashboard_html_exists`：`True`。
- `dashboard_html_zh_cn`：`True`。
- `dashboard_title_present`：`True`。
- `dashboard_card_count_current`：`True`。
- `dashboard_source_count_current`：`True`。
- `dashboard_ready_for_real_submission_false`：`True`。
- `dashboard_links_passed`：`True`。
- `dashboard_links_all_reports_exist`：`True`。
- `dashboard_links_all_href_rendered`：`True`。
- `dashboard_links_no_duplicate_titles`：`True`。
- `secret_scan_clean`：`True`。

## Blocking

- GUI HTML 展示入口已固化；本轮 in-app browser 的 file URL 预览被工具策略阻止，未绕过该限制，也未生成截图。
