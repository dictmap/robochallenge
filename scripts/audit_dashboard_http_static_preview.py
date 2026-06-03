#!/usr/bin/env python3
"""Audit local HTTP access for the static GUI dashboard without platform contact."""

from __future__ import annotations

import argparse
from functools import partial
import html
import http.server
import json
from pathlib import Path
import re
import socket
import sys
import threading
from typing import Any
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
DEFAULT_STATUS = RUNS_DIR / "dashboard_http_static_preview.json"
DEFAULT_REPORT = REPORTS_DIR / "dashboard_http_static_preview.md"
GUI_HTML = REPORTS_DIR / "submission_status_dashboard.html"
GUI_HTML_NAME = "submission_status_dashboard.html"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="审计 GUI dashboard 是否可经 127.0.0.1 HTTP 静态服务打开；不联网、不上传、不读取凭据。"
    )
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文报告输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def find_free_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def fetch_dashboard_over_http() -> dict[str, Any]:
    port = find_free_local_port()
    handler = partial(QuietHandler, directory=str(REPORTS_DIR))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{port}/{GUI_HTML_NAME}"
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "robochallenge-local-gui-audit"})
        with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310 - localhost only.
            body_bytes = response.read()
            content_type = response.headers.get("Content-Type", "")
            status_code = int(response.status)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    body = body_bytes.decode("utf-8", errors="replace")
    return {
        "url": url,
        "host": "127.0.0.1",
        "port": port,
        "status_code": status_code,
        "content_type": content_type,
        "body": body,
        "body_length": len(body),
    }


def extract_text_title(body: str) -> str:
    match = re.search(r"<h1>(.*?)</h1>", body, flags=re.S)
    if not match:
        return ""
    return html.unescape(re.sub(r"<.*?>", "", match.group(1)).strip())


def hrefs(body: str) -> list[str]:
    return re.findall(r'href="([^"]+)"', body)


def build_status() -> dict[str, Any]:
    dashboard = read_json(RUNS_DIR / "submission_status_dashboard.json")
    secret_scan = read_json(RUNS_DIR / "plaintext_secret_scan.json")
    fetched = fetch_dashboard_over_http()
    body = fetched["body"]
    extracted_hrefs = hrefs(body)
    external_hrefs = [
        item for item in extracted_hrefs if item.startswith(("http://", "https://", "//"))
    ]
    card_count = body.count('<article class="card ')
    done_count = body.count('<article class="card done">')
    blocked_count = body.count('<article class="card blocked">')
    watch_count = body.count('<article class="card watch">')
    h1_text = extract_text_title(body)
    evidence = {
        "dashboard_json_passed": dashboard.get("passed") is True,
        "dashboard_html_exists": GUI_HTML.exists() and GUI_HTML.is_file(),
        "http_host_loopback": fetched["host"] == "127.0.0.1",
        "http_status_200": fetched["status_code"] == 200,
        "http_content_type_html": "text/html" in fetched["content_type"],
        "http_body_nonempty": fetched["body_length"] > 1000,
        "http_h1_matches": h1_text == "RoboChallenge pi0.5 提交状态面板",
        "http_lang_zh_cn": '<html lang="zh-CN">' in body,
        "http_card_count_matches_dashboard": card_count == dashboard.get("card_count"),
        "http_done_count_matches_dashboard": done_count == dashboard.get("done_count"),
        "http_blocked_count_matches_dashboard": blocked_count == dashboard.get("blocked_count"),
        "http_watch_count_matches_dashboard": watch_count == dashboard.get("watch_count"),
        "http_ready_false_visible": "真实提交就绪" in body and "否" in body,
        "http_no_external_hrefs": not external_hrefs,
        "secret_scan_clean": secret_scan.get("passed") is True and secret_scan.get("hit_count") == 0,
    }
    leak_flags = {
        "credentials_printed": bool(dashboard.get("credentials_printed")) or bool(secret_scan.get("credentials_printed")),
        "link_values_printed": bool(dashboard.get("link_values_printed")) or bool(secret_scan.get("link_values_printed")),
        "secret_values_printed": bool(dashboard.get("secret_values_printed")) or bool(secret_scan.get("secret_values_printed")),
    }
    contact_flags = {
        "platform_contacted": False,
        "uploads_performed": False,
        "download_host_contacted": False,
        "external_network_contacted": False,
    }
    blocking = []
    for key, ok in evidence.items():
        if not ok:
            blocking.append(f"HTTP GUI 静态预览证据未通过 `{key}`。")
    if any(leak_flags.values()):
        blocking.append("HTTP GUI 静态预览存在凭据、链接或 secret 明文泄漏风险。")
    if any(contact_flags.values()):
        blocking.append("HTTP GUI 静态预览不应连接外部网络、上传或接触下载 host。")
    if not blocking:
        blocking.append("HTTP GUI 静态预览已通过；dashboard 可经 127.0.0.1 临时服务打开。")

    passed = bool(all(evidence.values()) and not any(leak_flags.values()) and not any(contact_flags.values()))
    return {
        "kind": "dashboard_http_static_preview",
        "passed": passed,
        "gui_html_path": "reports/submission_status_dashboard.html",
        "http_preview_url_shape": "http://127.0.0.1:<ephemeral>/submission_status_dashboard.html",
        "http_preview_host": fetched["host"],
        "http_preview_port": fetched["port"],
        "http_status_code": fetched["status_code"],
        "http_content_type": fetched["content_type"],
        "http_body_length": fetched["body_length"],
        "http_h1_text": h1_text,
        "http_card_count": card_count,
        "http_done_count": done_count,
        "http_blocked_count": blocked_count,
        "http_watch_count": watch_count,
        "dashboard_card_count": dashboard.get("card_count"),
        "dashboard_done_count": dashboard.get("done_count"),
        "dashboard_blocked_count": dashboard.get("blocked_count"),
        "dashboard_watch_count": dashboard.get("watch_count"),
        "external_href_count": len(external_hrefs),
        "external_hrefs": external_hrefs,
        "screenshot_created": False,
        "screenshot_boundary": "本审计验证 HTTP/HTML 可访问性；截图由 Browser 工具另行尝试，失败时不伪造截图。",
        "evidence": evidence,
        "leak_flags": leak_flags,
        "contact_flags": contact_flags,
        "platform_contacted": False,
        "uploads_performed": False,
        "credentials_read": False,
        "credentials_printed": False,
        "link_values_printed": False,
        "secret_values_printed": False,
        "blocking": blocking,
    }


def write_report(status: dict[str, Any], path: Path) -> None:
    lines = [
        "# GUI dashboard HTTP 静态预览审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- HTML 路径：`{status['gui_html_path']}`。",
        f"- HTTP 预览地址形状：`{status['http_preview_url_shape']}`。",
        f"- HTTP 状态码：`{status['http_status_code']}`。",
        f"- Content-Type：`{status['http_content_type']}`。",
        f"- H1：`{status['http_h1_text']}`。",
        f"- HTTP 卡片数量：`{status['http_card_count']}`。",
        f"- HTTP 已完成/待授权/关注：`{status['http_done_count']} / {status['http_blocked_count']} / {status['http_watch_count']}`。",
        f"- dashboard JSON 卡片数量：`{status['dashboard_card_count']}`。",
        f"- 外部链接数量：`{status['external_href_count']}`。",
        f"- 是否生成截图：`{status['screenshot_created']}`。",
        "",
        "## 可复用打开方式",
        "",
        "在仓库根目录运行：",
        "",
        "```bash",
        "python3 -m http.server 18085 --bind 127.0.0.1 --directory reports",
        "```",
        "",
        "然后打开：",
        "",
        "```text",
        "http://127.0.0.1:18085/submission_status_dashboard.html",
        "```",
        "",
        "## 边界",
        "",
        "- 本审计只启动本机 loopback 临时 HTTP 服务。",
        "- 不读取真实 token/submission id/local env 内容。",
        "- 不连接 RoboChallenge 平台、不上传、不下载 checkpoint。",
        f"- 截图边界：{status['screenshot_boundary']}",
        "",
        "## 证据",
        "",
    ]
    for key, ok in status["evidence"].items():
        lines.append(f"- `{key}`：`{ok}`。")
    lines.extend(["", "## Blocking", ""])
    for item in status["blocking"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args()
    status = build_status()
    args.status_path.parent.mkdir(parents=True, exist_ok=True)
    args.status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(status, args.report_path)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
