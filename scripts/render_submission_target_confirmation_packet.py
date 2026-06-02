#!/usr/bin/env python3
"""Render a no-contact packet for the submission target confirmation blocker."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
DEFAULT_STATUS = RUNS_DIR / "submission_target_confirmation_packet.json"
DEFAULT_REPORT = REPORTS_DIR / "submission_target_confirmation_packet.md"

EXPECTED_TARGET = {
    "benchmark": "Table30v2",
    "robot_type": "aloha",
    "task_name": "pack_the_toothbrush_holder",
    "prompt": (
        "Put the toothbrush and toothpaste into the toiletries case in sequence, "
        "close the case, and then place it into the basket."
    ),
    "recommended_route": "baseline_official_aloha",
    "submission_variant": "baseline",
}
CONFIRMATION_VALUE = "CONFIRM_TABLE30V2_ALOHA_BASELINE"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成提交对象确认包；不读取凭据、不联网、不上传。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文报告输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_status() -> dict[str, Any]:
    package = read_json(RUNS_DIR / "robochallenge_submission_package_audit.json")
    mapping = read_json(RUNS_DIR / "table30v2_aloha_mapping_audit.json")
    dry_run = read_json(RUNS_DIR / "table30v2_aloha_dry_run_status.json")
    quickstart = read_json(RUNS_DIR / "baseline_submission_quickstart.json")
    route_aware = read_json(RUNS_DIR / "route_aware_submission_blockers.json")
    web_form = read_json(RUNS_DIR / "web_form_field_packet.json")
    secret_scan = read_json(RUNS_DIR / "plaintext_secret_scan.json")

    selected = package.get("selected_target", {})
    task_desc = mapping.get("task_info", {}).get("task_desc", {})
    transform = dry_run.get("transform_smoke", {})
    after_padding = transform.get("after_padding", {})
    web_blocking_names = set(web_form.get("recommended_route_blocking_names", []))
    baseline_blocking = set(route_aware.get("baseline_current_blocking", []))

    target = {
        **EXPECTED_TARGET,
        "checkpoint": selected.get("checkpoint", ""),
        "checkpoint_exists": selected.get("checkpoint_exists") is True,
        "confirmation_value": CONFIRMATION_VALUE,
        "human_confirmation_text": "确认提交对象为 Table30v2 ALOHA baseline，不是原始 Table30，也不是 LoRA/web checkpoint 路线。",
    }
    evidence = {
        "package_audit_passed": package.get("passed") is True,
        "selected_benchmark_matches": selected.get("benchmark") == EXPECTED_TARGET["benchmark"],
        "selected_robot_type_matches": selected.get("robot_type") == EXPECTED_TARGET["robot_type"],
        "selected_task_name_matches": selected.get("task_name") == EXPECTED_TARGET["task_name"],
        "selected_prompt_matches": selected.get("prompt") == EXPECTED_TARGET["prompt"],
        "selected_checkpoint_exists": selected.get("checkpoint_exists") is True,
        "mapping_task_name_matches": task_desc.get("task_name") == EXPECTED_TARGET["task_name"],
        "mapping_prompt_matches": task_desc.get("prompt") == EXPECTED_TARGET["prompt"],
        "mapping_ready_for_converter": mapping.get("ready_for_dry_run_converter") is True,
        "mapping_lengths_match": mapping.get("lengths_match") is True,
        "dry_run_transform_smoke_present": bool(after_padding.get("state") and after_padding.get("actions")),
        "quickstart_recommends_baseline": quickstart.get("recommended_route") == EXPECTED_TARGET["recommended_route"],
        "quickstart_baseline_needs_no_link": quickstart.get("requires_checkpoint_link") is False,
        "route_aware_recommends_baseline": route_aware.get("recommended_route") == EXPECTED_TARGET["recommended_route"],
        "route_aware_baseline_keeps_target_confirmation_blocking": "SUBMISSION_TARGET_CONFIRMATION" in baseline_blocking,
        "web_form_recommends_baseline": web_form.get("recommended_route") == EXPECTED_TARGET["recommended_route"],
        "web_form_keeps_target_confirmation_out_of_field_blocking": "SUBMISSION_TARGET_CONFIRMATION"
        not in web_blocking_names,
        "secret_scan_clean": secret_scan.get("passed") is True and secret_scan.get("hit_count") == 0,
    }
    inputs = [package, mapping, dry_run, quickstart, route_aware, web_form, secret_scan]
    leak_flags = {
        "credentials_printed": any(bool(item.get("credentials_printed")) for item in inputs),
        "link_values_printed": any(
            bool(item.get("link_values_printed") or item.get("link_value_printed")) for item in inputs
        ),
        "secret_values_printed": any(bool(item.get("secret_values_printed")) for item in inputs),
    }
    contact_flags = {
        "platform_contacted": any(bool(item.get("platform_contacted")) for item in inputs),
        "uploads_performed": any(bool(item.get("uploads_performed") or item.get("upload_performed")) for item in inputs),
        "download_host_contacted": False,
    }
    passed = bool(all(evidence.values()) and not any(leak_flags.values()) and not any(contact_flags.values()))
    blocking: list[str] = []
    if not passed:
        for name, ok in evidence.items():
            if not ok:
                blocking.append(f"提交对象确认包输入证据未通过 `{name}`。")
        if any(leak_flags.values()):
            blocking.append("输入审计显示存在凭据或链接明文泄露风险。")
        if any(contact_flags.values()):
            blocking.append("输入审计显示曾连接平台、接触下载 host 或执行上传。")
    else:
        blocking.append(
            "确认包已生成；仍需用户明确确认提交 Table30v2 ALOHA baseline 后，才可视为满足 SUBMISSION_TARGET_CONFIRMATION。"
        )

    return {
        "kind": "submission_target_confirmation_packet",
        "passed": passed,
        "confirmation_id": "SUBMISSION_TARGET_CONFIRMATION",
        "target_user_confirmed": False,
        "recommended_confirmation_value": CONFIRMATION_VALUE,
        "recommended_route": EXPECTED_TARGET["recommended_route"],
        "submission_variant": EXPECTED_TARGET["submission_variant"],
        "target": target,
        "does_not_confirm_for_user": True,
        "does_not_contact_platform": True,
        "does_not_read_credentials": True,
        "does_not_upload": True,
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
    target = status["target"]
    lines = [
        "# 提交对象确认包",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 确认项：`{status['confirmation_id']}`。",
        f"- 推荐路线：`{status['recommended_route']}`。",
        f"- 推荐 variant：`{status['submission_variant']}`。",
        f"- 推荐确认值：`{status['recommended_confirmation_value']}`。",
        f"- 是否已经替用户确认：`{status['target_user_confirmed']}`。",
        "",
        "## 需要用户确认的目标",
        "",
        f"- Benchmark：`{target['benchmark']}`。",
        f"- Robot Type：`{target['robot_type']}`。",
        f"- Task Name：`{target['task_name']}`。",
        f"- Prompt：`{target['prompt']}`。",
        f"- 本地 checkpoint：`{target['checkpoint']}`。",
        f"- checkpoint 是否存在：`{target['checkpoint_exists']}`。",
        "",
        "## 边界",
        "",
        "- 本包只把当前可复现目标整理成可核对字段，不替用户做参赛目标确认。",
        "- 本包不读取 token、submission id、checkpoint link 或 local env 内容。",
        "- 本包不连接 RoboChallenge 平台，不上传 checkpoint，不生成 tar，也不启动真实 runner。",
        "",
        "## 输入证据",
        "",
    ]
    for key, value in status["evidence"].items():
        lines.append(f"- `{key}`：`{value}`。")
    lines.extend(["", "## 只读边界", ""])
    for key, value in status["contact_flags"].items():
        lines.append(f"- `{key}`：`{value}`。")
    for key, value in status["leak_flags"].items():
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
