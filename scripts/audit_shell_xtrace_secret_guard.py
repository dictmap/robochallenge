#!/usr/bin/env python3
"""Audit bash xtrace guard for submission wrappers without real credentials."""

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
DEFAULT_STATUS = RUNS_DIR / "shell_xtrace_secret_guard.json"
DEFAULT_REPORT = REPORTS_DIR / "shell_xtrace_secret_guard.md"

SYNTHETIC_TOKEN = "synthetic_xtrace_token_value_0001"
SYNTHETIC_SUBMISSION_ID = "synthetic_xtrace_submission_id_0001"
REDACTION = "[REDACTED_SYNTHETIC_VALUE]"

WRAPPERS = {
    "baseline_demo": "submission/run_table30v2_aloha_demo_template.sh",
    "lora_demo": "submission/run_table30v2_aloha_lora_demo_template.sh",
    "authorized_preflight": "submission/run_authorized_preflight_template.sh",
    "ready_real_runner": "submission/run_ready_real_submission_template.sh",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计 bash -x 场景下提交 wrapper 是否会泄漏凭据。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文报告输出路径。")
    return parser.parse_args()


def clean_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("ROBOCHALLENGE_"):
            env.pop(key, None)
    env["PYTHONIOENCODING"] = "utf-8"
    env["ROBOCHALLENGE_ENV_FILE"] = str(ROOT / "submission" / "__missing_env_for_xtrace_audit__.sh")
    env["ROBOCHALLENGE_USER_TOKEN"] = SYNTHETIC_TOKEN
    env["ROBOCHALLENGE_SUBMISSION_ID"] = SYNTHETIC_SUBMISSION_ID
    env["ROBOCHALLENGE_SUBMISSION_VARIANT"] = "baseline"
    env["ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD"] = "0"
    if extra:
        env.update(extra)
    return env


def redact(text: str) -> str:
    redacted = text
    for value in [SYNTHETIC_TOKEN, SYNTHETIC_SUBMISSION_ID]:
        redacted = redacted.replace(value, REDACTION)
    return redacted


def first_effective_command(path: Path) -> str:
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        stripped = line.strip()
        if index == 0 and stripped.startswith("#!"):
            continue
        if not stripped or stripped.startswith("#"):
            continue
        return stripped
    return ""


def run_case(name: str, script: str) -> dict[str, Any]:
    extra: dict[str, str] = {}
    expected_returncodes = [0]
    if name in {"baseline_demo", "lora_demo"}:
        extra["ROBOCHALLENGE_DRY_RUN"] = "1"
    elif name == "authorized_preflight":
        extra["ROBOCHALLENGE_REQUIRE_READY"] = "0"
    elif name == "ready_real_runner":
        expected_returncodes = [1]

    result = subprocess.run(
        ["bash", "-x", script],
        cwd=ROOT,
        env=clean_env(extra),
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
    protected_printed = SYNTHETIC_TOKEN in combined or SYNTHETIC_SUBMISSION_ID in combined
    trace_lines = [line for line in stderr.splitlines() if line.startswith("+ ")]
    unexpected_trace_lines = [line for line in trace_lines if line.strip() != "+ set +x"]
    return {
        "name": name,
        "script": script,
        "returncode": result.returncode,
        "expected_returncodes": expected_returncodes,
        "returncode_expected": result.returncode in expected_returncodes,
        "stdout_tail": redact(stdout[-1200:]),
        "stderr_tail": redact(stderr[-1200:]),
        "set_plus_x_trace_seen": any(line.strip() == "+ set +x" for line in trace_lines),
        "unexpected_trace_after_guard": bool(unexpected_trace_lines),
        "unexpected_trace_line_count": len(unexpected_trace_lines),
        "printed_protected_values": protected_printed,
        "leaked_value_count": int(SYNTHETIC_TOKEN in combined) + int(SYNTHETIC_SUBMISSION_ID in combined),
        "dry_run_called": "dry_run=true" in combined,
        "lengths_only_output": (
            protected_printed is False
            and f"user_token_length={len(SYNTHETIC_TOKEN)}" in combined
            and f"submission_id_length={len(SYNTHETIC_SUBMISSION_ID)}" in combined
        ),
        "ready_false": "ready_for_real_submission=false" in combined,
        "missing_confirmation": "missing explicit real-run confirmation" in combined,
        "stops_before_real_runner": "stop before real runner" in combined or "stop before dry-run and real runner" in combined,
        "real_runner_started": "confirmation accepted; starting real runner" in combined,
        "platform_contacted": False,
        "uploads_performed": False,
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
    wrapper_paths = {name: ROOT / rel for name, rel in WRAPPERS.items()}
    first_commands = {name: first_effective_command(path) if path.exists() else "" for name, path in wrapper_paths.items()}
    templates_disable_xtrace = {name: command == "set +x" for name, command in first_commands.items()}
    cases = [run_case(name, rel) for name, rel in WRAPPERS.items()]
    case_map = {item["name"]: item for item in cases}
    restore = restore_clean_submission_state()
    demo_cases = [case_map["baseline_demo"], case_map["lora_demo"]]
    evidence = {
        "all_templates_disable_xtrace_first": all(templates_disable_xtrace.values()),
        "all_cases_saw_set_plus_x_trace": all(item["set_plus_x_trace_seen"] for item in cases),
        "all_cases_stop_trace_after_guard": all(item["unexpected_trace_after_guard"] is False for item in cases),
        "all_cases_no_protected_values": all(item["printed_protected_values"] is False for item in cases),
        "demo_dry_runs_passed": all(item["returncode"] == 0 and item["dry_run_called"] for item in demo_cases),
        "demo_outputs_lengths_only": all(item["lengths_only_output"] for item in demo_cases),
        "authorized_preflight_passed": case_map["authorized_preflight"]["returncode"] == 0,
        "ready_runner_stops_before_real_runner": (
            case_map["ready_real_runner"]["returncode"] != 0
            and case_map["ready_real_runner"]["real_runner_started"] is False
            and (
                case_map["ready_real_runner"]["ready_false"]
                or case_map["ready_real_runner"]["missing_confirmation"]
                or case_map["ready_real_runner"]["stops_before_real_runner"]
            )
        ),
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
    passed = bool(all(evidence.values()) and not any(leak_flags.values()) and not any(contact_flags.values()))
    blocking = []
    if passed:
        blocking.append("bash -x 防泄漏审计已通过；四个提交入口都会先关闭 xtrace，合成凭据未出现在日志中。")
    else:
        for key, ok in evidence.items():
            if not ok:
                blocking.append(f"bash -x 防泄漏证据未通过 `{key}`。")
        if any(leak_flags.values()):
            blocking.append("bash -x 输出包含受保护的合成凭据值，必须先修复。")

    return {
        "kind": "shell_xtrace_secret_guard",
        "passed": passed,
        "recommended_route": "baseline_official_aloha",
        "case_count": len(cases),
        "synthetic_values_recorded": False,
        "synthetic_token_length": len(SYNTHETIC_TOKEN),
        "synthetic_submission_id_length": len(SYNTHETIC_SUBMISSION_ID),
        "templates_disable_xtrace": templates_disable_xtrace,
        "first_effective_commands": first_commands,
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
        "# bash xtrace 防泄漏审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 推荐路线：`{status['recommended_route']}`。",
        f"- 覆盖入口数量：`{status['case_count']}`。",
        f"- 是否记录 synthetic 明文：`{status['synthetic_values_recorded']}`。",
        f"- 是否连接平台：`{status['platform_contacted']}`。",
        f"- 是否上传：`{status['uploads_performed']}`。",
        "",
        "## xtrace 入口防护",
        "",
    ]
    for name, ok in status["templates_disable_xtrace"].items():
        lines.append(f"- `{name}`：首条有效命令为 `set +x` -> `{ok}`。")
    lines.extend(["", "## bash -x smoke", ""])
    for item in status["cases"]:
        lines.append(
            f"- `{item['name']}` / `{item['script']}`：returncode=`{item['returncode']}`，"
            f"set_plus_x_trace_seen=`{item['set_plus_x_trace_seen']}`，"
            f"unexpected_trace_after_guard=`{item['unexpected_trace_after_guard']}`，"
            f"printed_protected_values=`{item['printed_protected_values']}`，"
            f"real_runner_started=`{item['real_runner_started']}`。"
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
