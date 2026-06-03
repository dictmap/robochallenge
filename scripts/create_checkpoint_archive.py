#!/usr/bin/env python3
"""Create or dry-run the local LoRA checkpoint tar and sha256 artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
DEFAULT_STATUS = RUNS_DIR / "checkpoint_archive_dry_run.json"
DEFAULT_REPORT = REPORTS_DIR / "checkpoint_archive_dry_run.md"
ARCHIVE_PLAN_STATUS = RUNS_DIR / "checkpoint_archive_plan.json"
CHECKPOINT_DIR = RUNS_DIR / "openpi_rtc_lora_materialized_policy_checkpoint"
ARCHIVE_PATH = RUNS_DIR / "openpi_rtc_lora_materialized_policy_checkpoint.tar"
SHA256_PATH = RUNS_DIR / "openpi_rtc_lora_materialized_policy_checkpoint.tar.sha256"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="受控生成 LoRA checkpoint tar/sha256；默认只 dry-run。")
    parser.add_argument("--execute", action="store_true", help="真正生成 tar 和 sha256。默认不生成。")
    parser.add_argument(
        "--confirm-create-large-archive",
        action="store_true",
        help="二次确认生成约 12GB 归档；只有与 --execute 同时出现才会执行。",
    )
    parser.add_argument("--allow-existing", action="store_true", help="允许复用已存在的 tar。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文审计报告输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def git_check_ignore(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    result = subprocess.run(
        ["git", "-C", str(ROOT), "check-ignore", "-q", str(rel)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.returncode == 0


def disk_status(required_bytes: int) -> dict[str, Any]:
    usage = shutil.disk_usage(RUNS_DIR)
    free_gb = usage.free / 1024**3
    return {
        "free_space_bucket_gb": int(math.floor(free_gb / 10) * 10),
        "expected_archive_bytes": required_bytes,
        "expected_archive_gb": round(required_bytes / 1024**3, 3),
        "margin_factor_required": 2,
        "free_space_margin_passed": usage.free > required_bytes * 2,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024 * 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_archive_creation() -> None:
    subprocess.run(
        ["tar", "-C", str(RUNS_DIR), "-cf", str(ARCHIVE_PATH), CHECKPOINT_DIR.name],
        cwd=ROOT,
        check=True,
    )


def write_sha256() -> str:
    digest = sha256_file(ARCHIVE_PATH)
    rel_archive = ARCHIVE_PATH.relative_to(ROOT)
    SHA256_PATH.write_text(f"{digest}  {rel_archive}\n", encoding="utf-8")
    return digest


def build_status(args: argparse.Namespace) -> dict[str, Any]:
    plan = read_json(ARCHIVE_PLAN_STATUS)
    expected_archive_bytes = int(plan.get("expected_archive_bytes") or 0)
    if expected_archive_bytes <= 0:
        expected_archive_bytes = int(plan.get("disk", {}).get("required_bytes") or 0)

    tar_available = shutil.which("tar") is not None
    archive_absent_before = not ARCHIVE_PATH.exists()
    sha256_absent_before = not SHA256_PATH.exists()
    explicit_execute_gate = bool(args.execute and args.confirm_create_large_archive)
    missing_execute_confirmation = bool(args.execute and not args.confirm_create_large_archive)
    dry_run = not explicit_execute_gate

    status: dict[str, Any] = {
        "kind": "checkpoint_archive_dry_run",
        "passed": False,
        "dry_run": dry_run,
        "execute_requested": bool(args.execute),
        "confirm_create_large_archive": bool(args.confirm_create_large_archive),
        "explicit_execute_gate": explicit_execute_gate,
        "missing_execute_confirmation": missing_execute_confirmation,
        "archive_created": False,
        "sha256_created": False,
        "upload_performed": False,
        "credentials_read": False,
        "platform_contacted": False,
        "checkpoint_dir": "runs/openpi_rtc_lora_materialized_policy_checkpoint",
        "archive_path": "runs/openpi_rtc_lora_materialized_policy_checkpoint.tar",
        "sha256_path": "runs/openpi_rtc_lora_materialized_policy_checkpoint.tar.sha256",
        "checkpoint_dir_exists": CHECKPOINT_DIR.exists(),
        "archive_absent_before": archive_absent_before,
        "sha256_absent_before": sha256_absent_before,
        "archive_absent_after": None,
        "sha256_absent_after": None,
        "archive_git_ignored": git_check_ignore(ARCHIVE_PATH),
        "sha256_git_ignored": git_check_ignore(SHA256_PATH),
        "tar_available": tar_available,
        "disk": disk_status(expected_archive_bytes),
        "commands": {
            "dry_run": "python3 scripts/create_checkpoint_archive.py",
            "execute": "python3 scripts/create_checkpoint_archive.py --execute --confirm-create-large-archive",
            "tar_invocation": "tar -C runs -cf runs/openpi_rtc_lora_materialized_policy_checkpoint.tar openpi_rtc_lora_materialized_policy_checkpoint",
            "sha256_method": "python hashlib.sha256 -> runs/openpi_rtc_lora_materialized_policy_checkpoint.tar.sha256",
            "uses_shell": False,
            "destructive_commands": False,
        },
        "blocking": [
            "默认 dry-run 不生成 tar；真正生成约 12GB 归档必须显式使用 --execute --confirm-create-large-archive。",
            "本脚本不上传 checkpoint、不读取凭据、不连接 RoboChallenge 平台。",
            "baseline 官方 ALOHA 路线不需要生成 tar、上传 checkpoint 或填写 checkpoint link。",
            "LoRA/web checkpoint 路线才需要用户授权生成归档、上传并提供真实可访问 checkpoint link。",
            "baseline 真实提交仍需要用户目标确认、token、submission id、variant=baseline 和真实 runner 强确认。",
        ],
    }

    common_pass = all(
        [
            plan.get("passed"),
            status["checkpoint_dir_exists"],
            expected_archive_bytes > 10 * 1024**3,
            status["archive_git_ignored"],
            status["sha256_git_ignored"],
            status["tar_available"],
            status["disk"]["free_space_margin_passed"],
            status["commands"]["uses_shell"] is False,
            status["commands"]["destructive_commands"] is False,
        ]
    )

    if dry_run:
        if missing_execute_confirmation:
            status["blocking"].insert(0, "已请求 --execute，但缺少 --confirm-create-large-archive；为避免误解，本次不生成归档并返回失败。")
        status["archive_absent_after"] = not ARCHIVE_PATH.exists()
        status["sha256_absent_after"] = not SHA256_PATH.exists()
        status["passed"] = all(
            [
                common_pass,
                not missing_execute_confirmation,
                status["archive_absent_before"],
                status["sha256_absent_before"],
                status["archive_absent_after"],
                status["sha256_absent_after"],
                status["upload_performed"] is False,
                status["credentials_read"] is False,
                status["platform_contacted"] is False,
            ]
        )
        return status

    if not args.allow_existing and (not archive_absent_before or not sha256_absent_before):
        status["blocking"].insert(0, "目标 tar 或 sha256 已存在；请检查后删除，或显式传入 --allow-existing。")
        status["archive_absent_after"] = not ARCHIVE_PATH.exists()
        status["sha256_absent_after"] = not SHA256_PATH.exists()
        return status

    if common_pass:
        if not ARCHIVE_PATH.exists():
            run_archive_creation()
            status["archive_created"] = True
        digest = write_sha256()
        status["sha256_created"] = True
        status["sha256_prefix"] = digest[:12]

    status["archive_absent_after"] = not ARCHIVE_PATH.exists()
    status["sha256_absent_after"] = not SHA256_PATH.exists()
    archive_size_ok = ARCHIVE_PATH.exists() and ARCHIVE_PATH.stat().st_size >= expected_archive_bytes
    status["passed"] = all(
        [
            common_pass,
            archive_size_ok,
            SHA256_PATH.exists(),
            status["upload_performed"] is False,
            status["credentials_read"] is False,
            status["platform_contacted"] is False,
        ]
    )
    return status


def write_report(status: dict[str, Any], path: Path) -> None:
    lines = [
        "# Checkpoint 归档生成 dry-run",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 是否 dry-run：`{status['dry_run']}`。",
        f"- 是否请求执行：`{status['execute_requested']}`。",
        f"- 是否通过显式执行门槛：`{status['explicit_execute_gate']}`。",
        f"- 是否缺少执行确认：`{status['missing_execute_confirmation']}`。",
        f"- 是否生成 tar：`{status['archive_created']}`。",
        f"- 是否生成 sha256：`{status['sha256_created']}`。",
        f"- 是否上传：`{status['upload_performed']}`。",
        f"- 是否读取凭据：`{status['credentials_read']}`。",
        f"- 是否连接平台：`{status['platform_contacted']}`。",
        f"- 预期 tar 大小：`{status['disk']['expected_archive_gb']}` GB。",
        f"- runs 剩余空间 10GB 桶：`{status['disk']['free_space_bucket_gb']}` GB。",
        "",
        "## 路径状态",
        "",
        f"- checkpoint 目录存在：`{status['checkpoint_dir_exists']}`。",
        f"- tar 生成前不存在：`{status['archive_absent_before']}`。",
        f"- sha256 生成前不存在：`{status['sha256_absent_before']}`。",
        f"- tar 生成后不存在：`{status['archive_absent_after']}`。",
        f"- sha256 生成后不存在：`{status['sha256_absent_after']}`。",
        f"- tar 路径被 Git 忽略：`{status['archive_git_ignored']}`。",
        f"- sha256 路径被 Git 忽略：`{status['sha256_git_ignored']}`。",
        "",
        "## 命令",
        "",
    ]
    for key, value in status["commands"].items():
        lines.append(f"- `{key}`：`{value}`。")
    lines.extend(["", "## Blocking", ""])
    for item in status["blocking"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    status = build_status(args)
    args.status_path.parent.mkdir(parents=True, exist_ok=True)
    args.status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(status, args.report_path)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
