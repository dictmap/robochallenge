#!/usr/bin/env python3
"""Audit the Jupyter dashboard screenshot section without executing real submission code."""

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
DEFAULT_STATUS = RUNS_DIR / "notebook_dashboard_gui_section_audit.json"
DEFAULT_REPORT = REPORTS_DIR / "notebook_dashboard_gui_section_audit.md"

SECTION_MARKER = "第 47 节：GUI 首屏截图证据"
RUN_FLAG = "RUN_DASHBOARD_GUI_SCREENSHOT_PACKET"
GUI_PACKET_SCRIPT = "scripts/render_dashboard_gui_access_packet.py"
GUI_PACKET_STATUS = "runs/dashboard_gui_access_packet.json"
SCREENSHOT_PATH = "reports/submission_status_dashboard_browser.png"
HTML_PATH = "reports/submission_status_dashboard.html"

REQUIRED_FRAGMENTS = [
    SECTION_MARKER,
    RUN_FLAG,
    f"{RUN_FLAG} = True",
    GUI_PACKET_SCRIPT,
    GUI_PACKET_STATUS,
    SCREENSHOT_PATH,
    HTML_PATH,
    "IPython.display",
    "display(Image",
    "browser_visual_blocked_by_policy",
    "screenshot_created",
    "screenshot_size_bytes",
    "platform_contacted",
    "uploads_performed",
    "credentials_read",
]

FORBIDDEN_FRAGMENTS = [
    "submission/robochallenge_env.local.sh",
    "ROBOCHALLENGE_USER_TOKEN",
    "ROBOCHALLENGE_SUBMISSION_ID",
    "ROBOCHALLENGE_REAL_RUN_CONFIRM",
    "RUN_REAL_ROBOCHALLENGE_SUBMISSION",
    "run_authorized_preflight_template.sh",
    "run_ready_real_submission_template.sh",
    "run_table30v2_aloha_demo_template.sh",
    "demo.py",
    "getpass.",
    "input(",
    "requests.",
    "urllib.request",
    "subprocess.run(",
    "os.system(",
    "curl ",
    "wget ",
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
    parser = argparse.ArgumentParser(description="审计 Jupyter GUI 首屏截图章节；不执行真实提交。")
    parser.add_argument("--notebook", type=Path, default=NOTEBOOK, help="Notebook 路径。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文审计报告输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_notebook(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    return json.loads(text), text


def cell_source(cell: dict[str, Any]) -> str:
    source = cell.get("source", "")
    if isinstance(source, list):
        return "".join(source)
    return str(source)


def find_section(cells: list[dict[str, Any]]) -> tuple[int | None, dict[str, Any] | None, dict[str, Any] | None]:
    for index, cell in enumerate(cells):
        if cell.get("cell_type") != "markdown":
            continue
        if SECTION_MARKER not in cell_source(cell):
            continue
        code_cell = cells[index + 1] if index + 1 < len(cells) else None
        return index, cell, code_cell
    return None, None, None


def secret_pattern_hits(text: str) -> list[str]:
    return [name for name, pattern in SECRET_PATTERNS.items() if pattern.search(text)]


def build_status(notebook_path: Path) -> dict[str, Any]:
    notebook_exists = notebook_path.exists()
    nb, notebook_text = load_notebook(notebook_path) if notebook_exists else ({}, "")
    cells = nb.get("cells", []) if isinstance(nb, dict) else []
    section_index, markdown_cell, code_cell = find_section(cells)
    section_source = cell_source(markdown_cell or {}) + "\n" + cell_source(code_cell or {})
    code_source = cell_source(code_cell or {})
    gui_packet = read_json(ROOT / GUI_PACKET_STATUS)
    screenshot = ROOT / SCREENSHOT_PATH
    html = ROOT / HTML_PATH

    required_fragments = {fragment: fragment in section_source for fragment in REQUIRED_FRAGMENTS}
    forbidden_fragments = {fragment: fragment in section_source for fragment in FORBIDDEN_FRAGMENTS}
    code_cell_ok = bool(code_cell and code_cell.get("cell_type") == "code")
    code_cell_clean = bool(
        code_cell_ok
        and code_cell.get("execution_count") is None
        and not code_cell.get("outputs")
        and code_cell.get("id") == "dashboard-gui-screenshot-code"
    )
    semantic_checks = {
        "run_flag_default_true": f"{RUN_FLAG} = True" in code_source,
        "uses_gui_packet_script": GUI_PACKET_SCRIPT in code_source,
        "reads_gui_packet_json": GUI_PACKET_STATUS in code_source,
        "checks_packet_passed": "gui_packet.get('passed') is True" in code_source,
        "checks_browser_not_blocked": "gui_packet.get('browser_visual_blocked_by_policy') is False" in code_source,
        "checks_screenshot_created": "gui_packet.get('screenshot_created') is True" in code_source,
        "checks_screenshot_path": SCREENSHOT_PATH in code_source,
        "checks_screenshot_size": "screenshot_size_bytes" in code_source and "> 10000" in code_source,
        "checks_no_platform_contact": "gui_packet.get('platform_contacted') is False" in code_source,
        "checks_no_upload": "gui_packet.get('uploads_performed') is False" in code_source,
        "checks_no_credential_read": "gui_packet.get('credentials_read') is False" in code_source,
        "displays_screenshot_inline": "display(Image(filename=str(screenshot_path)))" in code_source,
        "does_not_read_local_env": "submission/robochallenge_env.local.sh" not in section_source,
        "does_not_call_real_runner": "run_ready_real_submission_template.sh" not in section_source
        and "RUN_REAL_ROBOCHALLENGE_SUBMISSION" not in section_source,
    }
    packet_checks = {
        "gui_packet_passed": gui_packet.get("passed") is True,
        "gui_packet_screenshot_created": gui_packet.get("screenshot_created") is True,
        "gui_packet_browser_not_blocked": gui_packet.get("browser_visual_blocked_by_policy") is False,
        "gui_packet_screenshot_path": gui_packet.get("screenshot_path") == SCREENSHOT_PATH,
        "gui_packet_screenshot_size": gui_packet.get("screenshot_size_bytes", 0) > 10_000,
        "screenshot_file_exists": screenshot.exists() and screenshot.is_file(),
        "html_file_exists": html.exists() and html.is_file(),
        "packet_no_platform_contact": gui_packet.get("platform_contacted") is False,
        "packet_no_upload": gui_packet.get("uploads_performed") is False,
        "packet_no_credential_read": gui_packet.get("credentials_read") is False,
    }
    secret_hits = secret_pattern_hits(section_source)
    whole_notebook_secret_hits = secret_pattern_hits(notebook_text)

    blocking = []
    if not notebook_exists:
        blocking.append("缺少主 Notebook。")
    if markdown_cell is None:
        blocking.append("Notebook 缺少第 47 节 GUI 首屏截图证据。")
    if not code_cell_ok:
        blocking.append("第 47 节后面缺少代码 cell。")
    if not code_cell_clean:
        blocking.append("第 47 节代码 cell 必须保持未执行、无输出，并使用稳定 id。")
    for fragment, ok in required_fragments.items():
        if not ok:
            blocking.append(f"第 47 节缺少关键片段：`{fragment}`。")
    for fragment, hit in forbidden_fragments.items():
        if hit:
            blocking.append(f"第 47 节包含禁止片段：`{fragment}`。")
    for name, ok in semantic_checks.items():
        if not ok:
            blocking.append(f"第 47 节语义检查未通过 `{name}`。")
    for name, ok in packet_checks.items():
        if not ok:
            blocking.append(f"GUI packet 证据检查未通过 `{name}`。")
    if secret_hits or whole_notebook_secret_hits:
        blocking.append("Notebook 第 47 节或 Notebook 本体疑似包含明文 token/submission id。")
    if not blocking:
        blocking.append("Jupyter GUI 首屏截图章节已通过语义审计，默认只读且可内联显示 PNG。")

    passed = bool(
        notebook_exists
        and section_index is not None
        and code_cell_clean
        and all(required_fragments.values())
        and not any(forbidden_fragments.values())
        and all(semantic_checks.values())
        and all(packet_checks.values())
        and not secret_hits
        and not whole_notebook_secret_hits
    )
    return {
        "kind": "notebook_dashboard_gui_section_audit",
        "passed": passed,
        "platform_contacted": False,
        "uploads_performed": False,
        "credentials_read": False,
        "credentials_printed": False,
        "link_values_printed": False,
        "secret_values_printed": False,
        "notebook_path": notebook_path.relative_to(ROOT).as_posix() if notebook_path.is_absolute() else str(notebook_path),
        "section_marker": SECTION_MARKER,
        "section_index": section_index,
        "run_flag": RUN_FLAG,
        "run_flag_default_true": semantic_checks["run_flag_default_true"],
        "code_cell_clean": code_cell_clean,
        "code_cell_id": code_cell.get("id") if code_cell else None,
        "gui_packet_script": GUI_PACKET_SCRIPT,
        "gui_packet_status": GUI_PACKET_STATUS,
        "screenshot_path": SCREENSHOT_PATH,
        "required_fragments": required_fragments,
        "forbidden_fragments": forbidden_fragments,
        "semantic_checks": semantic_checks,
        "packet_checks": packet_checks,
        "secret_pattern_hits": secret_hits,
        "whole_notebook_secret_pattern_hits": whole_notebook_secret_hits,
        "blocking": blocking,
    }


def write_report(status: dict[str, Any], path: Path) -> None:
    lines = [
        "# Notebook GUI 首屏截图章节审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- Notebook：`{status['notebook_path']}`。",
        f"- 章节：`{status['section_marker']}`。",
        f"- 章节索引：`{status['section_index']}`。",
        f"- 代码 cell id：`{status['code_cell_id']}`。",
        f"- 代码 cell 干净：`{status['code_cell_clean']}`。",
        f"- 默认运行 flag：`{status['run_flag']}` / `{status['run_flag_default_true']}`。",
        f"- GUI packet：`{status['gui_packet_status']}`。",
        f"- 截图路径：`{status['screenshot_path']}`。",
        f"- 是否连接平台：`{status['platform_contacted']}`。",
        f"- 是否上传：`{status['uploads_performed']}`。",
        f"- 是否读取真实凭据：`{status['credentials_read']}`。",
        "",
        "## 语义检查",
        "",
    ]
    for key, ok in status["semantic_checks"].items():
        lines.append(f"- `{key}`：`{ok}`。")
    lines.extend(["", "## GUI Packet 检查", ""])
    for key, ok in status["packet_checks"].items():
        lines.append(f"- `{key}`：`{ok}`。")
    lines.extend(["", "## 禁止片段", ""])
    for key, hit in status["forbidden_fragments"].items():
        lines.append(f"- `{key}`：`{hit}`。")
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
