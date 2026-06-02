#!/usr/bin/env python3
"""Audit the main RoboChallenge notebook structure without executing it."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "robochallenge_pi05_submit_cn.ipynb"
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = ROOT / "runs"
DEFAULT_STATUS = RUNS_DIR / "notebook_structure_audit.json"
DEFAULT_REPORT = REPORTS_DIR / "notebook_structure_audit.md"

BAD_MARKERS = [
    "\ufffd",
    "\u00e7",
    "\u00e8",
    "\u00e5",
    "\u00e6",
    "\u9422",
    "\u93bb",
    "\u7039",
    "\u9359",
    "\u9366",
    "\u93ac",
]
REQUIRED_MARKERS = [
    "# RoboChallenge pi0.5 复现与提交操作手册",
    "第 40 节：真实提交阻塞项摘要",
    "RUN_SUBMISSION_BLOCKERS_SUMMARY",
    "scripts/audit_submission_blockers_summary.py",
    "第 41 节：强确认真实 runner 模板审计",
    "RUN_READY_REAL_RUNNER_TEMPLATE_AUDIT",
    "scripts/audit_ready_real_runner_template.py",
    "第 42 节：授权后 checkpoint 归档模板审计",
    "RUN_AUTHORIZED_CHECKPOINT_ARCHIVE_TEMPLATE_AUDIT",
    "scripts/audit_authorized_checkpoint_archive_template.py",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计主 Notebook 结构、编码和提交阻塞项章节；不执行 Notebook。")
    parser.add_argument("--notebook", type=Path, default=NOTEBOOK, help="Notebook 路径。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文审计报告输出路径。")
    return parser.parse_args()


def load_notebook(path: Path) -> tuple[dict[str, Any], bytes, str]:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    return json.loads(text), raw, text


def build_status(notebook_path: Path) -> dict[str, Any]:
    nb, raw, text = load_notebook(notebook_path)
    cells = nb.get("cells", [])
    ids = [cell.get("id") for cell in cells]
    id_counts: dict[str, int] = {}
    for cell_id in ids:
        if isinstance(cell_id, str) and cell_id:
            id_counts[cell_id] = id_counts.get(cell_id, 0) + 1
    duplicate_ids = sorted([cell_id for cell_id, count in id_counts.items() if count > 1])
    missing_id_indexes = [
        index
        for index, cell in enumerate(cells)
        if not isinstance(cell.get("id"), str) or not cell.get("id")
    ]
    code_cells_with_outputs = [
        index for index, cell in enumerate(cells) if cell.get("cell_type") == "code" and cell.get("outputs")
    ]
    code_cells_with_execution_count = [
        index
        for index, cell in enumerate(cells)
        if cell.get("cell_type") == "code" and cell.get("execution_count") is not None
    ]
    marker_presence = {marker: marker in text for marker in REQUIRED_MARKERS}
    bad_marker_hits = [marker for marker in BAD_MARKERS if marker in text]
    crlf_count = raw.count(b"\r\n")
    notebook_path_rel = notebook_path.relative_to(ROOT).as_posix()
    blocking: list[str] = []
    if nb.get("nbformat") != 4:
        blocking.append("Notebook nbformat 不是 4。")
    if missing_id_indexes:
        blocking.append("Notebook 存在缺失 cell id 的单元。")
    if duplicate_ids:
        blocking.append("Notebook 存在重复 cell id。")
    if code_cells_with_outputs:
        blocking.append("源 Notebook 中存在已执行输出，应保持为可复跑的干净版本。")
    if code_cells_with_execution_count:
        blocking.append("源 Notebook 中存在 execution_count，应保持为未执行状态。")
    if crlf_count:
        blocking.append("Notebook 使用 CRLF 行尾，Linux/Jupyter 审计要求使用 LF。")
    if bad_marker_hits:
        blocking.append("Notebook 疑似包含乱码或替换字符。")
    for marker, ok in marker_presence.items():
        if not ok:
            blocking.append(f"Notebook 缺少关键章节或命令标记：{marker}")
    if not blocking:
        blocking.append("Notebook 结构、编码和提交阻塞项章节已通过静态审计。")
    passed = bool(
        nb.get("nbformat") == 4
        and len(cells) >= 40
        and not missing_id_indexes
        and not duplicate_ids
        and not code_cells_with_outputs
        and not code_cells_with_execution_count
        and crlf_count == 0
        and not bad_marker_hits
        and all(marker_presence.values())
    )
    return {
        "kind": "notebook_structure_audit",
        "passed": passed,
        "platform_contacted": False,
        "uploads_performed": False,
        "credentials_read": False,
        "credentials_printed": False,
        "link_values_printed": False,
        "secret_values_printed": False,
        "notebook_path": notebook_path_rel,
        "nbformat": nb.get("nbformat"),
        "nbformat_minor": nb.get("nbformat_minor"),
        "cell_count": len(cells),
        "missing_id_indexes": missing_id_indexes,
        "duplicate_ids": duplicate_ids,
        "code_cells_with_outputs": code_cells_with_outputs,
        "code_cells_with_execution_count": code_cells_with_execution_count,
        "crlf_count": crlf_count,
        "bad_marker_hits": bad_marker_hits,
        "required_markers": marker_presence,
        "blocking": blocking,
    }


def write_report(status: dict[str, Any], path: Path) -> None:
    lines = [
        "# Notebook 结构与编码审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- Notebook：`{status['notebook_path']}`。",
        f"- cell 数量：`{status['cell_count']}`。",
        f"- 缺失 cell id 数量：`{len(status['missing_id_indexes'])}`。",
        f"- 重复 cell id 数量：`{len(status['duplicate_ids'])}`。",
        f"- 带输出的代码 cell 数量：`{len(status['code_cells_with_outputs'])}`。",
        f"- 带 execution_count 的代码 cell 数量：`{len(status['code_cells_with_execution_count'])}`。",
        f"- CRLF 行尾数量：`{status['crlf_count']}`。",
        f"- 乱码哨兵命中数量：`{len(status['bad_marker_hits'])}`。",
        f"- 是否连接平台：`{status['platform_contacted']}`。",
        f"- 是否读取或打印凭据：`{status['credentials_read'] or status['credentials_printed']}`。",
        "",
        "## 关键章节标记",
        "",
    ]
    for marker, ok in status["required_markers"].items():
        lines.append(f"- `{marker}`：`{ok}`。")
    lines.extend(["", "## Blocking", ""])
    for item in status["blocking"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args()
    status = build_status(args.notebook)
    args.status_path.parent.mkdir(parents=True, exist_ok=True)
    with args.status_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(status, ensure_ascii=False, indent=2) + "\n")
    write_report(status, args.report_path)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
