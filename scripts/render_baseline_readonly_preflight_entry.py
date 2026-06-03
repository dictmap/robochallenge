#!/usr/bin/env python3
"""Render the first no-contact baseline preflight entry after user confirmation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
DEFAULT_STATUS = RUNS_DIR / "baseline_readonly_preflight_entry.json"
DEFAULT_REPORT = REPORTS_DIR / "baseline_readonly_preflight_entry.md"

TARGET_CONFIRMATION = "CONFIRM_TABLE30V2_ALOHA_BASELINE"
AUTHORIZED_PREFLIGHT_COMMAND = (
    "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_authorized_preflight_template.sh"
)
JUPYTER_LOCAL_ENV_ENTRY = "Notebook 第 44 节：RUN_SAFE_LOCAL_ENV_INPUT_TEMPLATE=True"
JUPYTER_AUTHORIZED_PREFLIGHT_ENTRY = "Notebook 第 45 节：RUN_AUTHORIZED_PREFLIGHT_TEMPLATE=True"
REQUIRED_FOR_READONLY_PREFLIGHT = [
    "SUBMISSION_TARGET_CONFIRMATION",
    "ROBOCHALLENGE_USER_TOKEN",
    "ROBOCHALLENGE_SUBMISSION_ID",
    "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline",
]
EXCLUDED_FROM_READONLY_PREFLIGHT = [
    "ROBOCHALLENGE_REAL_RUN_CONFIRM",
    "CHECKPOINT_ARCHIVE_AUTHORIZATION",
    "ROBOCHALLENGE_CHECKPOINT_LINK",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="生成 baseline 只读预检最短入口证据；不读凭据、不上传、不连接平台。"
    )
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文报告输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def command_by_step(packet: dict[str, Any], step: int) -> str:
    for item in packet.get("commands", []):
        if item.get("step") == step:
            return str(item.get("command", ""))
    return ""


def build_status() -> dict[str, Any]:
    quickstart = read_json(RUNS_DIR / "baseline_submission_quickstart.json")
    action_packet = read_json(RUNS_DIR / "next_user_action_packet.json")
    final_handoff = read_json(RUNS_DIR / "baseline_final_handoff_packet.json")
    jupyter_input = read_json(RUNS_DIR / "jupyter_input_template_audit.json")
    jupyter_authorized = read_json(RUNS_DIR / "jupyter_authorized_preflight_template_audit.json")
    target_confirmation = read_json(RUNS_DIR / "submission_target_confirmation_packet.json")
    route_aware = read_json(RUNS_DIR / "route_aware_submission_blockers.json")
    secret_scan = read_json(RUNS_DIR / "plaintext_secret_scan.json")

    final_commands = final_handoff.get("commands", [])
    final_second_command = final_commands[1].get("command") if len(final_commands) >= 2 else ""
    route_baseline_blocking = set(route_aware.get("baseline_current_blocking", []))
    action_baseline_blocking = set(action_packet.get("baseline_current_blocking", []))
    baseline_blocking = sorted(route_baseline_blocking or action_baseline_blocking)
    required = set(REQUIRED_FOR_READONLY_PREFLIGHT)
    excluded = set(EXCLUDED_FROM_READONLY_PREFLIGHT)
    target = target_confirmation.get("target", {})

    evidence = {
        "quickstart_passed": quickstart.get("passed") is True,
        "quickstart_command_2_exact": command_by_step(quickstart, 2) == AUTHORIZED_PREFLIGHT_COMMAND,
        "quickstart_recommends_baseline": quickstart.get("recommended_route") == "baseline_official_aloha",
        "quickstart_no_upload": quickstart.get("requires_checkpoint_upload") is False,
        "quickstart_no_link": quickstart.get("requires_checkpoint_link") is False,
        "action_packet_passed": action_packet.get("passed") is True,
        "action_packet_recommends_baseline": action_packet.get("recommended_route") == "baseline_official_aloha",
        "action_packet_target_confirmation_value_exact": action_packet.get("target_confirmation_value")
        == TARGET_CONFIRMATION,
        "action_packet_target_not_confirmed": action_packet.get("target_user_confirmed") is False,
        "final_handoff_passed": final_handoff.get("passed") is True,
        "final_handoff_second_command_exact": final_second_command == AUTHORIZED_PREFLIGHT_COMMAND,
        "final_handoff_first_three_no_contact": final_handoff.get("no_contact_command_count") == 3,
        "final_handoff_real_runner_requires_confirmation": final_handoff.get("real_runner_requires_confirmation")
        is True,
        "final_handoff_target_confirmation_value_exact": final_handoff.get("target_confirmation_value")
        == TARGET_CONFIRMATION,
        "final_handoff_target_not_confirmed": final_handoff.get("target_user_confirmed") is False,
        "jupyter_input_passed": jupyter_input.get("passed") is True,
        "jupyter_input_manual_target_confirmation": jupyter_input.get(
            "target_confirmation_manual_input_required"
        )
        is True,
        "jupyter_input_exact_target_confirmation": jupyter_input.get("target_confirmation_exact_match_required")
        is True,
        "jupyter_authorized_preflight_passed": jupyter_authorized.get("passed") is True,
        "target_confirmation_packet_passed": target_confirmation.get("passed") is True,
        "target_confirmation_value_exact": target_confirmation.get("recommended_confirmation_value")
        == TARGET_CONFIRMATION,
        "target_not_confirmed_for_user": target_confirmation.get("target_user_confirmed") is False,
        "target_does_not_confirm_for_user": target_confirmation.get("does_not_confirm_for_user") is True,
        "target_table30v2_aloha_task_exact": all(
            [
                target.get("benchmark") == "Table30v2",
                target.get("robot_type") == "aloha",
                target.get("task_name") == "pack_the_toothbrush_holder",
            ]
        ),
        "route_aware_passed": route_aware.get("passed") is True,
        "route_aware_recommends_baseline": route_aware.get("recommended_route") == "baseline_official_aloha",
        "route_aware_baseline_no_upload": route_aware.get("baseline_requires_checkpoint_upload") is False,
        "route_aware_baseline_no_link": route_aware.get("baseline_requires_checkpoint_link") is False,
        "route_aware_lora_web_keeps_upload": route_aware.get("lora_web_requires_checkpoint_upload") is True,
        "route_aware_lora_web_keeps_link": route_aware.get("lora_web_requires_checkpoint_link") is True,
        "readonly_required_ids_subset_current_blocking": required.issubset(route_baseline_blocking),
        "readonly_excluded_ids_not_required": required.isdisjoint(excluded),
        "real_runner_confirm_excluded_from_readonly_preflight": "ROBOCHALLENGE_REAL_RUN_CONFIRM" in excluded,
        "checkpoint_archive_auth_excluded_from_readonly_preflight": "CHECKPOINT_ARCHIVE_AUTHORIZATION" in excluded,
        "checkpoint_link_excluded_from_readonly_preflight": "ROBOCHALLENGE_CHECKPOINT_LINK" in excluded,
        "secret_scan_clean": secret_scan.get("passed") is True and secret_scan.get("hit_count") == 0,
    }

    leak_flags = {
        "credentials_printed": any(
            bool(item.get("credentials_printed"))
            for item in [
                quickstart,
                action_packet,
                final_handoff,
                jupyter_input,
                jupyter_authorized,
                target_confirmation,
                route_aware,
                secret_scan,
            ]
        ),
        "link_values_printed": any(
            bool(item.get("link_values_printed"))
            for item in [
                quickstart,
                action_packet,
                final_handoff,
                jupyter_input,
                jupyter_authorized,
                target_confirmation,
                route_aware,
                secret_scan,
            ]
        ),
        "secret_values_printed": any(
            bool(item.get("secret_values_printed"))
            for item in [
                quickstart,
                action_packet,
                final_handoff,
                jupyter_input,
                jupyter_authorized,
                target_confirmation,
                route_aware,
                secret_scan,
            ]
        ),
    }
    contact_flags = {
        "platform_contacted": any(
            bool(item.get("platform_contacted"))
            for item in [
                quickstart,
                action_packet,
                final_handoff,
                jupyter_input,
                jupyter_authorized,
                target_confirmation,
                route_aware,
            ]
        ),
        "uploads_performed": any(
            bool(item.get("uploads_performed"))
            for item in [
                quickstart,
                action_packet,
                final_handoff,
                jupyter_input,
                jupyter_authorized,
                target_confirmation,
                route_aware,
            ]
        ),
        "download_host_contacted": any(
            bool(item.get("contact_flags", {}).get("download_host_contacted"))
            for item in [
                quickstart,
                action_packet,
                final_handoff,
                jupyter_input,
                jupyter_authorized,
                target_confirmation,
                route_aware,
            ]
        ),
    }

    blocking = []
    for name, ok in evidence.items():
        if not ok:
            blocking.append(f"只读预检入口证据未通过 `{name}`。")
    if any(leak_flags.values()):
        blocking.append("输入证据显示存在凭据、链接或 secret 明文泄漏风险。")
    if any(contact_flags.values()):
        blocking.append("输入证据显示曾连接平台、上传或接触下载 host。")
    if not blocking:
        blocking.append(
            "baseline 只读预检入口已固化；用户确认目标并填写 token/submission id 后，先运行第 45 节或 shell 只读预检，"
            "仍不要设置真实 runner 强确认。"
        )

    passed = bool(all(evidence.values()) and not any(leak_flags.values()) and not any(contact_flags.values()))
    return {
        "kind": "baseline_readonly_preflight_entry",
        "passed": passed,
        "recommended_route": "baseline_official_aloha",
        "target_confirmation_value": TARGET_CONFIRMATION,
        "target_user_confirmed": False,
        "readonly_preflight_command": AUTHORIZED_PREFLIGHT_COMMAND,
        "jupyter_local_env_entry": JUPYTER_LOCAL_ENV_ENTRY,
        "jupyter_authorized_preflight_entry": JUPYTER_AUTHORIZED_PREFLIGHT_ENTRY,
        "required_user_inputs_for_readonly_preflight": REQUIRED_FOR_READONLY_PREFLIGHT,
        "excluded_from_readonly_preflight": EXCLUDED_FROM_READONLY_PREFLIGHT,
        "real_runner_confirm_required_for_real_submission": True,
        "real_runner_confirm_required_for_readonly_preflight": False,
        "requires_checkpoint_upload": False,
        "requires_checkpoint_link": False,
        "requires_checkpoint_archive_authorization": False,
        "baseline_current_blocking": baseline_blocking,
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
        "# Baseline 只读预检入口",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 推荐路线：`{status['recommended_route']}`。",
        f"- 目标确认值：`{status['target_confirmation_value']}`。",
        f"- 当前是否替用户确认：`{status['target_user_confirmed']}`。",
        f"- baseline 是否需要 checkpoint 上传：`{status['requires_checkpoint_upload']}`。",
        f"- baseline 是否需要 checkpoint link：`{status['requires_checkpoint_link']}`。",
        f"- 只读预检是否需要真实 runner 强确认：`{status['real_runner_confirm_required_for_readonly_preflight']}`。",
        "",
        "## 用户确认后最短入口",
        "",
        f"1. `{status['jupyter_local_env_entry']}`，只把真实 token、submission id 和确认值写入被 Git 忽略的 local env。",
        f"2. `{status['jupyter_authorized_preflight_entry']}`，或在 shell 运行 `{status['readonly_preflight_command']}`。",
        "3. 只读预检通过后，才进入 baseline dry-run gate；真实 runner 强确认不属于只读预检。",
        "",
        "## 只读预检需要的用户输入",
        "",
    ]
    for item in status["required_user_inputs_for_readonly_preflight"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## 不属于只读预检的项", ""])
    for item in status["excluded_from_readonly_preflight"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## 证据", ""])
    for key, ok in status["evidence"].items():
        lines.append(f"- `{key}`：`{ok}`。")
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
