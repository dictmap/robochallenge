#!/usr/bin/env python3
"""Audit that Jupyter and shell readonly preflight entries converge safely."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
NOTEBOOK = ROOT / "notebooks" / "robochallenge_pi05_submit_cn.ipynb"
DEFAULT_STATUS = RUNS_DIR / "readonly_preflight_jupyter_shell_parity.json"
DEFAULT_REPORT = REPORTS_DIR / "readonly_preflight_jupyter_shell_parity.md"

TARGET_CONFIRMATION = "CONFIRM_TABLE30V2_ALOHA_BASELINE"
LOCAL_ENV_PATH = "submission/robochallenge_env.local.sh"
WRAPPER = "submission/run_authorized_preflight_template.sh"
SHELL_READONLY_COMMAND = f"ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash {WRAPPER}"
JUPYTER_WRAPPER_COMMAND = f"bash {WRAPPER}"
JUPYTER_AUTHORIZED_COMMAND = f"source {LOCAL_ENV_PATH}; {JUPYTER_WRAPPER_COMMAND}"
SECTION_44 = "第 44 节：安全填空本地 env 入口"
SECTION_45 = "第 45 节：授权后 Jupyter 预检入口"

SECRET_PATTERNS = {
    "openai_api_key": re.compile(r"sk-proj-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{30,}"),
    "huggingface_token": re.compile(r"hf_[A-Za-z0-9]{20,}"),
    "github_token": re.compile(r"ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{20,}"),
    "robochallenge_token_assignment": re.compile(
        r"(?:export\s+)?ROBOCHALLENGE_(?:USER_)?TOKEN\s*=\s*[A-Za-z0-9][A-Za-z0-9_-]{19,}"
    ),
    "robochallenge_submission_assignment": re.compile(
        r"(?:export\s+)?ROBOCHALLENGE_SUBMISSION_ID\s*=\s*[A-Za-z0-9][A-Za-z0-9_-]{10,}"
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="审计 baseline 只读预检的 Jupyter 与 shell 入口一致性；不读凭据、不连接平台。"
    )
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文报告输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def cell_source(cell: dict[str, Any]) -> str:
    source = cell.get("source", "")
    if isinstance(source, list):
        return "".join(source)
    return str(source)


def load_notebook_text() -> tuple[str, list[dict[str, Any]]]:
    text = NOTEBOOK.read_text(encoding="utf-8") if NOTEBOOK.exists() else ""
    if not text:
        return "", []
    nb = json.loads(text)
    return text, nb.get("cells", [])


def section_pair(cells: list[dict[str, Any]], marker: str) -> tuple[str, str]:
    for index, cell in enumerate(cells):
        if cell.get("cell_type") != "markdown":
            continue
        markdown = cell_source(cell)
        if marker not in markdown:
            continue
        code = cell_source(cells[index + 1]) if index + 1 < len(cells) else ""
        return markdown, code
    return "", ""


def secret_hits(text: str) -> list[str]:
    return [name for name, pattern in SECRET_PATTERNS.items() if pattern.search(text)]


def build_status() -> dict[str, Any]:
    readonly_entry = read_json(RUNS_DIR / "baseline_readonly_preflight_entry.json")
    jupyter_input = read_json(RUNS_DIR / "jupyter_input_template_audit.json")
    jupyter_authorized = read_json(RUNS_DIR / "jupyter_authorized_preflight_template_audit.json")
    notebook_text, cells = load_notebook_text()
    section44_markdown, section44_code = section_pair(cells, SECTION_44)
    section45_markdown, section45_code = section_pair(cells, SECTION_45)
    section_text = "\n".join([section44_markdown, section44_code, section45_markdown, section45_code])

    shell_command = str(readonly_entry.get("readonly_preflight_command", ""))
    jupyter_audit_command = str(jupyter_authorized.get("authorized_preflight_command", ""))
    jupyter_code_has_source = f"source {LOCAL_ENV_PATH}" in section45_code
    jupyter_code_has_wrapper = JUPYTER_WRAPPER_COMMAND in section45_code

    evidence = {
        "readonly_entry_passed": readonly_entry.get("passed") is True,
        "shell_command_exact": shell_command == SHELL_READONLY_COMMAND,
        "shell_variant_prefix_present": shell_command.startswith("ROBOCHALLENGE_SUBMISSION_VARIANT=baseline "),
        "shell_uses_same_wrapper": shell_command.endswith(JUPYTER_WRAPPER_COMMAND),
        "shell_no_real_runner_confirm": "ROBOCHALLENGE_REAL_RUN_CONFIRM" not in shell_command,
        "shell_no_checkpoint_link": "ROBOCHALLENGE_CHECKPOINT_LINK" not in shell_command,
        "jupyter_input_passed": jupyter_input.get("passed") is True,
        "jupyter_input_writes_local_env": jupyter_input.get("local_env_path") == LOCAL_ENV_PATH,
        "jupyter_input_has_variant_key": "ROBOCHALLENGE_SUBMISSION_VARIANT"
        in set(jupyter_input.get("required_keys", {}).keys()),
        "jupyter_input_has_target_confirmation_key": "ROBOCHALLENGE_SUBMISSION_TARGET_CONFIRMATION"
        in set(jupyter_input.get("required_keys", {}).keys()),
        "jupyter_input_target_confirmation_exact": jupyter_input.get("target_confirmation_value")
        == TARGET_CONFIRMATION,
        "jupyter_input_target_confirmation_manual": jupyter_input.get(
            "target_confirmation_manual_input_required"
        )
        is True,
        "jupyter_input_target_confirmation_exact_match": jupyter_input.get(
            "target_confirmation_exact_match_required"
        )
        is True,
        "jupyter_authorized_passed": jupyter_authorized.get("passed") is True,
        "jupyter_authorized_default_off": jupyter_authorized.get("execution_default_false") is True,
        "jupyter_authorized_command_same_wrapper": jupyter_audit_command == JUPYTER_WRAPPER_COMMAND,
        "jupyter_code_sources_local_env": jupyter_code_has_source,
        "jupyter_code_uses_same_wrapper": jupyter_code_has_wrapper,
        "jupyter_code_has_safe_shell": "set -euo pipefail" in section45_code,
        "jupyter_code_redacts_sensitive_output": "redact_sensitive_output" in section45_code,
        "jupyter_code_no_real_runner": "run_ready_real_submission_template.sh" not in section45_code,
        "jupyter_code_no_checkpoint_archive": "run_authorized_checkpoint_archive_template.sh" not in section45_code,
        "routes_converge_to_same_wrapper": shell_command.endswith(jupyter_audit_command)
        and jupyter_code_has_wrapper,
        "variant_delivery_split_is_explicit": shell_command.startswith("ROBOCHALLENGE_SUBMISSION_VARIANT=baseline ")
        and "ROBOCHALLENGE_SUBMISSION_VARIANT" in section44_code,
        "target_confirmation_delivery_split_is_explicit": TARGET_CONFIRMATION in section44_code
        and jupyter_input.get("target_confirmation_exact_match_required") is True,
    }

    leak_flags = {
        "credentials_printed": any(
            bool(item.get("credentials_printed")) for item in [readonly_entry, jupyter_input, jupyter_authorized]
        ),
        "link_values_printed": any(
            bool(item.get("link_values_printed")) for item in [readonly_entry, jupyter_input, jupyter_authorized]
        ),
        "secret_values_printed": any(
            bool(item.get("secret_values_printed")) for item in [readonly_entry, jupyter_input, jupyter_authorized]
        ),
        "section_secret_hits": bool(secret_hits(section_text)),
        "whole_notebook_secret_hits": bool(secret_hits(notebook_text)),
    }
    contact_flags = {
        "platform_contacted": any(
            bool(item.get("platform_contacted")) for item in [readonly_entry, jupyter_input, jupyter_authorized]
        ),
        "uploads_performed": any(
            bool(item.get("uploads_performed")) for item in [readonly_entry, jupyter_input, jupyter_authorized]
        ),
        "download_host_contacted": any(
            bool(item.get("contact_flags", {}).get("download_host_contacted"))
            for item in [readonly_entry, jupyter_input, jupyter_authorized]
        ),
    }
    blocking = []
    for name, ok in evidence.items():
        if not ok:
            blocking.append(f"Jupyter/shell 只读预检一致性证据未通过：`{name}`。")
    if any(leak_flags.values()):
        blocking.append("检测到凭据、链接或 secret 泄漏风险。")
    if any(contact_flags.values()):
        blocking.append("检测到平台连接、上传或下载 host 访问痕迹。")
    if not blocking:
        blocking.append("Jupyter 与 shell 只读预检入口已闭环：两者进入同一 wrapper，variant 来源明确，不触发真实 runner。")

    passed = all(evidence.values()) and not any(leak_flags.values()) and not any(contact_flags.values())
    return {
        "kind": "readonly_preflight_jupyter_shell_parity",
        "passed": passed,
        "recommended_route": "baseline_official_aloha",
        "target_confirmation_value": TARGET_CONFIRMATION,
        "target_user_confirmed": False,
        "shell_readonly_command": SHELL_READONLY_COMMAND,
        "jupyter_authorized_command": JUPYTER_AUTHORIZED_COMMAND,
        "wrapper_template": WRAPPER,
        "routes_converge_to_same_wrapper": evidence["routes_converge_to_same_wrapper"],
        "shell_variant_source": "inline env prefix",
        "jupyter_variant_source": f"{SECTION_44} 写入 {LOCAL_ENV_PATH}",
        "jupyter_target_confirmation_source": f"{SECTION_44} 手动精确填写 {TARGET_CONFIRMATION}",
        "requires_checkpoint_link": False,
        "requires_checkpoint_upload": False,
        "real_runner_confirm_required_for_readonly_preflight": False,
        "real_runner_confirm_required_for_real_submission": True,
        "platform_contacted": False,
        "uploads_performed": False,
        "credentials_read": False,
        "credentials_printed": False,
        "link_values_printed": False,
        "secret_values_printed": False,
        "runner_started": False,
        "evidence": evidence,
        "leak_flags": leak_flags,
        "contact_flags": contact_flags,
        "blocking": blocking,
    }


def write_report(status: dict[str, Any], path: Path) -> None:
    lines = [
        "# Jupyter 与 shell 只读预检一致性审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 推荐路线：`{status['recommended_route']}`。",
        f"- 目标确认值：`{status['target_confirmation_value']}`。",
        f"- shell 入口：`{status['shell_readonly_command']}`。",
        f"- Jupyter 入口：`{status['jupyter_authorized_command']}`。",
        f"- 共同 wrapper：`{status['wrapper_template']}`。",
        f"- 两条入口是否收敛到同一 wrapper：`{status['routes_converge_to_same_wrapper']}`。",
        f"- shell variant 来源：`{status['shell_variant_source']}`。",
        f"- Jupyter variant 来源：`{status['jupyter_variant_source']}`。",
        f"- Jupyter 目标确认来源：`{status['jupyter_target_confirmation_source']}`。",
        f"- 是否需要 checkpoint link：`{status['requires_checkpoint_link']}`。",
        f"- 是否需要 checkpoint upload：`{status['requires_checkpoint_upload']}`。",
        f"- 只读预检是否需要真实 runner 强确认：`{status['real_runner_confirm_required_for_readonly_preflight']}`。",
        f"- 真实提交是否仍需要真实 runner 强确认：`{status['real_runner_confirm_required_for_real_submission']}`。",
        f"- 是否读取真实凭据：`{status['credentials_read']}`。",
        f"- 是否打印 token/link/submission id：`{status['credentials_printed'] or status['link_values_printed'] or status['secret_values_printed']}`。",
        f"- 是否连接平台：`{status['platform_contacted']}`。",
        f"- 是否上传：`{status['uploads_performed']}`。",
        f"- 是否启动 runner：`{status['runner_started']}`。",
        "",
        "## 机器证据",
        "",
    ]
    for key, ok in status["evidence"].items():
        lines.append(f"- `{key}`：`{ok}`。")
    lines.extend(["", "## 泄漏与联网边界", ""])
    for key, value in status["leak_flags"].items():
        lines.append(f"- `{key}`：`{value}`。")
    for key, value in status["contact_flags"].items():
        lines.append(f"- `{key}`：`{value}`。")
    lines.extend(["", "## Blocking", ""])
    for item in status["blocking"]:
        lines.append(f"- {item}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    status = build_status()
    args.status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(status, args.report_path)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
