#!/usr/bin/env python3
"""Render a no-contact packet that separates baseline and LoRA submission routes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = ROOT / "runs"
DEFAULT_STATUS = RUNS_DIR / "submission_variant_route_packet.json"
DEFAULT_REPORT = REPORTS_DIR / "submission_variant_route_packet.md"


LORA_BLOCKING_IDS = [
    "SUBMISSION_TARGET_CONFIRMATION",
    "ROBOCHALLENGE_USER_TOKEN",
    "ROBOCHALLENGE_SUBMISSION_ID",
    "ROBOCHALLENGE_SUBMISSION_VARIANT=lora",
    "CHECKPOINT_ARCHIVE_AUTHORIZATION",
    "ROBOCHALLENGE_CHECKPOINT_LINK",
    "ROBOCHALLENGE_REAL_RUN_CONFIRM",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成提交路线拆分包；不读取凭据、不联网、不上传。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文报告输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def runner_template_ready(runner: dict[str, Any]) -> bool:
    dry_run = runner.get("dry_run_no_contact", {})
    return bool(
        runner.get("exists")
        and runner.get("mentions_user_token")
        and runner.get("mentions_submission_id")
        and runner.get("mentions_expected_checkpoint")
        and runner.get("mentions_placeholder_guard")
        and runner.get("mentions_dry_run_guard")
        and runner.get("contains_plaintext_secret_pattern") is False
        and runner.get("bash_n", {}).get("passed")
        and runner.get("no_credentials_failfast", {}).get("passed")
        and runner.get("placeholder_credentials_failfast", {}).get("passed")
        and dry_run.get("passed")
        and dry_run.get("printed_secret") is False
        and dry_run.get("printed_checkpoint") is False
        and dry_run.get("has_checkpoint_length")
    )


def route(
    *,
    route_id: str,
    label: str,
    recommended: bool,
    local_runner_ready_without_credentials: bool,
    local_checkpoint_ready: bool,
    requires_checkpoint_upload: bool,
    requires_checkpoint_link_for_local_runner: bool,
    requires_checkpoint_upload_for_public_link: bool,
    current_blocking: list[str],
    evidence: dict[str, Any],
    note: str,
) -> dict[str, Any]:
    return {
        "id": route_id,
        "label": label,
        "recommended": recommended,
        "local_runner_ready_without_credentials": bool(local_runner_ready_without_credentials),
        "local_checkpoint_ready": bool(local_checkpoint_ready),
        "requires_checkpoint_upload": bool(requires_checkpoint_upload),
        "requires_checkpoint_link_for_local_runner": bool(requires_checkpoint_link_for_local_runner),
        "requires_checkpoint_upload_for_public_link": bool(requires_checkpoint_upload_for_public_link),
        "current_blocking": current_blocking,
        "evidence": evidence,
        "note": note,
    }


def any_top(items: list[dict[str, Any]], key: str) -> bool:
    return any(bool(item.get(key)) for item in items)


def build_status() -> dict[str, Any]:
    package = read_json(RUNS_DIR / "robochallenge_submission_package_audit.json")
    mapping = read_json(RUNS_DIR / "table30v2_aloha_mapping_audit.json")
    readiness = read_json(RUNS_DIR / "real_submission_readiness.json")
    lora_export = read_json(RUNS_DIR / "lora_checkpoint_export_readiness.json")
    lora_policy = read_json(RUNS_DIR / "openpi_rtc_lora_materialized_policy_smoke_status.json")
    upload_channels = read_json(RUNS_DIR / "checkpoint_upload_channels_audit.json")
    secret_scan = read_json(RUNS_DIR / "plaintext_secret_scan.json")

    selected = package.get("selected_target", {})
    restore = package.get("model_restore_materials", {})
    runners = package.get("runner_audit", {})
    baseline_runner = runners.get("baseline", {})
    lora_runner = runners.get("lora", {})
    env = readiness.get("env", {})
    token_present = env.get("ROBOCHALLENGE_USER_TOKEN", {}).get("present") is True
    submission_id_present = env.get("ROBOCHALLENGE_SUBMISSION_ID", {}).get("present") is True
    checkpoint_link_present = any(
        env.get(key, {}).get("present") is True
        for key in ["ROBOCHALLENGE_CHECKPOINT_LINK", "ROBOCHALLENGE_LORA_CHECKPOINT_LINK"]
    )

    baseline_runner_ready = runner_template_ready(baseline_runner)
    lora_runner_ready = runner_template_ready(lora_runner)
    baseline_checkpoint_ready = bool(
        selected.get("checkpoint_exists")
        and restore.get("official_aloha_checkpoint_exists")
        and selected.get("benchmark") == "Table30v2"
        and selected.get("robot_type") == "aloha"
    )
    mapping_ready = bool(mapping.get("ready_for_dry_run_converter") and mapping.get("lengths_match"))
    lora_checkpoint_ready = bool(
        restore.get("materialized_checkpoint_exists")
        and restore.get("materialize_passed")
        and restore.get("policy_smoke_passed")
        and restore.get("direct_demo_checkpoint_ready")
        and lora_export.get("local_export_ready")
        and lora_policy.get("passed")
        and lora_policy.get("policy_load_smoke", {}).get("passed")
    )

    baseline_current_blocking = [
        "SUBMISSION_TARGET_CONFIRMATION",
        "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline",
        "ROBOCHALLENGE_REAL_RUN_CONFIRM",
    ]
    if not token_present:
        baseline_current_blocking.insert(1, "ROBOCHALLENGE_USER_TOKEN")
    if not submission_id_present:
        baseline_current_blocking.insert(2, "ROBOCHALLENGE_SUBMISSION_ID")
    baseline_route = route(
        route_id="baseline_official_aloha",
        label="官方 Table30v2 ALOHA baseline",
        recommended=True,
        local_runner_ready_without_credentials=bool(
            package.get("passed") and baseline_checkpoint_ready and baseline_runner_ready and mapping_ready
        ),
        local_checkpoint_ready=baseline_checkpoint_ready,
        requires_checkpoint_upload=False,
        requires_checkpoint_link_for_local_runner=False,
        requires_checkpoint_upload_for_public_link=False,
        current_blocking=baseline_current_blocking,
        evidence={
            "package_audit_passed": package.get("passed") is True,
            "mapping_ready": mapping_ready,
            "official_checkpoint_exists": baseline_checkpoint_ready,
            "runner_template_ready_without_credentials": baseline_runner_ready,
            "token_present": token_present,
            "submission_id_present": submission_id_present,
        },
        note=(
            "本地 runner 路线使用 Linux 上已存在的官方 ALOHA checkpoint，"
            "不需要先生成 LoRA tar，也不需要 checkpoint link。仍需要用户 token、submission id、提交对象确认和真实 runner 强确认。"
        ),
    )
    lora_route = route(
        route_id="lora_materialized",
        label="LoRA 物化 checkpoint",
        recommended=False,
        local_runner_ready_without_credentials=bool(
            package.get("passed") and lora_checkpoint_ready and lora_runner_ready and mapping_ready
        ),
        local_checkpoint_ready=lora_checkpoint_ready,
        requires_checkpoint_upload=False,
        requires_checkpoint_link_for_local_runner=False,
        requires_checkpoint_upload_for_public_link=True,
        current_blocking=LORA_BLOCKING_IDS,
        evidence={
            "package_audit_passed": package.get("passed") is True,
            "mapping_ready": mapping_ready,
            "materialized_checkpoint_exists": restore.get("materialized_checkpoint_exists") is True,
            "lora_export_ready": lora_export.get("local_export_ready") is True,
            "policy_smoke_passed": lora_policy.get("passed") is True
            and lora_policy.get("policy_load_smoke", {}).get("passed") is True,
            "runner_template_ready_without_credentials": lora_runner_ready,
            "upload_channels_audited": upload_channels.get("passed") is True,
            "uploads_performed": upload_channels.get("uploads_performed") is True,
            "checkpoint_link_present": checkpoint_link_present,
        },
        note=(
            "本地 LoRA 物化 checkpoint 已能被 policy 加载；如果作为网页可访问 checkpoint 提交，"
            "仍需要用户授权归档/上传并回填真实 HTTPS checkpoint link。"
        ),
    )
    routes = [baseline_route, lora_route]

    inputs = [package, readiness, lora_export, lora_policy, upload_channels, secret_scan]
    leak_flags = {
        "credentials_printed": any_top(inputs, "credentials_printed"),
        "link_values_printed": any_top(inputs, "link_values_printed")
        or any_top(inputs, "link_value_printed"),
        "secret_values_printed": any_top(inputs, "secret_values_printed"),
    }
    contact_flags = {
        "platform_contacted": any_top(inputs, "platform_contacted"),
        "uploads_performed": any_top(inputs, "uploads_performed") or any_top(inputs, "upload_performed"),
        "download_host_contacted": False,
    }
    evidence = {
        "package_audit_passed": package.get("passed") is True,
        "readiness_gate_passed": readiness.get("passed") is True,
        "baseline_local_route_ready_without_credentials": baseline_route["local_runner_ready_without_credentials"],
        "baseline_does_not_need_upload_or_link": not baseline_route["requires_checkpoint_upload"]
        and not baseline_route["requires_checkpoint_link_for_local_runner"],
        "lora_local_checkpoint_ready": lora_route["local_checkpoint_ready"],
        "lora_public_link_still_needs_upload": lora_route["requires_checkpoint_upload_for_public_link"],
        "secret_scan_clean": secret_scan.get("passed") is True and secret_scan.get("hit_count") == 0,
    }
    passed = bool(
        len(routes) == 2
        and routes[0]["id"] == "baseline_official_aloha"
        and routes[1]["id"] == "lora_materialized"
        and all(evidence.values())
        and not any(leak_flags.values())
        and not any(contact_flags.values())
    )
    blocking = []
    if not passed:
        for name, ok in evidence.items():
            if not ok:
                blocking.append(f"提交路线拆分包输入证据未通过 `{name}`。")
        if any(leak_flags.values()):
            blocking.append("输入审计显示存在凭据或链接明文泄露风险。")
        if any(contact_flags.values()):
            blocking.append("输入审计显示曾连接平台、接触下载 host 或执行上传。")
    else:
        blocking.append("提交路线已拆分；默认建议先走官方 ALOHA baseline 本地 runner 路线。")

    return {
        "kind": "submission_variant_route_packet",
        "passed": passed,
        "recommended_default": "baseline_official_aloha",
        "route_count": len(routes),
        "routes": routes,
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
        "# 提交路线拆分包",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 推荐默认路线：`{status['recommended_default']}`。",
        f"- 路线数量：`{status['route_count']}`。",
        "",
        "## 路线",
        "",
    ]
    for item in status["routes"]:
        lines.append(f"### {item['label']}")
        lines.append("")
        lines.append(f"- route id：`{item['id']}`。")
        lines.append(f"- 是否推荐默认：`{item['recommended']}`。")
        lines.append(f"- 本地 runner 在未填凭据前是否已就绪：`{item['local_runner_ready_without_credentials']}`。")
        lines.append(f"- 本地 checkpoint 是否就绪：`{item['local_checkpoint_ready']}`。")
        lines.append(f"- 本地 runner 是否需要 checkpoint upload：`{item['requires_checkpoint_upload']}`。")
        lines.append(f"- 本地 runner 是否需要 checkpoint link：`{item['requires_checkpoint_link_for_local_runner']}`。")
        lines.append(f"- 生成公网 checkpoint link 是否仍需上传：`{item['requires_checkpoint_upload_for_public_link']}`。")
        lines.append(f"- 说明：{item['note']}")
        lines.append("- 当前阻塞：")
        for blocker in item["current_blocking"]:
            lines.append(f"  - `{blocker}`")
        lines.append("- 证据：")
        for key, value in item["evidence"].items():
            lines.append(f"  - `{key}`：`{value}`。")
        lines.append("")
    lines.extend(
        [
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
