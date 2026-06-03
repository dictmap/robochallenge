#!/usr/bin/env python3
"""Render a no-contact baseline dry-run gate packet for credential handoff."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = ROOT / "runs"
DEFAULT_STATUS = RUNS_DIR / "baseline_dry_run_gate.json"
DEFAULT_REPORT = REPORTS_DIR / "baseline_dry_run_gate.md"
SELF_BOOTSTRAP_EXCLUSIONS = ["previous_preflight_passed_or_absent"]

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
    parser = argparse.ArgumentParser(description="生成 baseline 授权后 dry-run gate 证据包；不读凭据、不联网、不上传。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文报告输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def command_by_step(commands: list[dict[str, Any]], step: int) -> str:
    for item in commands:
        if item.get("step") == step:
            return str(item.get("command", ""))
    return ""


def ids(items: list[dict[str, Any]] | list[str]) -> set[str]:
    output: set[str] = set()
    for item in items:
        if isinstance(item, dict):
            value = item.get("id")
        else:
            value = item
        if value:
            output.add(str(value))
    return output


def build_status() -> dict[str, Any]:
    route_packet = read_json(RUNS_DIR / "submission_variant_route_packet.json")
    quickstart = read_json(RUNS_DIR / "baseline_submission_quickstart.json")
    ready_runner = read_json(RUNS_DIR / "ready_real_runner_template_audit.json")
    authorized_execution = read_json(RUNS_DIR / "authorized_execution_checklist.json")
    action_packet = read_json(RUNS_DIR / "next_user_action_packet.json")
    route_aware = read_json(RUNS_DIR / "route_aware_submission_blockers.json")
    secret_scan = read_json(RUNS_DIR / "plaintext_secret_scan.json")
    previous_preflight = read_json(RUNS_DIR / "submission_preflight_bundle.json")

    quickstart_commands = quickstart.get("commands", [])
    synthetic = ready_runner.get("synthetic_no_confirm_smoke", {})
    wrong_confirm = ready_runner.get("synthetic_wrong_confirm_smoke", {})
    malformed_confirm_cases = ready_runner.get("malformed_confirmation_cases", [])
    baseline_decision_ids = ids(authorized_execution.get("required_user_decisions", []))
    action_decision_ids = ids(action_packet.get("required_user_decisions", []))
    route_aware_baseline_ids = ids(route_aware.get("baseline_current_blocking", []))
    route_aware_lora_ids = ids(route_aware.get("lora_web_current_blocking", []))

    authorized_preflight_command = command_by_step(quickstart_commands, 2)
    dry_run_gate_command = command_by_step(quickstart_commands, 3)
    real_runner_command = command_by_step(quickstart_commands, 4)

    evidence = {
        "route_packet_passed": route_packet.get("passed") is True,
        "recommended_route_baseline": route_packet.get("recommended_default") == "baseline_official_aloha",
        "quickstart_passed": quickstart.get("passed") is True,
        "quickstart_no_checkpoint_upload": quickstart.get("requires_checkpoint_upload") is False,
        "quickstart_no_checkpoint_link": quickstart.get("requires_checkpoint_link") is False,
        "authorized_preflight_command_exact": authorized_preflight_command == AUTHORIZED_PREFLIGHT_COMMAND,
        "dry_run_gate_command_exact": dry_run_gate_command == DRY_RUN_GATE_COMMAND,
        "real_runner_command_exact": real_runner_command == REAL_RUNNER_COMMAND,
        "ready_runner_template_passed": ready_runner.get("passed") is True,
        "ready_runner_default_baseline": ready_runner.get("default_variant") == "baseline",
        "synthetic_dry_run_called": synthetic.get("dry_run_called") is True,
        "synthetic_variant_baseline": synthetic.get("variant") == "baseline",
        "synthetic_missing_confirmation": synthetic.get("missing_confirmation") is True,
        "synthetic_stops_before_real_runner": synthetic.get("stops_before_real_runner") is True,
        "synthetic_real_runner_not_started": synthetic.get("real_runner_started") is False,
        "synthetic_no_protected_values_printed": synthetic.get("printed_protected_values") is False,
        "wrong_confirm_dry_run_called": wrong_confirm.get("dry_run_called") is True,
        "wrong_confirm_confirmation_present": wrong_confirm.get("confirmation_present") is True,
        "wrong_confirm_stops_before_real_runner": wrong_confirm.get("stops_before_real_runner") is True,
        "wrong_confirm_real_runner_not_started": wrong_confirm.get("real_runner_started") is False,
        "wrong_confirm_no_protected_values_printed": wrong_confirm.get("printed_protected_values") is False,
        "malformed_confirm_cases_rejected": ready_runner.get("malformed_confirmation_cases_rejected") is True,
        "malformed_confirm_case_count": ready_runner.get("malformed_confirmation_case_count") == 4,
        "malformed_confirm_real_runner_not_started": not any(
            item.get("real_runner_started") for item in malformed_confirm_cases
        ),
        "authorized_execution_passed": authorized_execution.get("passed") is True,
        "authorized_execution_baseline_required_ids": BASELINE_REQUIRED_IDS.issubset(baseline_decision_ids),
        "authorized_execution_baseline_no_lora_ids": not bool(BASELINE_REQUIRED_IDS & LORA_ONLY_IDS)
        and not bool(baseline_decision_ids & LORA_ONLY_IDS),
        "action_packet_passed": action_packet.get("passed") is True,
        "action_packet_baseline_required_ids": BASELINE_REQUIRED_IDS.issubset(action_decision_ids),
        "action_packet_baseline_no_lora_ids": not bool(action_decision_ids & LORA_ONLY_IDS),
        "route_aware_passed": route_aware.get("passed") is True,
        "route_aware_baseline_no_checkpoint_upload": route_aware.get("baseline_requires_checkpoint_upload") is False,
        "route_aware_baseline_no_checkpoint_link": route_aware.get("baseline_requires_checkpoint_link") is False,
        "route_aware_baseline_required_ids": BASELINE_REQUIRED_IDS.issubset(route_aware_baseline_ids),
        "route_aware_baseline_no_lora_ids": not bool(route_aware_baseline_ids & LORA_ONLY_IDS),
        "route_aware_lora_keeps_link_branch": LORA_ONLY_IDS.issubset(route_aware_lora_ids),
        "secret_scan_clean": secret_scan.get("passed") is True and secret_scan.get("hit_count") == 0,
        "previous_preflight_passed_or_absent": not previous_preflight or previous_preflight.get("passed") is True,
    }
    bootstrap_evidence = {
        key: value for key, value in evidence.items() if key not in set(SELF_BOOTSTRAP_EXCLUSIONS)
    }
    leak_flags = {
        "credentials_printed": any(
            bool(item.get("credentials_printed"))
            for item in [quickstart, ready_runner, authorized_execution, action_packet, route_aware]
        ),
        "link_values_printed": any(
            bool(item.get("link_values_printed"))
            for item in [quickstart, ready_runner, authorized_execution, action_packet, route_aware]
        ),
        "secret_values_printed": any(
            bool(item.get("secret_values_printed"))
            for item in [quickstart, ready_runner, authorized_execution, action_packet, route_aware, secret_scan]
        ),
    }
    contact_flags = {
        "platform_contacted": any(
            bool(item.get("platform_contacted"))
            for item in [quickstart, ready_runner, authorized_execution, action_packet, route_aware]
        ),
        "uploads_performed": any(
            bool(item.get("uploads_performed") or item.get("upload_performed"))
            for item in [quickstart, ready_runner, authorized_execution, action_packet, route_aware]
        ),
        "download_host_contacted": False,
    }
    passed = bool(all(bootstrap_evidence.values()) and not any(leak_flags.values()) and not any(contact_flags.values()))
    blocking = []
    if passed:
        blocking.append(
            "baseline dry-run gate 已固化；目标确认、token、submission id 和 variant=baseline 到位后先跑只读预检，"
            "再跑 dry-run gate，缺少真实 runner 强确认短语时不会启动 runner。"
        )
    else:
        for key, ok in bootstrap_evidence.items():
            if not ok:
                blocking.append(f"baseline dry-run gate 证据未通过 `{key}`。")
        if any(leak_flags.values()):
            blocking.append("输入审计显示存在凭据或链接明文泄露风险。")
        if any(contact_flags.values()):
            blocking.append("输入审计显示曾连接平台、上传或接触下载 host。")

    return {
        "kind": "baseline_dry_run_gate",
        "passed": passed,
        "recommended_route": "baseline_official_aloha",
        "requires_checkpoint_upload": False,
        "requires_checkpoint_link": False,
        "authorized_preflight_command": AUTHORIZED_PREFLIGHT_COMMAND,
        "dry_run_gate_command": DRY_RUN_GATE_COMMAND,
        "real_runner_command": REAL_RUNNER_COMMAND,
        "first_real_runner_wrapper_command": DRY_RUN_GATE_COMMAND,
        "stops_before_real_runner_without_confirmation": synthetic.get("stops_before_real_runner") is True
        and synthetic.get("real_runner_started") is False,
        "stops_before_real_runner_with_wrong_confirmation": wrong_confirm.get("stops_before_real_runner") is True
        and wrong_confirm.get("real_runner_started") is False,
        "stops_before_real_runner_with_malformed_confirmation": ready_runner.get(
            "malformed_confirmation_cases_rejected"
        )
        is True
        and not any(item.get("real_runner_started") for item in malformed_confirm_cases),
        "baseline_required_ids": sorted(BASELINE_REQUIRED_IDS),
        "lora_only_ids": sorted(LORA_ONLY_IDS),
        "evidence": evidence,
        "self_bootstrap_exclusions": SELF_BOOTSTRAP_EXCLUSIONS,
        "bootstrap_evidence": bootstrap_evidence,
        "bootstrap_evidence_passed": all(bootstrap_evidence.values()),
        "previous_preflight_passed_snapshot": evidence["previous_preflight_passed_or_absent"],
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
        "# Baseline dry-run gate 证据包",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 推荐路线：`{status['recommended_route']}`。",
        f"- baseline 是否需要 checkpoint upload：`{status['requires_checkpoint_upload']}`。",
        f"- baseline 是否需要 checkpoint link：`{status['requires_checkpoint_link']}`。",
        f"- 无真实确认短语时是否停在 runner 前：`{status['stops_before_real_runner_without_confirmation']}`。",
        f"- 错误确认短语时是否停在 runner 前：`{status['stops_before_real_runner_with_wrong_confirmation']}`。",
        f"- 畸形确认短语时是否停在 runner 前：`{status['stops_before_real_runner_with_malformed_confirmation']}`。",
        "",
        "## 目标确认、token、submission id、variant 到位后先跑",
        "",
        f"1. 授权前只读预检：`{status['authorized_preflight_command']}`",
        f"2. baseline wrapper dry-run gate：`{status['dry_run_gate_command']}`",
        f"3. 真实 runner 强确认命令：`{status['real_runner_command']}`",
        "",
        "第 2 条用于验证 wrapper 和 baseline runner 入口；缺少真实 runner 强确认短语时只会 dry-run，然后停在真实 runner 前。",
        "第 3 条只有用户明确授权真实提交时才运行，会连接 RoboChallenge 并启动真实 runner。",
        "",
        "## 路线边界",
        "",
        "- baseline 官方 ALOHA 路线不需要 checkpoint link、checkpoint upload 或归档授权。",
        "- LoRA / 网页 checkpoint 路线仍单独保留 checkpoint 归档、上传和真实 link 回填要求。",
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
    lines.extend(["", "## 自举快照", ""])
    lines.append("- `previous_preflight_passed_or_absent` 仅用于记录上一次预检快照，不作为本 gate 自身 `passed` 的硬前置。")
    for key in status["self_bootstrap_exclusions"]:
        lines.append(f"- `{key}`：当前快照 `{status['evidence'].get(key)}`。")
    lines.append(f"- 自举底层证据是否就绪：`{status['bootstrap_evidence_passed']}`。")
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
