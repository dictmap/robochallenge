#!/usr/bin/env python3
"""Smoke-test real-submission readiness gate scenarios without contacting the platform."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = ROOT / "runs"
DEFAULT_STATUS = RUNS_DIR / "real_submission_readiness_scenarios.json"
DEFAULT_REPORT = REPORTS_DIR / "real_submission_readiness_scenarios.md"

ENV_KEYS = [
    "ROBOCHALLENGE_USER_TOKEN",
    "ROBOCHALLENGE_SUBMISSION_ID",
    "ROBOCHALLENGE_CHECKPOINT_LINK",
    "ROBOCHALLENGE_LORA_CHECKPOINT_LINK",
]

SYNTHETIC_ENV = {
    "ROBOCHALLENGE_USER_TOKEN": "synthetic-readiness-token",
    "ROBOCHALLENGE_SUBMISSION_ID": "synthetic-readiness-submission",
    "ROBOCHALLENGE_LORA_CHECKPOINT_LINK": "https://example.invalid/robochallenge/checkpoint.tar",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="离线验证真实提交 readiness gate 的场景翻转逻辑。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文审计报告输出路径。")
    return parser.parse_args()


def run_gate(name: str, env_updates: dict[str, str]) -> dict[str, Any]:
    env = os.environ.copy()
    for key in ENV_KEYS:
        env.pop(key, None)
    env.update(env_updates)

    with tempfile.TemporaryDirectory(prefix=f"robochallenge_readiness_{name}_") as tmp:
        tmp_dir = Path(tmp)
        status_path = tmp_dir / "status.json"
        report_path = tmp_dir / "report.md"
        result = subprocess.run(
            [
                "python3",
                "scripts/audit_real_submission_readiness.py",
                "--status-path",
                str(status_path),
                "--report-path",
                str(report_path),
            ],
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
        status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.exists() else {}
        combined_output = "\n".join(
            [
                result.stdout,
                result.stderr,
                status_path.read_text(encoding="utf-8") if status_path.exists() else "",
                report_path.read_text(encoding="utf-8") if report_path.exists() else "",
            ]
        )
        leaked_values = [key for key, value in env_updates.items() if value and value in combined_output]
        return {
            "returncode": result.returncode,
            "gate_passed_field": status.get("passed"),
            "ready_for_real_submission": status.get("ready_for_real_submission"),
            "web_form_ready": status.get("web_form_ready"),
            "local_baseline_runner_ready": status.get("local_baseline_runner_ready"),
            "local_lora_runner_ready": status.get("local_lora_runner_ready"),
            "platform_contacted": status.get("platform_contacted"),
            "credentials_printed": status.get("credentials_printed"),
            "value_leak_detected": bool(leaked_values),
            "leaked_value_keys": leaked_values,
            "env_presence": {key: status.get("env", {}).get(key, {}).get("present") for key in ENV_KEYS},
            "url_flags": {key: status.get("env", {}).get(key, {}).get("looks_like_url") for key in ENV_KEYS},
            "blocking_count": len(status.get("blocking", [])),
        }


def build_status() -> dict[str, Any]:
    missing_env = run_gate("missing_env", {})
    synthetic_ready = run_gate("synthetic_ready", SYNTHETIC_ENV)

    missing_ok = all(
        [
            missing_env["returncode"] == 0,
            missing_env["gate_passed_field"] is True,
            missing_env["ready_for_real_submission"] is False,
            missing_env["web_form_ready"] is False,
            missing_env["local_baseline_runner_ready"] is False,
            missing_env["local_lora_runner_ready"] is False,
            missing_env["platform_contacted"] is False,
            missing_env["credentials_printed"] is False,
            missing_env["value_leak_detected"] is False,
        ]
    )
    synthetic_ok = all(
        [
            synthetic_ready["returncode"] == 0,
            synthetic_ready["gate_passed_field"] is True,
            synthetic_ready["ready_for_real_submission"] is True,
            synthetic_ready["web_form_ready"] is True,
            synthetic_ready["local_baseline_runner_ready"] is True,
            synthetic_ready["local_lora_runner_ready"] is True,
            synthetic_ready["platform_contacted"] is False,
            synthetic_ready["credentials_printed"] is False,
            synthetic_ready["value_leak_detected"] is False,
        ]
    )

    return {
        "kind": "real_submission_readiness_scenarios",
        "passed": missing_ok and synthetic_ok,
        "platform_contacted": False,
        "credentials_printed": False,
        "synthetic_values_recorded": False,
        "scenarios": {
            "missing_env_expected_blocked": missing_env,
            "synthetic_env_expected_ready_shape": synthetic_ready,
        },
        "expectations": {
            "missing_env_expected_blocked": missing_ok,
            "synthetic_env_expected_ready_shape": synthetic_ok,
        },
        "blocking": [
            "本审计只验证 readiness gate 的布尔逻辑翻转；synthetic ready 不代表真实提交完成。",
            "真实提交仍需要用户提供真实 token、submission id 和可访问 checkpoint link。",
        ],
    }


def write_report(status: dict[str, Any], path: Path) -> None:
    lines = [
        "# 真实提交 readiness 场景 smoke",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 是否连接 RoboChallenge 平台：`{status['platform_contacted']}`。",
        f"- 是否打印凭据：`{status['credentials_printed']}`。",
        f"- 是否记录 synthetic 明文值：`{status['synthetic_values_recorded']}`。",
        "- synthetic ready 只用于验证 gate 逻辑，不代表真实提交完成。",
        "",
        "## 场景",
        "",
    ]
    for name, scenario in status["scenarios"].items():
        lines.extend(
            [
                f"### {name}",
                "",
                f"- returncode：`{scenario['returncode']}`。",
                f"- ready_for_real_submission：`{scenario['ready_for_real_submission']}`。",
                f"- web_form_ready：`{scenario['web_form_ready']}`。",
                f"- local_baseline_runner_ready：`{scenario['local_baseline_runner_ready']}`。",
                f"- local_lora_runner_ready：`{scenario['local_lora_runner_ready']}`。",
                f"- platform_contacted：`{scenario['platform_contacted']}`。",
                f"- credentials_printed：`{scenario['credentials_printed']}`。",
                f"- value_leak_detected：`{scenario['value_leak_detected']}`。",
                "",
            ]
        )
    lines.extend(["## Blocking", ""])
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
