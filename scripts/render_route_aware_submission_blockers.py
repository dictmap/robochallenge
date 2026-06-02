#!/usr/bin/env python3
"""Render route-aware submission blockers without reading credentials."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = ROOT / "runs"
DEFAULT_STATUS = RUNS_DIR / "route_aware_submission_blockers.json"
DEFAULT_REPORT = REPORTS_DIR / "route_aware_submission_blockers.md"


BASELINE_REQUIRED_IDS = [
    "SUBMISSION_TARGET_CONFIRMATION",
    "ROBOCHALLENGE_USER_TOKEN",
    "ROBOCHALLENGE_SUBMISSION_ID",
    "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline",
    "ROBOCHALLENGE_REAL_RUN_CONFIRM",
]

LORA_WEB_REQUIRED_IDS = [
    "SUBMISSION_TARGET_CONFIRMATION",
    "ROBOCHALLENGE_USER_TOKEN",
    "ROBOCHALLENGE_SUBMISSION_ID",
    "ROBOCHALLENGE_SUBMISSION_VARIANT=lora",
    "CHECKPOINT_ARCHIVE_AUTHORIZATION",
    "ROBOCHALLENGE_CHECKPOINT_LINK",
    "ROBOCHALLENGE_REAL_RUN_CONFIRM",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成路线感知阻塞摘要；不读取凭据、不联网、不上传。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文报告输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def route_by_id(packet: dict[str, Any], route_id: str) -> dict[str, Any]:
    for item in packet.get("routes", []):
        if item.get("id") == route_id:
            return item
    return {}


def clean_ids(items: list[Any]) -> list[str]:
    result: list[str] = []
    for item in items:
        value = str(item).strip()
        if value and value not in result:
            result.append(value)
    return result


def build_status() -> dict[str, Any]:
    route_packet = read_json(RUNS_DIR / "submission_variant_route_packet.json")
    baseline_quickstart = read_json(RUNS_DIR / "baseline_submission_quickstart.json")
    readiness = read_json(RUNS_DIR / "real_submission_readiness.json")
    blockers_summary = read_json(RUNS_DIR / "submission_blockers_summary.json")
    action_packet = read_json(RUNS_DIR / "next_user_action_packet.json")
    web_form_packet = read_json(RUNS_DIR / "web_form_field_packet.json")
    secret_scan = read_json(RUNS_DIR / "plaintext_secret_scan.json")

    baseline_route = route_by_id(route_packet, "baseline_official_aloha")
    lora_route = route_by_id(route_packet, "lora_materialized")
    baseline_quickstart_ids = clean_ids(
        [item.get("id") for item in baseline_quickstart.get("required_user_inputs", [])]
    )
    baseline_current_blocking = clean_ids(
        baseline_route.get("current_blocking", []) or baseline_quickstart_ids or BASELINE_REQUIRED_IDS
    )
    lora_web_current_blocking = clean_ids(lora_route.get("current_blocking", []) or LORA_WEB_REQUIRED_IDS)

    baseline_requires_checkpoint_link = "ROBOCHALLENGE_CHECKPOINT_LINK" in baseline_current_blocking
    baseline_requires_archive_authorization = "CHECKPOINT_ARCHIVE_AUTHORIZATION" in baseline_current_blocking
    lora_requires_checkpoint_link = "ROBOCHALLENGE_CHECKPOINT_LINK" in lora_web_current_blocking
    lora_requires_archive_authorization = "CHECKPOINT_ARCHIVE_AUTHORIZATION" in lora_web_current_blocking

    evidence = {
        "route_packet_passed": route_packet.get("passed") is True,
        "recommended_default_is_baseline": route_packet.get("recommended_default") == "baseline_official_aloha",
        "baseline_quickstart_passed": baseline_quickstart.get("passed") is True,
        "baseline_quickstart_no_upload": baseline_quickstart.get("requires_checkpoint_upload") is False,
        "baseline_quickstart_no_link": baseline_quickstart.get("requires_checkpoint_link") is False,
        "baseline_route_local_runner_ready_without_credentials": baseline_route.get(
            "local_runner_ready_without_credentials"
        )
        is True,
        "baseline_route_no_upload": baseline_route.get("requires_checkpoint_upload") is False,
        "baseline_route_no_local_link": baseline_route.get("requires_checkpoint_link_for_local_runner") is False,
        "baseline_blocking_has_no_checkpoint_link": not baseline_requires_checkpoint_link,
        "baseline_blocking_has_no_archive_authorization": not baseline_requires_archive_authorization,
        "baseline_required_ids_complete": set(BASELINE_REQUIRED_IDS).issubset(set(baseline_current_blocking)),
        "lora_web_requires_checkpoint_link": lora_requires_checkpoint_link,
        "lora_web_requires_archive_authorization": lora_requires_archive_authorization,
        "lora_web_required_ids_complete": set(LORA_WEB_REQUIRED_IDS).issubset(set(lora_web_current_blocking)),
        "readiness_gate_passed": readiness.get("passed") is True,
        "readiness_currently_false": readiness.get("ready_for_real_submission") is False,
        "web_form_packet_passed": web_form_packet.get("passed") is True,
        "action_packet_passed": action_packet.get("passed") is True,
        "action_packet_recommends_baseline": action_packet.get("recommended_route") == "baseline_official_aloha",
        "action_packet_baseline_no_link": action_packet.get("baseline_requires_checkpoint_link") is False,
        "action_packet_lora_web_needs_link": action_packet.get("lora_web_requires_checkpoint_link") is True,
        "secret_scan_clean": secret_scan.get("passed") is True and secret_scan.get("hit_count") == 0,
    }
    inputs = [route_packet, baseline_quickstart, readiness, blockers_summary, action_packet, web_form_packet, secret_scan]
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
                blocking.append(f"路线感知阻塞摘要输入证据未通过 `{name}`。")
        if any(leak_flags.values()):
            blocking.append("输入审计显示存在凭据或链接明文泄露风险。")
        if any(contact_flags.values()):
            blocking.append("输入审计显示曾连接平台、接触下载 host 或执行上传。")
    else:
        blocking.append("路线感知阻塞摘要已生成；baseline 最短路线不需要 checkpoint link 或归档上传。")

    return {
        "kind": "route_aware_submission_blockers",
        "passed": passed,
        "recommended_route": "baseline_official_aloha",
        "baseline_requires_checkpoint_upload": False,
        "baseline_requires_checkpoint_link": False,
        "baseline_requires_archive_authorization": False,
        "lora_web_requires_checkpoint_upload": True,
        "lora_web_requires_checkpoint_link": True,
        "lora_web_requires_archive_authorization": True,
        "baseline_required_ids": BASELINE_REQUIRED_IDS,
        "baseline_current_blocking": baseline_current_blocking,
        "lora_web_required_ids": LORA_WEB_REQUIRED_IDS,
        "lora_web_current_blocking": lora_web_current_blocking,
        "legacy_global_blocking": blockers_summary.get("blocking", []) or readiness.get("blocking", []),
        "readiness_blocking": readiness.get("blocking", []),
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
        "# 路线感知阻塞摘要",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 推荐路线：`{status['recommended_route']}`。",
        f"- baseline 是否需要 checkpoint upload：`{status['baseline_requires_checkpoint_upload']}`。",
        f"- baseline 是否需要 checkpoint link：`{status['baseline_requires_checkpoint_link']}`。",
        f"- LoRA/web 是否需要 checkpoint upload：`{status['lora_web_requires_checkpoint_upload']}`。",
        f"- LoRA/web 是否需要 checkpoint link：`{status['lora_web_requires_checkpoint_link']}`。",
        "",
        "## Baseline 最短路线当前只差",
        "",
    ]
    for item in status["baseline_current_blocking"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## LoRA / 网页 checkpoint 路线当前只差", ""])
    for item in status["lora_web_current_blocking"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 如果先复现并提交官方 ALOHA baseline，本地 runner 不需要 checkpoint link，也不需要生成或上传 LoRA tar。",
            "- 只有选择 LoRA 物化 checkpoint 或网页 checkpoint 链接路线时，才进入归档、上传和 checkpoint link 回填流程。",
            "- 旧的全局 readiness 阻塞仍会列出 checkpoint link，因为它同时覆盖网页表单和 LoRA checkpoint 路线。",
            "",
            "## 旧全局阻塞（保留兼容）",
            "",
        ]
    )
    for item in status["legacy_global_blocking"]:
        lines.append(f"- {item}")
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
