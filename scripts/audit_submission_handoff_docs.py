#!/usr/bin/env python3
"""Audit the real-submission handoff document without reading or printing credentials."""

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
DEFAULT_DOC = SUBMISSION_DIR / "REAL_SUBMISSION_HANDOFF.md"
DEFAULT_STATUS = RUNS_DIR / "submission_handoff_docs_audit.json"
DEFAULT_REPORT = REPORTS_DIR / "submission_handoff_docs_audit.md"


REQUIRED_ENV_KEYS = [
    "ROBOCHALLENGE_SUBMISSION_TARGET_CONFIRMATION",
    "ROBOCHALLENGE_USER_TOKEN",
    "ROBOCHALLENGE_SUBMISSION_ID",
    "ROBOCHALLENGE_SUBMISSION_VARIANT",
    "ROBOCHALLENGE_LORA_CHECKPOINT_LINK",
]

REQUIRED_PATHS = [
    "submission/run_table30v2_aloha_demo_template.sh",
    "submission/run_table30v2_aloha_lora_demo_template.sh",
    "submission/run_authorized_preflight_template.sh",
    "submission/run_ready_real_submission_template.sh",
    "submission/run_authorized_checkpoint_archive_template.sh",
    "notebooks/robochallenge_pi05_submit_cn.ipynb",
    "submission/AUTHORIZED_SUBMISSION_SEQUENCE.md",
    "submission/robochallenge_env_template.sh",
    "runs/openpi_rtc_lora_materialized_policy_checkpoint",
    "runs/openpi_rtc_lora_materialized_policy_checkpoint.tar",
    "runs/openpi_rtc_lora_materialized_policy_checkpoint.tar.sha256",
    "scripts/audit_checkpoint_link_intake.py",
    "scripts/audit_checkpoint_link_download_verification.py",
    "scripts/audit_submission_env_template.py",
    "scripts/audit_submission_artifact_manifest.py",
    "scripts/audit_submission_blockers_summary.py",
    "scripts/render_route_aware_submission_blockers.py",
    "scripts/audit_jupyter_input_template.py",
    "scripts/audit_jupyter_authorized_preflight_template.py",
    "scripts/audit_authorized_preflight_template.py",
    "scripts/audit_ready_real_runner_template.py",
    "scripts/audit_authorized_checkpoint_archive_template.py",
    "scripts/audit_real_submission_readiness.py",
    "scripts/audit_submission_preflight_bundle.py",
    "reports/route_aware_submission_blockers.md",
]

REQUIRED_COMMAND_FRAGMENTS = {
    "checkpoint_link_intake": "python3 scripts/audit_checkpoint_link_intake.py",
    "checkpoint_link_download_default": "python3 scripts/audit_checkpoint_link_download_verification.py",
    "checkpoint_link_download_verify": "python3 scripts/audit_checkpoint_link_download_verification.py --verify-download",
    "submission_env_template": "python3 scripts/audit_submission_env_template.py",
    "submission_artifact_manifest": "python3 scripts/audit_submission_artifact_manifest.py",
    "submission_blockers_summary": "python3 scripts/audit_submission_blockers_summary.py",
    "route_aware_submission_blockers": "python3 scripts/render_route_aware_submission_blockers.py",
    "jupyter_input_template": "python3 scripts/audit_jupyter_input_template.py",
    "jupyter_authorized_preflight_template": "python3 scripts/audit_jupyter_authorized_preflight_template.py",
    "jupyter_input_enable_flag": "RUN_SAFE_LOCAL_ENV_INPUT_TEMPLATE=True",
    "target_confirmation_value": "CONFIRM_TABLE30V2_ALOHA_BASELINE",
    "jupyter_authorized_preflight_enable_flag": "RUN_JUPYTER_AUTHORIZED_PREFLIGHT=True",
    "authorized_preflight_template": "python3 scripts/audit_authorized_preflight_template.py",
    "ready_real_runner_template": "python3 scripts/audit_ready_real_runner_template.py",
    "authorized_checkpoint_archive_template": "python3 scripts/audit_authorized_checkpoint_archive_template.py",
    "authorized_checkpoint_archive_dry_run": "bash submission/run_authorized_checkpoint_archive_template.sh",
    "authorized_checkpoint_archive_confirm": (
        "ROBOCHALLENGE_ARCHIVE_CONFIRM=CREATE_ROBOCHALLENGE_CHECKPOINT_ARCHIVE "
        "bash submission/run_authorized_checkpoint_archive_template.sh"
    ),
    "authorized_preflight_runner": "bash submission/run_authorized_preflight_template.sh",
    "ready_real_runner": (
        "ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION "
        "bash submission/run_ready_real_submission_template.sh"
    ),
    "ready_real_runner_baseline": (
        "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline "
        "ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION "
        "bash submission/run_ready_real_submission_template.sh"
    ),
    "submission_preflight_bundle": "python3 scripts/audit_submission_preflight_bundle.py",
    "authorized_submission_sequence": "python3 scripts/audit_authorized_submission_sequence.py",
    "readiness_gate": "python3 scripts/audit_real_submission_readiness.py",
    "lora_runner_dry_run": "ROBOCHALLENGE_DRY_RUN=1 bash submission/run_table30v2_aloha_lora_demo_template.sh",
    "baseline_runner": "bash submission/run_table30v2_aloha_demo_template.sh",
    "lora_runner": "bash submission/run_table30v2_aloha_lora_demo_template.sh",
}

SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9_-]{30,}",
    r"hf_[A-Za-z0-9]{20,}",
    r"ROBOCHALLENGE_(?:USER_)?TOKEN\s*=\s*[A-Za-z0-9_-]{20,}",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计真实提交交接文档，不连接平台、不读取凭据明文。")
    parser.add_argument("--doc-path", type=Path, default=DEFAULT_DOC, help="交接文档路径。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文审计报告输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(text: str) -> str:
    return " ".join(text.split())


def scan_secret_patterns(text: str) -> list[str]:
    hits = []
    for pattern in SECRET_PATTERNS:
        if re.search(pattern, text):
            hits.append(pattern)
    return hits


def build_status(doc_path: Path) -> dict[str, Any]:
    exists = doc_path.exists()
    text = doc_path.read_text(encoding="utf-8") if exists else ""
    flat_text = normalize(text)
    real_submission = read_json(RUNS_DIR / "real_submission_readiness.json")
    export_audit = read_json(RUNS_DIR / "lora_checkpoint_export_readiness.json")
    upload_audit = read_json(RUNS_DIR / "checkpoint_upload_channels_audit.json")
    link_download = read_json(RUNS_DIR / "checkpoint_link_download_verification.json")
    jupyter_input = read_json(RUNS_DIR / "jupyter_input_template_audit.json")
    jupyter_authorized = read_json(RUNS_DIR / "jupyter_authorized_preflight_template_audit.json")
    ready_real_runner = read_json(RUNS_DIR / "ready_real_runner_template_audit.json")
    authorized_archive = read_json(RUNS_DIR / "authorized_checkpoint_archive_template_audit.json")
    route_aware_blockers = read_json(RUNS_DIR / "route_aware_submission_blockers.json")

    env_mentions = {key: key in text for key in REQUIRED_ENV_KEYS}
    path_mentions = {path: path in text for path in REQUIRED_PATHS}
    command_mentions = {
        name: normalize(fragment) in flat_text for name, fragment in REQUIRED_COMMAND_FRAGMENTS.items()
    }
    guardrails = {
        "says_no_plaintext_credentials": "不保存明文" in text and "不要把真实 token" in text,
        "says_no_fake_submission": "不要伪造" in text,
        "says_no_upload_without_authorization": "未获得用户授权" in text,
        "says_no_git_checkpoint": "不要把 `runs/openpi_rtc_lora_materialized_policy_checkpoint.tar`" in text,
        "says_stop_when_not_ready": "ready_for_real_submission=false" in text,
        "says_dry_run_no_credentials": "不会打印 token" in text and "submission id" in text,
        "says_dry_run_no_checkpoint_plaintext": "checkpoint 长度" in text
        and "checkpoint/link 明文" in text,
        "says_link_intake_no_plaintext": "不打印链接明文" in text,
        "says_download_verify_no_contact_by_default": "默认不联网、不下载" in text,
        "says_download_verify_no_plaintext": "不打印链接明文" in text and "HEAD 和 1MiB Range smoke" in text,
        "uses_placeholders_instead_of_values": "<真实 user token>" in text and "<真实 checkpoint 下载 URL>" in text,
        "says_real_runner_requires_confirmation": "ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION"
        in text
        and "停在真实 runner 前" in text,
        "says_archive_requires_confirmation": "ROBOCHALLENGE_ARCHIVE_CONFIRM=CREATE_ROBOCHALLENGE_CHECKPOINT_ARCHIVE"
        in text
        and "stop before creating tar" in text,
        "says_jupyter_input_default_safe": "RUN_SAFE_LOCAL_ENV_INPUT_TEMPLATE=False" in text
        and "RUN_SAFE_LOCAL_ENV_INPUT_TEMPLATE=True" in text
        and "默认" in text,
        "says_jupyter_preflight_default_safe": "RUN_JUPYTER_AUTHORIZED_PREFLIGHT_TEMPLATE_AUDIT=True"
        in text
        and "RUN_JUPYTER_AUTHORIZED_PREFLIGHT=False" in text
        and "RUN_JUPYTER_AUTHORIZED_PREFLIGHT=True" in text,
        "says_jupyter_values_stay_local": "Notebook 源码" in text
        and "Notebook 输出" in text
        and "submission/robochallenge_env.local.sh" in text,
        "says_baseline_target_confirmation": "ROBOCHALLENGE_SUBMISSION_TARGET_CONFIRMATION=CONFIRM_TABLE30V2_ALOHA_BASELINE"
        in text,
        "says_route_aware_summary_exists": "reports/route_aware_submission_blockers.md" in text,
        "says_baseline_no_checkpoint_link": "baseline 官方路线不需要 checkpoint link" in text,
        "says_baseline_no_upload_or_archive": "checkpoint upload 或归档授权" in text,
        "says_lora_web_requires_link": "LoRA/web checkpoint 路线才需要上传和真实 checkpoint link" in text,
        "says_global_readiness_is_not_baseline_gate": "以路线感知摘要判断 baseline 最短路径" in text,
    }
    secret_hits = scan_secret_patterns(text)
    input_evidence = {
        "real_submission_gate_exists": bool(real_submission),
        "real_submission_gate_passed": bool(real_submission.get("passed")),
        "real_submission_currently_blocked": real_submission.get("ready_for_real_submission") is False,
        "export_audit_local_ready": bool(export_audit.get("local_export_ready")),
        "upload_audit_passed": bool(upload_audit.get("passed")),
        "upload_not_performed": upload_audit.get("uploads_performed") is False,
        "link_download_audit_passed": bool(link_download.get("passed")),
        "link_download_not_requested": link_download.get("verify_download_requested") is False,
        "link_download_host_not_contacted": link_download.get("verification", {}).get("download_host_contacted") is False,
        "link_download_no_plaintext": link_download.get("link_value_printed") is False,
        "jupyter_input_template_passed": jupyter_input.get("passed") is True,
        "jupyter_input_default_false": jupyter_input.get("run_flag_default_false") is True,
        "jupyter_input_local_env_ignored": jupyter_input.get("local_env_ignored", {}).get("ignored") is True,
        "jupyter_authorized_preflight_template_passed": jupyter_authorized.get("passed") is True,
        "jupyter_authorized_preflight_audit_default_true": jupyter_authorized.get("audit_default_true") is True,
        "jupyter_authorized_preflight_execution_default_false": jupyter_authorized.get("execution_default_false")
        is True,
        "jupyter_authorized_preflight_runner_not_started": jupyter_authorized.get("runner_started") is False,
        "ready_real_runner_template_passed": ready_real_runner.get("passed") is True,
        "ready_real_runner_no_confirm_blocks": ready_real_runner.get("synthetic_no_confirm_smoke", {}).get("passed")
        is True,
        "authorized_checkpoint_archive_template_passed": authorized_archive.get("passed") is True,
        "authorized_checkpoint_archive_no_confirm_blocks": authorized_archive.get("no_confirm_smoke", {}).get(
            "passed"
        )
        is True,
        "route_aware_blockers_passed": route_aware_blockers.get("passed") is True,
        "route_aware_recommended_baseline": route_aware_blockers.get("recommended_route") == "baseline_official_aloha",
        "route_aware_baseline_no_link": route_aware_blockers.get("baseline_requires_checkpoint_link") is False,
        "route_aware_baseline_no_upload": route_aware_blockers.get("baseline_requires_checkpoint_upload") is False,
        "route_aware_lora_web_needs_link": route_aware_blockers.get("lora_web_requires_checkpoint_link") is True,
    }
    passed = bool(
        exists
        and all(env_mentions.values())
        and all(path_mentions.values())
        and all(command_mentions.values())
        and all(guardrails.values())
        and not secret_hits
        and all(input_evidence.values())
    )
    blocking = []
    if not exists:
        blocking.append("缺少真实提交交接文档。")
    for key, ok in env_mentions.items():
        if not ok:
            blocking.append(f"交接文档缺少环境变量 `{key}`。")
    for path, ok in path_mentions.items():
        if not ok:
            blocking.append(f"交接文档缺少路径 `{path}`。")
    for name, ok in command_mentions.items():
        if not ok:
            blocking.append(f"交接文档缺少命令片段 `{name}`。")
    for name, ok in guardrails.items():
        if not ok:
            blocking.append(f"交接文档缺少安全边界 `{name}`。")
    if secret_hits:
        blocking.append("交接文档疑似包含明文 token 或密钥模式。")
    if not input_evidence["real_submission_gate_passed"]:
        blocking.append("真实提交 readiness gate 的状态文件缺失或未通过。")
    if not input_evidence["export_audit_local_ready"]:
        blocking.append("LoRA checkpoint 导出审计尚未显示本地就绪。")
    if not input_evidence["upload_audit_passed"]:
        blocking.append("checkpoint 上传通道审计尚未通过。")
    if not input_evidence["link_download_audit_passed"]:
        blocking.append("checkpoint link 下载校验审计尚未通过。")
    if not input_evidence["jupyter_input_template_passed"]:
        blocking.append("Jupyter 第 44 节安全填空入口审计尚未通过。")
    if not input_evidence["jupyter_input_default_false"]:
        blocking.append("Jupyter 第 44 节安全填空入口未证明默认关闭。")
    if not input_evidence["jupyter_input_local_env_ignored"]:
        blocking.append("Jupyter 第 44 节本地 env 文件未证明被 Git 忽略。")
    if not input_evidence["jupyter_authorized_preflight_template_passed"]:
        blocking.append("Jupyter 第 45 节授权预检入口审计尚未通过。")
    if not input_evidence["jupyter_authorized_preflight_audit_default_true"]:
        blocking.append("Jupyter 第 45 节未证明默认只跑静态审计。")
    if not input_evidence["jupyter_authorized_preflight_execution_default_false"]:
        blocking.append("Jupyter 第 45 节未证明授权预检默认关闭。")
    if not input_evidence["jupyter_authorized_preflight_runner_not_started"]:
        blocking.append("Jupyter 第 45 节未证明不会启动真实 runner。")
    if not input_evidence["ready_real_runner_template_passed"]:
        blocking.append("强确认真实 runner 模板审计尚未通过。")
    if not input_evidence["ready_real_runner_no_confirm_blocks"]:
        blocking.append("强确认真实 runner 模板未证明无确认时会阻断。")
    if not input_evidence["authorized_checkpoint_archive_template_passed"]:
        blocking.append("授权后 checkpoint 归档模板审计尚未通过。")
    if not input_evidence["authorized_checkpoint_archive_no_confirm_blocks"]:
        blocking.append("授权后 checkpoint 归档模板未证明无确认时会阻断。")
    if blocking == []:
        blocking.append(
            "无文档侧阻塞；baseline 仍取决于用户目标确认、token、submission id、variant=baseline 和真实 runner 强确认，"
            "LoRA/web checkpoint 路线额外取决于授权上传和真实 checkpoint link。"
        )

    return {
        "kind": "submission_handoff_docs_audit",
        "passed": passed,
        "doc_path": doc_path.relative_to(ROOT).as_posix(),
        "platform_contacted": False,
        "uploads_performed": False,
        "credentials_printed": False,
        "secret_patterns_found": secret_hits,
        "env_mentions": env_mentions,
        "path_mentions": path_mentions,
        "command_mentions": command_mentions,
        "guardrails": guardrails,
        "input_evidence": input_evidence,
        "blocking": blocking,
    }


def write_report(status: dict[str, Any], path: Path) -> None:
    lines = [
        "# 真实提交交接文档审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 文档路径：`{status['doc_path']}`。",
        f"- 是否连接 RoboChallenge 平台：`{status['platform_contacted']}`。",
        f"- 是否执行上传：`{status['uploads_performed']}`。",
        f"- 是否打印凭据：`{status['credentials_printed']}`。",
        f"- 是否发现疑似明文密钥：`{bool(status['secret_patterns_found'])}`。",
        "",
        "## 必需环境变量提及",
        "",
    ]
    for key, value in status["env_mentions"].items():
        lines.append(f"- `{key}`：`{value}`。")
    lines.extend(["", "## 必需路径提及", ""])
    for key, value in status["path_mentions"].items():
        lines.append(f"- `{key}`：`{value}`。")
    lines.extend(["", "## 必需命令提及", ""])
    for key, value in status["command_mentions"].items():
        lines.append(f"- `{key}`：`{value}`。")
    lines.extend(["", "## 安全边界", ""])
    for key, value in status["guardrails"].items():
        lines.append(f"- `{key}`：`{value}`。")
    lines.extend(["", "## 输入证据", ""])
    for key, value in status["input_evidence"].items():
        lines.append(f"- `{key}`：`{value}`。")
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
