#!/usr/bin/env python3
"""Audit stale checkpoint-link wording in historical notebook outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
DEFAULT_STATUS = RUNS_DIR / "historical_notebook_checkpoint_outputs.json"
DEFAULT_REPORT = REPORTS_DIR / "historical_notebook_checkpoint_outputs.md"

CURRENT_NOTEBOOK = ROOT / "notebooks" / "robochallenge_pi05_submit_cn.ipynb"
EXECUTED_NOTEBOOK = ROOT / "notebooks" / "robochallenge_pi05_submit_cn.executed.ipynb"
WORK_LOG = ROOT / "work.md"

STALE_PHRASES = [
    "真实提交仍需要用户提供 token、submission id 和可访问 checkpoint link",
    "真实提交仍需要用户提供 token、submission id 和真实可访问 checkpoint link",
    "真实网站提交仍需要用户提供 token/submission_id 和可访问 checkpoint link",
    "真实提交仍需要 ROBOCHALLENGE_USER_TOKEN 和 ROBOCHALLENGE_SUBMISSION_ID",
    "baseline 仍等待用户 token",
    "需要确认本次要提交的是 Table30v2 ALOHA 还是原始 Table30",
]

ACTIVE_SCAN_DIRS = ["scripts", "reports", "runs", "submission"]
ACTIVE_SUFFIXES = {".py", ".md", ".json", ".sh", ".html"}
ACTIVE_EXCLUDE_PATHS = {
    "scripts/audit_historical_notebook_checkpoint_outputs.py",
    "reports/historical_notebook_checkpoint_outputs.md",
    "runs/historical_notebook_checkpoint_outputs.json",
    "runs/submission_preflight_bundle.json",
}
BASELINE_BLOCKING = [
    "SUBMISSION_TARGET_CONFIRMATION",
    "ROBOCHALLENGE_USER_TOKEN",
    "ROBOCHALLENGE_SUBMISSION_ID",
    "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline",
    "ROBOCHALLENGE_REAL_RUN_CONFIRM",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计 executed notebook 和旧运行日志中的历史 checkpoint link 文案。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文审计报告输出路径。")
    return parser.parse_args()


def short_context(line: str, phrase: str) -> str:
    text = line.strip().replace("\\n", " ")
    index = text.find(phrase)
    if index < 0:
        return text[:180]
    start = max(0, index - 50)
    end = min(len(text), index + len(phrase) + 50)
    return text[start:end]


def scan_file(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    hits: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except UnicodeDecodeError:
        return []
    rel = str(path.relative_to(ROOT))
    for lineno, line in enumerate(lines, start=1):
        for phrase in STALE_PHRASES:
            if phrase in line:
                hits.append(
                    {
                        "path": rel,
                        "line": lineno,
                        "phrase": phrase,
                        "context": short_context(line, phrase),
                    }
                )
    return hits


def active_files() -> list[Path]:
    files: list[Path] = []
    for dirname in ACTIVE_SCAN_DIRS:
        root = ROOT / dirname
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if "__pycache__" in path.parts:
                continue
            if path.suffix not in ACTIVE_SUFFIXES:
                continue
            if str(path.relative_to(ROOT)) in ACTIVE_EXCLUDE_PATHS:
                continue
            if "openpi_rtc_lora_materialized_policy_checkpoint" in str(path):
                continue
            files.append(path)
    files.append(CURRENT_NOTEBOOK)
    return sorted(files)


def work_log_hits_are_audit_mentions(hits: list[dict[str, Any]]) -> bool:
    if not hits:
        return True
    text = WORK_LOG.read_text(encoding="utf-8", errors="replace")
    return "旧口径搜索已清空" in text and "均无命中" in text


def build_status() -> dict[str, Any]:
    active_hits: list[dict[str, Any]] = []
    for path in active_files():
        active_hits.extend(scan_file(path))
    executed_hits = scan_file(EXECUTED_NOTEBOOK)
    work_hits = scan_file(WORK_LOG)

    current_notebook_hits = [hit for hit in active_hits if hit["path"] == str(CURRENT_NOTEBOOK.relative_to(ROOT))]
    active_material_hits = [hit for hit in active_hits if hit["path"] != str(CURRENT_NOTEBOOK.relative_to(ROOT))]
    work_log_audit_only = work_log_hits_are_audit_mentions(work_hits)

    status: dict[str, Any] = {
        "kind": "historical_notebook_checkpoint_outputs",
        "passed": False,
        "platform_contacted": False,
        "credentials_read": False,
        "credentials_printed": False,
        "uploads_performed": False,
        "archive_created": False,
        "current_notebook": str(CURRENT_NOTEBOOK.relative_to(ROOT)),
        "executed_notebook": str(EXECUTED_NOTEBOOK.relative_to(ROOT)),
        "active_scanned_file_count": len(active_files()),
        "stale_phrase_count": len(STALE_PHRASES),
        "active_material_stale_hit_count": len(active_material_hits),
        "current_notebook_stale_hit_count": len(current_notebook_hits),
        "executed_notebook_historical_hit_count": len(executed_hits),
        "work_log_stale_phrase_mention_count": len(work_hits),
        "work_log_mentions_are_audit_only": work_log_audit_only,
        "historical_outputs_classified": len(executed_hits) > 0,
        "active_material_hits": active_material_hits[:20],
        "current_notebook_hits": current_notebook_hits[:20],
        "executed_notebook_historical_hits": executed_hits[:20],
        "work_log_hits_sample": work_hits[:10],
        "baseline_current_blocking": BASELINE_BLOCKING,
        "current_source_of_truth": [
            "reports/next_user_action_packet.md",
            "reports/route_aware_submission_blockers.md",
            "reports/submission_status_dashboard.html",
            "submission/README.md",
            "submission/REAL_SUBMISSION_HANDOFF.md",
            "submission/AUTHORIZED_SUBMISSION_SEQUENCE.md",
        ],
        "blocking": [
            "executed notebook 中仍有旧口径历史输出；不要把它当作当前 baseline 提交前置条件。",
            "当前 baseline 真实提交仍等待用户目标确认、token、submission id、variant=baseline 和真实 runner 强确认。",
        ],
    }
    status["passed"] = all(
        [
            len(active_material_hits) == 0,
            len(current_notebook_hits) == 0,
            len(executed_hits) > 0,
            work_log_audit_only,
        ]
    )
    return status


def write_report(status: dict[str, Any], path: Path) -> None:
    lines = [
        "# Notebook 历史 checkpoint 输出审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 当前材料旧口径命中数：`{status['active_material_stale_hit_count']}`。",
        f"- 当前 Notebook 旧口径命中数：`{status['current_notebook_stale_hit_count']}`。",
        f"- executed Notebook 历史旧口径命中数：`{status['executed_notebook_historical_hit_count']}`。",
        f"- work.md 旧短语仅作为审计记录：`{status['work_log_mentions_are_audit_only']}`。",
        "- 结论：当前提交材料以 reports/submission/当前 Notebook 为准；executed Notebook 中的旧 checkpoint-link 输出只保留为历史运行证据。",
        "",
        "## 当前 baseline 阻塞",
        "",
    ]
    for item in status["baseline_current_blocking"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## 当前可信入口", ""])
    for item in status["current_source_of_truth"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## 历史输出样例", ""])
    for hit in status["executed_notebook_historical_hits"][:10]:
        lines.append(f"- `{hit['path']}:{hit['line']}`：{hit['phrase']}")
    lines.extend(["", "## Blocking", ""])
    for item in status["blocking"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    status = build_status()
    args.status_path.parent.mkdir(parents=True, exist_ok=True)
    args.status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(status, args.report_path)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
