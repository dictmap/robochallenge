#!/usr/bin/env python3
"""Audit the workspace for plaintext credentials without printing matched values."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = ROOT / "runs"
DEFAULT_STATUS = RUNS_DIR / "plaintext_secret_scan.json"
DEFAULT_REPORT = REPORTS_DIR / "plaintext_secret_scan.md"


PATTERNS = {
    "openai_api_key": re.compile(r"sk-proj-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{30,}"),
    "huggingface_token": re.compile(r"hf_[A-Za-z0-9]{20,}"),
    "github_token": re.compile(r"ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{20,}"),
    "aws_access_key_id": re.compile(r"AKIA[0-9A-Z]{16}"),
    "private_key_header": re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
    "robochallenge_token_assignment": re.compile(
        r"(?:export\s+)?ROBOCHALLENGE_(?:USER_)?TOKEN\s*=\s*[A-Za-z0-9][A-Za-z0-9_-]{19,}"
    ),
    "robochallenge_submission_assignment": re.compile(
        r"(?:export\s+)?ROBOCHALLENGE_SUBMISSION_ID\s*=\s*[A-Za-z0-9][A-Za-z0-9_-]{10,}"
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="扫描仓库明文凭据模式，不打印匹配值。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文审计报告输出路径。")
    return parser.parse_args()


def git_paths() -> list[str]:
    paths: list[str] = []
    for command in (["git", "ls-files", "-z"], ["git", "ls-files", "--others", "--exclude-standard", "-z"]):
        output = subprocess.check_output(command, cwd=ROOT)
        paths.extend(path for path in output.decode("utf-8").split("\0") if path)
    return sorted(set(paths))


def is_text_file(path: Path) -> bool:
    data = path.read_bytes()[:4096]
    return b"\0" not in data


def scan_file(path: Path, rel: str) -> list[dict[str, Any]]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="ignore")
    hits = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for name, pattern in PATTERNS.items():
            if pattern.search(line):
                hits.append({"path": rel, "line": line_no, "pattern": name})
    return hits


def build_status() -> dict[str, Any]:
    paths = git_paths()
    scanned_files = 0
    skipped_binary = 0
    hits: list[dict[str, Any]] = []
    for rel in paths:
        path = ROOT / rel
        if not path.is_file():
            continue
        if not is_text_file(path):
            skipped_binary += 1
            continue
        scanned_files += 1
        hits.extend(scan_file(path, rel))
    return {
        "kind": "plaintext_secret_scan",
        "passed": len(hits) == 0,
        "platform_contacted": False,
        "uploads_performed": False,
        "secret_values_printed": False,
        "scan_scope": "git tracked files plus unignored untracked files",
        "scanned_files": scanned_files,
        "skipped_binary_files": skipped_binary,
        "pattern_count": len(PATTERNS),
        "hit_count": len(hits),
        "hits": hits,
        "blocking": [
            "如发现命中项，先移除明文凭据并轮换对应 token，再重新运行本审计。",
            "本审计不替代真实平台权限检查；baseline 真实提交仍需要用户目标确认、token、submission id、variant=baseline 和真实 runner 强确认。",
        ],
    }


def write_report(status: dict[str, Any], path: Path) -> None:
    lines = [
        "# 明文凭据扫描",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 扫描范围：`{status['scan_scope']}`。",
        f"- 扫描文本文件数：`{status['scanned_files']}`。",
        f"- 跳过二进制文件数：`{status['skipped_binary_files']}`。",
        f"- 规则数量：`{status['pattern_count']}`。",
        f"- 命中数量：`{status['hit_count']}`。",
        f"- 是否连接平台：`{status['platform_contacted']}`。",
        f"- 是否执行上传：`{status['uploads_performed']}`。",
        f"- 是否打印匹配值：`{status['secret_values_printed']}`。",
        "",
        "## 命中项",
        "",
    ]
    if status["hits"]:
        for item in status["hits"]:
            lines.append(f"- `{item['path']}` 第 `{item['line']}` 行：`{item['pattern']}`。")
    else:
        lines.append("- 未发现明文凭据模式。")
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
