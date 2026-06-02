#!/usr/bin/env python3
"""Verify synthetic credential dry-runs print lengths only and start no runner."""

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
DEFAULT_STATUS = RUNS_DIR / "synthetic_dry_run_redaction.json"
DEFAULT_REPORT = REPORTS_DIR / "synthetic_dry_run_redaction.md"

SYNTHETIC_TOKEN = "synthetic_user_token_shape_value_0001"
SYNTHETIC_SUBMISSION_ID = "synthetic_submission_id_shape_value_0001"

TEMPLATES = {
    "baseline": "submission/run_table30v2_aloha_demo_template.sh",
    "lora": "submission/run_table30v2_aloha_lora_demo_template.sh",
}

EXPECTED_OUTPUT_KEYS = [
    "dry_run=true",
    "checkpoint_length=",
    "prompt_length=",
    "user_token_length=",
    "submission_id_length=",
    "robot_type=aloha",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="验证 synthetic dry-run 只输出长度，不打印凭据明文。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文报告输出路径。")
    return parser.parse_args()


def sanitized_env() -> dict[str, str]:
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("ROBOCHALLENGE_"):
            env.pop(key, None)
    env["PYTHONIOENCODING"] = "utf-8"
    env["ROBOCHALLENGE_USER_TOKEN"] = SYNTHETIC_TOKEN
    env["ROBOCHALLENGE_SUBMISSION_ID"] = SYNTHETIC_SUBMISSION_ID
    env["ROBOCHALLENGE_DRY_RUN"] = "1"
    return env


def run_case(route: str) -> dict[str, Any]:
    script = TEMPLATES[route]
    result = subprocess.run(
        ["bash", script],
        cwd=ROOT,
        env=sanitized_env(),
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
    expected_keys = {key: key in combined for key in EXPECTED_OUTPUT_KEYS}
    protected_values = [SYNTHETIC_TOKEN, SYNTHETIC_SUBMISSION_ID]
    printed_protected = any(value in combined for value in protected_values)
    return {
        "route": route,
        "script": script,
        "returncode": result.returncode,
        "stdout_tail": stdout[-1000:],
        "stderr_tail": stderr[-1000:],
        "expected_keys": expected_keys,
        "dry_run_passed": result.returncode == 0 and all(expected_keys.values()),
        "reported_user_token_length": f"user_token_length={len(SYNTHETIC_TOKEN)}" in combined,
        "reported_submission_id_length": f"submission_id_length={len(SYNTHETIC_SUBMISSION_ID)}" in combined,
        "outputs_lengths_only": (
            printed_protected is False
            and f"user_token_length={len(SYNTHETIC_TOKEN)}" in combined
            and f"submission_id_length={len(SYNTHETIC_SUBMISSION_ID)}" in combined
        ),
        "real_runner_started": "confirmation accepted; starting real runner" in combined or "Traceback" in combined,
        "printed_protected_values": printed_protected,
        "leaked_value_count": sum(1 for value in protected_values if value in combined),
    }


def build_status() -> dict[str, Any]:
    cases = [run_case("baseline"), run_case("lora")]
    case_map = {item["route"]: item for item in cases}
    evidence = {
        "baseline_dry_run_passed": case_map["baseline"].get("dry_run_passed") is True,
        "lora_dry_run_passed": case_map["lora"].get("dry_run_passed") is True,
        "baseline_outputs_lengths_only": case_map["baseline"].get("outputs_lengths_only") is True,
        "lora_outputs_lengths_only": case_map["lora"].get("outputs_lengths_only") is True,
        "baseline_real_runner_not_started": case_map["baseline"].get("real_runner_started") is False,
        "lora_real_runner_not_started": case_map["lora"].get("real_runner_started") is False,
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
        blocking.append("synthetic dry-run 已验证只输出长度字段，不打印 token/submission id 明文。")
    else:
        for key, ok in evidence.items():
            if not ok:
                blocking.append(f"synthetic dry-run 脱敏证据未通过 `{key}`。")
        if any(leak_flags.values()):
            blocking.append("synthetic dry-run 输出包含受保护假值，需先修复脱敏边界。")

    return {
        "kind": "synthetic_dry_run_redaction",
        "passed": passed,
        "recommended_route": "baseline_official_aloha",
        "case_count": len(cases),
        "baseline_dry_run_passed": evidence["baseline_dry_run_passed"],
        "lora_dry_run_passed": evidence["lora_dry_run_passed"],
        "baseline_outputs_lengths_only": evidence["baseline_outputs_lengths_only"],
        "lora_outputs_lengths_only": evidence["lora_outputs_lengths_only"],
        "baseline_real_runner_not_started": evidence["baseline_real_runner_not_started"],
        "lora_real_runner_not_started": evidence["lora_real_runner_not_started"],
        "synthetic_token_length": len(SYNTHETIC_TOKEN),
        "synthetic_submission_id_length": len(SYNTHETIC_SUBMISSION_ID),
        "synthetic_values_recorded": False,
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
        "# Synthetic dry-run 脱敏审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 推荐路线：`{status['recommended_route']}`。",
        f"- baseline dry-run 是否通过：`{status['baseline_dry_run_passed']}`。",
        f"- LoRA dry-run 是否通过：`{status['lora_dry_run_passed']}`。",
        f"- baseline 是否只输出长度：`{status['baseline_outputs_lengths_only']}`。",
        f"- LoRA 是否只输出长度：`{status['lora_outputs_lengths_only']}`。",
        f"- baseline 是否未启动真实 runner：`{status['baseline_real_runner_not_started']}`。",
        f"- LoRA 是否未启动真实 runner：`{status['lora_real_runner_not_started']}`。",
        f"- 是否记录 synthetic 明文：`{status['synthetic_values_recorded']}`。",
        "",
        "## 覆盖的命令",
        "",
    ]
    for item in status["cases"]:
        lines.append(
            f"- `{item['script']}`：returncode=`{item['returncode']}`，"
            f"dry_run_passed=`{item['dry_run_passed']}`，"
            f"outputs_lengths_only=`{item['outputs_lengths_only']}`。"
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
