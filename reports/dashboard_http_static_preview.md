# GUI dashboard HTTP 静态预览审计

## 结论

- 审计状态：`passed=True`。
- HTML 路径：`reports/submission_status_dashboard.html`。
- HTTP 预览地址形状：`http://127.0.0.1:<ephemeral>/submission_status_dashboard.html`。
- HTTP 状态码：`200`。
- Content-Type：`text/html`。
- H1：`RoboChallenge pi0.5 提交状态面板`。
- HTTP 卡片数量：`41`。
- HTTP 已完成/待授权/关注：`35 / 5 / 1`。
- dashboard JSON 卡片数量：`41`。
- 外部链接数量：`0`。
- 是否生成截图：`False`。

## 可复用打开方式

在仓库根目录运行：

```bash
python3 -m http.server 18085 --bind 127.0.0.1 --directory reports
```

然后打开：

```text
http://127.0.0.1:18085/submission_status_dashboard.html
```

## 边界

- 本审计只启动本机 loopback 临时 HTTP 服务。
- 不读取真实 token/submission id/local env 内容。
- 不连接 RoboChallenge 平台、不上传、不下载 checkpoint。
- 截图边界：本审计验证 HTTP/HTML 可访问性；截图由 Browser 工具另行尝试，失败时不伪造截图。

## 证据

- `dashboard_json_passed`：`True`。
- `dashboard_html_exists`：`True`。
- `http_host_loopback`：`True`。
- `http_status_200`：`True`。
- `http_content_type_html`：`True`。
- `http_body_nonempty`：`True`。
- `http_h1_matches`：`True`。
- `http_lang_zh_cn`：`True`。
- `http_card_count_matches_dashboard`：`True`。
- `http_done_count_matches_dashboard`：`True`。
- `http_blocked_count_matches_dashboard`：`True`。
- `http_watch_count_matches_dashboard`：`True`。
- `http_ready_false_visible`：`True`。
- `http_no_external_hrefs`：`True`。
- `secret_scan_clean`：`True`。

## Blocking

- HTTP GUI 静态预览已通过；dashboard 可经 127.0.0.1 临时服务打开。
