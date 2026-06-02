#!/usr/bin/env python3
"""Audit UTF-8 decoding and mojibake sentinels for Chinese handoff artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
DEFAULT_STATUS = RUNS_DIR / "chinese_utf8_artifact_audit.json"
DEFAULT_REPORT = REPORTS_DIR / "chinese_utf8_artifact_audit.md"

SCAN_PREFIXES = (
    "README.md",
    "work.md",
    "reports/",
    "runs/",
    "notebooks/",
    "submission/",
)
TEXT_SUFFIXES = {".md", ".html", ".json", ".ipynb", ".sh", ".txt"}
EXCLUDE_PATHS = {
    "runs/table30v2_aloha_dry_run_samples.jsonl",
}
BAD_MARKERS = {
    "replacement_character": "�",
    "latin1_mojibake_a_tilde": "Ã",
    "latin1_mojibake_a_circumflex": "Â",
    "cp936_mojibake_1": "鍩",
    "cp936_mojibake_2": "绗",
    "cp936_mojibake_3": "闃",
    "cp936_mojibake_4": "鎻",
    "cp936_mojibake_5": "鐘",
    "cp936_mojibake_6": "銆",
    "cp936_mojibake_7": "锛",
    "cp936_mojibake_8": "乣",
    "cp936_mojibake_9": "宍",
}
REQUIRED_PHRASES = {
    "dashboard_html_title": ("reports/submission_status_dashboard.html", "RoboChallenge pi0.5 提交状态面板"),
    "dashboard_html_utf8_meta": ("reports/submission_status_dashboard.html", '<meta charset="utf-8"'),
    "preflight_report_title": ("reports/submission_preflight_bundle.md", "真实提交前预检汇总"),
    "local_env_smoke_parent_confirm": ("reports/baseline_local_env_smoke.md", "父环境确认短语"),
    "handoff_rehearsal_parent_confirm": ("reports/baseline_final_handoff_rehearsal.md", "父环境确认短语"),
    "notebook_json_cn": ("notebooks/robochallenge_pi05_submit_cn.ipynb", "baseline final handoff"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计中文交接产物是否为 UTF-8，且无常见乱码哨兵。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文报告输出路径。")
    return parser.parse_args()


def git_tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return []
    return sorted(item for item in result.stdout.decode("utf-8", errors="replace").split("\0") if item)


def should_scan(rel: str) -> bool:
    if rel in EXCLUDE_PATHS:
        return False
    if not any(rel == prefix or rel.startswith(prefix) for prefix in SCAN_PREFIXES):
        return False
    return Path(rel).suffix in TEXT_SUFFIXES or rel in {"README.md", "work.md"}


def scan_file(rel: str) -> dict[str, Any]:
    path = ROOT / rel
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
        decode_error = ""
    except UnicodeDecodeError as exc:
        text = raw.decode("utf-8", errors="replace")
        decode_error = str(exc)
    marker_hits: list[dict[str, Any]] = []
    for name, marker in BAD_MARKERS.items():
        start = 0
        while True:
            index = text.find(marker, start)
            if index < 0:
                break
            line_no = text.count("\n", 0, index) + 1
            marker_hits.append({"marker": name, "line": line_no})
            start = index + len(marker)
    return {
        "path": rel,
        "size_bytes": len(raw),
        "utf8_decode_ok": decode_error == "",
        "decode_error": decode_error,
        "bad_marker_count": len(marker_hits),
        "bad_marker_hits": marker_hits[:20],
    }


def phrase_checks() -> dict[str, dict[str, Any]]:
    checks: dict[str, dict[str, Any]] = {}
    for key, (rel, phrase) in REQUIRED_PHRASES.items():
        path = ROOT / rel
        if not path.exists():
            checks[key] = {"path": rel, "present": False, "reason": "missing_file"}
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        checks[key] = {"path": rel, "present": phrase in text, "phrase_length": len(phrase)}
    return checks


def build_status() -> dict[str, Any]:
    tracked = git_tracked_files()
    scanned_paths = [rel for rel in tracked if should_scan(rel)]
    file_results = [scan_file(rel) for rel in scanned_paths]
    decode_errors = [item for item in file_results if not item["utf8_decode_ok"]]
    marker_hits = [item for item in file_results if item["bad_marker_count"]]
    phrase_status = phrase_checks()
    passed = bool(
        scanned_paths
        and not decode_errors
        and not marker_hits
        and phrase_status
        and all(item.get("present") is True for item in phrase_status.values())
    )
    blocking: list[str] = []
    if passed:
        blocking.append("中文交接产物 UTF-8 解码与乱码哨兵扫描通过。")
    else:
        if not scanned_paths:
            blocking.append("未找到可扫描的中文交接产物。")
        for item in decode_errors[:10]:
            blocking.append(f"`{item['path']}` UTF-8 解码失败。")
        for item in marker_hits[:10]:
            blocking.append(f"`{item['path']}` 命中乱码哨兵 {item['bad_marker_hits'][:3]}。")
        for key, item in phrase_status.items():
            if item.get("present") is not True:
                blocking.append(f"`{key}` 必需中文/UTF-8 片段缺失。")
    return {
        "kind": "chinese_utf8_artifact_audit",
        "passed": passed,
        "scanned_file_count": len(file_results),
        "decode_error_count": len(decode_errors),
        "bad_marker_hit_file_count": len(marker_hits),
        "bad_marker_hit_count": sum(item["bad_marker_count"] for item in file_results),
        "required_phrase_checks": phrase_status,
        "sampled_files": file_results[:80],
        "decode_error_paths": [item["path"] for item in decode_errors],
        "bad_marker_hit_paths": [item["path"] for item in marker_hits],
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
        "# 中文 UTF-8 与乱码哨兵审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 扫描文件数：`{status['scanned_file_count']}`。",
        f"- UTF-8 解码错误数：`{status['decode_error_count']}`。",
        f"- 乱码哨兵命中文件数：`{status['bad_marker_hit_file_count']}`。",
        f"- 乱码哨兵命中总数：`{status['bad_marker_hit_count']}`。",
        "",
        "## 必需片段",
        "",
    ]
    for key, item in status["required_phrase_checks"].items():
        lines.append(f"- `{key}`：`present={item.get('present')}`，path=`{item.get('path')}`。")
    lines.extend(["", "## 边界", ""])
    lines.append("- 本审计只读取 Git 跟踪的文本产物，不读取 local env，不连接 RoboChallenge 平台，不上传文件。")
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
