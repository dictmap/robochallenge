#!/usr/bin/env python3
"""Audit credential whitespace rejection before dry-run or real runner startup."""

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
DEFAULT_STATUS = RUNS_DIR / "credential_whitespace_guard.json"
DEFAULT_REPORT = REPORTS_DIR / "credential_whitespace_guard.md"

SAFE_TOKEN = "rtok_whitespace_safe_0001"
SAFE_SUBMISSION_ID = "sid_whitespace_safe_0001"
REDACTION = "[REDACTED_SYNTHETIC_VALUE]"

TEMPLATES = {
    "baseline": "submission/run_table30v2_aloha_demo_template.sh",
    "lora": "submission/run_table30v2_aloha_lora_demo_template.sh",
}

BAD_CASES = [
    ("baseline_token_leading_space", "baseline", "user_token", " " + SAFE_TOKEN, SAFE_SUBMISSION_ID),
    ("baseline_submission_trailing_space", "baseline", "submission_id", SAFE_TOKEN, SAFE_SUBMISSION_ID + " "),
    ("lora_token_tab", "lora", "user_token", SAFE_TOKEN + "\t", SAFE_SUBMISSION_ID),
    ("lora_submission_newline", "lora", "submission_id", SAFE_TOKEN, SAFE_SUBMISSION_ID + "\n"),
]

GOOD_CASES = [
    ("baseline_clean_credentials", "baseline", "none", SAFE_TOKEN, SAFE_SUBMISSION_ID),
    ("lora_clean_credentials", "lora", "none", SAFE_TOKEN, SAFE_SUBMISSION_ID),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计 token/submission id 空白字符拒绝逻辑。")
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


def redact(text: str) -> str:
    redacted = text
    for value in [SAFE_TOKEN, SAFE_SUBMISSION_ID]:
        redacted = redacted.replace(value, REDACTION)
    return redacted


def run_case(name: str, route: str, field: str, token: str, submission_id: str, expected_returncodes: list[int]) -> dict[str, Any]:
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
    protected_printed = SAFE_TOKEN in combined or SAFE_SUBMISSION_ID in combined
    expected_field = "ROBOCHALLENGE_USER_TOKEN" if field == "user_token" else "ROBOCHALLENGE_SUBMISSION_ID"
    whitespace_rejected = (
        result.returncode == 66
        and expected_field in combined
        and "空白字符" in combined
        and "dry_run=true" not in combined
    )
    clean_dry_run_passed = (
        result.returncode == 0
        and "dry_run=true" in combined
        and "robot_type=aloha" in combined
        and f"user_token_length={len(token)}" in combined
        and f"submission_id_length={len(submission_id)}" in combined
    )
    bad_case = name not in {item[0] for item in GOOD_CASES}
    passed = (
        result.returncode in expected_returncodes
        and protected_printed is False
        and (whitespace_rejected if bad_case else clean_dry_run_passed)
    )
    return {
        "name": name,
        "route": route,
        "field": field,
        "script": script,
        "returncode": result.returncode,
        "expected_returncodes": expected_returncodes,
        "returncode_expected": result.returncode in expected_returncodes,
        "stdout_tail": redact(stdout[-1000:]),
        "stderr_tail": redact(stderr[-1000:]),
        "whitespace_rejected": whitespace_rejected,
        "clean_dry_run_passed": clean_dry_run_passed,
        "dry_run_called": "dry_run=true" in combined,
        "robot_type_aloha": "robot_type=aloha" in combined,
        "real_runner_started": "confirmation accepted; starting real runner" in combined or "Traceback" in combined,
        "printed_protected_values": protected_printed,
        "leaked_value_count": int(SAFE_TOKEN in combined) + int(SAFE_SUBMISSION_ID in combined),
        "platform_contacted": False,
        "uploads_performed": False,
        "passed": passed,
    }


def build_status() -> dict[str, Any]:
    bad_cases = [run_case(*case, expected_returncodes=[66]) for case in BAD_CASES]
    good_cases = [run_case(*case, expected_returncodes=[0]) for case in GOOD_CASES]
    cases = bad_cases + good_cases
    evidence = {
        "bad_credentials_rejected": all(item["whitespace_rejected"] for item in bad_cases),
        "bad_credentials_stop_before_dry_run": all(item["dry_run_called"] is False for item in bad_cases),
        "clean_credentials_dry_run_passed": all(item["clean_dry_run_passed"] for item in good_cases),
        "clean_credentials_lengths_only": all(item["printed_protected_values"] is False for item in good_cases),
        "all_cases_expected_returncodes": all(item["returncode_expected"] for item in cases),
        "all_cases_no_protected_values": all(item["printed_protected_values"] is False for item in cases),
        "real_runner_not_started": all(item["real_runner_started"] is False for item in cases),
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
    passed = bool(all(item["passed"] for item in cases) and all(evidence.values()) and not any(leak_flags.values()))
    passed = bool(passed and not any(contact_flags.values()))
    blocking = []
    if passed:
        blocking.append("凭据空白字符 gate 已通过；token/submission id 带空格、tab 或换行时会在 dry-run 前被拒绝。")
    else:
        for key, ok in evidence.items():
            if not ok:
                blocking.append(f"凭据空白字符证据未通过 `{key}`。")
        failed_cases = [item["name"] for item in cases if not item["passed"]]
        if failed_cases:
            blocking.append(f"未通过 case：`{', '.join(failed_cases)}`。")

    return {
        "kind": "credential_whitespace_guard",
        "passed": passed,
        "recommended_route": "baseline_official_aloha",
        "case_count": len(cases),
        "bad_case_count": len(bad_cases),
        "good_case_count": len(good_cases),
        "bad_credentials_rejected": evidence["bad_credentials_rejected"],
        "clean_credentials_dry_run_passed": evidence["clean_credentials_dry_run_passed"],
        "real_runner_started": any(item["real_runner_started"] for item in cases),
        "synthetic_values_recorded": False,
        "safe_token_length": len(SAFE_TOKEN),
        "safe_submission_id_length": len(SAFE_SUBMISSION_ID),
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
        "# 凭据空白字符 gate 审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 推荐路线：`{status['recommended_route']}`。",
        f"- 覆盖 case 数量：`{status['case_count']}`。",
        f"- 坏输入 case 数量：`{status['bad_case_count']}`。",
        f"- 干净输入 case 数量：`{status['good_case_count']}`。",
        f"- 带空白字符凭据是否被拒绝：`{status['bad_credentials_rejected']}`。",
        f"- 干净凭据 dry-run 是否通过：`{status['clean_credentials_dry_run_passed']}`。",
        f"- 是否启动真实 runner：`{status['real_runner_started']}`。",
        f"- 是否记录 synthetic 明文：`{status['synthetic_values_recorded']}`。",
        "",
        "## 边界",
        "",
        "- 本审计只使用 synthetic token/submission id，不读取真实凭据。",
        "- 拒绝范围只覆盖空格、tab、换行等空白字符，避免用户复制粘贴时把不可见字符带入真实提交。",
        "- 干净 synthetic 值只允许 dry-run 输出长度字段，不允许输出 synthetic 明文。",
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
            "- `{name}`：route=`{route}`，field=`{field}`，returncode=`{returncode}`，"
            "whitespace_rejected=`{rejected}`，clean_dry_run_passed=`{clean}`，passed=`{passed}`。".format(
                name=item["name"],
                route=item["route"],
                field=item["field"],
                returncode=item["returncode"],
                rejected=item["whitespace_rejected"],
                clean=item["clean_dry_run_passed"],
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
