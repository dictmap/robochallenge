#!/usr/bin/env python3
"""Render a no-contact packet of RoboChallenge web-form fields."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = ROOT / "runs"
DEFAULT_STATUS = RUNS_DIR / "web_form_field_packet.json"
DEFAULT_REPORT = REPORTS_DIR / "web_form_field_packet.md"
GITHUB_REPO_LINK = "https://github.com/dictmap/robochallenge/tree/main"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成 RoboChallenge 网页表单字段包；不读取凭据、不联网、不上传。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文报告输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def field(name: str, value: str, ready: bool, source: str, note: str, *, secret: bool = False) -> dict[str, Any]:
    return {
        "name": name,
        "value": "[REDACTED]" if secret and value else value,
        "ready": bool(ready),
        "source": source,
        "note": note,
        "secret": secret,
    }


def build_status() -> dict[str, Any]:
    package = read_json(RUNS_DIR / "robochallenge_submission_package_audit.json")
    readiness = read_json(RUNS_DIR / "real_submission_readiness.json")
    link_intake = read_json(RUNS_DIR / "checkpoint_link_intake.json")
    link_download = read_json(RUNS_DIR / "checkpoint_link_download_verification.json")
    upload_channels = read_json(RUNS_DIR / "checkpoint_upload_channels_audit.json")
    action_packet = read_json(RUNS_DIR / "next_user_action_packet.json")
    secret_scan = read_json(RUNS_DIR / "plaintext_secret_scan.json")

    selected = package.get("selected_target", {})
    env = readiness.get("env", {})
    inputs = readiness.get("inputs", {})
    link_current = link_intake.get("current_env", {})
    link_ready = link_current.get("link_shape_ready") is True
    accepted_link_keys = link_current.get("accepted_link_keys", [])
    token_present = env.get("ROBOCHALLENGE_USER_TOKEN", {}).get("present") is True
    submission_id_present = env.get("ROBOCHALLENGE_SUBMISSION_ID", {}).get("present") is True
    web_form_ready = readiness.get("web_form_ready") is True

    fields = [
        field(
            "Benchmark",
            selected.get("benchmark", "Table30v2"),
            selected.get("benchmark") == "Table30v2",
            "runs/robochallenge_submission_package_audit.json",
            "当前可复现链路是 Table30v2；原始 Table30 仍需单独补齐。",
        ),
        field(
            "Robot Type",
            selected.get("robot_type", "aloha"),
            selected.get("robot_type") == "aloha",
            "runs/table30v2_aloha_mapping_audit.json",
            "当前 runner 和数据映射均为 ALOHA。",
        ),
        field(
            "Task Name",
            selected.get("task_name", ""),
            bool(selected.get("task_name")),
            "runs/table30v2_aloha_mapping_audit.json",
            "已验证任务链为 pack_the_toothbrush_holder。",
        ),
        field(
            "Prompt",
            selected.get("prompt", ""),
            bool(selected.get("prompt")),
            "submission/submission_manifest_template.json",
            "runner 默认 prompt 与任务说明一致。",
        ),
        field(
            "Inference Code Link",
            GITHUB_REPO_LINK,
            True,
            "submission/submission_manifest_template.json",
            "建议填写当前 GitHub 主分支；不要在链接里携带凭据。",
        ),
        field(
            "Fine-tuning / Restore Evidence",
            GITHUB_REPO_LINK,
            True,
            "reports/robochallenge_submission_package_checklist.md",
            "同仓库包含 scripts、notebooks、reports 和 LoRA 恢复/物化证据。",
        ),
        field(
            "Checkpoint Link",
            accepted_link_keys[0] if accepted_link_keys else "",
            link_ready,
            "runs/checkpoint_link_intake.json",
            "需要用户授权上传后填入真实可访问 HTTPS 链接；当前不打印链接明文。",
            secret=True,
        ),
        field(
            "RoboChallenge User Token",
            "",
            token_present,
            "runs/real_submission_readiness.json",
            "只能写入本地 env 或 shell，不能写入 tracked 文件。",
            secret=True,
        ),
        field(
            "RoboChallenge Submission ID",
            "",
            submission_id_present,
            "runs/real_submission_readiness.json",
            "必须来自 RoboChallenge 页面，不能伪造。",
            secret=True,
        ),
        field(
            "Submission Variant",
            "baseline 或 lora_materialized",
            False,
            "runs/next_user_action_packet.json",
            "需要用户确认提交官方 ALOHA baseline 还是 LoRA 物化 checkpoint。",
        ),
        field(
            "Checkpoint Upload / Archive",
            "pending_user_authorization",
            upload_channels.get("uploads_performed") is True or inputs.get("uploads_performed") is True,
            "runs/checkpoint_upload_channels_audit.json",
            "LoRA 版本需要用户授权生成 tar、选择上传通道并得到 checkpoint link。",
        ),
        field(
            "Authorized Notebook Entry",
            "Notebook 第 44/45 节",
            action_packet.get("passed") is True,
            "reports/next_user_action_packet.md",
            "推荐先通过 Jupyter 写入 local env，再跑授权预检。",
        ),
    ]
    ready_fields = [item for item in fields if item["ready"]]
    missing_fields = [item for item in fields if not item["ready"]]
    evidence = {
        "package_audit_passed": package.get("passed") is True,
        "readiness_gate_passed": readiness.get("passed") is True,
        "current_web_form_not_ready": readiness.get("web_form_ready") is False,
        "link_intake_passed": link_intake.get("passed") is True,
        "link_download_default_no_contact": link_download.get("verification", {}).get("download_host_contacted") is False,
        "upload_channels_audited": upload_channels.get("passed") is True,
        "action_packet_passed": action_packet.get("passed") is True,
        "secret_scan_clean": secret_scan.get("passed") is True and secret_scan.get("hit_count") == 0,
    }
    leak_flags = {
        "credentials_printed": any(
            bool(item.get("credentials_printed"))
            for item in [package, readiness, link_intake, link_download, upload_channels, action_packet, secret_scan]
        ),
        "link_values_printed": any(
            bool(item.get("link_values_printed") or item.get("link_value_printed"))
            for item in [link_intake, link_download, action_packet, secret_scan]
        ),
        "secret_values_printed": any(
            bool(item.get("secret_values_printed")) for item in [action_packet, secret_scan]
        ),
    }
    contact_flags = {
        "platform_contacted": any(
            bool(item.get("platform_contacted")) for item in [readiness, link_intake, link_download, action_packet]
        ),
        "uploads_performed": any(
            bool(item.get("uploads_performed") or item.get("upload_performed"))
            for item in [readiness, link_intake, upload_channels, action_packet]
        ),
        "download_host_contacted": link_download.get("verification", {}).get("download_host_contacted") is True,
    }
    passed = bool(all(evidence.values()) and not any(leak_flags.values()) and not any(contact_flags.values()))
    blocking = []
    if not passed:
        for name, ok in evidence.items():
            if not ok:
                blocking.append(f"网页表单字段包输入证据未通过 `{name}`。")
        if any(leak_flags.values()):
            blocking.append("输入审计显示存在凭据或链接明文泄露风险。")
        if any(contact_flags.values()):
            blocking.append("输入审计显示曾连接平台、接触下载 host 或执行上传。")
    blocking.extend(
        [
            f"字段 `{item['name']}` 仍未就绪：{item['note']}"
            for item in missing_fields
            if item["name"] in {"Checkpoint Link", "RoboChallenge User Token", "RoboChallenge Submission ID"}
        ]
    )
    if not blocking:
        blocking.append("网页字段来源已整理；真实提交仍以 readiness gate 为准。")

    return {
        "kind": "web_form_field_packet",
        "passed": passed,
        "web_form_ready": web_form_ready,
        "ready_field_count": len(ready_fields),
        "missing_field_count": len(missing_fields),
        "field_count": len(fields),
        "fields": fields,
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
        "# RoboChallenge 网页表单字段包",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- Web 表单当前是否就绪：`{status['web_form_ready']}`。",
        f"- 字段数：`{status['field_count']}`，已就绪 `{status['ready_field_count']}`，待用户补齐 `{status['missing_field_count']}`。",
        "",
        "## 字段清单",
        "",
    ]
    for item in status["fields"]:
        lines.append(f"- `{item['name']}`：ready=`{item['ready']}`，value=`{item['value']}`。")
        lines.append(f"  来源：`{item['source']}`。{item['note']}")
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
