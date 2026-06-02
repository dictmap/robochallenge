#!/usr/bin/env python3
"""Audit local env runtime permission gates before shell wrappers source secrets."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
DEFAULT_STATUS = RUNS_DIR / "local_env_runtime_permission_gate.json"
DEFAULT_REPORT = REPORTS_DIR / "local_env_runtime_permission_gate.md"

SYNTHETIC_TOKEN = "synthetic_runtime_gate_token_0001"
SYNTHETIC_SUBMISSION_ID = "synthetic_runtime_gate_submission_0001"
REDACTION = "[REDACTED_SYNTHETIC_VALUE]"

CASES = [
    {
        "name": "authorized_bad_permissions",
        "script": "submission/run_authorized_preflight_template.sh",
        "mode": 0o644,
        "expected_returncodes": [65],
        "must_reject_permissions": True,
    },
    {
        "name": "ready_bad_permissions",
        "script": "submission/run_ready_real_submission_template.sh",
        "mode": 0o644,
        "expected_returncodes": [65],
        "must_reject_permissions": True,
    },
    {
        "name": "authorized_owner_only",
        "script": "submission/run_authorized_preflight_template.sh",
        "mode": 0o600,
        "expected_returncodes": [0],
        "must_reject_permissions": False,
    },
    {
        "name": "ready_owner_only",
        "script": "submission/run_ready_real_submission_template.sh",
        "mode": 0o600,
        "expected_returncodes": [1],
        "must_reject_permissions": False,
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计 local env 运行时权限 gate；不读取真实凭据。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文报告输出路径。")
    return parser.parse_args()


def clean_env(env_file: Path) -> dict[str, str]:
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("ROBOCHALLENGE_"):
            env.pop(key, None)
    env["PYTHONIOENCODING"] = "utf-8"
    env["ROBOCHALLENGE_ENV_FILE"] = str(env_file)
    return env


def redact(text: str) -> str:
    redacted = text
    for value in [SYNTHETIC_TOKEN, SYNTHETIC_SUBMISSION_ID]:
        redacted = redacted.replace(value, REDACTION)
    return redacted


def write_synthetic_env(path: Path, mode: int) -> None:
    path.write_text(
        "\n".join(
            [
                "# synthetic runtime permission gate; no real values",
                f"export ROBOCHALLENGE_USER_TOKEN='{SYNTHETIC_TOKEN}'",
                f"export ROBOCHALLENGE_SUBMISSION_ID='{SYNTHETIC_SUBMISSION_ID}'",
                "export ROBOCHALLENGE_SUBMISSION_VARIANT='baseline'",
                "export ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD='0'",
                "",
            ]
        ),
        encoding="utf-8",
    )
    path.chmod(mode)


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="robochallenge-runtime-env-gate-") as tmpdir:
        env_file = Path(tmpdir) / "robochallenge_env.local.sh"
        write_synthetic_env(env_file, case["mode"])
        result = subprocess.run(
            ["bash", case["script"]],
            cwd=ROOT,
            env=clean_env(env_file),
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
        permission_rejected = (
            result.returncode == 65
            and "local env permissions are too broad" in combined
            and "chmod 600" in combined
        )
        permission_accepted = (
            result.returncode != 65
            and "local env permissions are too broad" not in combined
            and "chmod 600" not in combined
        )
        bad_case = bool(case["must_reject_permissions"])
        case_passed = (
            result.returncode in case["expected_returncodes"]
            and protected_printed is False
            and (permission_rejected if bad_case else permission_accepted)
        )
        payload = {
            "name": case["name"],
            "script": case["script"],
            "mode_octal": oct(case["mode"]),
            "returncode": result.returncode,
            "expected_returncodes": case["expected_returncodes"],
            "returncode_expected": result.returncode in case["expected_returncodes"],
            "permission_rejected": permission_rejected,
            "permission_accepted": permission_accepted,
            "stdout_tail": redact(stdout[-1200:]),
            "stderr_tail": redact(stderr[-1200:]),
            "printed_protected_values": protected_printed,
            "dry_run_called": "dry_run=true" in combined,
            "ready_false": "ready_for_real_submission=false" in combined,
            "missing_confirmation": "missing explicit real-run confirmation" in combined,
            "real_runner_started": "confirmation accepted; starting real runner" in combined,
            "platform_contacted": False,
            "uploads_performed": False,
            "passed": case_passed,
        }
    payload["synthetic_env_file_removed_after_case"] = not env_file.exists()
    return payload


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
    cases = [run_case(case) for case in CASES]
    case_map = {item["name"]: item for item in cases}
    restore = restore_clean_submission_state()
    bad_cases = [case_map["authorized_bad_permissions"], case_map["ready_bad_permissions"]]
    owner_only_cases = [case_map["authorized_owner_only"], case_map["ready_owner_only"]]
    evidence = {
        "bad_permissions_rejected": all(item["permission_rejected"] for item in bad_cases),
        "bad_permissions_stop_before_dry_run": all(item["dry_run_called"] is False for item in bad_cases),
        "bad_permissions_no_protected_values": all(item["printed_protected_values"] is False for item in bad_cases),
        "owner_only_permissions_accepted": all(item["permission_accepted"] for item in owner_only_cases),
        "owner_only_no_protected_values": all(item["printed_protected_values"] is False for item in owner_only_cases),
        "all_cases_expected_returncodes": all(item["returncode_expected"] for item in cases),
        "all_cases_temp_env_removed": all(item["synthetic_env_file_removed_after_case"] for item in cases),
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
    passed = bool(all(item["passed"] for item in cases) and all(evidence.values()) and not any(leak_flags.values()))
    passed = bool(passed and not any(contact_flags.values()))
    blocking = []
    if passed:
        blocking.append("local env 运行时权限 gate 已通过；权限过宽会在 source 前被拒绝，owner-only synthetic 文件可进入授权边界。")
    else:
        for key, ok in evidence.items():
            if not ok:
                blocking.append(f"local env runtime 权限证据未通过 `{key}`。")
        failed_cases = [item["name"] for item in cases if not item["passed"]]
        if failed_cases:
            blocking.append(f"未通过 case：`{', '.join(failed_cases)}`。")

    return {
        "kind": "local_env_runtime_permission_gate",
        "passed": passed,
        "recommended_route": "baseline_official_aloha",
        "case_count": len(cases),
        "synthetic_values_recorded": False,
        "synthetic_token_length": len(SYNTHETIC_TOKEN),
        "synthetic_submission_id_length": len(SYNTHETIC_SUBMISSION_ID),
        "bad_permissions_rejected": evidence["bad_permissions_rejected"],
        "owner_only_permissions_accepted": evidence["owner_only_permissions_accepted"],
        "content_read_before_permission_check": False,
        "real_runner_started": any(item["real_runner_started"] for item in cases),
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
        "# Local env runtime 权限 gate 审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 推荐路线：`{status['recommended_route']}`。",
        f"- 覆盖 case 数量：`{status['case_count']}`。",
        f"- 权限过宽是否拒绝：`{status['bad_permissions_rejected']}`。",
        f"- owner-only 权限是否放行：`{status['owner_only_permissions_accepted']}`。",
        f"- 是否在权限检查前读取内容：`{status['content_read_before_permission_check']}`。",
        f"- 是否启动真实 runner：`{status['real_runner_started']}`。",
        f"- 是否记录 synthetic 明文：`{status['synthetic_values_recorded']}`。",
        "",
        "## 边界",
        "",
        "- 本审计只使用临时 synthetic local env，不读取真实 `submission/robochallenge_env.local.sh` 内容。",
        "- `0644` 临时 env 必须在 `source` 前失败，并提示 `chmod 600`。",
        "- `0600` 临时 env 允许进入授权预检或 ready runner 的既有阻断边界，但不允许启动真实 runner。",
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
            "- `{name}`：mode=`{mode}`，returncode=`{returncode}`，"
            "permission_rejected=`{rejected}`，permission_accepted=`{accepted}`，passed=`{passed}`。".format(
                name=item["name"],
                mode=item["mode_octal"],
                returncode=item["returncode"],
                rejected=item["permission_rejected"],
                accepted=item["permission_accepted"],
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
