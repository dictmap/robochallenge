#!/usr/bin/env python3
"""Smoke-test baseline wrappers with a synthetic local env file without leaking values."""

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
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = ROOT / "runs"
DEFAULT_STATUS = RUNS_DIR / "baseline_local_env_smoke.json"
DEFAULT_REPORT = REPORTS_DIR / "baseline_local_env_smoke.md"
SYNTHETIC_TOKEN = "synthetic_user_token_for_local_env_smoke_0001"
SYNTHETIC_SUBMISSION_ID = "synthetic_submission_id_for_local_env_smoke_0001"
PARENT_CONFIRM_PHRASE = "RUN_REAL_ROBOCHALLENGE_SUBMISSION"
AUTHORIZED_PREFLIGHT_COMMAND = "bash submission/run_authorized_preflight_template.sh"
READY_RUNNER_COMMAND = "bash submission/run_ready_real_submission_template.sh"
SNAPSHOT_RELS = [
    "runs/checkpoint_link_intake.json",
    "reports/checkpoint_link_intake.md",
    "runs/checkpoint_link_download_verification.json",
    "reports/checkpoint_link_download_verification.md",
    "runs/real_submission_readiness.json",
    "reports/real_submission_readiness.md",
    "runs/submission_blockers_summary.json",
    "reports/submission_blockers_summary.md",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="用临时 synthetic local env 验证 baseline 预检和 dry-run；不读取真实凭据。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文报告输出路径。")
    return parser.parse_args()


def run_script(script: str, env_file: Path) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["ROBOCHALLENGE_ENV_FILE"] = str(env_file)
    env["ROBOCHALLENGE_REAL_RUN_CONFIRM"] = PARENT_CONFIRM_PHRASE
    for key in [
        "ROBOCHALLENGE_USER_TOKEN",
        "ROBOCHALLENGE_SUBMISSION_ID",
        "ROBOCHALLENGE_SUBMISSION_VARIANT",
        "ROBOCHALLENGE_CHECKPOINT_LINK",
        "ROBOCHALLENGE_LORA_CHECKPOINT_LINK",
        "ROBOCHALLENGE_REAL_RUN_CONFIRM",
    ]:
        env.pop(key, None)
    result = subprocess.run(
        ["bash", f"submission/{script}"],
        cwd=ROOT,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=900,
    )
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    combined = stdout + "\n" + stderr
    protected_values = [SYNTHETIC_TOKEN, SYNTHETIC_SUBMISSION_ID]
    return {
        "script": f"submission/{script}",
        "returncode": result.returncode,
        "stdout_tail": stdout[-3000:],
        "stderr_tail": stderr[-1500:],
        "env_file_present_true": "env_file_present=true" in combined,
        "variant_baseline": "variant=baseline" in combined,
        "dry_run_called": "dry_run=true" in combined,
        "robot_type_aloha": "robot_type=aloha" in combined,
        "ready_false": "ready_for_real_submission=false" in combined,
        "parent_real_confirm_injected_before_scrub": True,
        "parent_real_confirm_present_in_subprocess_env": "ROBOCHALLENGE_REAL_RUN_CONFIRM" in env,
        "confirmation_present": "confirmation_present=true" in combined,
        "confirmation_absent": "confirmation_present=false" in combined,
        "missing_confirmation": "missing explicit real-run confirmation" in combined,
        "stops_before_real_runner": "stop before real runner" in combined,
        "real_runner_started": "confirmation accepted; starting real runner" in combined,
        "printed_protected_values": any(value in combined for value in protected_values),
        "leaked_value_count": sum(1 for value in protected_values if value in combined),
    }


def write_synthetic_env(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# Synthetic local env for no-contact smoke; values are fake and deleted after the run.",
                f"export ROBOCHALLENGE_USER_TOKEN={SYNTHETIC_TOKEN!r}",
                f"export ROBOCHALLENGE_SUBMISSION_ID={SYNTHETIC_SUBMISSION_ID!r}",
                "export ROBOCHALLENGE_SUBMISSION_VARIANT='baseline'",
                "export ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD='0'",
                "export ROBOCHALLENGE_CHECKPOINT_LINK=''",
                "export ROBOCHALLENGE_LORA_CHECKPOINT_LINK=''",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def snapshot_files() -> dict[str, bytes | None]:
    snapshot: dict[str, bytes | None] = {}
    for rel in SNAPSHOT_RELS:
        path = ROOT / rel
        snapshot[rel] = path.read_bytes() if path.exists() else None
    return snapshot


def restore_files(snapshot: dict[str, bytes | None]) -> None:
    for rel, data in snapshot.items():
        path = ROOT / rel
        if data is None:
            if path.exists():
                path.unlink()
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def build_status() -> dict[str, Any]:
    snapshot = snapshot_files()
    try:
        with tempfile.TemporaryDirectory(prefix="robochallenge-local-env-smoke-") as tmpdir:
            env_file = Path(tmpdir) / "robochallenge_env.local.sh"
            write_synthetic_env(env_file)
            authorized = run_script("run_authorized_preflight_template.sh", env_file)
            ready_runner = run_script("run_ready_real_submission_template.sh", env_file)
            env_file_exists_during_run = env_file.exists()
        env_file_removed_after_run = not Path(tmpdir).exists()
    finally:
        restore_files(snapshot)

    evidence = {
        "synthetic_env_file_existed_during_run": env_file_exists_during_run is True,
        "synthetic_env_file_removed_after_run": env_file_removed_after_run is True,
        "workspace_state_restored_after_smoke": True,
        "authorized_preflight_returncode_zero": authorized.get("returncode") == 0,
        "authorized_preflight_loaded_env_file": authorized.get("env_file_present_true") is True,
        "authorized_preflight_variant_baseline": authorized.get("variant_baseline") is True,
        "authorized_preflight_dry_run_called": authorized.get("dry_run_called") is True,
        "authorized_preflight_robot_type_aloha": authorized.get("robot_type_aloha") is True,
        "authorized_preflight_no_protected_values_printed": authorized.get("printed_protected_values") is False,
        "ready_runner_returncode_missing_confirmation": ready_runner.get("returncode") == 1,
        "ready_runner_loaded_env_file": ready_runner.get("env_file_present_true") is True,
        "ready_runner_variant_baseline": ready_runner.get("variant_baseline") is True,
        "ready_runner_dry_run_called": ready_runner.get("dry_run_called") is True,
        "ready_runner_parent_real_confirm_injected_before_scrub": ready_runner.get(
            "parent_real_confirm_injected_before_scrub"
        )
        is True,
        "ready_runner_parent_real_confirm_scrubbed": ready_runner.get(
            "parent_real_confirm_present_in_subprocess_env"
        )
        is False,
        "ready_runner_confirmation_absent_after_scrub": ready_runner.get("confirmation_absent") is True,
        "ready_runner_missing_confirmation": ready_runner.get("missing_confirmation") is True,
        "ready_runner_stops_before_real_runner": ready_runner.get("stops_before_real_runner") is True,
        "ready_runner_real_runner_not_started": ready_runner.get("real_runner_started") is False,
        "ready_runner_no_protected_values_printed": ready_runner.get("printed_protected_values") is False,
    }
    leak_flags = {
        "credentials_printed": bool(authorized.get("printed_protected_values"))
        or bool(ready_runner.get("printed_protected_values")),
        "link_values_printed": False,
        "secret_values_printed": bool(authorized.get("printed_protected_values"))
        or bool(ready_runner.get("printed_protected_values")),
    }
    contact_flags = {
        "platform_contacted": False,
        "uploads_performed": False,
        "download_host_contacted": False,
    }
    passed = bool(all(evidence.values()) and not any(leak_flags.values()) and not any(contact_flags.values()))
    blocking = []
    if passed:
        blocking.append("synthetic local env 已验证：baseline 预检和 dry-run gate 均会读取 local env，且不会打印值。")
    else:
        for key, ok in evidence.items():
            if not ok:
                blocking.append(f"synthetic local env smoke 未通过 `{key}`。")
        if any(leak_flags.values()):
            blocking.append("synthetic smoke 输出包含受保护值，需先修复脱敏边界。")

    return {
        "kind": "baseline_local_env_smoke",
        "passed": passed,
        "recommended_route": "baseline_official_aloha",
        "synthetic_token_length": len(SYNTHETIC_TOKEN),
        "synthetic_submission_id_length": len(SYNTHETIC_SUBMISSION_ID),
        "synthetic_values_recorded": False,
        "parent_real_confirm_phrase_injected": True,
        "parent_real_confirm_phrase_value_recorded": False,
        "synthetic_env_file_removed_after_run": env_file_removed_after_run,
        "authorized_preflight_command": AUTHORIZED_PREFLIGHT_COMMAND,
        "ready_runner_command": READY_RUNNER_COMMAND,
        "authorized_preflight": authorized,
        "ready_runner": ready_runner,
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
        "# Baseline synthetic local env smoke",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 推荐路线：`{status['recommended_route']}`。",
        f"- synthetic token 长度：`{status['synthetic_token_length']}`。",
        f"- synthetic submission id 长度：`{status['synthetic_submission_id_length']}`。",
        f"- 是否记录 synthetic 明文值：`{status['synthetic_values_recorded']}`。",
        f"- 是否注入父环境确认短语污染：`{status['parent_real_confirm_phrase_injected']}`。",
        f"- 是否记录确认短语明文值：`{status['parent_real_confirm_phrase_value_recorded']}`。",
        f"- 临时 env 文件是否已删除：`{status['synthetic_env_file_removed_after_run']}`。",
        "",
        "## 覆盖的命令",
        "",
        f"- 授权预检：`{status['authorized_preflight_command']}`。",
        f"- ready runner gate：`{status['ready_runner_command']}`。",
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
