#!/usr/bin/env python3
"""Audit the tracked submission environment template without reading local secrets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = ROOT / "runs"
DEFAULT_TEMPLATE = ROOT / "submission/robochallenge_env_template.sh"
DEFAULT_STATUS = RUNS_DIR / "submission_env_template_audit.json"
DEFAULT_REPORT = REPORTS_DIR / "submission_env_template_audit.md"

REQUIRED_KEYS = [
    "ROBOCHALLENGE_USER_TOKEN",
    "ROBOCHALLENGE_SUBMISSION_ID",
    "ROBOCHALLENGE_LORA_CHECKPOINT_LINK",
    "ROBOCHALLENGE_CHECKPOINT_LINK",
]
LOCAL_SECRET_PATHS = [
    "submission/robochallenge_env.local.sh",
    ".env",
    ".env.local",
]
SECRET_PATTERNS = {
    "openai_api_key": re.compile(r"sk-proj-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{30,}"),
    "huggingface_token": re.compile(r"hf_[A-Za-z0-9]{20,}"),
    "github_token": re.compile(r"ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{20,}"),
    "robochallenge_token_assignment": re.compile(
        r"(?:export\s+)?ROBOCHALLENGE_(?:USER_)?TOKEN\s*=\s*[A-Za-z0-9][A-Za-z0-9_-]{19,}"
    ),
    "robochallenge_submission_assignment": re.compile(
        r"(?:export\s+)?ROBOCHALLENGE_SUBMISSION_ID\s*=\s*[A-Za-z0-9][A-Za-z0-9_-]{10,}"
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计真实提交环境变量模板；不读取本地真实凭据副本。")
    parser.add_argument("--template-path", type=Path, default=DEFAULT_TEMPLATE, help="tracked 模板路径。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文审计报告输出路径。")
    return parser.parse_args()


def git_check_ignore(rel: str) -> dict[str, Any]:
    result = subprocess.run(
        ["git", "check-ignore", "-q", rel],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return {
        "path": rel,
        "ignored": result.returncode == 0,
        "returncode": result.returncode,
    }


def parse_exports(text: str) -> dict[str, str]:
    exports: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("export "):
            continue
        left, sep, right = line[len("export ") :].partition("=")
        if sep:
            exports[left.strip()] = right.strip().strip('"').strip("'")
    return exports


def secret_pattern_hits(text: str) -> list[str]:
    return [name for name, pattern in SECRET_PATTERNS.items() if pattern.search(text)]


def build_status(template_path: Path) -> dict[str, Any]:
    template_exists = template_path.exists()
    text = template_path.read_text(encoding="utf-8") if template_exists else ""
    exports = parse_exports(text)
    required_present = {key: key in exports for key in REQUIRED_KEYS}
    placeholder_values = {
        key: bool(exports.get(key, "").startswith("<真实 ") and exports.get(key, "").endswith(">"))
        for key in REQUIRED_KEYS
    }
    local_ignore = {path: git_check_ignore(path) for path in LOCAL_SECRET_PATHS}
    hits = secret_pattern_hits(text)
    blocking = []
    if not template_exists:
        blocking.append("缺少 tracked 环境变量模板。")
    for key, ok in required_present.items():
        if not ok:
            blocking.append(f"模板缺少 `{key}`。")
    for key, ok in placeholder_values.items():
        if not ok:
            blocking.append(f"模板中的 `{key}` 不是占位符。")
    for path, item in local_ignore.items():
        if not item["ignored"]:
            blocking.append(f"真实本地副本路径 `{path}` 未被 Git 忽略。")
    if hits:
        blocking.append("模板疑似包含真实 token、submission id 或第三方密钥模式。")
    if not blocking:
        blocking.append("无模板侧阻塞；真实提交仍取决于用户提供凭据、submission id 和 checkpoint link。")

    passed = bool(
        template_exists
        and all(required_present.values())
        and all(placeholder_values.values())
        and all(item["ignored"] for item in local_ignore.values())
        and not hits
    )
    return {
        "kind": "submission_env_template_audit",
        "passed": passed,
        "template_path": template_path.relative_to(ROOT).as_posix(),
        "platform_contacted": False,
        "uploads_performed": False,
        "credentials_read": False,
        "credentials_printed": False,
        "secret_values_printed": False,
        "required_present": required_present,
        "placeholder_values": placeholder_values,
        "local_secret_paths": local_ignore,
        "secret_pattern_hits": hits,
        "recommended_local_copy": "submission/robochallenge_env.local.sh",
        "blocking": blocking,
    }


def write_report(status: dict[str, Any], path: Path) -> None:
    lines = [
        "# 真实提交环境变量模板审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 模板路径：`{status['template_path']}`。",
        f"- 建议本地副本：`{status['recommended_local_copy']}`。",
        f"- 是否连接 RoboChallenge 平台：`{status['platform_contacted']}`。",
        f"- 是否执行上传：`{status['uploads_performed']}`。",
        f"- 是否读取真实凭据：`{status['credentials_read']}`。",
        f"- 是否打印真实凭据：`{status['credentials_printed']}`。",
        f"- 是否发现疑似密钥模式：`{bool(status['secret_pattern_hits'])}`。",
        "",
        "## 必需变量",
        "",
    ]
    for key in REQUIRED_KEYS:
        lines.append(
            f"- `{key}`：present=`{status['required_present'][key]}`，placeholder=`{status['placeholder_values'][key]}`。"
        )
    lines.extend(["", "## Git 忽略检查", ""])
    for path_key, item in status["local_secret_paths"].items():
        lines.append(f"- `{path_key}`：ignored=`{item['ignored']}`。")
    lines.extend(["", "## Blocking", ""])
    for item in status["blocking"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args()
    status = build_status(args.template_path)
    args.status_path.parent.mkdir(parents=True, exist_ok=True)
    args.status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(status, args.report_path)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
