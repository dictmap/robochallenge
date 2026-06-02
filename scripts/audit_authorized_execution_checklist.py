#!/usr/bin/env python3
"""Build a no-contact checklist for user-authorized RoboChallenge execution."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = ROOT / "runs"
DEFAULT_STATUS = RUNS_DIR / "authorized_execution_checklist.json"
DEFAULT_REPORT = REPORTS_DIR / "authorized_execution_checklist.md"

REQUIRED_USER_DECISIONS = [
    {
        "id": "SUBMISSION_TARGET_CONFIRMATION",
        "label": "提交对象确认",
        "required": True,
        "detail": "需要用户确认提交 Table30v2 ALOHA；原始 Table30 还不能直接沿用当前链路。",
    },
    {
        "id": "ROBOCHALLENGE_USER_TOKEN",
        "label": "RoboChallenge user token",
        "required": True,
        "detail": "只能放入本地 shell 或被 Git 忽略的 local env 文件，不能写入 tracked 文件。",
    },
    {
        "id": "ROBOCHALLENGE_SUBMISSION_ID",
        "label": "RoboChallenge submission id",
        "required": True,
        "detail": "必须来自 RoboChallenge 页面，不能伪造。",
    },
    {
        "id": "ROBOCHALLENGE_CHECKPOINT_LINK",
        "label": "真实 checkpoint link",
        "required": True,
        "detail": "LoRA 提交需要可访问 checkpoint link；默认只做脱敏形态检查。",
    },
    {
        "id": "CHECKPOINT_ARCHIVE_AUTHORIZATION",
        "label": "checkpoint 归档授权",
        "required": True,
        "detail": "生成 11GB+ tar 前必须显式设置归档确认短语。",
    },
    {
        "id": "ROBOCHALLENGE_REAL_RUN_CONFIRM",
        "label": "真实 runner 强确认",
        "required": True,
        "detail": "启动真实 runner 前必须显式设置真实提交确认短语。",
    },
]

AUTHORIZED_STEPS = [
    {
        "step": 1,
        "name": "Jupyter 安全填空本地 env",
        "command": "Notebook 第 44 节：RUN_SAFE_LOCAL_ENV_INPUT_TEMPLATE=True",
        "guard": "只写入被 Git 忽略的 submission/robochallenge_env.local.sh；不把真实 token/link 写入 Notebook 源码或 tracked 文件。",
    },
    {
        "step": 2,
        "name": "填写本地 env",
        "command": "cp submission/robochallenge_env_template.sh submission/robochallenge_env.local.sh",
        "guard": "只编辑被 Git 忽略的 local env 文件；不把真实 token 写入 tracked 文件。",
    },
    {
        "step": 3,
        "name": "加载本地 env",
        "command": "source submission/robochallenge_env.local.sh",
        "guard": "shell 中加载，不打印变量值。",
    },
    {
        "step": 4,
        "name": "Jupyter 授权预检",
        "command": "Notebook 第 45 节：RUN_JUPYTER_AUTHORIZED_PREFLIGHT=True",
        "guard": "只运行授权预检模板；不生成 tar、不上传、不启动真实 runner。",
    },
    {
        "step": 5,
        "name": "只读预检",
        "command": "bash submission/run_authorized_preflight_template.sh",
        "guard": "如果 ready_for_real_submission=false，必须停止。",
    },
    {
        "step": 6,
        "name": "可选下载校验",
        "command": "python3 scripts/audit_checkpoint_link_download_verification.py --verify-download",
        "guard": "只有用户明确允许联网验证 checkpoint link 时才运行。",
    },
    {
        "step": 7,
        "name": "可选 checkpoint 归档",
        "command": (
            "ROBOCHALLENGE_ARCHIVE_CONFIRM=CREATE_ROBOCHALLENGE_CHECKPOINT_ARCHIVE "
            "bash submission/run_authorized_checkpoint_archive_template.sh"
        ),
        "guard": "只有用户明确授权生成 11GB+ tar 时才运行。",
    },
    {
        "step": 8,
        "name": "真实 runner 强确认",
        "command": (
            "ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION "
            "bash submission/run_ready_real_submission_template.sh"
        ),
        "guard": "只有 readiness、dry-run 和确认短语全部通过后才会进入真实 runner。",
    },
]

MUST_STOP_IF = [
    "未确认提交对象是 Table30v2 ALOHA。",
    "缺少 ROBOCHALLENGE_USER_TOKEN。",
    "缺少 ROBOCHALLENGE_SUBMISSION_ID。",
    "缺少真实 checkpoint link。",
    "ready_for_real_submission=false。",
    "link_shape_ready=false。",
    "未设置 ROBOCHALLENGE_ARCHIVE_CONFIRM 但试图生成 checkpoint tar。",
    "未设置 ROBOCHALLENGE_REAL_RUN_CONFIRM 但试图启动真实 runner。",
]

REQUIRED_EVIDENCE_KEYS = [
    "readiness_gate_passed",
    "readiness_currently_false",
    "web_form_currently_false",
    "token_missing_as_expected",
    "submission_id_missing_as_expected",
    "checkpoint_link_missing_as_expected",
    "env_template_passed",
    "local_env_ignored",
    "jupyter_input_template_passed",
    "jupyter_local_env_ignored",
    "jupyter_authorized_preflight_template_passed",
    "jupyter_authorized_preflight_default_off",
    "authorized_preflight_template_passed",
    "ready_real_runner_template_passed",
    "real_runner_confirmation_phrase",
    "real_runner_no_confirm_blocks",
    "authorized_archive_template_passed",
    "archive_confirmation_phrase",
    "archive_no_confirm_blocks",
    "archive_not_created_without_confirm",
    "authorized_sequence_passed",
    "notebook_structure_passed",
    "secret_scan_clean",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成授权执行清单；不读取凭据、不联网、不上传。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文报告输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def values_false(*values: Any) -> bool:
    return all(value is False for value in values)


def build_status() -> dict[str, Any]:
    preflight = read_json(RUNS_DIR / "submission_preflight_bundle.json")
    blockers = read_json(RUNS_DIR / "submission_blockers_summary.json")
    readiness = read_json(RUNS_DIR / "real_submission_readiness.json")
    link_intake = read_json(RUNS_DIR / "checkpoint_link_intake.json")
    env_template = read_json(RUNS_DIR / "submission_env_template_audit.json")
    jupyter_input = read_json(RUNS_DIR / "jupyter_input_template_audit.json")
    jupyter_authorized = read_json(RUNS_DIR / "jupyter_authorized_preflight_template_audit.json")
    authorized_preflight = read_json(RUNS_DIR / "authorized_preflight_template_audit.json")
    ready_real_runner = read_json(RUNS_DIR / "ready_real_runner_template_audit.json")
    authorized_archive = read_json(RUNS_DIR / "authorized_checkpoint_archive_template_audit.json")
    authorized_sequence = read_json(RUNS_DIR / "authorized_submission_sequence_audit.json")
    secret_scan = read_json(RUNS_DIR / "plaintext_secret_scan.json")
    notebook_structure = read_json(RUNS_DIR / "notebook_structure_audit.json")

    readiness_env = readiness.get("env", {})
    blockers_state = blockers.get("current_state", {})
    archive_smoke = authorized_archive.get("no_confirm_smoke", {})
    runner_smoke = ready_real_runner.get("synthetic_no_confirm_smoke", {})

    evidence = {
        "preflight_bundle_passed": preflight.get("passed") is True,
        "preflight_go_no_go_blocked": preflight.get("go_no_go") == "blocked",
        "blockers_summary_passed": blockers.get("passed") is True,
        "blockers_summary_go_no_go_blocked": blockers_state.get("go_no_go") == "blocked",
        "readiness_gate_passed": readiness.get("passed") is True,
        "readiness_currently_false": readiness.get("ready_for_real_submission") is False,
        "web_form_currently_false": readiness.get("web_form_ready") is False,
        "token_missing_as_expected": readiness_env.get("ROBOCHALLENGE_USER_TOKEN", {}).get("present") is False,
        "submission_id_missing_as_expected": readiness_env.get("ROBOCHALLENGE_SUBMISSION_ID", {}).get("present")
        is False,
        "checkpoint_link_missing_as_expected": link_intake.get("current_env", {}).get("link_shape_ready") is False,
        "env_template_passed": env_template.get("passed") is True,
        "local_env_ignored": env_template.get("local_secret_paths", {})
        .get("submission/robochallenge_env.local.sh", {})
        .get("ignored")
        is True,
        "jupyter_input_template_passed": jupyter_input.get("passed") is True,
        "jupyter_local_env_ignored": jupyter_input.get("local_env_ignored", {}).get("ignored") is True,
        "jupyter_authorized_preflight_template_passed": jupyter_authorized.get("passed") is True,
        "jupyter_authorized_preflight_default_off": jupyter_authorized.get("execution_default_false") is True,
        "authorized_preflight_template_passed": authorized_preflight.get("passed") is True,
        "ready_real_runner_template_passed": ready_real_runner.get("passed") is True,
        "real_runner_confirmation_phrase": ready_real_runner.get("confirmation_phrase")
        == "RUN_REAL_ROBOCHALLENGE_SUBMISSION",
        "real_runner_no_confirm_blocks": runner_smoke.get("passed") is True,
        "authorized_archive_template_passed": authorized_archive.get("passed") is True,
        "archive_confirmation_phrase": authorized_archive.get("confirmation_phrase")
        == "CREATE_ROBOCHALLENGE_CHECKPOINT_ARCHIVE",
        "archive_no_confirm_blocks": archive_smoke.get("passed") is True,
        "archive_not_created_without_confirm": archive_smoke.get("archive_created") is False,
        "authorized_sequence_passed": authorized_sequence.get("passed") is True,
        "notebook_structure_passed": notebook_structure.get("passed") is True,
        "secret_scan_clean": secret_scan.get("passed") is True and secret_scan.get("hit_count") == 0,
    }

    leak_flags = {
        "credentials_printed": bool(preflight.get("leak_flags", {}).get("credentials_printed"))
        or bool(blockers.get("credentials_printed"))
        or bool(readiness.get("credentials_printed"))
        or bool(jupyter_input.get("credentials_printed"))
        or bool(jupyter_authorized.get("credentials_printed"))
        or bool(authorized_preflight.get("credentials_printed"))
        or bool(ready_real_runner.get("credentials_printed"))
        or bool(authorized_archive.get("credentials_printed")),
        "link_values_printed": bool(preflight.get("leak_flags", {}).get("link_values_printed"))
        or bool(blockers.get("link_values_printed"))
        or bool(link_intake.get("link_values_printed"))
        or bool(jupyter_input.get("link_values_printed"))
        or bool(jupyter_authorized.get("link_values_printed"))
        or bool(authorized_preflight.get("link_values_printed"))
        or bool(ready_real_runner.get("link_values_printed"))
        or bool(authorized_archive.get("link_values_printed")),
        "secret_values_printed": bool(preflight.get("leak_flags", {}).get("secret_values_printed"))
        or bool(blockers.get("secret_values_printed"))
        or bool(secret_scan.get("secret_values_printed"))
        or bool(jupyter_input.get("secret_values_printed"))
        or bool(jupyter_authorized.get("secret_values_printed"))
        or bool(authorized_preflight.get("secret_values_printed"))
        or bool(ready_real_runner.get("secret_values_printed"))
        or bool(authorized_archive.get("secret_values_printed")),
    }
    contact_flags = {
        "platform_contacted": bool(preflight.get("contact_flags", {}).get("platform_contacted"))
        or bool(blockers.get("platform_contacted"))
        or bool(readiness.get("platform_contacted"))
        or bool(jupyter_input.get("platform_contacted"))
        or bool(jupyter_authorized.get("platform_contacted"))
        or bool(authorized_preflight.get("platform_contacted"))
        or bool(ready_real_runner.get("platform_contacted"))
        or bool(authorized_archive.get("platform_contacted")),
        "uploads_performed": bool(preflight.get("contact_flags", {}).get("uploads_performed"))
        or bool(blockers.get("uploads_performed"))
        or bool(readiness.get("uploads_performed"))
        or bool(jupyter_input.get("uploads_performed"))
        or bool(jupyter_authorized.get("uploads_performed"))
        or bool(authorized_preflight.get("uploads_performed"))
        or bool(ready_real_runner.get("uploads_performed"))
        or bool(authorized_archive.get("uploads_performed")),
        "download_host_contacted": bool(preflight.get("contact_flags", {}).get("download_host_contacted")),
    }

    required_evidence_passed = all(evidence.get(key) is True for key in REQUIRED_EVIDENCE_KEYS)
    passed = bool(required_evidence_passed and not any(leak_flags.values()) and not any(contact_flags.values()))
    current_blocking = list(blockers.get("blocking", [])) or list(preflight.get("blocking", []))
    return {
        "kind": "authorized_execution_checklist",
        "passed": passed,
        "go_no_go": "blocked_by_user_inputs",
        "ready_for_real_submission": False,
        "platform_contacted": False,
        "uploads_performed": False,
        "credentials_read": False,
        "credentials_printed": False,
        "link_values_printed": False,
        "secret_values_printed": False,
        "current_runnable_target": "Table30v2 ALOHA",
        "current_release_gap": "pi0.6/pi0.7 未发现公开 checkpoint；本清单只覆盖 pi0.5 当前链路。",
        "required_user_decisions": REQUIRED_USER_DECISIONS,
        "authorized_steps": AUTHORIZED_STEPS,
        "must_stop_if": MUST_STOP_IF,
        "evidence": evidence,
        "required_evidence_keys": REQUIRED_EVIDENCE_KEYS,
        "required_evidence_passed": required_evidence_passed,
        "leak_flags": leak_flags,
        "contact_flags": contact_flags,
        "blocking": current_blocking,
    }


def write_report(status: dict[str, Any], path: Path) -> None:
    lines = [
        "# 授权执行清单审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- go/no-go：`{status['go_no_go']}`。",
        f"- 当前可运行目标：`{status['current_runnable_target']}`。",
        f"- 真实提交就绪：`{status['ready_for_real_submission']}`。",
        f"- 是否连接平台：`{status['platform_contacted']}`。",
        f"- 是否上传：`{status['uploads_performed']}`。",
        f"- 是否读取真实凭据：`{status['credentials_read']}`。",
        "",
        "## 需要用户确认或提供",
        "",
    ]
    for item in status["required_user_decisions"]:
        lines.append(f"- `{item['id']}`：{item['detail']}")
    lines.extend(["", "## 授权后执行顺序", ""])
    for item in status["authorized_steps"]:
        lines.append(f"{item['step']}. {item['name']}：`{item['command']}`")
        lines.append(f"   - 边界：{item['guard']}")
    lines.extend(["", "## 必须停止的情况", ""])
    for item in status["must_stop_if"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 本地证据", ""])
    for key, ok in status["evidence"].items():
        lines.append(f"- `{key}`：`{ok}`。")
    lines.extend(["", "## 当前阻塞项", ""])
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
