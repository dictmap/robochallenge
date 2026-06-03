#!/usr/bin/env python3
"""Audit whether the local workspace is ready to run a real RoboChallenge submission."""

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
SUBMISSION_DIR = ROOT / "submission"
DEFAULT_STATUS = RUNS_DIR / "real_submission_readiness.json"
DEFAULT_REPORT = REPORTS_DIR / "real_submission_readiness.md"
TARGET_CONFIRMATION_VALUE = "CONFIRM_TABLE30V2_ALOHA_BASELINE"


ENV_KEYS = [
    "ROBOCHALLENGE_USER_TOKEN",
    "ROBOCHALLENGE_SUBMISSION_ID",
    "ROBOCHALLENGE_SUBMISSION_TARGET_CONFIRMATION",
    "ROBOCHALLENGE_CHECKPOINT_LINK",
    "ROBOCHALLENGE_LORA_CHECKPOINT_LINK",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计真实 RoboChallenge 提交前置条件，不连接平台、不打印凭据。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文审计报告输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def env_probe() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for key in ENV_KEYS:
        value = os.environ.get(key, "")
        result[key] = {
            "present": bool(value),
            "length": len(value) if value else 0,
            "looks_like_url": bool(re.match(r"^https?://", value)) if value else False,
            "matches_target_confirmation": value == TARGET_CONFIRMATION_VALUE
            if key == "ROBOCHALLENGE_SUBMISSION_TARGET_CONFIRMATION"
            else None,
        }
    return result


def bash_syntax(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "passed": False, "returncode": None, "stderr": "missing"}
    try:
        result = subprocess.run(
            ["bash", "-n"],
            input=path.read_text(encoding="utf-8"),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except FileNotFoundError:
        return {"exists": True, "passed": False, "returncode": None, "stderr": "bash not found"}
    stderr = result.stderr or ""
    if "WSL" in stderr and "execvpe(/bin/bash) failed" in stderr:
        stderr = "bash unavailable in current Windows shell"
    else:
        stderr = "".join(ch if ch in "\n\r\t" or (ord(ch) >= 32 and ch != "\ufffd") else "?" for ch in stderr)
    return {
        "exists": True,
        "passed": result.returncode == 0,
        "returncode": result.returncode,
        "stderr": stderr.strip(),
    }


def build_status() -> dict[str, Any]:
    submission_audit = read_json(RUNS_DIR / "robochallenge_submission_package_audit.json")
    export_audit = read_json(RUNS_DIR / "lora_checkpoint_export_readiness.json")
    upload_audit = read_json(RUNS_DIR / "checkpoint_upload_channels_audit.json")
    manifest = read_json(SUBMISSION_DIR / "submission_manifest_template.json")
    env = env_probe()

    baseline_runner = SUBMISSION_DIR / "run_table30v2_aloha_demo_template.sh"
    lora_runner = SUBMISSION_DIR / "run_table30v2_aloha_lora_demo_template.sh"
    selected_target = submission_audit.get("selected_target", {})
    baseline_checkpoint = Path(selected_target.get("checkpoint", ""))
    lora_checkpoint = ROOT / "runs/openpi_rtc_lora_materialized_policy_checkpoint"

    has_user_token = env["ROBOCHALLENGE_USER_TOKEN"]["present"]
    has_submission_id = env["ROBOCHALLENGE_SUBMISSION_ID"]["present"]
    has_target_confirmation = env["ROBOCHALLENGE_SUBMISSION_TARGET_CONFIRMATION"]["matches_target_confirmation"]
    has_any_checkpoint_link = (
        env["ROBOCHALLENGE_CHECKPOINT_LINK"]["looks_like_url"]
        or env["ROBOCHALLENGE_LORA_CHECKPOINT_LINK"]["looks_like_url"]
    )

    local_baseline_runner_ready = bool(
        submission_audit.get("passed")
        and bash_syntax(baseline_runner)["passed"]
        and baseline_checkpoint.exists()
        and has_user_token
        and has_submission_id
        and has_target_confirmation
    )
    local_lora_runner_ready = bool(
        submission_audit.get("passed")
        and export_audit.get("local_export_ready")
        and bash_syntax(lora_runner)["passed"]
        and lora_checkpoint.exists()
        and has_user_token
        and has_submission_id
        and has_target_confirmation
    )
    web_form_ready = bool(
        manifest.get("status") == "template_pending_credentials"
        and upload_audit.get("passed")
        and has_user_token
        and has_submission_id
        and has_target_confirmation
        and has_any_checkpoint_link
    )
    ready_for_real_submission = local_baseline_runner_ready or local_lora_runner_ready or web_form_ready

    blocking = []
    if not has_user_token:
        blocking.append("缺少 ROBOCHALLENGE_USER_TOKEN。")
    if not has_submission_id:
        blocking.append("缺少 ROBOCHALLENGE_SUBMISSION_ID。")
    if not has_target_confirmation:
        blocking.append("缺少或未精确匹配 ROBOCHALLENGE_SUBMISSION_TARGET_CONFIRMATION=CONFIRM_TABLE30V2_ALOHA_BASELINE。")
    if not has_any_checkpoint_link:
        blocking.append("缺少真实可访问 checkpoint link；可使用 ROBOCHALLENGE_CHECKPOINT_LINK 或 ROBOCHALLENGE_LORA_CHECKPOINT_LINK 记录。")
    if not upload_audit.get("passed"):
        blocking.append("checkpoint 上传通道审计未通过。")
    if upload_audit.get("uploads_performed") is False:
        blocking.append("尚未执行 checkpoint 上传，本地 tar 文件也未生成。")
    if not blocking:
        blocking.append("无本地阻塞；可以进入真实提交入口，但本脚本不会自动提交。")

    return {
        "kind": "real_submission_readiness",
        "passed": True,
        "ready_for_real_submission": ready_for_real_submission,
        "web_form_ready": web_form_ready,
        "local_baseline_runner_ready": local_baseline_runner_ready,
        "local_lora_runner_ready": local_lora_runner_ready,
        "platform_contacted": False,
        "credentials_printed": False,
        "env": env,
        "runner_checks": {
            "baseline": bash_syntax(baseline_runner),
            "lora": bash_syntax(lora_runner),
        },
        "inputs": {
            "submission_audit_passed": bool(submission_audit.get("passed")),
            "export_audit_local_ready": bool(export_audit.get("local_export_ready")),
            "upload_audit_passed": bool(upload_audit.get("passed")),
            "uploads_performed": upload_audit.get("uploads_performed"),
            "manifest_status": manifest.get("status"),
            "baseline_checkpoint_exists": baseline_checkpoint.exists(),
            "lora_checkpoint_exists": lora_checkpoint.exists(),
        },
        "blocking": blocking,
    }


def write_report(status: dict[str, Any], path: Path) -> None:
    lines = [
        "# 真实提交 readiness gate",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 可进入真实提交：`{status['ready_for_real_submission']}`。",
        f"- Web 表单就绪：`{status['web_form_ready']}`。",
        f"- 本地 baseline runner 就绪：`{status['local_baseline_runner_ready']}`。",
        f"- 本地 LoRA runner 就绪：`{status['local_lora_runner_ready']}`。",
        f"- 是否连接 RoboChallenge 平台：`{status['platform_contacted']}`。",
        f"- 是否打印凭据：`{status['credentials_printed']}`。",
        "",
        "## 环境变量状态",
        "",
    ]
    for key, item in status["env"].items():
        lines.append(
            f"- `{key}`：present=`{item['present']}`，length=`{item['length']}`，looks_like_url=`{item['looks_like_url']}`。"
        )
    lines.extend(["", "## 输入证据", ""])
    for key, value in status["inputs"].items():
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
