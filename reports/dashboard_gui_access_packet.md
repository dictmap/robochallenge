# GUI dashboard 展示入口

## 结论

- 审计状态：`passed=True`。
- HTML 路径：`reports/submission_status_dashboard.html`。
- 本机绝对路径：`/home/yjl/robochallenge/repo/reports/submission_status_dashboard.html`。
- 卡片数量：`41`。
- 来源数量：`41`。
- 已完成/待授权/关注：`35 / 5 / 1`。
- 是否已满足真实提交：`False`。
- HTTP loopback 静态预览：`True`。
- HTTP 预览地址形状：`http://127.0.0.1:<ephemeral>/submission_status_dashboard.html`。
- HTTP 预览卡片数量：`41`。
- HTTP 外部链接数量：`0`。

## 浏览器边界

- 本轮是否尝试 GUI 预览：`True`。
- 是否被浏览器策略阻止：`True`。
- 是否生成截图：`False`。
- 边界说明：`in-app browser blocked local file URL preview; this packet does not bypass it`。

## HTTP 打开方式

```bash
python3 -m http.server 18085 --bind 127.0.0.1 --directory reports
```

```text
http://127.0.0.1:18085/submission_status_dashboard.html
```

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
- `http_static_preview_passed`：`True`。
- `http_static_preview_loopback`：`True`。
- `http_static_preview_card_count_matches`：`True`。
- `http_static_preview_no_external_hrefs`：`True`。
- `secret_scan_clean`：`True`。

## Blocking

- GUI HTML 展示入口已固化，且 HTTP loopback 静态预览已通过；Browser 截图接口本轮仍未生成截图。
