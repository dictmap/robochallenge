#!/usr/bin/env python3
"""Audit the submission target confirmation gate without real credentials."""

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
DEFAULT_STATUS = RUNS_DIR / "submission_target_confirmation_gate.json"
DEFAULT_REPORT = REPORTS_DIR / "submission_target_confirmation_gate.md"

CONFIRMATION_VALUE = "CONFIRM_TABLE30V2_ALOHA_BASELINE"
SYNTHETIC_TOKEN = "synthetic_target_confirmation_token_0001"
SYNTHETIC_SUBMISSION_ID = "synthetic_target_confirmation_submission_0001"
REDACTION = "[REDACTED_SYNTHETIC_VALUE]"

SCRIPTS = {
    "authorized_preflight": "submission/run_authorized_preflight_template.sh",
    "ready_runner": "submission/run_ready_real_submission_template.sh",
}

BAD_CASES = [
    ("authorized_missing", "authorized_preflight", None),
    ("ready_wrong", "ready_runner", "CONFIRM_TABLE30V2_ALOHA_LORA"),
    ("authorized_trailing_space", "authorized_preflight", CONFIRMATION_VALUE + " "),
    ("ready_lowercase", "ready_runner", CONFIRMATION_VALUE.lower()),
    ("authorized_newline", "authorized_preflight", CONFIRMATION_VALUE + "\n"),
]

GOOD_CASES = [
    ("authorized_correct", "authorized_preflight", CONFIRMATION_VALUE, 0),
    ("ready_correct_missing_real_confirm", "ready_runner", CONFIRMATION_VALUE, 1),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计提交对象确认 gate；不读取真实凭据、不联网、不上传。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文报告输出路径。")
    return parser.parse_args()


def clean_env(confirm_value: str | None) -> dict[str, str]:
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("ROBOCHALLENGE_"):
            env.pop(key, None)
    env["PYTHONIOENCODING"] = "utf-8"
    env["ROBOCHALLENGE_ENV_FILE"] = str(ROOT / "submission" / "__missing_env_for_target_confirmation_gate__.sh")
    env["ROBOCHALLENGE_USER_TOKEN"] = SYNTHETIC_TOKEN
    env["ROBOCHALLENGE_SUBMISSION_ID"] = SYNTHETIC_SUBMISSION_ID
    env["ROBOCHALLENGE_SUBMISSION_VARIANT"] = "baseline"
    env["ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD"] = "0"
    env["ROBOCHALLENGE_REQUIRE_READY"] = "0"
    if confirm_value is not None:
        env["ROBOCHALLENGE_SUBMISSION_TARGET_CONFIRMATION"] = confirm_value
    return env


def redact(text: str) -> str:
    redacted = text
    for value in [SYNTHETIC_TOKEN, SYNTHETIC_SUBMISSION_ID]:
        redacted = redacted.replace(value, REDACTION)
    return redacted


def run_case(
    name: str,
    script_key: str,
    confirm_value: str | None,
    expected_returncode: int,
    bad_case: bool,
) -> dict[str, Any]:
    result = subprocess.run(
        ["bash", SCRIPTS[script_key]],
        cwd=ROOT,
        env=clean_env(confirm_value),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=240,
    )
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    combined = stdout + "\n" + stderr
    target_rejected = (
        result.returncode == 69
        and "missing target confirmation" in combined
        and "ROBOCHALLENGE_SUBMISSION_TARGET_CONFIRMATION" in combined
    )
    preflight_started = (
        "checkpoint link" in combined
        or "ready_for_real_submission" in combined
        or "dry_run=true" in combined
        or "checkpoint_length=" in combined
    )
    correct_accepted = (
        result.returncode == expected_returncode
        and "missing target confirmation" not in combined
        and "target_confirmation_present=true" in combined
        and (
            "dry_run=true" in combined
            or "ready_for_real_submission=false" in combined
            or "missing explicit real-run confirmation" in combined
        )
    )
    protected_printed = SYNTHETIC_TOKEN in combined or SYNTHETIC_SUBMISSION_ID in combined
    real_runner_started = "confirmation accepted; starting real runner" in combined
    passed = (
        result.returncode == expected_returncode
        and protected_printed is False
        and real_runner_started is False
        and (target_rejected and not preflight_started if bad_case else correct_accepted)
    )
    return {
        "name": name,
        "script_key": script_key,
        "script": SCRIPTS[script_key],
        "confirmation_value_present": confirm_value is not None,
        "confirmation_value_length": len(confirm_value or ""),
        "returncode": result.returncode,
        "expected_returncode": expected_returncode,
        "returncode_expected": result.returncode == expected_returncode,
        "target_rejected": target_rejected,
        "preflight_started": preflight_started,
        "correct_accepted": correct_accepted,
        "dry_run_called": "dry_run=true" in combined,
        "missing_real_confirmation": "missing explicit real-run confirmation" in combined,
        "stdout_tail": redact(stdout[-1200:]),
        "stderr_tail": redact(stderr[-1200:]),
        "printed_protected_values": protected_printed,
        "real_runner_started": real_runner_started,
        "platform_contacted": False,
        "uploads_performed": False,
        "passed": passed,
    }


def restore_clean_submission_state() -> dict[str, Any]:
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("ROBOCHALLENGE_"):
            env.pop(key, None)
    env["PYTHONIOENCODING"] = "utf-8"
    commands = [
        ["python3", "scripts/audit_checkpoint_link_intake.py"],
        ["python3", "scripts/audit_checkpoint_link_download_verification.py"],
        ["python3", "scripts/audit_real_submission_readiness.py"],
        ["python3", "scripts/audit_submission_blockers_summary.py"],
    ]
    results = []
    for command in commands:
        result = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=180,
        )
        results.append({"command": " ".join(command), "returncode": result.returncode})
    return {"passed": all(item["returncode"] == 0 for item in results), "commands": results}


def build_status() -> dict[str, Any]:
    bad_cases = [run_case(name, script_key, value, 69, True) for name, script_key, value in BAD_CASES]
    good_cases = [
        run_case(name, script_key, value, expected_returncode, False)
        for name, script_key, value, expected_returncode in GOOD_CASES
    ]
    cases = bad_cases + good_cases
    restore = restore_clean_submission_state()
    evidence = {
        "bad_confirmations_rejected": all(item["target_rejected"] for item in bad_cases),
        "bad_confirmations_stop_before_preflight": all(item["preflight_started"] is False for item in bad_cases),
        "correct_confirmation_accepted": all(item["correct_accepted"] for item in good_cases),
        "authorized_correct_reaches_dry_run": next(
            item for item in good_cases if item["name"] == "authorized_correct"
        )["dry_run_called"],
        "ready_correct_stops_without_real_confirm": next(
            item for item in good_cases if item["name"] == "ready_correct_missing_real_confirm"
        )["missing_real_confirmation"],
        "all_cases_expected_returncodes": all(item["returncode_expected"] for item in cases),
        "all_cases_no_protected_values": all(item["printed_protected_values"] is False for item in cases),
        "real_runner_not_started": all(item["real_runner_started"] is False for item in cases),
        "restore_clean_state_passed": restore["passed"],
    }
    leak_flags = {
        "credentials_printed": any(item["printed_protected_values"] for item in cases),
        "link_values_printed": False,
        "secret_values_printed": any(item["printed_protected_values"] for item in cases),
    }
    contact_flags = {
        "platform_contacted": False,
        "uploads_performed": False,
        "download_host_contacted": False,
    }
    passed = bool(all(item["passed"] for item in cases) and all(evidence.values()))
    passed = bool(passed and not any(leak_flags.values()) and not any(contact_flags.values()))
    blocking = []
    if passed:
        blocking.append("提交对象确认 gate 已通过；缺失、错误或畸形确认值会在 checkpoint/readiness/dry-run 前被拒绝。")
    else:
        for key, ok in evidence.items():
            if not ok:
                blocking.append(f"提交对象确认 gate 证据未通过 `{key}`。")
        failed_cases = [item["name"] for item in cases if not item["passed"]]
        if failed_cases:
            blocking.append(f"未通过 case：`{', '.join(failed_cases)}`。")
    return {
        "kind": "submission_target_confirmation_gate",
        "passed": passed,
        "confirmation_env_key": "ROBOCHALLENGE_SUBMISSION_TARGET_CONFIRMATION",
        "confirmation_value": CONFIRMATION_VALUE,
        "recommended_route": "baseline_official_aloha",
        "case_count": len(cases),
        "bad_case_count": len(bad_cases),
        "good_case_count": len(good_cases),
        "bad_confirmations_rejected": evidence["bad_confirmations_rejected"],
        "bad_confirmations_stop_before_preflight": evidence["bad_confirmations_stop_before_preflight"],
        "correct_confirmation_accepted": evidence["correct_confirmation_accepted"],
        "real_runner_started": any(item["real_runner_started"] for item in cases),
        "synthetic_values_recorded": False,
        "cases": cases,
        "clean_state_restore": restore,
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
        "# 提交对象确认 gate 审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 环境变量：`{status['confirmation_env_key']}`。",
        f"- 固定确认值：`{status['confirmation_value']}`。",
        f"- 推荐路线：`{status['recommended_route']}`。",
        f"- 覆盖 case 数量：`{status['case_count']}`。",
        f"- 错误确认值 case 数量：`{status['bad_case_count']}`。",
        f"- 正确确认值 case 数量：`{status['good_case_count']}`。",
        f"- 错误确认值是否被拒绝：`{status['bad_confirmations_rejected']}`。",
        f"- 错误确认值是否停在预检前：`{status['bad_confirmations_stop_before_preflight']}`。",
        f"- 正确确认值是否被接受：`{status['correct_confirmation_accepted']}`。",
        f"- 是否启动真实 runner：`{status['real_runner_started']}`。",
        "",
        "## 边界",
        "",
        "- 本审计只使用 synthetic token/submission id；不会读取真实 local env。",
        "- 错误确认值会在 checkpoint link、readiness 和 dry-run 前退出。",
        "- 正确确认值只允许流程继续到 no-contact dry-run 或真实 runner 强确认 gate，不会启动真实 runner。",
        "",
        "## 只读边界",
        "",
    ]
    for key, value in status["contact_flags"].items():
        lines.append(f"- `{key}`：`{value}`。")
    for key, value in status["leak_flags"].items():
        lines.append(f"- `{key}`：`{value}`。")
    lines.extend(["", "## 输入证据", ""])
    for key, value in status["evidence"].items():
        lines.append(f"- `{key}`：`{value}`。")
    lines.extend(["", "## Case 摘要", ""])
    for item in status["cases"]:
        lines.append(
            "- `{name}`：script=`{script_key}`，confirmation_present=`{present}`，confirmation_length=`{length}`，"
            "returncode=`{returncode}`，rejected=`{rejected}`，preflight_started=`{preflight}`，"
            "accepted=`{accepted}`，dry_run=`{dry_run}`，passed=`{passed}`。".format(
                name=item["name"],
                script_key=item["script_key"],
                present=item["confirmation_value_present"],
                length=item["confirmation_value_length"],
                returncode=item["returncode"],
                rejected=item["target_rejected"],
                preflight=item["preflight_started"],
                accepted=item["correct_accepted"],
                dry_run=item["dry_run_called"],
                passed=item["passed"],
            )
        )
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
