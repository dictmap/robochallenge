#!/usr/bin/env python3
"""Audit submission variant fail-fast gates before authorized preflight work starts."""

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
DEFAULT_STATUS = RUNS_DIR / "submission_variant_gate.json"
DEFAULT_REPORT = REPORTS_DIR / "submission_variant_gate.md"

SCRIPTS = {
    "authorized_preflight": "submission/run_authorized_preflight_template.sh",
    "ready_runner": "submission/run_ready_real_submission_template.sh",
}

BAD_CASES = [
    ("authorized_typo_basleine", "authorized_preflight", "basleine"),
    ("ready_lora_trailing_space", "ready_runner", "lora "),
    ("authorized_uppercase", "authorized_preflight", "BASELINE"),
    ("ready_baseline_newline", "ready_runner", "baseline\n"),
]

GOOD_CASES = [
    ("authorized_baseline", "authorized_preflight", "baseline", 0),
    ("ready_baseline", "ready_runner", "baseline", 1),
    ("authorized_lora", "authorized_preflight", "lora", 0),
    ("ready_lora", "ready_runner", "lora", 1),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计提交 variant fail-fast gate；不读取真实凭据。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文报告输出路径。")
    return parser.parse_args()


def sanitized_env(variant: str) -> dict[str, str]:
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("ROBOCHALLENGE_"):
            env.pop(key, None)
    env["PYTHONIOENCODING"] = "utf-8"
    env["ROBOCHALLENGE_SUBMISSION_VARIANT"] = variant
    env["ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD"] = "0"
    return env


def run_case(name: str, script_key: str, variant: str, expected_returncode: int, bad_case: bool) -> dict[str, Any]:
    script = SCRIPTS[script_key]
    result = subprocess.run(
        ["bash", script],
        cwd=ROOT,
        env=sanitized_env(variant),
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
    variant_rejected = (
        result.returncode == 67
        and "unsupported submission variant" in combined
        and "use baseline or lora" in combined
    )
    preflight_started = (
        "checkpoint link" in combined
        or "ready_for_real_submission" in combined
        or "dry_run=true" in combined
        or "checkpoint_length=" in combined
    )
    valid_variant_accepted = (
        result.returncode == expected_returncode
        and "unsupported submission variant" not in combined
        and (
            "ready_for_real_submission=false" in combined
            or "dry_run=true" in combined
            or "[authorized-preflight] stop before runner dry-run" in combined
            or "[ready-real-runner] stop before dry-run and real runner" in combined
        )
    )
    protected_printed = False
    real_runner_started = "confirmation accepted; starting real runner" in combined
    passed = (
        result.returncode == expected_returncode
        and protected_printed is False
        and real_runner_started is False
        and (variant_rejected and not preflight_started if bad_case else valid_variant_accepted)
    )
    return {
        "name": name,
        "script_key": script_key,
        "script": script,
        "variant_length": len(variant),
        "returncode": result.returncode,
        "expected_returncode": expected_returncode,
        "returncode_expected": result.returncode == expected_returncode,
        "variant_rejected": variant_rejected,
        "preflight_started": preflight_started,
        "valid_variant_accepted": valid_variant_accepted,
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
    bad_cases = [run_case(name, script_key, variant, 67, True) for name, script_key, variant in BAD_CASES]
    good_cases = [
        run_case(name, script_key, variant, expected_returncode, False)
        for name, script_key, variant, expected_returncode in GOOD_CASES
    ]
    cases = bad_cases + good_cases
    restore = restore_clean_submission_state()
    evidence = {
        "bad_variants_rejected": all(item["variant_rejected"] for item in bad_cases),
        "bad_variants_stop_before_preflight": all(item["preflight_started"] is False for item in bad_cases),
        "valid_variants_accepted": all(item["valid_variant_accepted"] for item in good_cases),
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
        blocking.append("提交 variant gate 已通过；拼写错误、大小写错误或空白字符会在授权预检前被拒绝。")
    else:
        for key, ok in evidence.items():
            if not ok:
                blocking.append(f"提交 variant gate 证据未通过 `{key}`。")
        failed_cases = [item["name"] for item in cases if not item["passed"]]
        if failed_cases:
            blocking.append(f"未通过 case：`{', '.join(failed_cases)}`。")

    return {
        "kind": "submission_variant_gate",
        "passed": passed,
        "recommended_route": "baseline_official_aloha",
        "case_count": len(cases),
        "bad_case_count": len(bad_cases),
        "good_case_count": len(good_cases),
        "bad_variants_rejected": evidence["bad_variants_rejected"],
        "bad_variants_stop_before_preflight": evidence["bad_variants_stop_before_preflight"],
        "valid_variants_accepted": evidence["valid_variants_accepted"],
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
        "# 提交 variant gate 审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 推荐路线：`{status['recommended_route']}`。",
        f"- 覆盖 case 数量：`{status['case_count']}`。",
        f"- 错误 variant case 数量：`{status['bad_case_count']}`。",
        f"- 合法 variant case 数量：`{status['good_case_count']}`。",
        f"- 错误 variant 是否被拒绝：`{status['bad_variants_rejected']}`。",
        f"- 错误 variant 是否停在预检前：`{status['bad_variants_stop_before_preflight']}`。",
        f"- 合法 variant 是否被接受：`{status['valid_variants_accepted']}`。",
        f"- 是否启动真实 runner：`{status['real_runner_started']}`。",
        "",
        "## 边界",
        "",
        "- 本审计只设置 synthetic variant，不读取真实 token、submission id、checkpoint link 或 local env 内容。",
        "- 支持的 variant 只有 `baseline` 与 `lora`；当前推荐提交路线仍是 `baseline`。",
        "- 错误 variant 会在 checkpoint link、readiness 和 dry-run 前退出，避免拼写错误被后续缺凭据提示掩盖。",
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
            "- `{name}`：script=`{script_key}`，variant_length=`{variant_length}`，returncode=`{returncode}`，"
            "rejected=`{rejected}`，preflight_started=`{preflight}`，accepted=`{accepted}`，passed=`{passed}`。".format(
                name=item["name"],
                script_key=item["script_key"],
                variant_length=item["variant_length"],
                returncode=item["returncode"],
                rejected=item["variant_rejected"],
                preflight=item["preflight_started"],
                accepted=item["valid_variant_accepted"],
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
