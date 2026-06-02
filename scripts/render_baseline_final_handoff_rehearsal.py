#!/usr/bin/env python3
"""Rehearse the first three baseline final-handoff commands with synthetic inputs."""

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
DEFAULT_STATUS = RUNS_DIR / "baseline_final_handoff_rehearsal.json"
DEFAULT_REPORT = REPORTS_DIR / "baseline_final_handoff_rehearsal.md"

SYNTHETIC_TOKEN = "synthetic_user_token_for_final_handoff_rehearsal_0001"
SYNTHETIC_SUBMISSION_ID = "synthetic_submission_id_for_final_handoff_rehearsal_0001"
PARENT_CONFIRM_PHRASE = "RUN_REAL_ROBOCHALLENGE_SUBMISSION"

EXPECTED_FIRST_THREE_COMMANDS = [
    "python3 scripts/render_baseline_credential_hygiene.py",
    "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_authorized_preflight_template.sh",
    "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_ready_real_submission_template.sh",
]

SNAPSHOT_RELS = [
    "runs/baseline_credential_hygiene.json",
    "reports/baseline_credential_hygiene.md",
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
    parser = argparse.ArgumentParser(
        description="按 baseline final handoff 的前三条 no-contact 命令做 synthetic 演练；不读真实凭据、不联网、不上传。"
    )
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文报告输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_synthetic_env(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# Synthetic local env for final-handoff rehearsal; fake values are deleted after the run.",
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
    path.chmod(0o600)


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


def snapshot_restored(snapshot: dict[str, bytes | None]) -> bool:
    for rel, data in snapshot.items():
        path = ROOT / rel
        if data is None:
            if path.exists():
                return False
            continue
        if not path.exists() or path.read_bytes() != data:
            return False
    return True


def scrub_env(env_file: Path) -> dict[str, str]:
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
        "ROBOCHALLENGE_ARCHIVE_CONFIRM",
    ]:
        env.pop(key, None)
    return env


def run_handoff_command(command: str, env_file: Path) -> dict[str, Any]:
    env = scrub_env(env_file)
    result = subprocess.run(
        ["bash", "-lc", command],
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
        "command": command,
        "returncode": result.returncode,
        "stdout_line_count": len(stdout.splitlines()),
        "stderr_line_count": len(stderr.splitlines()),
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


def commands_from_handoff(packet: dict[str, Any]) -> list[str]:
    ordered = sorted(packet.get("commands", []), key=lambda item: item.get("step", 0))
    return [str(item.get("command", "")) for item in ordered[:3]]


def no_contact_declared_for_first_three(packet: dict[str, Any]) -> bool:
    ordered = sorted(packet.get("commands", []), key=lambda item: item.get("step", 0))
    return len(ordered) >= 3 and all(item.get("no_contact") is True for item in ordered[:3])


def status_after_rehearsal() -> dict[str, Any]:
    generated = [
        read_json(RUNS_DIR / "baseline_credential_hygiene.json"),
        read_json(RUNS_DIR / "checkpoint_link_intake.json"),
        read_json(RUNS_DIR / "checkpoint_link_download_verification.json"),
        read_json(RUNS_DIR / "real_submission_readiness.json"),
        read_json(RUNS_DIR / "submission_blockers_summary.json"),
    ]
    download = generated[2]
    return {
        "baseline_credential_hygiene": generated[0],
        "download_host_contacted": bool(download.get("verification", {}).get("download_host_contacted")),
        "platform_contacted": any(bool(item.get("platform_contacted")) for item in generated),
        "uploads_performed": any(
            bool(item.get("uploads_performed") or item.get("upload_performed")) for item in generated
        ),
        "credentials_printed": any(bool(item.get("credentials_printed")) for item in generated),
        "link_values_printed": any(bool(item.get("link_values_printed")) for item in generated),
        "secret_values_printed": any(bool(item.get("secret_values_printed")) for item in generated),
    }


def build_status() -> dict[str, Any]:
    handoff_packet = read_json(RUNS_DIR / "baseline_final_handoff_packet.json")
    packet_first_three = commands_from_handoff(handoff_packet)
    snapshot = snapshot_files()
    commands: list[dict[str, Any]] = []
    generated_status: dict[str, Any] = {}
    env_file_exists_during_run = False
    env_file_removed_after_run = False
    restored = False

    try:
        with tempfile.TemporaryDirectory(prefix="robochallenge-handoff-rehearsal-") as tmpdir:
            tmp_path = Path(tmpdir)
            env_file = tmp_path / "robochallenge_env.local.sh"
            write_synthetic_env(env_file)
            for command in packet_first_three:
                commands.append(run_handoff_command(command, env_file))
            env_file_exists_during_run = env_file.exists()
            generated_status = status_after_rehearsal()
        env_file_removed_after_run = not tmp_path.exists()
    finally:
        restore_files(snapshot)
        restored = snapshot_restored(snapshot)

    step1 = commands[0] if len(commands) > 0 else {}
    step2 = commands[1] if len(commands) > 1 else {}
    step3 = commands[2] if len(commands) > 2 else {}
    credential_status = generated_status.get("baseline_credential_hygiene", {})

    evidence = {
        "handoff_packet_passed": handoff_packet.get("passed") is True,
        "handoff_first_three_commands_exact": packet_first_three == EXPECTED_FIRST_THREE_COMMANDS,
        "handoff_first_three_declared_no_contact": no_contact_declared_for_first_three(handoff_packet),
        "rehearsal_command_count": len(commands) == 3,
        "synthetic_env_file_existed_during_run": env_file_exists_during_run is True,
        "synthetic_env_file_removed_after_run": env_file_removed_after_run is True,
        "workspace_state_restored_after_rehearsal": restored is True,
        "step1_returncode_zero": step1.get("returncode") == 0,
        "step1_credential_hygiene_passed": credential_status.get("kind") == "baseline_credential_hygiene"
        and credential_status.get("passed") is True,
        "step1_no_protected_values_printed": step1.get("printed_protected_values") is False,
        "step2_returncode_zero": step2.get("returncode") == 0,
        "step2_loaded_env_file": step2.get("env_file_present_true") is True,
        "step2_variant_baseline": step2.get("variant_baseline") is True,
        "step2_dry_run_called": step2.get("dry_run_called") is True,
        "step2_robot_type_aloha": step2.get("robot_type_aloha") is True,
        "step2_no_protected_values_printed": step2.get("printed_protected_values") is False,
        "step3_returncode_missing_confirmation": step3.get("returncode") == 1,
        "step3_loaded_env_file": step3.get("env_file_present_true") is True,
        "step3_variant_baseline": step3.get("variant_baseline") is True,
        "step3_dry_run_called": step3.get("dry_run_called") is True,
        "step3_parent_real_confirm_injected_before_scrub": step3.get(
            "parent_real_confirm_injected_before_scrub"
        )
        is True,
        "step3_parent_real_confirm_scrubbed": step3.get("parent_real_confirm_present_in_subprocess_env") is False,
        "step3_confirmation_absent_after_scrub": step3.get("confirmation_absent") is True,
        "step3_missing_confirmation": step3.get("missing_confirmation") is True,
        "step3_stops_before_real_runner": step3.get("stops_before_real_runner") is True,
        "step3_real_runner_not_started": step3.get("real_runner_started") is False,
        "step3_no_protected_values_printed": step3.get("printed_protected_values") is False,
    }
    leak_flags = {
        "credentials_printed": bool(generated_status.get("credentials_printed"))
        or any(bool(command.get("printed_protected_values")) for command in commands),
        "link_values_printed": bool(generated_status.get("link_values_printed")),
        "secret_values_printed": bool(generated_status.get("secret_values_printed"))
        or any(bool(command.get("printed_protected_values")) for command in commands),
    }
    contact_flags = {
        "platform_contacted": bool(generated_status.get("platform_contacted")),
        "uploads_performed": bool(generated_status.get("uploads_performed")),
        "download_host_contacted": bool(generated_status.get("download_host_contacted")),
    }
    passed = bool(all(evidence.values()) and not any(leak_flags.values()) and not any(contact_flags.values()))
    blocking: list[str] = []
    if passed:
        blocking.append(
            "baseline final handoff 前三条命令已用 synthetic local env 按顺序演练；前三步不会启动真实 runner，"
            "第四步仍必须等待用户明确授权。"
        )
    else:
        for key, ok in evidence.items():
            if not ok:
                blocking.append(f"baseline final handoff rehearsal 未通过 `{key}`。")
        if any(leak_flags.values()):
            blocking.append("rehearsal 输出或上游产物存在凭据/链接/密文泄露风险。")
        if any(contact_flags.values()):
            blocking.append("rehearsal 检测到平台、上传或下载 host 接触风险。")

    return {
        "kind": "baseline_final_handoff_rehearsal",
        "passed": passed,
        "recommended_route": "baseline_official_aloha",
        "command_count": len(commands),
        "expected_first_three_commands": EXPECTED_FIRST_THREE_COMMANDS,
        "handoff_first_three_commands": packet_first_three,
        "commands": commands,
        "synthetic_token_length": len(SYNTHETIC_TOKEN),
        "synthetic_submission_id_length": len(SYNTHETIC_SUBMISSION_ID),
        "synthetic_values_recorded": False,
        "parent_real_confirm_phrase_injected": True,
        "parent_real_confirm_phrase_value_recorded": False,
        "synthetic_env_file_removed_after_run": env_file_removed_after_run,
        "workspace_state_restored_after_rehearsal": restored,
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
        "# Baseline final handoff 前三步演练",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 推荐路线：`{status['recommended_route']}`。",
        f"- 演练命令数：`{status['command_count']}`。",
        f"- synthetic token 长度：`{status['synthetic_token_length']}`。",
        f"- synthetic submission id 长度：`{status['synthetic_submission_id_length']}`。",
        f"- 是否记录 synthetic 明文值：`{status['synthetic_values_recorded']}`。",
        f"- 是否注入父环境确认短语污染：`{status['parent_real_confirm_phrase_injected']}`。",
        f"- 是否记录确认短语明文值：`{status['parent_real_confirm_phrase_value_recorded']}`。",
        f"- 临时 env 文件是否已删除：`{status['synthetic_env_file_removed_after_run']}`。",
        f"- 工作区状态是否已恢复：`{status['workspace_state_restored_after_rehearsal']}`。",
        "",
        "## 已演练命令",
        "",
    ]
    for index, command in enumerate(status["handoff_first_three_commands"], start=1):
        result = status["commands"][index - 1] if index - 1 < len(status["commands"]) else {}
        lines.append(f"{index}. `{command}`，返回码：`{result.get('returncode')}`。")
    lines.extend(["", "## 边界", ""])
    lines.append("- 本演练只使用临时 synthetic local env，不读取真实 token、submission id 或 checkpoint link。")
    lines.append("- 本演练会恢复 wrapper 刷新的 readiness/link/blockers 状态文件，只保留本 rehearsal 产物。")
    lines.append("- 第四条真实 runner 确认命令没有执行，仍必须等待用户明确授权。")
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
