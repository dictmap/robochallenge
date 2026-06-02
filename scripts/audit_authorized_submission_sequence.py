#!/usr/bin/env python3
"""Audit the user-authorized real-submission sequence without executing it."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = ROOT / "runs"
SUBMISSION_DIR = ROOT / "submission"
DEFAULT_DOC = SUBMISSION_DIR / "AUTHORIZED_SUBMISSION_SEQUENCE.md"
DEFAULT_STATUS = RUNS_DIR / "authorized_submission_sequence_audit.json"
DEFAULT_REPORT = REPORTS_DIR / "authorized_submission_sequence_audit.md"

REQUIRED_COMMANDS = [
    "python3 scripts/validate_repro_workspace.py",
    "python3 scripts/audit_plaintext_secrets.py",
    "python3 scripts/audit_submission_env_template.py",
    "python3 scripts/audit_submission_artifact_manifest.py",
    "python3 scripts/create_checkpoint_archive.py",
    "cp submission/robochallenge_env_template.sh submission/robochallenge_env.local.sh",
    "source submission/robochallenge_env.local.sh",
    "python3 scripts/audit_checkpoint_link_intake.py",
    "python3 scripts/audit_real_submission_readiness.py",
    "python3 scripts/audit_submission_blockers_summary.py",
    "bash submission/run_authorized_preflight_template.sh",
    "python3 scripts/create_checkpoint_archive.py --execute --confirm-create-large-archive",
    "ROBOCHALLENGE_DRY_RUN=1 bash submission/run_table30v2_aloha_lora_demo_template.sh",
    "bash submission/run_table30v2_aloha_lora_demo_template.sh",
    "bash submission/run_table30v2_aloha_demo_template.sh",
]

REQUIRED_ENV_KEYS = [
    "ROBOCHALLENGE_USER_TOKEN",
    "ROBOCHALLENGE_SUBMISSION_ID",
    "ROBOCHALLENGE_LORA_CHECKPOINT_LINK",
]

REQUIRED_GUARDRAILS = {
    "no_credentials_saved": ["不保存", "user_token", "submission_id"],
    "local_env_copy_only": ["submission/robochallenge_env.local.sh", "tracked 模板"],
    "no_auto_without_authorization": ["没有用户明确授权", "不生成 tar", "不上传 checkpoint"],
    "no_git_checkpoint": ["不要把 `runs/openpi_rtc_lora_materialized_policy_checkpoint.tar`", "提交进 Git"],
    "link_gate_before_readiness": ["audit_checkpoint_link_intake.py", "audit_real_submission_readiness.py"],
    "dry_run_before_real_runner": ["ROBOCHALLENGE_DRY_RUN=1", "bash submission/run_table30v2_aloha_lora_demo_template.sh"],
    "dry_run_no_checkpoint_plaintext": ["checkpoint 长度", "checkpoint link 明文"],
    "stop_on_not_ready": ["ready_for_real_submission=false", "停止"],
    "stop_on_bad_link": ["link_shape_ready=false", "停止"],
}

SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9_-]{30,}",
    r"hf_[A-Za-z0-9]{20,}",
    r"ghp_[A-Za-z0-9]{30,}",
    r"github_pat_[A-Za-z0-9_]{20,}",
    r"ROBOCHALLENGE_(?:USER_)?TOKEN\s*=\s*[A-Za-z0-9_-]{20,}",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计用户授权后的真实提交顺序，不执行提交命令。")
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC, help="授权后提交顺序清单路径。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文审计报告输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(text: str) -> str:
    return " ".join(text.split())


def command_order(text: str) -> dict[str, Any]:
    lines = [line.strip() for line in text.splitlines()]
    positions: dict[str, int] = {}
    last_positions: dict[str, int] = {}
    for command in REQUIRED_COMMANDS:
        indexes = [index for index, line in enumerate(lines) if line == command]
        if indexes:
            positions[command] = indexes[0]
            last_positions[command] = indexes[-1]
        else:
            positions[command] = -1
            last_positions[command] = -1
    present = {command: index >= 0 for command, index in positions.items()}
    ordered_subset = [
        "source submission/robochallenge_env.local.sh",
        "python3 scripts/audit_checkpoint_link_intake.py",
        "python3 scripts/audit_real_submission_readiness.py",
        "bash submission/run_authorized_preflight_template.sh",
        "ROBOCHALLENGE_DRY_RUN=1 bash submission/run_table30v2_aloha_lora_demo_template.sh",
        "bash submission/run_table30v2_aloha_lora_demo_template.sh",
    ]
    ordered = all(
        present[ordered_subset[i]]
        and present[ordered_subset[i + 1]]
        and last_positions[ordered_subset[i]] < last_positions[ordered_subset[i + 1]]
        for i in range(len(ordered_subset) - 1)
    )
    return {
        "present": present,
        "positions": positions,
        "last_positions": last_positions,
        "critical_order_passed": ordered,
    }


def scan_secret_patterns(text: str) -> list[str]:
    return [pattern for pattern in SECRET_PATTERNS if re.search(pattern, text)]


def build_status(doc_path: Path) -> dict[str, Any]:
    exists = doc_path.exists()
    text = doc_path.read_text(encoding="utf-8") if exists else ""
    commands = command_order(text)
    env_mentions = {key: key in text for key in REQUIRED_ENV_KEYS}
    guardrails = {
        name: all(fragment in text for fragment in fragments) for name, fragments in REQUIRED_GUARDRAILS.items()
    }
    secret_hits = scan_secret_patterns(text)

    archive_dry_run = read_json(RUNS_DIR / "checkpoint_archive_dry_run.json")
    link_intake = read_json(RUNS_DIR / "checkpoint_link_intake.json")
    env_template = read_json(RUNS_DIR / "submission_env_template_audit.json")
    artifact_manifest = read_json(RUNS_DIR / "submission_artifact_manifest.json")
    readiness = read_json(RUNS_DIR / "real_submission_readiness.json")
    blockers_summary = read_json(RUNS_DIR / "submission_blockers_summary.json")
    authorized_preflight = read_json(RUNS_DIR / "authorized_preflight_template_audit.json")
    plaintext_scan = read_json(RUNS_DIR / "plaintext_secret_scan.json")
    handoff = read_json(RUNS_DIR / "submission_handoff_docs_audit.json")

    input_evidence = {
        "archive_dry_run_passed": archive_dry_run.get("passed") is True,
        "archive_not_created": archive_dry_run.get("archive_created") is False,
        "link_intake_passed": link_intake.get("passed") is True,
        "current_link_missing_as_expected": link_intake.get("current_env", {}).get("link_shape_ready") is False,
        "env_template_audit_passed": env_template.get("passed") is True,
        "env_template_local_copy_ignored": env_template.get("local_secret_paths", {})
        .get("submission/robochallenge_env.local.sh", {})
        .get("ignored")
        is True,
        "artifact_manifest_passed": artifact_manifest.get("passed") is True,
        "artifact_manifest_no_forbidden_tracked": artifact_manifest.get("forbidden_tracked_paths") == [],
        "readiness_gate_passed": readiness.get("passed") is True,
        "readiness_currently_blocked": readiness.get("ready_for_real_submission") is False,
        "blockers_summary_passed": blockers_summary.get("passed") is True,
        "blockers_summary_go_no_go_blocked": blockers_summary.get("current_state", {}).get("go_no_go") == "blocked",
        "blockers_summary_ready_false": blockers_summary.get("current_state", {}).get("ready_for_real_submission")
        is False,
        "authorized_preflight_template_passed": authorized_preflight.get("passed") is True,
        "authorized_preflight_no_credentials_smoke_passed": authorized_preflight.get("no_credentials_smoke", {}).get(
            "passed"
        )
        is True,
        "plaintext_scan_passed": plaintext_scan.get("passed") is True,
        "plaintext_hit_count_zero": plaintext_scan.get("hit_count") == 0,
        "handoff_docs_passed": handoff.get("passed") is True,
    }
    no_contact = all(
        [
            archive_dry_run.get("platform_contacted") is False,
            archive_dry_run.get("upload_performed") is False,
            link_intake.get("platform_contacted") is False,
            link_intake.get("uploads_performed") is False,
            env_template.get("platform_contacted") is False,
            env_template.get("uploads_performed") is False,
            env_template.get("credentials_read") is False,
            env_template.get("credentials_printed") is False,
            env_template.get("secret_values_printed") is False,
            artifact_manifest.get("platform_contacted") is False,
            artifact_manifest.get("uploads_performed") is False,
            artifact_manifest.get("credentials_read") is False,
            artifact_manifest.get("credentials_printed") is False,
            artifact_manifest.get("link_values_printed") is False,
            artifact_manifest.get("secret_values_printed") is False,
            readiness.get("platform_contacted") is False,
            blockers_summary.get("platform_contacted") is False,
            blockers_summary.get("uploads_performed") is False,
            blockers_summary.get("credentials_read") is False,
            blockers_summary.get("credentials_printed") is False,
            blockers_summary.get("link_values_printed") is False,
            blockers_summary.get("secret_values_printed") is False,
            authorized_preflight.get("platform_contacted") is False,
            authorized_preflight.get("uploads_performed") is False,
            authorized_preflight.get("credentials_read") is False,
            authorized_preflight.get("credentials_printed") is False,
            authorized_preflight.get("link_values_printed") is False,
            authorized_preflight.get("secret_values_printed") is False,
            handoff.get("platform_contacted") is False,
        ]
    )

    passed = bool(
        exists
        and all(commands["present"].values())
        and commands["critical_order_passed"]
        and all(env_mentions.values())
        and all(guardrails.values())
        and all(input_evidence.values())
        and not secret_hits
        and no_contact
    )
    blocking = []
    if not exists:
        blocking.append("缺少用户授权后的真实提交顺序清单。")
    for command, ok in commands["present"].items():
        if not ok:
            blocking.append(f"清单缺少命令 `{command}`。")
    if not commands["critical_order_passed"]:
        blocking.append("关键命令顺序未通过：link intake -> readiness -> dry-run -> real runner。")
    for key, ok in env_mentions.items():
        if not ok:
            blocking.append(f"清单缺少环境变量 `{key}`。")
    for name, ok in guardrails.items():
        if not ok:
            blocking.append(f"清单缺少安全护栏 `{name}`。")
    for name, ok in input_evidence.items():
        if not ok:
            blocking.append(f"输入证据未通过 `{name}`。")
    if secret_hits:
        blocking.append("清单疑似包含明文 token 或密钥模式。")
    if not no_contact:
        blocking.append("审计输入显示曾连接平台或执行上传。")
    if not blocking:
        blocking.append("清单侧无阻塞；真实执行仍需要用户授权、真实凭据和真实 checkpoint link。")

    return {
        "kind": "authorized_submission_sequence_audit",
        "passed": passed,
        "doc_path": doc_path.relative_to(ROOT).as_posix() if exists else str(doc_path),
        "platform_contacted": False,
        "uploads_performed": False,
        "archive_created": False,
        "credentials_printed": False,
        "link_values_printed": False,
        "commands": commands,
        "env_mentions": env_mentions,
        "guardrails": guardrails,
        "input_evidence": input_evidence,
        "secret_patterns_found": secret_hits,
        "no_contact_evidence": no_contact,
        "blocking": blocking,
    }


def write_report(status: dict[str, Any], path: Path) -> None:
    lines = [
        "# 用户授权后提交顺序审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 清单路径：`{status['doc_path']}`。",
        f"- 是否连接平台：`{status['platform_contacted']}`。",
        f"- 是否执行上传：`{status['uploads_performed']}`。",
        f"- 是否生成归档：`{status['archive_created']}`。",
        f"- 是否打印凭据或链接明文：`{status['credentials_printed'] or status['link_values_printed']}`。",
        f"- 关键顺序是否通过：`{status['commands']['critical_order_passed']}`。",
        "",
        "## 命令覆盖",
        "",
    ]
    for command, ok in status["commands"]["present"].items():
        lines.append(f"- `{command}`：`{ok}`。")
    lines.extend(["", "## 环境变量覆盖", ""])
    for key, ok in status["env_mentions"].items():
        lines.append(f"- `{key}`：`{ok}`。")
    lines.extend(["", "## 安全护栏", ""])
    for key, ok in status["guardrails"].items():
        lines.append(f"- `{key}`：`{ok}`。")
    lines.extend(["", "## 输入证据", ""])
    for key, ok in status["input_evidence"].items():
        lines.append(f"- `{key}`：`{ok}`。")
    lines.extend(["", "## Blocking", ""])
    for item in status["blocking"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    status = build_status(args.doc_path)
    args.status_path.parent.mkdir(parents=True, exist_ok=True)
    args.status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(status, args.report_path)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
