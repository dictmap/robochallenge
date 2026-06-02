#!/usr/bin/env python3
"""Audit the user-authorized checkpoint archive wrapper without creating tar files."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = ROOT / "runs"
TEMPLATE = ROOT / "submission" / "run_authorized_checkpoint_archive_template.sh"
DEFAULT_STATUS = RUNS_DIR / "authorized_checkpoint_archive_template_audit.json"
DEFAULT_REPORT = REPORTS_DIR / "authorized_checkpoint_archive_template_audit.md"
CONFIRM_PHRASE = "CREATE_ROBOCHALLENGE_CHECKPOINT_ARCHIVE"
ARCHIVE_PATH = RUNS_DIR / "openpi_rtc_lora_materialized_policy_checkpoint.tar"
SHA256_PATH = RUNS_DIR / "openpi_rtc_lora_materialized_policy_checkpoint.tar.sha256"

SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9_-]{30,}",
    r"hf_[A-Za-z0-9]{20,}",
    r"ghp_[A-Za-z0-9]{30,}",
    r"github_pat_[A-Za-z0-9_]{20,}",
    r"ROBOCHALLENGE_(?:USER_)?TOKEN\s*=\s*[A-Za-z0-9_-]{20,}",
]

REQUIRED_FRAGMENTS = {
    "runs_archive_plan": "python3 scripts/audit_checkpoint_archive_plan.py",
    "runs_split_plan": "python3 scripts/audit_checkpoint_split_plan.py",
    "runs_archive_dry_run": "python3 scripts/create_checkpoint_archive.py",
    "requires_archive_confirm_env": "ROBOCHALLENGE_ARCHIVE_CONFIRM",
    "confirmation_phrase": CONFIRM_PHRASE,
    "execute_gate": "--execute --confirm-create-large-archive",
    "stops_before_tar": "stop before creating tar",
    "upload_separate_authorization": "upload still requires separate user authorization",
}

FORBIDDEN_FRAGMENTS = {
    "uploads_with_rclone": "rclone copy",
    "uploads_with_aws": "aws s3 cp",
    "uploads_with_curl": "curl -T",
    "uploads_with_gh_release": "gh release upload",
    "uploads_with_hf": "hf upload",
    "calls_lora_runner": "run_table30v2_aloha_lora_demo_template.sh",
    "calls_baseline_runner": "run_table30v2_aloha_demo_template.sh",
    "mentions_demo_py": "demo.py",
    "reads_user_token": "ROBOCHALLENGE_USER_TOKEN",
    "reads_submission_id": "ROBOCHALLENGE_SUBMISSION_ID",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计授权后 checkpoint 归档模板；不生成 tar、不上传。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文审计报告输出路径。")
    return parser.parse_args()


def run_command(args: list[str], env: dict[str, str] | None = None, timeout: int = 900) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    merged_env["PYTHONIOENCODING"] = "utf-8"
    for key in [
        "ROBOCHALLENGE_ARCHIVE_CONFIRM",
        "ROBOCHALLENGE_USER_TOKEN",
        "ROBOCHALLENGE_SUBMISSION_ID",
        "ROBOCHALLENGE_CHECKPOINT_LINK",
        "ROBOCHALLENGE_LORA_CHECKPOINT_LINK",
    ]:
        merged_env.pop(key, None)
    if env:
        merged_env.update(env)
    return subprocess.run(
        args,
        cwd=ROOT,
        env=merged_env,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=timeout,
    )


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def scan_secret_patterns(text: str) -> list[str]:
    return [pattern for pattern in SECRET_PATTERNS if re.search(pattern, text)]


def no_confirm_smoke() -> dict[str, Any]:
    archive_absent_before = not ARCHIVE_PATH.exists()
    sha256_absent_before = not SHA256_PATH.exists()
    result = run_command(["bash", "submission/run_authorized_checkpoint_archive_template.sh"])
    output = (result.stdout or "") + "\n" + (result.stderr or "")
    archive_dry_run = read_json(RUNS_DIR / "checkpoint_archive_dry_run.json")
    archive_absent_after = not ARCHIVE_PATH.exists()
    sha256_absent_after = not SHA256_PATH.exists()
    status = {
        "returncode": result.returncode,
        "stdout_tail": (result.stdout or "")[-3000:],
        "stderr_tail": (result.stderr or "")[-1000:],
        "archive_absent_before": archive_absent_before,
        "sha256_absent_before": sha256_absent_before,
        "archive_absent_after": archive_absent_after,
        "sha256_absent_after": sha256_absent_after,
        "missing_confirmation": "missing explicit archive confirmation" in output,
        "stops_before_creating_tar": "stop before creating tar" in output,
        "archive_created": archive_dry_run.get("archive_created"),
        "sha256_created": archive_dry_run.get("sha256_created"),
        "upload_performed": archive_dry_run.get("upload_performed"),
        "credentials_read": archive_dry_run.get("credentials_read"),
        "platform_contacted": archive_dry_run.get("platform_contacted"),
        "dry_run_passed": archive_dry_run.get("passed") is True,
        "confirm_phrase_accepted": "confirmation accepted; starting archive creation" in output,
    }
    status["passed"] = all(
        [
            result.returncode != 0,
            status["archive_absent_before"],
            status["sha256_absent_before"],
            status["archive_absent_after"],
            status["sha256_absent_after"],
            status["missing_confirmation"],
            status["stops_before_creating_tar"],
            status["archive_created"] is False,
            status["sha256_created"] is False,
            status["upload_performed"] is False,
            status["credentials_read"] is False,
            status["platform_contacted"] is False,
            status["dry_run_passed"],
            not status["confirm_phrase_accepted"],
        ]
    )
    return status


def build_status() -> dict[str, Any]:
    exists = TEMPLATE.exists()
    text = TEMPLATE.read_text(encoding="utf-8") if exists else ""
    bash_n = run_command(["bash", "-n", str(TEMPLATE)], timeout=120) if exists else None
    required = {name: fragment in text for name, fragment in REQUIRED_FRAGMENTS.items()}
    forbidden = {name: fragment in text for name, fragment in FORBIDDEN_FRAGMENTS.items()}
    secret_hits = scan_secret_patterns(text)
    smoke = no_confirm_smoke() if exists else {}
    archive_plan = read_json(RUNS_DIR / "checkpoint_archive_plan.json")
    split_plan = read_json(RUNS_DIR / "checkpoint_split_plan.json")
    archive_dry_run = read_json(RUNS_DIR / "checkpoint_archive_dry_run.json")

    input_evidence = {
        "archive_plan_passed": archive_plan.get("passed") is True,
        "split_plan_passed": split_plan.get("passed") is True,
        "archive_dry_run_passed": archive_dry_run.get("passed") is True,
        "archive_not_created": archive_dry_run.get("archive_created") is False,
        "sha256_not_created": archive_dry_run.get("sha256_created") is False,
        "upload_not_performed": archive_dry_run.get("upload_performed") is False,
        "credentials_not_read": archive_dry_run.get("credentials_read") is False,
        "platform_not_contacted": archive_dry_run.get("platform_contacted") is False,
    }
    passed = bool(
        exists
        and bash_n is not None
        and bash_n.returncode == 0
        and all(required.values())
        and not any(forbidden.values())
        and not secret_hits
        and smoke.get("passed")
        and all(input_evidence.values())
    )
    blocking: list[str] = []
    if not exists:
        blocking.append("缺少授权后 checkpoint 归档模板。")
    if bash_n is None or bash_n.returncode != 0:
        blocking.append("授权后 checkpoint 归档模板 bash 语法检查未通过。")
    for key, ok in required.items():
        if not ok:
            blocking.append(f"模板缺少必要片段：{key}。")
    for key, found in forbidden.items():
        if found:
            blocking.append(f"模板包含禁止片段：{key}。")
    if secret_hits:
        blocking.append("模板疑似包含明文 token 或密钥模式。")
    for key, ok in input_evidence.items():
        if not ok:
            blocking.append(f"输入证据未通过：{key}。")
    if not smoke.get("passed"):
        blocking.append("无确认 smoke 未能证明模板停在生成 tar 前。")
    if not blocking:
        blocking.append("授权后 checkpoint 归档模板已通过；没有确认短语时不会生成 tar。")
    return {
        "kind": "authorized_checkpoint_archive_template_audit",
        "passed": passed,
        "platform_contacted": False,
        "uploads_performed": False,
        "credentials_read": False,
        "credentials_printed": False,
        "link_values_printed": False,
        "secret_values_printed": False,
        "template_path": "submission/run_authorized_checkpoint_archive_template.sh",
        "confirmation_phrase": CONFIRM_PHRASE,
        "bash_n": {
            "returncode": bash_n.returncode if bash_n else None,
            "passed": bash_n.returncode == 0 if bash_n else False,
            "stderr": (bash_n.stderr or "").strip() if bash_n else "missing",
        },
        "required_fragments": required,
        "forbidden_fragments": forbidden,
        "secret_patterns_found": secret_hits,
        "no_confirm_smoke": smoke,
        "input_evidence": input_evidence,
        "blocking": blocking,
    }


def write_report(status: dict[str, Any], path: Path) -> None:
    lines = [
        "# 授权后 checkpoint 归档模板审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 模板路径：`{status['template_path']}`。",
        f"- 确认短语：`{status['confirmation_phrase']}`。",
        f"- bash 语法检查：`{status['bash_n']['passed']}`。",
        f"- 无确认 smoke：`{status['no_confirm_smoke'].get('passed')}`。",
        f"- 是否生成 tar：`{status['no_confirm_smoke'].get('archive_created')}`。",
        f"- 是否上传：`{status['uploads_performed']}`。",
        f"- 是否读取或打印凭据：`{status['credentials_read'] or status['credentials_printed']}`。",
        "",
        "## 必要片段",
        "",
    ]
    for key, value in status["required_fragments"].items():
        lines.append(f"- `{key}`：`{value}`。")
    lines.extend(["", "## 禁止片段", ""])
    for key, value in status["forbidden_fragments"].items():
        lines.append(f"- `{key}`：`{value}`。")
    lines.extend(["", "## 无确认 smoke", ""])
    for key, value in status["no_confirm_smoke"].items():
        if key.endswith("_tail"):
            continue
        lines.append(f"- `{key}`：`{value}`。")
    lines.extend(["", "## 输入证据", ""])
    for key, value in status["input_evidence"].items():
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
