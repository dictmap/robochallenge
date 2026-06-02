#!/usr/bin/env python3
"""Audit the Jupyter authorized-preflight cell without reading local credentials."""

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
DEFAULT_STATUS = RUNS_DIR / "jupyter_authorized_preflight_template_audit.json"
DEFAULT_REPORT = REPORTS_DIR / "jupyter_authorized_preflight_template_audit.md"

SECTION_MARKER = "第 45 节：授权后 Jupyter 预检入口"
AUDIT_FLAG = "RUN_JUPYTER_AUTHORIZED_PREFLIGHT_TEMPLATE_AUDIT"
EXECUTION_FLAG = "RUN_JUPYTER_AUTHORIZED_PREFLIGHT"
LOCAL_ENV_PATH = "submission/robochallenge_env.local.sh"
AUTHORIZED_PREFLIGHT = "bash submission/run_authorized_preflight_template.sh"
REQUIRED_KEYS = [
    "ROBOCHALLENGE_USER_TOKEN",
    "ROBOCHALLENGE_SUBMISSION_ID",
    "ROBOCHALLENGE_LORA_CHECKPOINT_LINK",
    "ROBOCHALLENGE_CHECKPOINT_LINK",
]
REQUIRED_FRAGMENTS = [
    SECTION_MARKER,
    AUDIT_FLAG,
    f"{AUDIT_FLAG} = True",
    EXECUTION_FLAG,
    f"{EXECUTION_FLAG} = False",
    "scripts/audit_jupyter_authorized_preflight_template.py",
    LOCAL_ENV_PATH,
    AUTHORIZED_PREFLIGHT,
    "source submission/robochallenge_env.local.sh",
    "set -euo pipefail",
    "redact_sensitive_output",
    "subprocess.run",
    "returncode",
    *REQUIRED_KEYS,
]
FORBIDDEN_FRAGMENTS = [
    "set -x",
    "cat submission/robochallenge_env.local.sh",
    "print(env_values",
    "print(open(",
    "--verify-download",
    "RUN_REAL_ROBOCHALLENGE_SUBMISSION",
    "CREATE_ROBOCHALLENGE_CHECKPOINT_ARCHIVE",
    "run_ready_real_submission_template.sh",
    "run_table30v2_aloha_demo_template.sh",
    "run_table30v2_aloha_lora_demo_template.sh",
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
    parser = argparse.ArgumentParser(
        description="审计 Notebook 授权后 Jupyter 预检入口；不执行 Notebook，不读取本地凭据。"
    )
    parser.add_argument("--notebook", type=Path, default=NOTEBOOK, help="Notebook 路径。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文审计报告输出路径。")
    return parser.parse_args()


def load_notebook(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    return json.loads(text), text


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
    required_fragments = {fragment: fragment in section_source for fragment in REQUIRED_FRAGMENTS}
    forbidden_fragments = {fragment: fragment in section_source for fragment in FORBIDDEN_FRAGMENTS}
    required_keys = {key: key in section_source for key in REQUIRED_KEYS}
    code_cell_ok = bool(code_cell and code_cell.get("cell_type") == "code")
    code_cell_clean = bool(
        code_cell_ok
        and not code_cell.get("outputs")
        and code_cell.get("execution_count") is None
        and isinstance(code_cell.get("id"), str)
        and bool(code_cell.get("id"))
    )
    execution_default_false = f"{EXECUTION_FLAG} = False" in section_source
    audit_default_true = f"{AUDIT_FLAG} = True" in section_source
    secret_hits = secret_pattern_hits(section_source)
    whole_notebook_secret_hits = secret_pattern_hits(text)

    blocking = []
    if not notebook_exists:
        blocking.append("缺少 Notebook。")
    if markdown_cell is None:
        blocking.append("Notebook 缺少第 45 节授权后 Jupyter 预检入口。")
    if not code_cell_ok:
        blocking.append("第 45 节后面缺少代码 cell。")
    if not code_cell_clean:
        blocking.append("第 45 节代码 cell 必须保持未执行、无输出、带稳定 cell id。")
    if not execution_default_false:
        blocking.append("授权后 Jupyter 预检入口必须默认不执行真实 local env 预检。")
    if not audit_default_true:
        blocking.append("第 45 节应默认只执行静态审计，便于 Jupyter 内复跑。")
    for fragment, ok in required_fragments.items():
        if not ok:
            blocking.append(f"授权后 Jupyter 预检入口缺少关键片段：`{fragment}`。")
    for fragment, hit in forbidden_fragments.items():
        if hit:
            blocking.append(f"授权后 Jupyter 预检入口包含禁止片段：`{fragment}`。")
    if not all(required_keys.values()):
        blocking.append("授权后 Jupyter 预检入口没有覆盖全部必要环境变量名。")
    if secret_hits or whole_notebook_secret_hits:
        blocking.append("Notebook 授权后预检入口或 Notebook 本体疑似包含明文 token/submission id。")
    if not blocking:
        blocking.append("授权后 Jupyter 预检入口已就绪；默认只审计，不读取 local env，不连接平台，不启动 runner。")

    passed = bool(
        notebook_exists
        and section_index is not None
        and code_cell_clean
        and execution_default_false
        and audit_default_true
        and all(required_fragments.values())
        and not any(forbidden_fragments.values())
        and all(required_keys.values())
        and not secret_hits
        and not whole_notebook_secret_hits
    )
    return {
        "kind": "jupyter_authorized_preflight_template_audit",
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
        "execution_flag": EXECUTION_FLAG,
        "execution_default_false": execution_default_false,
        "local_env_path": LOCAL_ENV_PATH,
        "authorized_preflight_command": AUTHORIZED_PREFLIGHT,
        "required_keys": required_keys,
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
        "# 授权后 Jupyter 预检入口审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- Notebook：`{status['notebook_path']}`。",
        f"- 章节：`{status['section_marker']}`。",
        f"- 静态审计默认开启：`{status['audit_default_true']}`。",
        f"- local env 预检默认执行：`{not status['execution_default_false']}`。",
        f"- 本地 env 路径：`{status['local_env_path']}`。",
        f"- 授权预检命令：`{status['authorized_preflight_command']}`。",
        f"- 是否读取真实凭据：`{status['credentials_read']}`。",
        f"- 是否打印 token/link/submission id：`{status['credentials_printed'] or status['link_values_printed'] or status['secret_values_printed']}`。",
        f"- 是否连接 RoboChallenge 平台：`{status['platform_contacted']}`。",
        f"- 是否启动真实 runner：`{status['runner_started']}`。",
        "",
        "## 必要变量名",
        "",
    ]
    for key, ok in status["required_keys"].items():
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
