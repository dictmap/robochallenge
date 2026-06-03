#!/usr/bin/env python3
"""Audit that the GUI dashboard screenshot covers the current dashboard evidence."""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
DEFAULT_STATUS = RUNS_DIR / "dashboard_screenshot_coverage_audit.json"
DEFAULT_REPORT = REPORTS_DIR / "dashboard_screenshot_coverage_audit.md"
DASHBOARD_STATUS = RUNS_DIR / "submission_status_dashboard.json"
GUI_PACKET_STATUS = RUNS_DIR / "dashboard_gui_access_packet.json"
GUI_HTML = REPORTS_DIR / "submission_status_dashboard.html"
SCREENSHOT = REPORTS_DIR / "submission_status_dashboard_browser.png"
SCREENSHOT_REL = "reports/submission_status_dashboard_browser.png"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

REQUIRED_HTML_PHRASES = [
    "RoboChallenge pi0.5 提交状态面板",
    "pi0.5 ALOHA 离线执行",
    "inference=162",
    "交接报告一致性",
    "mismatch=0",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="审计 GUI dashboard 截图覆盖范围；不联网、不上传、不读取凭据。"
    )
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文审计报告输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def parse_png(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        return {
            "exists": False,
            "size_bytes": 0,
            "signature_ok": False,
            "ihdr_ok": False,
            "width": 0,
            "height": 0,
        }
    data = path.read_bytes()
    signature_ok = data.startswith(PNG_SIGNATURE)
    ihdr_ok = len(data) >= 24 and data[12:16] == b"IHDR"
    width = 0
    height = 0
    if signature_ok and ihdr_ok:
        width, height = struct.unpack(">II", data[16:24])
    return {
        "exists": True,
        "size_bytes": len(data),
        "signature_ok": signature_ok,
        "ihdr_ok": ihdr_ok,
        "width": width,
        "height": height,
    }


def build_status() -> dict[str, Any]:
    dashboard = read_json(DASHBOARD_STATUS)
    gui_packet = read_json(GUI_PACKET_STATUS)
    html_exists = GUI_HTML.exists() and GUI_HTML.is_file()
    html_text = GUI_HTML.read_text(encoding="utf-8") if html_exists else ""
    png = parse_png(SCREENSHOT)
    phrase_hits = {phrase: phrase in html_text for phrase in REQUIRED_HTML_PHRASES}

    evidence = {
        "dashboard_status_passed": dashboard.get("passed") is True,
        "dashboard_card_count_current": dashboard.get("card_count") == 42,
        "dashboard_source_count_current": dashboard.get("source_count") == 42,
        "dashboard_ready_for_real_submission_false": dashboard.get("ready_for_real_submission") is False,
        "dashboard_key_handoff_consistency_passed": dashboard.get("key_handoff_report_consistency_passed") is True,
        "dashboard_key_handoff_mismatch_zero": dashboard.get("key_handoff_report_consistency_mismatch_count") == 0,
        "gui_packet_passed": gui_packet.get("passed") is True,
        "gui_packet_screenshot_created": gui_packet.get("screenshot_created") is True,
        "gui_packet_screenshot_path_exact": gui_packet.get("screenshot_path") == SCREENSHOT_REL,
        "gui_packet_screenshot_size_matches_file": gui_packet.get("screenshot_size_bytes") == png["size_bytes"],
        "html_exists": html_exists,
        "html_required_phrases_present": all(phrase_hits.values()),
        "html_key_handoff_card_present": phrase_hits["交接报告一致性"] and phrase_hits["mismatch=0"],
        "png_exists": png["exists"],
        "png_signature_ok": png["signature_ok"],
        "png_ihdr_ok": png["ihdr_ok"],
        "png_width_expected": png["width"] >= 1400,
        "png_height_expected_full_page": png["height"] >= 5000,
        "png_size_expected_full_page": png["size_bytes"] >= 100_000,
    }
    leak_flags = {
        "credentials_printed": any(bool(item.get("credentials_printed")) for item in [dashboard, gui_packet]),
        "link_values_printed": any(bool(item.get("link_values_printed")) for item in [dashboard, gui_packet]),
        "secret_values_printed": any(bool(item.get("secret_values_printed")) for item in [dashboard, gui_packet]),
    }
    contact_flags = {
        "platform_contacted": any(bool(item.get("platform_contacted")) for item in [dashboard, gui_packet]),
        "uploads_performed": any(bool(item.get("uploads_performed")) for item in [dashboard, gui_packet]),
        "download_host_contacted": any(
            bool(item.get("contact_flags", {}).get("download_host_contacted")) for item in [dashboard, gui_packet]
        ),
        "external_network_contacted": any(
            bool(item.get("contact_flags", {}).get("external_network_contacted")) for item in [dashboard, gui_packet]
        ),
    }

    blocking = []
    for name, ok in evidence.items():
        if not ok:
            blocking.append(f"GUI 截图覆盖审计未通过 `{name}`。")
    if any(leak_flags.values()):
        blocking.append("GUI 截图覆盖审计发现凭据、链接或 secret 明文泄漏风险。")
    if any(contact_flags.values()):
        blocking.append("GUI 截图覆盖审计发现平台连接、上传或外部下载 host 接触风险。")
    if not blocking:
        blocking.append("GUI 截图为当前 42 卡 dashboard 的整页 PNG，且 HTML 覆盖关键交接一致性卡片。")

    passed = bool(all(evidence.values()) and not any(leak_flags.values()) and not any(contact_flags.values()))
    return {
        "kind": "dashboard_screenshot_coverage_audit",
        "passed": passed,
        "screenshot_path": SCREENSHOT_REL,
        "screenshot_size_bytes": png["size_bytes"],
        "screenshot_width": png["width"],
        "screenshot_height": png["height"],
        "dashboard_card_count": dashboard.get("card_count"),
        "dashboard_source_count": dashboard.get("source_count"),
        "required_html_phrase_count": len(REQUIRED_HTML_PHRASES),
        "required_html_phrase_hits": phrase_hits,
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
        "# GUI dashboard 截图覆盖审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 截图路径：`{status['screenshot_path']}`。",
        f"- 截图大小：`{status['screenshot_size_bytes']}` bytes。",
        f"- 截图尺寸：`{status['screenshot_width']} x {status['screenshot_height']}`。",
        f"- dashboard 卡片数：`{status['dashboard_card_count']}`。",
        f"- dashboard 来源数：`{status['dashboard_source_count']}`。",
        f"- HTML 必需短语数量：`{status['required_html_phrase_count']}`。",
        "",
        "## HTML 覆盖",
        "",
    ]
    for phrase, ok in status["required_html_phrase_hits"].items():
        lines.append(f"- `{phrase}`：`{ok}`。")
    lines.extend(["", "## 证据", ""])
    for key, ok in status["evidence"].items():
        lines.append(f"- `{key}`：`{ok}`。")
    lines.extend(
        [
            "",
            "## 边界",
            "",
            "- 本审计只读取本地 dashboard JSON、HTML 和 PNG 文件。",
            "- 本审计不连接 RoboChallenge 平台、不上传 checkpoint、不启动真实 runner、不读取真实 token 或 local env 内容。",
            "",
            "## Blocking",
            "",
        ]
    )
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
