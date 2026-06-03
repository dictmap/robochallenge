#!/usr/bin/env python3
"""Audit dashboard card counts and local report links without contacting services."""

from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = ROOT / "runs"
DEFAULT_STATUS = RUNS_DIR / "submission_dashboard_links_audit.json"
DEFAULT_REPORT = REPORTS_DIR / "submission_dashboard_links_audit.md"
DASHBOARD_STATUS = RUNS_DIR / "submission_status_dashboard.json"
DASHBOARD_HTML = REPORTS_DIR / "submission_status_dashboard.html"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计 GUI dashboard 卡片计数和本地报告链接。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文报告输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def is_local_report_path(value: str) -> bool:
    path = Path(value)
    return (
        bool(value)
        and value.startswith("reports/")
        and not path.is_absolute()
        and ".." not in path.parts
        and "://" not in value
    )


def build_status() -> dict[str, Any]:
    dashboard = read_json(DASHBOARD_STATUS)
    html = DASHBOARD_HTML.read_text(encoding="utf-8") if DASHBOARD_HTML.exists() else ""
    cards = dashboard.get("cards", [])
    if not isinstance(cards, list):
        cards = []

    missing_reports: list[str] = []
    nonlocal_reports: list[str] = []
    missing_html_hrefs: list[str] = []
    duplicate_titles: list[str] = []
    seen_titles: set[str] = set()
    for item in cards:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", ""))
        if title in seen_titles:
            duplicate_titles.append(title)
        seen_titles.add(title)
        report = str(item.get("report", ""))
        if not is_local_report_path(report):
            nonlocal_reports.append(report)
            continue
        if not (ROOT / report).exists():
            missing_reports.append(report)
        expected_href = f'href="../{escape(report)}"'
        if expected_href not in html:
            missing_html_hrefs.append(report)

    state_counts = {
        "done": sum(1 for item in cards if isinstance(item, dict) and item.get("state") == "done"),
        "blocked": sum(1 for item in cards if isinstance(item, dict) and item.get("state") == "blocked"),
        "watch": sum(1 for item in cards if isinstance(item, dict) and item.get("state") == "watch"),
    }
    evidence = {
        "dashboard_json_exists": DASHBOARD_STATUS.exists(),
        "dashboard_html_exists": DASHBOARD_HTML.exists(),
        "dashboard_passed": dashboard.get("passed") is True,
        "card_count_matches": dashboard.get("card_count") == len(cards),
        "done_count_matches": dashboard.get("done_count") == state_counts["done"],
        "blocked_count_matches": dashboard.get("blocked_count") == state_counts["blocked"],
        "watch_count_matches": dashboard.get("watch_count") == state_counts["watch"],
        "all_reports_local": not nonlocal_reports,
        "all_reports_exist": not missing_reports,
        "all_report_hrefs_rendered": not missing_html_hrefs,
        "no_duplicate_titles": not duplicate_titles,
        "html_declares_utf8": '<meta charset="utf-8"' in html,
        "html_is_chinese": 'lang="zh-CN"' in html,
        "html_has_no_external_links": "http://" not in html and "https://" not in html and "file://" not in html,
        "html_has_blocking_section": "当前阻塞" in html,
    }
    passed = bool(all(evidence.values()) and len(cards) >= 38)
    blocking: list[str] = []
    if passed:
        blocking.append("GUI dashboard 链接审计通过；所有卡片报告链接均为本地已存在文件。")
    else:
        for key, ok in evidence.items():
            if not ok:
                blocking.append(f"GUI dashboard 链接审计未通过 `{key}`。")
        if len(cards) < 38:
            blocking.append(f"GUI dashboard 卡片数量低于预期：`{len(cards)}`。")
    return {
        "kind": "submission_dashboard_links_audit",
        "passed": passed,
        "platform_contacted": False,
        "uploads_performed": False,
        "credentials_read": False,
        "credentials_printed": False,
        "link_values_printed": False,
        "secret_values_printed": False,
        "dashboard_status_path": DASHBOARD_STATUS.relative_to(ROOT).as_posix(),
        "dashboard_html_path": DASHBOARD_HTML.relative_to(ROOT).as_posix(),
        "card_count": len(cards),
        "source_count": dashboard.get("source_count"),
        "done_count": state_counts["done"],
        "blocked_count": state_counts["blocked"],
        "watch_count": state_counts["watch"],
        "ready_for_real_submission": dashboard.get("ready_for_real_submission"),
        "missing_report_count": len(missing_reports),
        "nonlocal_report_count": len(nonlocal_reports),
        "missing_html_href_count": len(missing_html_hrefs),
        "duplicate_title_count": len(duplicate_titles),
        "missing_reports": missing_reports,
        "nonlocal_reports": nonlocal_reports,
        "missing_html_hrefs": missing_html_hrefs,
        "duplicate_titles": duplicate_titles,
        "evidence": evidence,
        "blocking": blocking,
    }


def write_report(status: dict[str, Any], path: Path) -> None:
    lines = [
        "# GUI dashboard 链接审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- Dashboard JSON：`{status['dashboard_status_path']}`。",
        f"- Dashboard HTML：`{status['dashboard_html_path']}`。",
        f"- 卡片数量：`{status['card_count']}`。",
        f"- 已完成 / 阻塞 / 关注：`{status['done_count']}` / `{status['blocked_count']}` / `{status['watch_count']}`。",
        f"- 真实提交就绪：`{status['ready_for_real_submission']}`。",
        f"- 缺失报告链接数：`{status['missing_report_count']}`。",
        f"- 非本地报告链接数：`{status['nonlocal_report_count']}`。",
        f"- HTML 未渲染 href 数：`{status['missing_html_href_count']}`。",
        f"- 重复标题数：`{status['duplicate_title_count']}`。",
        "",
        "## 证据",
        "",
    ]
    for key, value in status["evidence"].items():
        lines.append(f"- `{key}`：`{value}`。")
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
