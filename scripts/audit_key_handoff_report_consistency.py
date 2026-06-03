#!/usr/bin/env python3
"""Audit that key handoff Markdown reports agree with their JSON status."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
DEFAULT_STATUS = RUNS_DIR / "key_handoff_report_consistency.json"
DEFAULT_REPORT = REPORTS_DIR / "key_handoff_report_consistency.md"

REPORT_PAIRS = [
    (
        "baseline_submission_quickstart",
        "runs/baseline_submission_quickstart.json",
        "reports/baseline_submission_quickstart.md",
    ),
    (
        "baseline_readonly_preflight_entry",
        "runs/baseline_readonly_preflight_entry.json",
        "reports/baseline_readonly_preflight_entry.md",
    ),
    (
        "authorized_execution_checklist",
        "runs/authorized_execution_checklist.json",
        "reports/authorized_execution_checklist.md",
    ),
    (
        "authorized_checkpoint_archive_template",
        "runs/authorized_checkpoint_archive_template_audit.json",
        "reports/authorized_checkpoint_archive_template_audit.md",
    ),
    (
        "ready_real_runner_template",
        "runs/ready_real_runner_template_audit.json",
        "reports/ready_real_runner_template_audit.md",
    ),
    (
        "notebook_dashboard_gui_section",
        "runs/notebook_dashboard_gui_section_audit.json",
        "reports/notebook_dashboard_gui_section_audit.md",
    ),
    (
        "submission_preflight_bundle",
        "runs/submission_preflight_bundle.json",
        "reports/submission_preflight_bundle.md",
    ),
    (
        "submission_artifact_manifest",
        "runs/submission_artifact_manifest.json",
        "reports/submission_artifact_manifest.md",
    ),
    (
        "chinese_utf8_artifacts",
        "runs/chinese_utf8_artifact_audit.json",
        "reports/chinese_utf8_artifact_audit.md",
    ),
    (
        "plaintext_secret_scan",
        "runs/plaintext_secret_scan.json",
        "reports/plaintext_secret_scan.md",
    ),
]

STATUS_LINE_RE = re.compile(r"审计状态：`passed=(True|False)`")
BAD_MARKERS = ("???", "�", "\ufffd")
SECRET_PATTERNS = {
    "huggingface_token": re.compile(r"hf_[A-Za-z0-9]{20,}"),
    "github_token": re.compile(r"ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{20,}"),
    "robochallenge_token_assignment": re.compile(
        r"(?:export\s+)?ROBOCHALLENGE_(?:USER_)?TOKEN\s*=\s*[A-Za-z0-9][A-Za-z0-9_-]{19,}"
    ),
    "submission_id_assignment": re.compile(r"ROBOCHALLENGE_SUBMISSION_ID\s*=\s*[A-Za-z0-9_-]{8,}"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计关键交接 Markdown 报告与 JSON 状态是否一致。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文审计报告输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def extract_markdown_passed(text: str) -> bool | None:
    match = STATUS_LINE_RE.search(text)
    if not match:
        return None
    return match.group(1) == "True"


def scan_secret_patterns(text: str) -> list[str]:
    return [name for name, pattern in SECRET_PATTERNS.items() if pattern.search(text)]


def build_status() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    blocking: list[str] = []
    secret_hits: list[dict[str, str]] = []

    for name, json_rel, md_rel in REPORT_PAIRS:
        json_path = ROOT / json_rel
        md_path = ROOT / md_rel
        json_data = read_json(json_path)
        md_text = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
        json_passed = json_data.get("passed")
        md_passed = extract_markdown_passed(md_text)
        md_has_status_line = md_passed is not None
        status_matches = md_has_status_line and md_passed is json_passed
        bad_marker_count = sum(md_text.count(marker) for marker in BAD_MARKERS)
        report_secret_hits = scan_secret_patterns(md_text)
        if report_secret_hits:
            for hit in report_secret_hits:
                secret_hits.append({"report": md_rel, "pattern": hit})
        check = {
            "name": name,
            "json_path": json_rel,
            "report_path": md_rel,
            "json_exists": json_path.exists(),
            "report_exists": md_path.exists(),
            "json_passed": json_passed,
            "markdown_passed": md_passed,
            "markdown_has_status_line": md_has_status_line,
            "status_matches": status_matches,
            "bad_marker_count": bad_marker_count,
            "secret_pattern_hits": report_secret_hits,
        }
        checks.append(check)
        if not json_path.exists():
            blocking.append(f"{json_rel} 不存在。")
        if not md_path.exists():
            blocking.append(f"{md_rel} 不存在。")
        if not md_has_status_line:
            blocking.append(f"{md_rel} 缺少审计状态行。")
        if md_has_status_line and not status_matches:
            blocking.append(
                f"{md_rel} 的 Markdown 状态 `{md_passed}` 与 {json_rel} 的 JSON 状态 `{json_passed}` 不一致。"
            )
        if bad_marker_count:
            blocking.append(f"{md_rel} 命中乱码哨兵 {bad_marker_count} 次。")
        if report_secret_hits:
            blocking.append(f"{md_rel} 疑似包含明文凭据模式。")

    if not blocking:
        blocking.append("关键交接 Markdown 报告与 JSON 状态一致，未发现本地镜像滞后迹象。")

    passed = all(
        [
            all(item["json_exists"] and item["report_exists"] for item in checks),
            all(item["markdown_has_status_line"] for item in checks),
            all(item["status_matches"] for item in checks),
            all(item["bad_marker_count"] == 0 for item in checks),
            not secret_hits,
        ]
    )
    return {
        "kind": "key_handoff_report_consistency",
        "passed": passed,
        "platform_contacted": False,
        "uploads_performed": False,
        "credentials_read": False,
        "credentials_printed": False,
        "link_values_printed": False,
        "secret_values_printed": False,
        "checked_report_count": len(REPORT_PAIRS),
        "mismatch_count": sum(not item["status_matches"] for item in checks),
        "missing_status_line_count": sum(not item["markdown_has_status_line"] for item in checks),
        "bad_marker_hit_count": sum(int(item["bad_marker_count"]) for item in checks),
        "secret_pattern_hit_count": len(secret_hits),
        "checks": checks,
        "secret_pattern_hits": secret_hits,
        "blocking": blocking,
    }


def write_report(status: dict[str, Any], path: Path) -> None:
    lines = [
        "# 关键交接报告一致性审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 检查报告数量：`{status['checked_report_count']}`。",
        f"- Markdown/JSON 状态不一致数量：`{status['mismatch_count']}`。",
        f"- 缺少审计状态行数量：`{status['missing_status_line_count']}`。",
        f"- 中文乱码哨兵命中数量：`{status['bad_marker_hit_count']}`。",
        f"- 明文凭据模式命中数量：`{status['secret_pattern_hit_count']}`。",
        "",
        "## 检查项",
        "",
    ]
    for item in status["checks"]:
        lines.extend(
            [
                f"### {item['name']}",
                "",
                f"- JSON：`{item['json_path']}`。",
                f"- 报告：`{item['report_path']}`。",
                f"- JSON passed：`{item['json_passed']}`。",
                f"- Markdown passed：`{item['markdown_passed']}`。",
                f"- 状态一致：`{item['status_matches']}`。",
                f"- 乱码哨兵命中：`{item['bad_marker_count']}`。",
                "",
            ]
        )
    lines.extend(["## Blocking", ""])
    for item in status["blocking"]:
        lines.append(f"- {item}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    status = build_status()
    args.status_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    args.status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(status, args.report_path)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
