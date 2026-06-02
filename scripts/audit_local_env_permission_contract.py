#!/usr/bin/env python3
"""Audit local env file permission contract without reading credential values."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
LOCAL_ENV_REL = "submission/robochallenge_env.local.sh"
ENV_TEMPLATE_REL = "submission/robochallenge_env_template.sh"
DEFAULT_STATUS = RUNS_DIR / "local_env_permission_contract.json"
DEFAULT_REPORT = REPORTS_DIR / "local_env_permission_contract.md"
RECOMMENDED_CHMOD = "chmod 600 submission/robochallenge_env.local.sh"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计 local env 权限契约；不读取真实凭据内容。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文报告输出路径。")
    return parser.parse_args()


def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def git_check_ignore(rel: str) -> bool:
    return run_git(["check-ignore", "-q", rel]).returncode == 0


def git_is_tracked(rel: str) -> bool:
    return run_git(["ls-files", "--error-unmatch", rel]).returncode == 0


def mode_info(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "exists": False,
            "mode_octal": "",
            "owner_readable": False,
            "group_or_other_has_any_permission": False,
            "owner_only_permissions": True,
        }
    mode = stat.S_IMODE(path.stat().st_mode)
    group_or_other_bits = mode & (stat.S_IRWXG | stat.S_IRWXO)
    return {
        "exists": True,
        "mode_octal": oct(mode),
        "owner_readable": bool(mode & stat.S_IRUSR),
        "group_or_other_has_any_permission": group_or_other_bits != 0,
        "owner_only_permissions": group_or_other_bits == 0,
    }


def synthetic_chmod_smoke() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="robochallenge-local-env-perm-") as tmpdir:
        path = Path(tmpdir) / "robochallenge_env.local.sh"
        path.write_text("# synthetic placeholder file; no real values\n", encoding="utf-8")
        path.chmod(0o600)
        info = mode_info(path)
    return {
        "created": True,
        "removed_after_run": not Path(tmpdir).exists(),
        "mode_octal": info["mode_octal"],
        "owner_only_permissions": info["owner_only_permissions"],
        "owner_readable": info["owner_readable"],
    }


def build_status() -> dict[str, Any]:
    local_env_path = ROOT / LOCAL_ENV_REL
    env_template_path = ROOT / ENV_TEMPLATE_REL
    template_text = env_template_path.read_text(encoding="utf-8") if env_template_path.exists() else ""
    local_info = mode_info(local_env_path)
    synthetic = synthetic_chmod_smoke()
    evidence = {
        "env_template_exists": env_template_path.exists(),
        "env_template_mentions_local_copy": LOCAL_ENV_REL in template_text,
        "env_template_recommends_chmod_600": RECOMMENDED_CHMOD in template_text,
        "local_env_gitignored": git_check_ignore(LOCAL_ENV_REL),
        "local_env_not_tracked": git_is_tracked(LOCAL_ENV_REL) is False,
        "local_env_content_not_read": True,
        "local_env_absent_or_owner_only": local_info["owner_only_permissions"] is True,
        "synthetic_chmod_600_owner_only": synthetic["owner_only_permissions"] is True,
        "synthetic_chmod_600_owner_readable": synthetic["owner_readable"] is True,
        "synthetic_file_removed_after_run": synthetic["removed_after_run"] is True,
    }
    leak_flags = {
        "credentials_printed": False,
        "link_values_printed": False,
        "secret_values_printed": False,
    }
    contact_flags = {
        "platform_contacted": False,
        "uploads_performed": False,
        "download_host_contacted": False,
    }
    passed = bool(all(evidence.values()) and not any(leak_flags.values()) and not any(contact_flags.values()))
    blocking = []
    if passed:
        blocking.append("local env 权限契约已通过；真实凭据文件应保持 Git 忽略、未跟踪且 chmod 600。")
    else:
        for key, ok in evidence.items():
            if not ok:
                blocking.append(f"local env 权限证据未通过 `{key}`。")
        if local_info["exists"] and not local_info["owner_only_permissions"]:
            blocking.append(f"请执行 `{RECOMMENDED_CHMOD}` 后重新审计。")

    return {
        "kind": "local_env_permission_contract",
        "passed": passed,
        "recommended_route": "baseline_official_aloha",
        "recommended_local_env": LOCAL_ENV_REL,
        "recommended_chmod_command": RECOMMENDED_CHMOD,
        "local_env_exists": local_info["exists"],
        "local_env_mode_octal": local_info["mode_octal"],
        "local_env_owner_only_permissions": local_info["owner_only_permissions"],
        "local_env_group_or_other_has_any_permission": local_info["group_or_other_has_any_permission"],
        "local_env_content_read": False,
        "synthetic_chmod_smoke": synthetic,
        "evidence": evidence,
        "leak_flags": leak_flags,
        "contact_flags": contact_flags,
        "platform_contacted": False,
        "uploads_performed": False,
        "credentials_read": False,
        "credentials_printed": False,
        "link_values_printed": False,
        "secret_values_printed": False,
        "blocking": blocking,
    }


def write_report(status: dict[str, Any], path: Path) -> None:
    lines = [
        "# Local env 权限契约审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 推荐路线：`{status['recommended_route']}`。",
        f"- 建议本地凭据文件：`{status['recommended_local_env']}`。",
        f"- 建议权限命令：`{status['recommended_chmod_command']}`。",
        f"- 本地凭据文件是否存在：`{status['local_env_exists']}`。",
        f"- 本地凭据文件权限：`{status['local_env_mode_octal']}`。",
        f"- 本地凭据文件是否仅 owner 有权限：`{status['local_env_owner_only_permissions']}`。",
        f"- 是否读取本地凭据文件内容：`{status['local_env_content_read']}`。",
        "",
        "## 边界",
        "",
        "- 本审计只读取文件元数据和模板文本，不读取真实 local env 内容。",
        "- 如果真实 local env 文件存在，建议权限必须收敛到 `chmod 600`。",
        "- Windows/PowerShell 侧权限语义不同；最终提交前以 Linux 端审计结果为准。",
        "",
        "## 只读边界",
        "",
    ]
    for key, value in status["contact_flags"].items():
        lines.append(f"- `{key}`：`{value}`。")
    for key, value in status["leak_flags"].items():
        lines.append(f"- `{key}`：`{value}`。")
    lines.extend(["", "## 输入证据", ""])
    for key, value in status["evidence"].items():
        lines.append(f"- `{key}`：`{value}`。")
    lines.extend(["", "## Blocking", ""])
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
