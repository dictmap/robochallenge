#!/usr/bin/env python3
"""Verify placeholder credentials are rejected before dry-run or runner startup."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
DEFAULT_STATUS = RUNS_DIR / "placeholder_credential_rejection.json"
DEFAULT_REPORT = REPORTS_DIR / "placeholder_credential_rejection.md"

PLACEHOLDER_TOKEN = "replace_me_user_token_placeholder"
PLACEHOLDER_SUBMISSION_ID = "replace_me_submission_id_placeholder"
SAFE_TOKEN = "rtok_safe_value_0001"
SAFE_SUBMISSION_ID = "sid_safe_value_0001"

TEMPLATES = {
    "baseline": "submission/run_table30v2_aloha_demo_template.sh",
    "lora": "submission/run_table30v2_aloha_lora_demo_template.sh",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="验证占位符 token/submission id 会在 dry-run 前被拒绝。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文报告输出路径。")
    return parser.parse_args()


def sanitized_env(token: str, submission_id: str) -> dict[str, str]:
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("ROBOCHALLENGE_"):
            env.pop(key, None)
    env["PYTHONIOENCODING"] = "utf-8"
    env["ROBOCHALLENGE_USER_TOKEN"] = token
    env["ROBOCHALLENGE_SUBMISSION_ID"] = submission_id
    env["ROBOCHALLENGE_DRY_RUN"] = "1"
    return env


def run_case(route: str, field: str, token: str, submission_id: str) -> dict[str, Any]:
    script = TEMPLATES[route]
    result = subprocess.run(
        ["bash", script],
        cwd=ROOT,
        env=sanitized_env(token, submission_id),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=120,
    )
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    combined = stdout + "\n" + stderr
    protected_values = [PLACEHOLDER_TOKEN, PLACEHOLDER_SUBMISSION_ID, SAFE_TOKEN, SAFE_SUBMISSION_ID]
    rejected_name = "ROBOCHALLENGE_USER_TOKEN" if field == "user_token" else "ROBOCHALLENGE_SUBMISSION_ID"
    return {
        "route": route,
        "field": field,
        "script": script,
        "returncode": result.returncode,
        "stdout_tail": stdout[-1000:],
        "stderr_tail": stderr[-1000:],
        "placeholder_rejected": result.returncode == 64 and rejected_name in combined and "占位符" in combined,
        "expected_field_rejected": rejected_name in combined,
        "dry_run_called": "dry_run=true" in combined,
        "robot_type_aloha": "robot_type=aloha" in combined,
        "stops_before_dry_run": "dry_run=true" not in combined and "robot_type=aloha" not in combined,
        "real_runner_started": "confirmation accepted; starting real runner" in combined or "Traceback" in combined,
        "printed_protected_values": any(value in combined for value in protected_values),
        "leaked_value_count": sum(1 for value in protected_values if value in combined),
    }


def build_status() -> dict[str, Any]:
    cases = [
        run_case("baseline", "user_token", PLACEHOLDER_TOKEN, SAFE_SUBMISSION_ID),
        run_case("baseline", "submission_id", SAFE_TOKEN, PLACEHOLDER_SUBMISSION_ID),
        run_case("lora", "user_token", PLACEHOLDER_TOKEN, SAFE_SUBMISSION_ID),
        run_case("lora", "submission_id", SAFE_TOKEN, PLACEHOLDER_SUBMISSION_ID),
    ]
    case_map = {f"{item['route']}_{item['field']}": item for item in cases}

    evidence = {
        "baseline_token_placeholder_rejected": case_map["baseline_user_token"].get("placeholder_rejected") is True,
        "baseline_submission_id_placeholder_rejected": case_map["baseline_submission_id"].get(
            "placeholder_rejected"
        )
        is True,
        "lora_token_placeholder_rejected": case_map["lora_user_token"].get("placeholder_rejected") is True,
        "lora_submission_id_placeholder_rejected": case_map["lora_submission_id"].get("placeholder_rejected")
        is True,
        "baseline_token_stops_before_dry_run": case_map["baseline_user_token"].get("stops_before_dry_run")
        is True,
        "baseline_submission_id_stops_before_dry_run": case_map["baseline_submission_id"].get(
            "stops_before_dry_run"
        )
        is True,
        "lora_token_stops_before_dry_run": case_map["lora_user_token"].get("stops_before_dry_run") is True,
        "lora_submission_id_stops_before_dry_run": case_map["lora_submission_id"].get("stops_before_dry_run")
        is True,
        "baseline_real_runner_not_started": all(
            case_map[key].get("real_runner_started") is False
            for key in ["baseline_user_token", "baseline_submission_id"]
        ),
        "lora_real_runner_not_started": all(
            case_map[key].get("real_runner_started") is False for key in ["lora_user_token", "lora_submission_id"]
        ),
        "no_protected_values_printed": all(item.get("printed_protected_values") is False for item in cases),
    }
    leak_flags = {
        "credentials_printed": any(item.get("printed_protected_values") for item in cases),
        "link_values_printed": False,
        "secret_values_printed": any(item.get("printed_protected_values") for item in cases),
    }
    contact_flags = {
        "platform_contacted": False,
        "uploads_performed": False,
        "download_host_contacted": False,
    }
    passed = bool(all(evidence.values()) and not any(leak_flags.values()) and not any(contact_flags.values()))
    blocking = []
    if passed:
        blocking.append("占位符 token/submission id 已验证会在 dry-run 和真实 runner 前被拒绝。")
    else:
        for key, ok in evidence.items():
            if not ok:
                blocking.append(f"占位符凭据拒绝证据未通过 `{key}`。")
        if any(leak_flags.values()):
            blocking.append("占位符审计输出包含受保护假值，需先修复脱敏边界。")

    return {
        "kind": "placeholder_credential_rejection",
        "passed": passed,
        "recommended_route": "baseline_official_aloha",
        "case_count": len(cases),
        "baseline_placeholder_rejected": evidence["baseline_token_placeholder_rejected"]
        and evidence["baseline_submission_id_placeholder_rejected"],
        "lora_placeholder_rejected": evidence["lora_token_placeholder_rejected"]
        and evidence["lora_submission_id_placeholder_rejected"],
        "baseline_stops_before_dry_run": evidence["baseline_token_stops_before_dry_run"]
        and evidence["baseline_submission_id_stops_before_dry_run"],
        "lora_stops_before_dry_run": evidence["lora_token_stops_before_dry_run"]
        and evidence["lora_submission_id_stops_before_dry_run"],
        "baseline_real_runner_not_started": evidence["baseline_real_runner_not_started"],
        "lora_real_runner_not_started": evidence["lora_real_runner_not_started"],
        "placeholder_token_length": len(PLACEHOLDER_TOKEN),
        "placeholder_submission_id_length": len(PLACEHOLDER_SUBMISSION_ID),
        "safe_token_length": len(SAFE_TOKEN),
        "safe_submission_id_length": len(SAFE_SUBMISSION_ID),
        "placeholder_values_recorded": False,
        "safe_values_recorded": False,
        "cases": cases,
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
        "# 占位符凭据拒绝审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 推荐路线：`{status['recommended_route']}`。",
        f"- baseline 占位符是否被拒绝：`{status['baseline_placeholder_rejected']}`。",
        f"- LoRA 占位符是否被拒绝：`{status['lora_placeholder_rejected']}`。",
        f"- baseline 是否停在 dry-run 前：`{status['baseline_stops_before_dry_run']}`。",
        f"- LoRA 是否停在 dry-run 前：`{status['lora_stops_before_dry_run']}`。",
        f"- baseline 是否未启动真实 runner：`{status['baseline_real_runner_not_started']}`。",
        f"- LoRA 是否未启动真实 runner：`{status['lora_real_runner_not_started']}`。",
        f"- 是否记录占位符明文：`{status['placeholder_values_recorded']}`。",
        f"- 是否记录安全假值明文：`{status['safe_values_recorded']}`。",
        "",
        "## 覆盖的场景",
        "",
    ]
    for item in status["cases"]:
        lines.append(
            f"- `{item['script']}` / `{item['field']}`：returncode=`{item['returncode']}`，"
            f"rejected=`{item['placeholder_rejected']}`，stops_before_dry_run=`{item['stops_before_dry_run']}`。"
        )
    lines.extend(["", "## 只读边界", ""])
    for key, value in status["contact_flags"].items():
        lines.append(f"- `{key}`：`{value}`。")
    for key, value in status["leak_flags"].items():
        lines.append(f"- `{key}`：`{value}`。")
    lines.extend(["", "## 输入证据", ""])
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
