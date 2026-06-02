#!/usr/bin/env python3
"""Render the final no-contact handoff packet for the baseline route."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = ROOT / "runs"
DEFAULT_STATUS = RUNS_DIR / "baseline_final_handoff_packet.json"
DEFAULT_REPORT = REPORTS_DIR / "baseline_final_handoff_packet.md"

LOCAL_ENV_REL = "submission/robochallenge_env.local.sh"
CREDENTIAL_HYGIENE_COMMAND = "python3 scripts/render_baseline_credential_hygiene.py"
AUTHORIZED_PREFLIGHT_COMMAND = (
    "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_authorized_preflight_template.sh"
)
DRY_RUN_GATE_COMMAND = (
    "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_ready_real_submission_template.sh"
)
REAL_RUNNER_COMMAND = (
    "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline "
    "ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION "
    "bash submission/run_ready_real_submission_template.sh"
)

BASELINE_REQUIRED_IDS = {
    "SUBMISSION_TARGET_CONFIRMATION",
    "ROBOCHALLENGE_USER_TOKEN",
    "ROBOCHALLENGE_SUBMISSION_ID",
    "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline",
    "ROBOCHALLENGE_REAL_RUN_CONFIRM",
}
LORA_ONLY_IDS = {"CHECKPOINT_ARCHIVE_AUTHORIZATION", "ROBOCHALLENGE_CHECKPOINT_LINK"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成 baseline 最终交接包；不读取凭据、不联网、不上传。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文报告输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def ids(items: list[dict[str, Any]] | list[str]) -> set[str]:
    output: set[str] = set()
    for item in items:
        value = item.get("id") if isinstance(item, dict) else item
        if value:
            output.add(str(value))
    return output


def command_by_step(commands: list[dict[str, Any]], step: int) -> str:
    for item in commands:
        if item.get("step") == step:
            return str(item.get("command", ""))
    return ""


def build_commands() -> list[dict[str, Any]]:
    return [
        {
            "step": 1,
            "name": "凭据卫生检查",
            "command": CREDENTIAL_HYGIENE_COMMAND,
            "no_contact": True,
            "requires_user_credentials": False,
            "starts_real_runner": False,
        },
        {
            "step": 2,
            "name": "baseline 授权前只读预检",
            "command": AUTHORIZED_PREFLIGHT_COMMAND,
            "no_contact": True,
            "requires_user_credentials": True,
            "starts_real_runner": False,
        },
        {
            "step": 3,
            "name": "baseline dry-run gate",
            "command": DRY_RUN_GATE_COMMAND,
            "no_contact": True,
            "requires_user_credentials": True,
            "starts_real_runner": False,
        },
        {
            "step": 4,
            "name": "真实 runner 强确认入口",
            "command": REAL_RUNNER_COMMAND,
            "no_contact": False,
            "requires_user_credentials": True,
            "requires_real_run_confirmation": True,
            "starts_real_runner": True,
        },
    ]


def no_leak(items: list[dict[str, Any]], key: str) -> bool:
    return not any(bool(item.get(key)) for item in items)


def no_contact(items: list[dict[str, Any]], key: str) -> bool:
    return not any(bool(item.get(key) or item.get("upload_performed")) for item in items)


def build_status() -> dict[str, Any]:
    route_packet = read_json(RUNS_DIR / "submission_variant_route_packet.json")
    quickstart = read_json(RUNS_DIR / "baseline_submission_quickstart.json")
    dry_run_gate = read_json(RUNS_DIR / "baseline_dry_run_gate.json")
    credential_hygiene = read_json(RUNS_DIR / "baseline_credential_hygiene.json")
    local_env_smoke = read_json(RUNS_DIR / "baseline_local_env_smoke.json")
    authorized_execution = read_json(RUNS_DIR / "authorized_execution_checklist.json")
    action_packet = read_json(RUNS_DIR / "next_user_action_packet.json")
    route_aware = read_json(RUNS_DIR / "route_aware_submission_blockers.json")
    secret_scan = read_json(RUNS_DIR / "plaintext_secret_scan.json")

    inputs = [
        route_packet,
        quickstart,
        dry_run_gate,
        credential_hygiene,
        local_env_smoke,
        authorized_execution,
        action_packet,
        route_aware,
        secret_scan,
    ]
    commands = build_commands()
    command_strings = [item["command"] for item in commands]
    no_contact_prefix = commands[:3]
    real_runner_step = commands[3]

    quickstart_commands = quickstart.get("commands", [])
    baseline_blocking = ids(route_aware.get("baseline_current_blocking", []))
    lora_blocking = ids(route_aware.get("lora_web_current_blocking", []))
    authorized_ids = ids(authorized_execution.get("required_user_decisions", []))
    action_ids = ids(action_packet.get("required_user_decisions", []))
    credential_required_ids = ids(credential_hygiene.get("baseline_required_ids", []))
    dry_run_required_ids = ids(dry_run_gate.get("baseline_required_ids", []))
    local_env_authorized = local_env_smoke.get("authorized_preflight", {})
    local_env_ready = local_env_smoke.get("ready_runner", {})

    evidence = {
        "route_packet_passed": route_packet.get("passed") is True,
        "route_packet_recommends_baseline": route_packet.get("recommended_default") == "baseline_official_aloha",
        "quickstart_passed": quickstart.get("passed") is True,
        "quickstart_command_2_exact": command_by_step(quickstart_commands, 2) == AUTHORIZED_PREFLIGHT_COMMAND,
        "quickstart_command_3_exact": command_by_step(quickstart_commands, 3) == DRY_RUN_GATE_COMMAND,
        "quickstart_command_4_exact": command_by_step(quickstart_commands, 4) == REAL_RUNNER_COMMAND,
        "dry_run_gate_passed": dry_run_gate.get("passed") is True,
        "dry_run_gate_command_exact": dry_run_gate.get("dry_run_gate_command") == DRY_RUN_GATE_COMMAND,
        "dry_run_gate_real_command_exact": dry_run_gate.get("real_runner_command") == REAL_RUNNER_COMMAND,
        "dry_run_gate_stops_before_real_runner": dry_run_gate.get(
            "stops_before_real_runner_without_confirmation"
        )
        is True,
        "credential_hygiene_passed": credential_hygiene.get("passed") is True,
        "credential_hygiene_local_env_gitignored": credential_hygiene.get("local_env_gitignored") is True,
        "credential_hygiene_local_env_not_tracked": credential_hygiene.get("local_env_tracked") is False,
        "credential_hygiene_does_not_read_local_env": credential_hygiene.get("local_env_content_read") is False,
        "local_env_smoke_passed": local_env_smoke.get("passed") is True,
        "local_env_smoke_values_not_recorded": local_env_smoke.get("synthetic_values_recorded") is False,
        "local_env_smoke_temp_env_removed": local_env_smoke.get("synthetic_env_file_removed_after_run") is True,
        "local_env_smoke_authorized_preflight_baseline": local_env_authorized.get("variant_baseline") is True,
        "local_env_smoke_ready_runner_stops": local_env_ready.get("stops_before_real_runner") is True,
        "authorized_execution_passed": authorized_execution.get("passed") is True,
        "authorized_execution_required_ids_complete": BASELINE_REQUIRED_IDS.issubset(authorized_ids),
        "action_packet_passed": action_packet.get("passed") is True,
        "action_packet_required_ids_complete": BASELINE_REQUIRED_IDS.issubset(action_ids),
        "route_aware_passed": route_aware.get("passed") is True,
        "route_aware_recommends_baseline": route_aware.get("recommended_route") == "baseline_official_aloha",
        "route_aware_baseline_no_checkpoint_upload": route_aware.get("baseline_requires_checkpoint_upload") is False,
        "route_aware_baseline_no_checkpoint_link": route_aware.get("baseline_requires_checkpoint_link") is False,
        "route_aware_baseline_blocking_exact": baseline_blocking == BASELINE_REQUIRED_IDS,
        "route_aware_baseline_no_lora_ids": not bool(baseline_blocking & LORA_ONLY_IDS),
        "route_aware_lora_keeps_checkpoint_requirements": LORA_ONLY_IDS.issubset(lora_blocking),
        "credential_hygiene_required_ids_complete": BASELINE_REQUIRED_IDS.issubset(credential_required_ids),
        "dry_run_gate_required_ids_complete": BASELINE_REQUIRED_IDS.issubset(dry_run_required_ids),
        "secret_scan_clean": secret_scan.get("passed") is True and secret_scan.get("hit_count") == 0,
        "handoff_command_count": len(commands) == 4,
        "handoff_command_order_exact": command_strings
        == [
            CREDENTIAL_HYGIENE_COMMAND,
            AUTHORIZED_PREFLIGHT_COMMAND,
            DRY_RUN_GATE_COMMAND,
            REAL_RUNNER_COMMAND,
        ],
        "handoff_first_three_no_contact": all(item.get("no_contact") is True for item in no_contact_prefix),
        "handoff_real_runner_requires_confirmation": real_runner_step.get("requires_real_run_confirmation") is True
        and "RUN_REAL_ROBOCHALLENGE_SUBMISSION" in real_runner_step.get("command", ""),
    }
    leak_flags = {
        "credentials_printed": not no_leak(inputs, "credentials_printed"),
        "link_values_printed": not no_leak(inputs, "link_values_printed"),
        "secret_values_printed": not no_leak(inputs, "secret_values_printed"),
    }
    contact_flags = {
        "platform_contacted": not no_contact(inputs, "platform_contacted"),
        "uploads_performed": not no_contact(inputs, "uploads_performed"),
        "download_host_contacted": False,
    }
    passed = bool(all(evidence.values()) and not any(leak_flags.values()) and not any(contact_flags.values()))
    blocking = []
    if passed:
        blocking.append(
            "baseline 最终交接包已固化；拿到用户凭据后先跑前三个 no-contact 步骤，"
            "只有用户明确授权时才运行第四个真实 runner 强确认命令。"
        )
    else:
        for key, ok in evidence.items():
            if not ok:
                blocking.append(f"baseline final handoff 证据未通过 `{key}`。")
        if any(leak_flags.values()):
            blocking.append("输入审计显示存在凭据或链接明文泄露风险。")
        if any(contact_flags.values()):
            blocking.append("输入审计显示曾连接平台、上传或接触下载 host。")

    return {
        "kind": "baseline_final_handoff_packet",
        "passed": passed,
        "recommended_route": "baseline_official_aloha",
        "recommended_local_env": LOCAL_ENV_REL,
        "local_env_content_read": False,
        "requires_checkpoint_upload": False,
        "requires_checkpoint_link": False,
        "requires_checkpoint_archive_authorization": False,
        "baseline_current_blocking": sorted(baseline_blocking),
        "lora_only_ids": sorted(LORA_ONLY_IDS),
        "commands": commands,
        "command_count": len(commands),
        "no_contact_command_count": len(no_contact_prefix),
        "real_runner_command": REAL_RUNNER_COMMAND,
        "real_runner_requires_confirmation": True,
        "real_runner_command_starts_platform_submission": True,
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
        "# Baseline 最终交接包",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 推荐路线：`{status['recommended_route']}`。",
        f"- 建议本地凭据文件：`{status['recommended_local_env']}`。",
        f"- 是否读取 local env 内容：`{status['local_env_content_read']}`。",
        f"- baseline 是否需要 checkpoint upload：`{status['requires_checkpoint_upload']}`。",
        f"- baseline 是否需要 checkpoint link：`{status['requires_checkpoint_link']}`。",
        f"- baseline 是否需要 checkpoint 归档授权：`{status['requires_checkpoint_archive_authorization']}`。",
        f"- 前三步 no-contact 命令数量：`{status['no_contact_command_count']}`。",
        f"- 真实 runner 是否需要强确认：`{status['real_runner_requires_confirmation']}`。",
        "",
        "## 凭据后执行顺序",
        "",
    ]
    for item in status["commands"]:
        lines.append(f"{item['step']}. {item['name']}：`{item['command']}`")
        lines.append(
            "   - "
            f"no_contact=`{item.get('no_contact')}`；"
            f"requires_user_credentials=`{item.get('requires_user_credentials')}`；"
            f"starts_real_runner=`{item.get('starts_real_runner')}`。"
        )
    lines.extend(
        [
            "",
            "## 当前 baseline 只差",
            "",
        ]
    )
    for item in status["baseline_current_blocking"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## 边界",
            "",
            "- 本包没有读取真实 token、submission id 或 checkpoint link。",
            "- 前三条命令只用于卫生检查、只读预检和 dry-run gate；第四条命令会启动真实 runner，只能在用户明确授权后运行。",
            "- checkpoint 归档、上传和 checkpoint link 仍属于 LoRA/web checkpoint 路线，不是 baseline 官方 ALOHA 路线的前置条件。",
            "",
            "## 只读边界",
            "",
        ]
    )
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
