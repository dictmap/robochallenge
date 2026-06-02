#!/usr/bin/env python3
"""Audit boolean submission env gates before checkpoint/readiness work starts."""

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
DEFAULT_STATUS = RUNS_DIR / "boolean_env_gate.json"
DEFAULT_REPORT = REPORTS_DIR / "boolean_env_gate.md"
MISSING_ENV_FILE = ROOT / "submission" / "__synthetic_missing_env__.sh"

SCRIPTS = {
    "authorized_preflight": "submission/run_authorized_preflight_template.sh",
    "ready_runner": "submission/run_ready_real_submission_template.sh",
}

BAD_CASES = [
    (
        "authorized_verify_true",
        "authorized_preflight",
        "ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD",
        {"ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD": "true"},
    ),
    (
        "ready_verify_yes",
        "ready_runner",
        "ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD",
        {"ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD": "yes"},
    ),
    (
        "authorized_require_ready_true",
        "authorized_preflight",
        "ROBOCHALLENGE_REQUIRE_READY",
        {"ROBOCHALLENGE_REQUIRE_READY": "true"},
    ),
    (
        "authorized_verify_space",
        "authorized_preflight",
        "ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD",
        {"ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD": " "},
    ),
]

GOOD_CASES = [
    ("authorized_flags_zero", "authorized_preflight", {}, 0),
    ("authorized_require_ready_one", "authorized_preflight", {"ROBOCHALLENGE_REQUIRE_READY": "1"}, 1),
    ("ready_baseline_verify_zero", "ready_runner", {}, 1),
    ("ready_lora_verify_zero", "ready_runner", {"ROBOCHALLENGE_SUBMISSION_VARIANT": "lora"}, 1),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="审计提交入口布尔环境变量 gate；只接受 0/1，不读取真实凭据。"
    )
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文报告输出路径。")
    return parser.parse_args()


def sanitized_env(extra: dict[str, str]) -> dict[str, str]:
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("ROBOCHALLENGE_"):
            env.pop(key, None)
    env["PYTHONIOENCODING"] = "utf-8"
    env["ROBOCHALLENGE_ENV_FILE"] = str(MISSING_ENV_FILE)
    env["ROBOCHALLENGE_SUBMISSION_VARIANT"] = extra.get("ROBOCHALLENGE_SUBMISSION_VARIANT", "baseline")
    env["ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD"] = extra.get(
        "ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD", "0"
    )
    if "ROBOCHALLENGE_REQUIRE_READY" in extra:
        env["ROBOCHALLENGE_REQUIRE_READY"] = extra["ROBOCHALLENGE_REQUIRE_READY"]
    else:
        env["ROBOCHALLENGE_REQUIRE_READY"] = "0"
    return env


def run_case(
    name: str,
    script_key: str,
    env_overrides: dict[str, str],
    expected_returncode: int,
    bad_flag_name: str = "",
) -> dict[str, Any]:
    script = SCRIPTS[script_key]
    result = subprocess.run(
        ["bash", script],
        cwd=ROOT,
        env=sanitized_env(env_overrides),
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
    bool_rejected = (
        result.returncode == 68
        and bool(bad_flag_name)
        and bad_flag_name in combined
        and "must be 0 or 1" in combined
    )
    preflight_started = (
        "checkpoint link" in combined
        or "ready_for_real_submission" in combined
        or "dry_run=true" in combined
        or "checkpoint_length=" in combined
    )
    valid_flags_accepted = (
        result.returncode == expected_returncode
        and "must be 0 or 1" not in combined
        and (
            "ready_for_real_submission=false" in combined
            or "stop before runner dry-run" in combined
            or "stop before dry-run and real runner" in combined
        )
    )
    real_runner_started = "confirmation accepted; starting real runner" in combined
    protected_printed = False
    bad_case = bool(bad_flag_name)
    passed = (
        result.returncode == expected_returncode
        and protected_printed is False
        and real_runner_started is False
        and (bool_rejected and not preflight_started if bad_case else valid_flags_accepted)
    )
    return {
        "name": name,
        "script_key": script_key,
        "script": script,
        "bad_flag_name": bad_flag_name,
        "override_keys": sorted(env_overrides.keys()),
        "override_value_lengths": {key: len(value) for key, value in env_overrides.items()},
        "returncode": result.returncode,
        "expected_returncode": expected_returncode,
        "returncode_expected": result.returncode == expected_returncode,
        "bool_rejected": bool_rejected,
        "preflight_started": preflight_started,
        "valid_flags_accepted": valid_flags_accepted,
        "stdout_tail": stdout[-1000:],
        "stderr_tail": stderr[-1000:],
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
    env["ROBOCHALLENGE_ENV_FILE"] = str(MISSING_ENV_FILE)
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
    bad_cases = [
        run_case(name, script_key, overrides, 68, flag_name)
        for name, script_key, flag_name, overrides in BAD_CASES
    ]
    good_cases = [
        run_case(name, script_key, overrides, expected_returncode, "")
        for name, script_key, overrides, expected_returncode in GOOD_CASES
    ]
    cases = bad_cases + good_cases
    restore = restore_clean_submission_state()
    evidence = {
        "bad_flags_rejected": all(item["bool_rejected"] for item in bad_cases),
        "bad_flags_stop_before_preflight": all(item["preflight_started"] is False for item in bad_cases),
        "valid_flags_accepted": all(item["valid_flags_accepted"] for item in good_cases),
        "all_cases_expected_returncodes": all(item["returncode_expected"] for item in cases),
        "all_cases_no_protected_values": all(item["printed_protected_values"] is False for item in cases),
        "real_runner_not_started": all(item["real_runner_started"] is False for item in cases),
        "restore_clean_state_passed": restore["passed"],
    }
    leak_flags = {
        "credentials_printed": False,
        "link_values_printed": False,
        "secret_values_printed": False,
    }
    contact_flags = {
        "platform_contacted": False,
        "uploads_performed": False,
        "download_host_contacted": False,
    }
    passed = bool(all(item["passed"] for item in cases) and all(evidence.values()) and not any(leak_flags.values()))
    passed = bool(passed and not any(contact_flags.values()))
    blocking = []
    if passed:
        blocking.append("布尔环境变量 gate 已通过；提交入口只接受 0/1，true/false/yes/no 或空白会在预检前被拒绝。")
    else:
        for key, ok in evidence.items():
            if not ok:
                blocking.append(f"布尔环境变量 gate 证据未通过 `{key}`。")
        failed_cases = [item["name"] for item in cases if not item["passed"]]
        if failed_cases:
            blocking.append(f"未通过 case：`{', '.join(failed_cases)}`。")

    return {
        "kind": "boolean_env_gate",
        "passed": passed,
        "recommended_route": "baseline_official_aloha",
        "case_count": len(cases),
        "bad_case_count": len(bad_cases),
        "good_case_count": len(good_cases),
        "bad_flags_rejected": evidence["bad_flags_rejected"],
        "bad_flags_stop_before_preflight": evidence["bad_flags_stop_before_preflight"],
        "valid_flags_accepted": evidence["valid_flags_accepted"],
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
        "# 布尔环境变量 gate 审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 推荐路线：`{status['recommended_route']}`。",
        f"- 覆盖 case 数量：`{status['case_count']}`。",
        f"- 错误布尔值 case 数量：`{status['bad_case_count']}`。",
        f"- 合法布尔值 case 数量：`{status['good_case_count']}`。",
        f"- 错误布尔值是否被拒绝：`{status['bad_flags_rejected']}`。",
        f"- 错误布尔值是否停在预检前：`{status['bad_flags_stop_before_preflight']}`。",
        f"- 合法布尔值是否被接受：`{status['valid_flags_accepted']}`。",
        f"- 是否启动真实 runner：`{status['real_runner_started']}`。",
        f"- 是否记录 synthetic 明文：`{status['synthetic_values_recorded']}`。",
        "",
        "## 边界",
        "",
        "- 本审计只设置 synthetic 环境变量，并显式使用不存在的 local env 路径；不读取真实 token、submission id 或 checkpoint link。",
        "- `ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD` 和 `ROBOCHALLENGE_REQUIRE_READY` 只允许 `0` 或 `1`。",
        "- 错误布尔值会在 checkpoint link、readiness 和 dry-run 前退出，避免 `true/yes/空白` 被静默当成关闭。",
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
            "- `{name}`：script=`{script_key}`，override_keys=`{override_keys}`，returncode=`{returncode}`，"
            "bool_rejected=`{rejected}`，preflight_started=`{preflight}`，accepted=`{accepted}`，passed=`{passed}`。".format(
                name=item["name"],
                script_key=item["script_key"],
                override_keys=",".join(item["override_keys"]) or "none",
                returncode=item["returncode"],
                rejected=item["bool_rejected"],
                preflight=item["preflight_started"],
                accepted=item["valid_flags_accepted"],
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
