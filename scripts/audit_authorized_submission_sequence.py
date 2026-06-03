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
    "python3 scripts/audit_jupyter_input_template.py",
    "python3 scripts/audit_jupyter_authorized_preflight_template.py",
    "python3 scripts/render_route_aware_submission_blockers.py",
    "python3 scripts/render_baseline_submission_quickstart.py",
    "cp submission/robochallenge_env_template.sh submission/robochallenge_env.local.sh",
    "source submission/robochallenge_env.local.sh",
    "python3 scripts/audit_checkpoint_link_intake.py",
    "python3 scripts/audit_real_submission_readiness.py",
    "python3 scripts/audit_submission_blockers_summary.py",
    "python3 scripts/audit_ready_real_runner_template.py",
    "python3 scripts/audit_authorized_checkpoint_archive_template.py",
    "bash submission/run_authorized_preflight_template.sh",
    "bash submission/run_authorized_checkpoint_archive_template.sh",
    (
        "ROBOCHALLENGE_ARCHIVE_CONFIRM=CREATE_ROBOCHALLENGE_CHECKPOINT_ARCHIVE "
        "bash submission/run_authorized_checkpoint_archive_template.sh"
    ),
    "ROBOCHALLENGE_DRY_RUN=1 bash submission/run_table30v2_aloha_lora_demo_template.sh",
    "ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION bash submission/run_ready_real_submission_template.sh",
    (
        "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline "
        "ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION "
        "bash submission/run_ready_real_submission_template.sh"
    ),
    "bash submission/run_table30v2_aloha_lora_demo_template.sh",
    "bash submission/run_table30v2_aloha_demo_template.sh",
]

REQUIRED_ENV_KEYS = [
    "ROBOCHALLENGE_SUBMISSION_TARGET_CONFIRMATION",
    "ROBOCHALLENGE_USER_TOKEN",
    "ROBOCHALLENGE_SUBMISSION_ID",
    "ROBOCHALLENGE_SUBMISSION_VARIANT",
    "ROBOCHALLENGE_LORA_CHECKPOINT_LINK",
]

REQUIRED_PATHS = [
    "notebooks/robochallenge_pi05_submit_cn.ipynb",
    "scripts/audit_jupyter_input_template.py",
    "scripts/audit_jupyter_authorized_preflight_template.py",
    "scripts/render_route_aware_submission_blockers.py",
    "scripts/render_baseline_submission_quickstart.py",
    "submission/robochallenge_env.local.sh",
]

REQUIRED_GUARDRAILS = {
    "no_credentials_saved": ["不保存", "user_token", "submission_id"],
    "local_env_copy_only": ["submission/robochallenge_env.local.sh", "tracked 模板"],
    "jupyter_input_default_safe": [
        "RUN_SAFE_LOCAL_ENV_INPUT_TEMPLATE=False",
        "RUN_SAFE_LOCAL_ENV_INPUT_TEMPLATE=True",
        "getpass",
    ],
    "jupyter_preflight_default_safe": [
        "RUN_JUPYTER_AUTHORIZED_PREFLIGHT_TEMPLATE_AUDIT=True",
        "RUN_JUPYTER_AUTHORIZED_PREFLIGHT=False",
        "RUN_JUPYTER_AUTHORIZED_PREFLIGHT=True",
        "默认只执行静态审计",
    ],
    "jupyter_values_stay_local": ["真实值只能进入", "Git 忽略", "不写入 tracked 模板、Git、Notebook、报告"],
    "route_aware_baseline_no_link": [
        "路线感知摘要",
        "baseline 不需要 checkpoint link",
        "LoRA/web checkpoint 路线仍必须显示需要归档/上传授权和真实 checkpoint link",
    ],
    "baseline_quickstart_first": [
        "默认先走官方 Table30v2 ALOHA baseline",
        "render_baseline_submission_quickstart.py",
        "不需要生成 tar、不需要上传 checkpoint、不需要 checkpoint link",
    ],
    "baseline_local_env_link_optional": [
        "ROBOCHALLENGE_SUBMISSION_TARGET_CONFIRMATION=CONFIRM_TABLE30V2_ALOHA_BASELINE",
        "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline",
        "ROBOCHALLENGE_CHECKPOINT_LINK` 可以留空",
    ],
    "target_confirmation_exact_match": [
        "ROBOCHALLENGE_SUBMISSION_TARGET_CONFIRMATION=CONFIRM_TABLE30V2_ALOHA_BASELINE",
        "目标确认",
    ],
    "lora_web_link_branch": [
        "只有明确选择 LoRA/web checkpoint 路线",
        "才继续执行下面的归档、上传和 link 回填步骤",
    ],
    "no_auto_without_authorization": ["没有用户明确授权", "不生成 tar", "不上传 checkpoint"],
    "no_git_checkpoint": ["不要把 `runs/openpi_rtc_lora_materialized_policy_checkpoint.tar`", "提交进 Git"],
    "link_gate_before_readiness": ["audit_checkpoint_link_intake.py", "audit_real_submission_readiness.py"],
    "dry_run_before_real_runner": ["ROBOCHALLENGE_DRY_RUN=1", "bash submission/run_table30v2_aloha_lora_demo_template.sh"],
    "dry_run_no_checkpoint_plaintext": ["checkpoint 长度", "checkpoint link 明文"],
    "archive_confirmation_required": [
        "ROBOCHALLENGE_ARCHIVE_CONFIRM=CREATE_ROBOCHALLENGE_CHECKPOINT_ARCHIVE",
        "stop before creating tar",
    ],
    "real_runner_confirmation_required": [
        "ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION",
        "停在真实 runner 前",
    ],
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
        "ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION bash submission/run_ready_real_submission_template.sh",
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
    path_mentions = {path: path in text for path in REQUIRED_PATHS}
    guardrails = {
        name: all(fragment in text for fragment in fragments) for name, fragments in REQUIRED_GUARDRAILS.items()
    }
    secret_hits = scan_secret_patterns(text)

    archive_dry_run = read_json(RUNS_DIR / "checkpoint_archive_dry_run.json")
    link_intake = read_json(RUNS_DIR / "checkpoint_link_intake.json")
    env_template = read_json(RUNS_DIR / "submission_env_template_audit.json")
    jupyter_input = read_json(RUNS_DIR / "jupyter_input_template_audit.json")
    jupyter_authorized = read_json(RUNS_DIR / "jupyter_authorized_preflight_template_audit.json")
    artifact_manifest = read_json(RUNS_DIR / "submission_artifact_manifest.json")
    route_aware_blockers = read_json(RUNS_DIR / "route_aware_submission_blockers.json")
    baseline_quickstart = read_json(RUNS_DIR / "baseline_submission_quickstart.json")
    readiness = read_json(RUNS_DIR / "real_submission_readiness.json")
    blockers_summary = read_json(RUNS_DIR / "submission_blockers_summary.json")
    authorized_preflight = read_json(RUNS_DIR / "authorized_preflight_template_audit.json")
    ready_real_runner = read_json(RUNS_DIR / "ready_real_runner_template_audit.json")
    authorized_archive = read_json(RUNS_DIR / "authorized_checkpoint_archive_template_audit.json")
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
        "jupyter_input_template_passed": jupyter_input.get("passed") is True,
        "jupyter_input_default_false": jupyter_input.get("run_flag_default_false") is True,
        "jupyter_input_local_env_ignored": jupyter_input.get("local_env_ignored", {}).get("ignored") is True,
        "jupyter_authorized_preflight_template_passed": jupyter_authorized.get("passed") is True,
        "jupyter_authorized_preflight_audit_default_true": jupyter_authorized.get("audit_default_true") is True,
        "jupyter_authorized_preflight_execution_default_false": jupyter_authorized.get("execution_default_false")
        is True,
        "jupyter_authorized_preflight_runner_not_started": jupyter_authorized.get("runner_started") is False,
        "artifact_manifest_passed": artifact_manifest.get("passed") is True,
        "artifact_manifest_no_forbidden_tracked": artifact_manifest.get("forbidden_tracked_paths") == [],
        "route_aware_blockers_passed": route_aware_blockers.get("passed") is True,
        "route_aware_recommended_baseline": route_aware_blockers.get("recommended_route") == "baseline_official_aloha",
        "route_aware_baseline_no_link": route_aware_blockers.get("baseline_requires_checkpoint_link") is False,
        "route_aware_baseline_no_upload": route_aware_blockers.get("baseline_requires_checkpoint_upload") is False,
        "route_aware_lora_web_needs_link": route_aware_blockers.get("lora_web_requires_checkpoint_link") is True,
        "baseline_quickstart_passed": baseline_quickstart.get("passed") is True,
        "baseline_quickstart_no_link": baseline_quickstart.get("requires_checkpoint_link") is False,
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
        "ready_real_runner_template_passed": ready_real_runner.get("passed") is True,
        "ready_real_runner_no_credentials_smoke_passed": ready_real_runner.get("no_credentials_smoke", {}).get(
            "passed"
        )
        is True,
        "ready_real_runner_no_confirm_smoke_passed": ready_real_runner.get("synthetic_no_confirm_smoke", {}).get(
            "passed"
        )
        is True,
        "authorized_checkpoint_archive_template_passed": authorized_archive.get("passed") is True,
        "authorized_checkpoint_archive_no_confirm_smoke_passed": authorized_archive.get("no_confirm_smoke", {}).get(
            "passed"
        )
        is True,
        "authorized_checkpoint_archive_not_created": authorized_archive.get("no_confirm_smoke", {}).get(
            "archive_created"
        )
        is False,
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
            jupyter_input.get("platform_contacted") is False,
            jupyter_input.get("uploads_performed") is False,
            jupyter_input.get("credentials_read") is False,
            jupyter_input.get("credentials_printed") is False,
            jupyter_input.get("link_values_printed") is False,
            jupyter_input.get("secret_values_printed") is False,
            jupyter_authorized.get("platform_contacted") is False,
            jupyter_authorized.get("uploads_performed") is False,
            jupyter_authorized.get("credentials_read") is False,
            jupyter_authorized.get("credentials_printed") is False,
            jupyter_authorized.get("link_values_printed") is False,
            jupyter_authorized.get("secret_values_printed") is False,
            jupyter_authorized.get("runner_started") is False,
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
            ready_real_runner.get("platform_contacted") is False,
            ready_real_runner.get("uploads_performed") is False,
            ready_real_runner.get("credentials_read") is False,
            ready_real_runner.get("credentials_printed") is False,
            ready_real_runner.get("link_values_printed") is False,
            ready_real_runner.get("secret_values_printed") is False,
            authorized_archive.get("platform_contacted") is False,
            authorized_archive.get("uploads_performed") is False,
            authorized_archive.get("credentials_read") is False,
            authorized_archive.get("credentials_printed") is False,
            authorized_archive.get("link_values_printed") is False,
            authorized_archive.get("secret_values_printed") is False,
            handoff.get("platform_contacted") is False,
        ]
    )

    passed = bool(
        exists
        and all(commands["present"].values())
        and commands["critical_order_passed"]
        and all(env_mentions.values())
        and all(path_mentions.values())
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
    for path, ok in path_mentions.items():
        if not ok:
            blocking.append(f"清单缺少路径 `{path}`。")
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
        blocking.append(
            "清单侧无阻塞；baseline 仍需要用户目标确认、token、submission id、variant=baseline 和真实 runner 强确认，"
            "LoRA/web checkpoint 路线额外需要授权上传和真实 checkpoint link。"
        )

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
        "path_mentions": path_mentions,
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
    lines.extend(["", "## 路径覆盖", ""])
    for key, ok in status["path_mentions"].items():
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
