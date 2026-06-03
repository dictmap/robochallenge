#!/usr/bin/env python3
"""Render a no-contact packet for opening the static GUI dashboard."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
DEFAULT_STATUS = RUNS_DIR / "dashboard_gui_access_packet.json"
DEFAULT_REPORT = REPORTS_DIR / "dashboard_gui_access_packet.md"
GUI_HTML = REPORTS_DIR / "submission_status_dashboard.html"
GUI_HTML_REL = "reports/submission_status_dashboard.html"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="生成 GUI dashboard 展示入口证据；不绕过浏览器 file URL 策略，不联网、不上传。"
    )
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文报告输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_status() -> dict[str, Any]:
    dashboard = read_json(RUNS_DIR / "submission_status_dashboard.json")
    dashboard_links = read_json(RUNS_DIR / "submission_dashboard_links_audit.json")
    http_preview = read_json(RUNS_DIR / "dashboard_http_static_preview.json")
    secret_scan = read_json(RUNS_DIR / "plaintext_secret_scan.json")
    html_exists = GUI_HTML.exists() and GUI_HTML.is_file()
    html_text = GUI_HTML.read_text(encoding="utf-8") if html_exists else ""
    evidence = {
        "dashboard_status_passed": dashboard.get("passed") is True,
        "dashboard_html_path_exact": dashboard.get("html_path") == GUI_HTML_REL,
        "dashboard_html_exists": html_exists,
        "dashboard_html_zh_cn": '<html lang="zh-CN">' in html_text,
        "dashboard_title_present": "RoboChallenge pi0.5 提交状态面板" in html_text,
        "dashboard_card_count_current": dashboard.get("card_count", 0) >= 39,
        "dashboard_source_count_current": dashboard.get("source_count", 0) >= 39,
        "dashboard_ready_for_real_submission_false": dashboard.get("ready_for_real_submission") is False,
        "dashboard_links_passed": dashboard_links.get("passed") is True,
        "dashboard_links_all_reports_exist": dashboard_links.get("missing_report_count") == 0,
        "dashboard_links_all_href_rendered": dashboard_links.get("missing_html_href_count") == 0,
        "dashboard_links_no_duplicate_titles": dashboard_links.get("duplicate_title_count") == 0,
        "http_static_preview_passed": http_preview.get("passed") is True,
        "http_static_preview_loopback": http_preview.get("http_preview_host") == "127.0.0.1",
        "http_static_preview_card_count_matches": http_preview.get("evidence", {}).get(
            "http_card_count_matches_dashboard"
        )
        is True,
        "http_static_preview_no_external_hrefs": http_preview.get("external_href_count") == 0,
        "secret_scan_clean": secret_scan.get("passed") is True and secret_scan.get("hit_count") == 0,
    }
    leak_flags = {
        "credentials_printed": any(
            bool(item.get("credentials_printed")) for item in [dashboard, dashboard_links, http_preview, secret_scan]
        ),
        "link_values_printed": any(
            bool(item.get("link_values_printed")) for item in [dashboard, dashboard_links, http_preview, secret_scan]
        ),
        "secret_values_printed": any(
            bool(item.get("secret_values_printed")) for item in [dashboard, dashboard_links, http_preview, secret_scan]
        ),
    }
    contact_flags = {
        "platform_contacted": any(bool(item.get("platform_contacted")) for item in [dashboard, dashboard_links, http_preview]),
        "uploads_performed": any(bool(item.get("uploads_performed")) for item in [dashboard, dashboard_links, http_preview]),
        "download_host_contacted": any(
            bool(item.get("contact_flags", {}).get("download_host_contacted"))
            for item in [dashboard, dashboard_links, http_preview]
        ),
        "external_network_contacted": bool(http_preview.get("contact_flags", {}).get("external_network_contacted")),
    }
    blocking = []
    for name, ok in evidence.items():
        if not ok:
            blocking.append(f"GUI 展示入口证据未通过 `{name}`。")
    if any(leak_flags.values()):
        blocking.append("GUI 展示入口证据存在凭据、链接或 secret 明文泄漏风险。")
    if any(contact_flags.values()):
        blocking.append("GUI 展示入口证据显示曾连接平台、上传或接触下载 host。")
    if not blocking:
        blocking.append(
            "GUI HTML 展示入口已固化，且 HTTP loopback 静态预览已通过；Browser 截图接口本轮仍未生成截图。"
        )

    passed = bool(all(evidence.values()) and not any(leak_flags.values()) and not any(contact_flags.values()))
    return {
        "kind": "dashboard_gui_access_packet",
        "passed": passed,
        "gui_html_path": GUI_HTML_REL,
        "gui_html_absolute_path": str(GUI_HTML),
        "dashboard_card_count": dashboard.get("card_count"),
        "dashboard_source_count": dashboard.get("source_count"),
        "dashboard_done_count": dashboard.get("done_count"),
        "dashboard_blocked_count": dashboard.get("blocked_count"),
        "dashboard_watch_count": dashboard.get("watch_count"),
        "ready_for_real_submission": dashboard.get("ready_for_real_submission"),
        "browser_visual_attempted": True,
        "browser_visual_blocked_by_policy": True,
        "browser_visual_policy_boundary": "in-app browser blocked local file URL preview; this packet does not bypass it",
        "http_static_preview_passed": http_preview.get("passed") is True,
        "http_static_preview_url_shape": http_preview.get("http_preview_url_shape", ""),
        "http_static_preview_card_count": http_preview.get("http_card_count"),
        "http_static_preview_done_count": http_preview.get("http_done_count"),
        "http_static_preview_blocked_count": http_preview.get("http_blocked_count"),
        "http_static_preview_watch_count": http_preview.get("http_watch_count"),
        "http_static_preview_external_href_count": http_preview.get("external_href_count"),
        "screenshot_created": False,
        "screenshot_path": "",
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
        "# GUI dashboard 展示入口",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- HTML 路径：`{status['gui_html_path']}`。",
        f"- 本机绝对路径：`{status['gui_html_absolute_path']}`。",
        f"- 卡片数量：`{status['dashboard_card_count']}`。",
        f"- 来源数量：`{status['dashboard_source_count']}`。",
        f"- 已完成/待授权/关注：`{status['dashboard_done_count']} / {status['dashboard_blocked_count']} / {status['dashboard_watch_count']}`。",
        f"- 是否已满足真实提交：`{status['ready_for_real_submission']}`。",
        f"- HTTP loopback 静态预览：`{status['http_static_preview_passed']}`。",
        f"- HTTP 预览地址形状：`{status['http_static_preview_url_shape']}`。",
        f"- HTTP 预览卡片数量：`{status['http_static_preview_card_count']}`。",
        f"- HTTP 外部链接数量：`{status['http_static_preview_external_href_count']}`。",
        "",
        "## 浏览器边界",
        "",
        f"- 本轮是否尝试 GUI 预览：`{status['browser_visual_attempted']}`。",
        f"- 是否被浏览器策略阻止：`{status['browser_visual_blocked_by_policy']}`。",
        f"- 是否生成截图：`{status['screenshot_created']}`。",
        f"- 边界说明：`{status['browser_visual_policy_boundary']}`。",
        "",
        "## HTTP 打开方式",
        "",
        "```bash",
        "python3 -m http.server 18085 --bind 127.0.0.1 --directory reports",
        "```",
        "",
        "```text",
        "http://127.0.0.1:18085/submission_status_dashboard.html",
        "```",
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
