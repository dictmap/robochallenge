#!/usr/bin/env python3
"""Audit the Jupyter-only local env input template without reading secrets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "robochallenge_pi05_submit_cn.ipynb"
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = ROOT / "runs"
DEFAULT_STATUS = RUNS_DIR / "jupyter_input_template_audit.json"
DEFAULT_REPORT = REPORTS_DIR / "jupyter_input_template_audit.md"

SECTION_MARKER = "第 44 节：安全填空本地 env 入口"
RUN_FLAG = "RUN_SAFE_LOCAL_ENV_INPUT_TEMPLATE"
LOCAL_ENV_PATH = "submission/robochallenge_env.local.sh"
REQUIRED_KEYS = [
    "ROBOCHALLENGE_USER_TOKEN",
    "ROBOCHALLENGE_SUBMISSION_ID",
    "ROBOCHALLENGE_SUBMISSION_VARIANT",
    "ROBOCHALLENGE_LORA_CHECKPOINT_LINK",
    "ROBOCHALLENGE_CHECKPOINT_LINK",
]
REQUIRED_FRAGMENTS = [
    SECTION_MARKER,
    RUN_FLAG,
    f"{RUN_FLAG} = False",
    "import getpass",
    "import shlex",
    "getpass.getpass",
    "shlex.quote",
    "is_placeholder_like",
    "PLACEHOLDER_MARKERS",
    "missing_or_placeholder",
    "normalize_submission_variant",
    "required_for_variant",
    'submission_variant == "lora"',
    "ROBOCHALLENGE_CHECKPOINT_LINK [baseline 可留空]",
    "baseline 官方 ALOHA 路线只要求 token 和 submission id，不要求 checkpoint link",
    "scripts/render_route_aware_submission_blockers.py",
    "reports/baseline_submission_quickstart.md",
    "baseline 不因 checkpoint link 留空进入 LoRA 上传流程",
    "os.chmod",
    LOCAL_ENV_PATH,
    *REQUIRED_KEYS,
]
FORBIDDEN_FRAGMENTS = [
    "print(token",
    "print(env_values",
    "print(value",
    "display(env_values",
    "ROBOCHALLENGE_USER_TOKEN =",
    "ROBOCHALLENGE_SUBMISSION_ID =",
    "ROBOCHALLENGE_LORA_CHECKPOINT_LINK =",
    "ROBOCHALLENGE_CHECKPOINT_LINK =",
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
        description="审计 Notebook 中的安全填空本地 env 入口；不执行 Notebook，不读取本地凭据。"
    )
    parser.add_argument("--notebook", type=Path, default=NOTEBOOK, help="Notebook 路径。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文审计报告输出路径。")
    return parser.parse_args()


def git_check_ignore(rel: str) -> dict[str, Any]:
    result = subprocess.run(
        ["git", "check-ignore", "-q", rel],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return {"path": rel, "ignored": result.returncode == 0, "returncode": result.returncode}


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
    variant_logic = {
        "submission_variant_supported": "ROBOCHALLENGE_SUBMISSION_VARIANT" in section_source
        and "normalize_submission_variant" in section_source,
        "baseline_checkpoint_link_optional": "ROBOCHALLENGE_CHECKPOINT_LINK [baseline 可留空]" in section_source,
        "recommended_route_baseline": "默认 variant 是 `baseline`" in section_source
        and "baseline 官方 ALOHA 路线" in section_source,
        "lora_checkpoint_link_required": 'submission_variant == "lora"' in section_source
        and "ROBOCHALLENGE_LORA_CHECKPOINT_LINK" in section_source
        and "required_for_variant.extend" in section_source,
    }
    route_guidance = {
        "baseline_guides_to_route_aware": "scripts/render_route_aware_submission_blockers.py" in section_source,
        "baseline_quickstart_referenced": "reports/baseline_submission_quickstart.md" in section_source,
        "baseline_no_checkpoint_link": "不要求 checkpoint link" in section_source,
        "baseline_no_lora_upload_when_link_blank": "baseline 不因 checkpoint link 留空进入 LoRA 上传流程"
        in section_source,
        "lora_web_upload_flow_separate": "LoRA 上传流程" in section_source,
    }
    code_cell_ok = bool(code_cell and code_cell.get("cell_type") == "code")
    code_cell_clean = bool(
        code_cell_ok
        and not code_cell.get("outputs")
        and code_cell.get("execution_count") is None
        and isinstance(code_cell.get("id"), str)
        and bool(code_cell.get("id"))
    )
    run_flag_default_false = f"{RUN_FLAG} = False" in section_source
    local_env_ignore = git_check_ignore(LOCAL_ENV_PATH)
    secret_hits = secret_pattern_hits(section_source)
    whole_notebook_secret_hits = secret_pattern_hits(text)

    blocking = []
    if not notebook_exists:
        blocking.append("缺少 Notebook。")
    if markdown_cell is None:
        blocking.append("Notebook 缺少第 44 节安全填空入口。")
    if not code_cell_ok:
        blocking.append("第 44 节后面缺少代码 cell。")
    if not code_cell_clean:
        blocking.append("第 44 节代码 cell 必须保持未执行、无输出、带稳定 cell id。")
    if not run_flag_default_false:
        blocking.append("安全填空入口必须默认不执行。")
    for fragment, ok in required_fragments.items():
        if not ok:
            blocking.append(f"安全填空入口缺少关键片段：`{fragment}`。")
    for fragment, hit in forbidden_fragments.items():
        if hit:
            blocking.append(f"安全填空入口包含禁止片段：`{fragment}`。")
    if not all(required_keys.values()):
        blocking.append("安全填空入口没有覆盖全部必要环境变量。")
    if not all(variant_logic.values()):
        blocking.append("安全填空入口没有正确区分 baseline 与 LoRA 的 checkpoint link 要求。")
    if not all(route_guidance.values()):
        blocking.append("安全填空入口没有把 baseline 默认路线和 LoRA/web checkpoint 上传路线清晰分离。")
    if not local_env_ignore["ignored"]:
        blocking.append(f"`{LOCAL_ENV_PATH}` 没有被 Git 忽略。")
    if secret_hits or whole_notebook_secret_hits:
        blocking.append("Notebook 安全填空入口或 Notebook 本体疑似包含明文 token/submission id。")
    if not blocking:
        blocking.append("Jupyter 安全填空本地 env 入口已就绪；当前未读取、未写入、未打印真实凭据。")

    passed = bool(
        notebook_exists
        and section_index is not None
        and code_cell_clean
        and run_flag_default_false
        and all(required_fragments.values())
        and not any(forbidden_fragments.values())
        and all(required_keys.values())
        and all(variant_logic.values())
        and all(route_guidance.values())
        and local_env_ignore["ignored"]
        and not secret_hits
        and not whole_notebook_secret_hits
    )
    return {
        "kind": "jupyter_input_template_audit",
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
        "run_flag_default_false": run_flag_default_false,
        "local_env_path": LOCAL_ENV_PATH,
        "local_env_ignored": local_env_ignore,
        "required_keys": required_keys,
        "recommended_route": "baseline_official_aloha" if route_guidance["baseline_guides_to_route_aware"] else "",
        "baseline_requires_checkpoint_link": False if route_guidance["baseline_no_checkpoint_link"] else None,
        "baseline_requires_checkpoint_upload": False
        if route_guidance["baseline_no_lora_upload_when_link_blank"]
        else None,
        "lora_web_requires_checkpoint_link": True if variant_logic["lora_checkpoint_link_required"] else None,
        "lora_web_requires_checkpoint_upload": True if route_guidance["lora_web_upload_flow_separate"] else None,
        "variant_logic": variant_logic,
        "route_guidance": route_guidance,
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
        "# Jupyter 安全填空本地 env 入口审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- Notebook：`{status['notebook_path']}`。",
        f"- 章节：`{status['section_marker']}`。",
        f"- 入口默认执行：`{not status['run_flag_default_false']}`。",
        f"- 本地 env 路径：`{status['local_env_path']}`。",
        f"- 本地 env 已被 Git 忽略：`{status['local_env_ignored']['ignored']}`。",
        f"- 是否读取真实凭据：`{status['credentials_read']}`。",
        f"- 是否打印 token/link/submission id：`{status['credentials_printed'] or status['link_values_printed'] or status['secret_values_printed']}`。",
        f"- 是否连接 RoboChallenge 平台：`{status['platform_contacted']}`。",
        f"- 是否执行上传：`{status['uploads_performed']}`。",
        f"- 推荐路线：`{status['recommended_route']}`。",
        f"- baseline 是否要求 checkpoint link：`{status['baseline_requires_checkpoint_link']}`。",
        f"- baseline 是否要求 checkpoint upload：`{status['baseline_requires_checkpoint_upload']}`。",
        f"- LoRA/web 是否要求 checkpoint link：`{status['lora_web_requires_checkpoint_link']}`。",
        f"- LoRA/web 是否要求 checkpoint upload：`{status['lora_web_requires_checkpoint_upload']}`。",
        "",
        "## 必要变量",
        "",
    ]
    for key, ok in status["required_keys"].items():
        lines.append(f"- `{key}`：`{ok}`。")
    lines.extend(["", "## Variant 逻辑", ""])
    for key, ok in status["variant_logic"].items():
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
