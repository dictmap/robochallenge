#!/usr/bin/env python3
"""Audit the Jupyter final-handoff cell without running a real submission."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "robochallenge_pi05_submit_cn.ipynb"
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = ROOT / "runs"
DEFAULT_STATUS = RUNS_DIR / "jupyter_final_handoff_template_audit.json"
DEFAULT_REPORT = REPORTS_DIR / "jupyter_final_handoff_template_audit.md"

SECTION_MARKER = "第 46 节：baseline final handoff 交接包"
AUDIT_FLAG = "RUN_JUPYTER_BASELINE_FINAL_HANDOFF_TEMPLATE_AUDIT"
PACKET_FLAG = "RUN_JUPYTER_BASELINE_FINAL_HANDOFF_PACKET"
REAL_RUNNER_FLAG = "RUN_JUPYTER_BASELINE_REAL_RUNNER"
FINAL_HANDOFF_SCRIPT = "scripts/render_baseline_final_handoff_packet.py"
FINAL_HANDOFF_AUDIT_SCRIPT = "scripts/audit_jupyter_final_handoff_template.py"
FINAL_HANDOFF_REPORT = "reports/baseline_final_handoff_packet.md"
FINAL_HANDOFF_STATUS = "runs/baseline_final_handoff_packet.json"
REAL_RUNNER_COMMAND = (
    "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline "
    "ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION "
    "bash submission/run_ready_real_submission_template.sh"
)
REQUIRED_COMMANDS = [
    "python3 scripts/render_baseline_credential_hygiene.py",
    "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_authorized_preflight_template.sh",
    "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_ready_real_submission_template.sh",
    REAL_RUNNER_COMMAND,
]
REQUIRED_FRAGMENTS = [
    SECTION_MARKER,
    AUDIT_FLAG,
    f"{AUDIT_FLAG} = True",
    PACKET_FLAG,
    f"{PACKET_FLAG} = True",
    REAL_RUNNER_FLAG,
    f"{REAL_RUNNER_FLAG} = False",
    FINAL_HANDOFF_AUDIT_SCRIPT,
    FINAL_HANDOFF_SCRIPT,
    FINAL_HANDOFF_REPORT,
    FINAL_HANDOFF_STATUS,
    "baseline_official_aloha",
    "前三步 no-contact",
    "第四条真实 runner",
    "RUN_REAL_ROBOCHALLENGE_SUBMISSION",
    "submission/robochallenge_env.local.sh",
    *REQUIRED_COMMANDS,
]
FORBIDDEN_FRAGMENTS = [
    "set -x",
    "cat submission/robochallenge_env.local.sh",
    "print(open(",
    "RUN_JUPYTER_BASELINE_REAL_RUNNER = True",
    "os.system(",
    "subprocess.run(",
    "run_cmd([\"bash\"",
    "run_cmd(['bash'",
    "run_cmd([\"sh\"",
    "run_cmd(['sh'",
]
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
    parser = argparse.ArgumentParser(description="审计 Notebook final handoff 交接包入口；不执行真实提交。")
    parser.add_argument("--notebook", type=Path, default=NOTEBOOK, help="Notebook 路径。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文审计报告输出路径。")
    return parser.parse_args()


def load_notebook(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    return json.loads(text), text


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def cell_source(cell: dict[str, Any]) -> str:
    source = cell.get("source", "")
    if isinstance(source, list):
        return "".join(source)
    return str(source)


def find_section_cells(cells: list[dict[str, Any]]) -> tuple[int | None, dict[str, Any] | None, dict[str, Any] | None]:
    for index, cell in enumerate(cells):
        if cell.get("cell_type") != "markdown":
            continue
        if SECTION_MARKER not in cell_source(cell):
            continue
        next_cell = cells[index + 1] if index + 1 < len(cells) else None
        return index, cell, next_cell
    return None, None, None


def secret_pattern_hits(text: str) -> list[str]:
    return [name for name, pattern in SECRET_PATTERNS.items() if pattern.search(text)]


def build_status(notebook_path: Path) -> dict[str, Any]:
    notebook_exists = notebook_path.exists()
    nb, text = load_notebook(notebook_path) if notebook_exists else ({}, "")
    cells = nb.get("cells", []) if isinstance(nb, dict) else []
    section_index, markdown_cell, code_cell = find_section_cells(cells)
    section_source = cell_source(markdown_cell or {}) + "\n" + cell_source(code_cell or {})
    final_handoff = read_json(RUNS_DIR / "baseline_final_handoff_packet.json")
    final_commands = [item.get("command") for item in final_handoff.get("commands", [])]

    required_fragments = {fragment: fragment in section_source for fragment in REQUIRED_FRAGMENTS}
    forbidden_fragments = {fragment: fragment in section_source for fragment in FORBIDDEN_FRAGMENTS}
    code_cell_ok = bool(code_cell and code_cell.get("cell_type") == "code")
    code_cell_clean = bool(
        code_cell_ok
        and not code_cell.get("outputs")
        and code_cell.get("execution_count") is None
        and isinstance(code_cell.get("id"), str)
        and bool(code_cell.get("id"))
    )
    audit_default_true = f"{AUDIT_FLAG} = True" in section_source
    packet_default_true = f"{PACKET_FLAG} = True" in section_source
    real_runner_default_false = f"{REAL_RUNNER_FLAG} = False" in section_source
    route_guidance = {
        "recommended_route_baseline": "baseline_official_aloha" in section_source,
        "baseline_no_checkpoint_link": "baseline 是否需要 checkpoint link: False" in section_source
        or "baseline 不需要 checkpoint link" in section_source,
        "baseline_no_checkpoint_upload": "baseline 是否需要 checkpoint upload: False" in section_source
        or "baseline 不需要 checkpoint upload" in section_source,
        "real_runner_manual_only": "第四条真实 runner" in section_source
        and "RUN_REAL_ROBOCHALLENGE_SUBMISSION" in section_source,
    }
    command_evidence = {
        "final_handoff_json_passed": final_handoff.get("passed") is True,
        "final_handoff_command_count": final_handoff.get("command_count") == 4,
        "final_handoff_no_contact_command_count": final_handoff.get("no_contact_command_count") == 3,
        "final_handoff_real_runner_requires_confirmation": final_handoff.get(
            "real_runner_requires_confirmation"
        )
        is True,
        "notebook_lists_all_commands": all(command in section_source for command in REQUIRED_COMMANDS),
        "json_commands_match_expected": final_commands == REQUIRED_COMMANDS,
    }
    secret_hits = secret_pattern_hits(section_source)
    whole_notebook_secret_hits = secret_pattern_hits(text)

    blocking = []
    if not notebook_exists:
        blocking.append("缺少 Notebook。")
    if markdown_cell is None:
        blocking.append("Notebook 缺少第 46 节 baseline final handoff 交接包。")
    if not code_cell_ok:
        blocking.append("第 46 节后面缺少代码 cell。")
    if not code_cell_clean:
        blocking.append("第 46 节代码 cell 必须保持未执行、无输出、带稳定 cell id。")
    if not audit_default_true:
        blocking.append("第 46 节应默认启用静态审计。")
    if not packet_default_true:
        blocking.append("第 46 节应默认生成 no-contact final handoff 包。")
    if not real_runner_default_false:
        blocking.append("第 46 节真实 runner 标志必须默认关闭。")
    for fragment, ok in required_fragments.items():
        if not ok:
            blocking.append(f"第 46 节缺少关键片段：`{fragment}`。")
    for fragment, hit in forbidden_fragments.items():
        if hit:
            blocking.append(f"第 46 节包含禁止片段：`{fragment}`。")
    if not all(route_guidance.values()):
        blocking.append("第 46 节没有清晰说明 baseline/no-contact/真实 runner 强确认边界。")
    for key, ok in command_evidence.items():
        if not ok:
            blocking.append(f"final handoff 命令证据未通过 `{key}`。")
    if secret_hits or whole_notebook_secret_hits:
        blocking.append("Notebook final handoff 节或 Notebook 本体疑似包含明文 token/submission id。")
    if not blocking:
        blocking.append("Jupyter final handoff 交接包入口已就绪；默认只审计和生成 no-contact 交接包。")

    passed = bool(
        notebook_exists
        and section_index is not None
        and code_cell_clean
        and audit_default_true
        and packet_default_true
        and real_runner_default_false
        and all(required_fragments.values())
        and not any(forbidden_fragments.values())
        and all(route_guidance.values())
        and all(command_evidence.values())
        and not secret_hits
        and not whole_notebook_secret_hits
    )
    return {
        "kind": "jupyter_final_handoff_template_audit",
        "passed": passed,
        "platform_contacted": False,
        "uploads_performed": False,
        "credentials_read": False,
        "credentials_printed": False,
        "link_values_printed": False,
        "secret_values_printed": False,
        "runner_started": False,
        "notebook_path": notebook_path.relative_to(ROOT).as_posix() if notebook_path.is_absolute() else str(notebook_path),
        "section_marker": SECTION_MARKER,
        "section_index": section_index,
        "audit_flag": AUDIT_FLAG,
        "audit_default_true": audit_default_true,
        "packet_flag": PACKET_FLAG,
        "packet_default_true": packet_default_true,
        "real_runner_flag": REAL_RUNNER_FLAG,
        "real_runner_default_false": real_runner_default_false,
        "final_handoff_script": FINAL_HANDOFF_SCRIPT,
        "final_handoff_report": FINAL_HANDOFF_REPORT,
        "recommended_route": "baseline_official_aloha" if route_guidance["recommended_route_baseline"] else "",
        "baseline_requires_checkpoint_link": False if route_guidance["baseline_no_checkpoint_link"] else None,
        "baseline_requires_checkpoint_upload": False if route_guidance["baseline_no_checkpoint_upload"] else None,
        "command_count": final_handoff.get("command_count"),
        "no_contact_command_count": final_handoff.get("no_contact_command_count"),
        "real_runner_requires_confirmation": final_handoff.get("real_runner_requires_confirmation"),
        "route_guidance": route_guidance,
        "command_evidence": command_evidence,
        "required_fragments": required_fragments,
        "forbidden_fragments": forbidden_fragments,
        "code_cell_clean": code_cell_clean,
        "code_cell_id": code_cell.get("id") if code_cell else None,
        "secret_pattern_hits": secret_hits,
        "whole_notebook_secret_pattern_hits": whole_notebook_secret_hits,
        "blocking": blocking,
    }


def write_report(status: dict[str, Any], path: Path) -> None:
    lines = [
        "# Jupyter final handoff 交接包入口审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- Notebook：`{status['notebook_path']}`。",
        f"- 章节：`{status['section_marker']}`。",
        f"- 静态审计默认开启：`{status['audit_default_true']}`。",
        f"- final handoff 包默认生成：`{status['packet_default_true']}`。",
        f"- 真实 runner 默认关闭：`{status['real_runner_default_false']}`。",
        f"- 推荐路线：`{status['recommended_route']}`。",
        f"- baseline 是否要求 checkpoint link：`{status['baseline_requires_checkpoint_link']}`。",
        f"- baseline 是否要求 checkpoint upload：`{status['baseline_requires_checkpoint_upload']}`。",
        f"- final handoff 命令数：`{status['command_count']}`。",
        f"- no-contact 命令数：`{status['no_contact_command_count']}`。",
        f"- 真实 runner 是否需要强确认：`{status['real_runner_requires_confirmation']}`。",
        f"- 是否读取真实凭据：`{status['credentials_read']}`。",
        f"- 是否连接平台：`{status['platform_contacted']}`。",
        f"- 是否启动真实 runner：`{status['runner_started']}`。",
        "",
        "## 命令证据",
        "",
    ]
    for key, ok in status["command_evidence"].items():
        lines.append(f"- `{key}`：`{ok}`。")
    lines.extend(["", "## 路线引导", ""])
    for key, ok in status["route_guidance"].items():
        lines.append(f"- `{key}`：`{ok}`。")
    lines.extend(["", "## 关键片段", ""])
    for fragment, ok in status["required_fragments"].items():
        lines.append(f"- `{fragment}`：`{ok}`。")
    lines.extend(["", "## 禁止片段", ""])
    for fragment, hit in status["forbidden_fragments"].items():
        lines.append(f"- `{fragment}`：`{hit}`。")
    lines.extend(["", "## Blocking", ""])
    for item in status["blocking"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args()
    status = build_status(args.notebook)
    args.status_path.parent.mkdir(parents=True, exist_ok=True)
    args.status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(status, args.report_path)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
