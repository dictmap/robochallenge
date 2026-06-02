#!/usr/bin/env python3
"""Audit the local checkpoint archive plan without creating tar files or uploading."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import shutil
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = ROOT / "runs"
DEFAULT_STATUS = RUNS_DIR / "checkpoint_archive_plan.json"
DEFAULT_REPORT = REPORTS_DIR / "checkpoint_archive_plan.md"
EXPORT_STATUS = RUNS_DIR / "lora_checkpoint_export_readiness.json"
UPLOAD_STATUS = RUNS_DIR / "checkpoint_upload_channels_audit.json"
CHECKPOINT_DIR = RUNS_DIR / "openpi_rtc_lora_materialized_policy_checkpoint"
ARCHIVE_PATH = RUNS_DIR / "openpi_rtc_lora_materialized_policy_checkpoint.tar"
SHA256_PATH = RUNS_DIR / "openpi_rtc_lora_materialized_policy_checkpoint.tar.sha256"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计 LoRA checkpoint 本地 tar/sha256 归档计划，不生成大文件。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文审计报告输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def git_check_ignore(path: Path) -> dict[str, Any]:
    rel = path.relative_to(ROOT)
    result = subprocess.run(
        ["git", "-C", str(ROOT), "check-ignore", "-v", str(rel)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {"ignored": result.returncode == 0, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}


def disk_bucket_status(required_bytes: int) -> dict[str, Any]:
    usage = shutil.disk_usage(RUNS_DIR)
    free_gb = usage.free / 1024**3
    return {
        "free_space_bucket_gb": int(math.floor(free_gb / 10) * 10),
        "required_bytes": required_bytes,
        "required_gb_rounded": round(required_bytes / 1024**3, 3),
        "margin_factor_required": 2,
        "free_space_margin_passed": usage.free > required_bytes * 2,
    }


def build_status() -> dict[str, Any]:
    export_status = read_json(EXPORT_STATUS)
    upload_status = read_json(UPLOAD_STATUS)
    inventory = export_status.get("inventory", {})
    tar_smoke = export_status.get("tar_stream_smoke", {})
    expected_archive_bytes = int(tar_smoke.get("archive_stream_bytes") or inventory.get("total_size_bytes") or 0)
    create_command = (
        "tar -C runs -cf runs/openpi_rtc_lora_materialized_policy_checkpoint.tar "
        "openpi_rtc_lora_materialized_policy_checkpoint"
    )
    sha256_command = (
        "sha256sum runs/openpi_rtc_lora_materialized_policy_checkpoint.tar > "
        "runs/openpi_rtc_lora_materialized_policy_checkpoint.tar.sha256"
    )
    optional_split_command = (
        "split -b 4G -d -a 3 runs/openpi_rtc_lora_materialized_policy_checkpoint.tar "
        "runs/openpi_rtc_lora_materialized_policy_checkpoint.tar.part-"
    )
    archive_ignore = git_check_ignore(ARCHIVE_PATH)
    sha_ignore = git_check_ignore(SHA256_PATH)
    part_ignore = git_check_ignore(RUNS_DIR / "openpi_rtc_lora_materialized_policy_checkpoint.tar.part-000")
    disk = disk_bucket_status(expected_archive_bytes)
    required_inputs = {
        "export_audit_local_ready": bool(export_status.get("local_export_ready")),
        "tar_stream_smoke_passed": bool(tar_smoke.get("passed")),
        "upload_audit_passed": bool(upload_status.get("passed")),
        "checkpoint_dir_exists": CHECKPOINT_DIR.exists(),
        "archive_absent": not ARCHIVE_PATH.exists(),
        "sha256_absent": not SHA256_PATH.exists(),
        "uploads_not_performed": upload_status.get("uploads_performed") is False,
    }
    commands_safe = all(
        [
            create_command.startswith("tar -C runs -cf runs/"),
            " /home/" not in create_command,
            "rm " not in create_command,
            sha256_command.startswith("sha256sum runs/"),
            ">" in sha256_command,
            optional_split_command.startswith("split -b 4G"),
        ]
    )
    passed = all(
        [
            all(required_inputs.values()),
            expected_archive_bytes > 10 * 1024**3,
            archive_ignore["ignored"],
            sha_ignore["ignored"],
            part_ignore["ignored"],
            disk["free_space_margin_passed"],
            commands_safe,
        ]
    )
    return {
        "kind": "checkpoint_archive_plan",
        "passed": passed,
        "archive_created": False,
        "upload_performed": False,
        "credentials_read": False,
        "checkpoint_dir": "runs/openpi_rtc_lora_materialized_policy_checkpoint",
        "archive_path": "runs/openpi_rtc_lora_materialized_policy_checkpoint.tar",
        "sha256_path": "runs/openpi_rtc_lora_materialized_policy_checkpoint.tar.sha256",
        "expected_archive_bytes": expected_archive_bytes,
        "expected_archive_gb": round(expected_archive_bytes / 1024**3, 3),
        "required_inputs": required_inputs,
        "git_ignore": {
            "archive_ignored": archive_ignore["ignored"],
            "sha256_ignored": sha_ignore["ignored"],
            "split_part_ignored": part_ignore["ignored"],
        },
        "disk": disk,
        "commands": {
            "create_archive": create_command,
            "write_sha256": sha256_command,
            "optional_split_4g": optional_split_command,
            "commands_safe": commands_safe,
        },
        "blocking": [
            "本审计不生成 tar、不计算真实 sha256、不上传 checkpoint。",
            "真实上传仍需要用户选择并授权存储位置，再提供可访问 checkpoint link。",
        ],
    }


def write_report(status: dict[str, Any], path: Path) -> None:
    lines = [
        "# Checkpoint 归档计划审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 是否生成 tar：`{status['archive_created']}`。",
        f"- 是否执行上传：`{status['upload_performed']}`。",
        f"- 是否读取凭据：`{status['credentials_read']}`。",
        f"- 预计 tar 大小：`{status['expected_archive_gb']}` GB。",
        f"- runs 剩余空间十 GB 桶：`{status['disk']['free_space_bucket_gb']}` GB。",
        f"- 空间余量是否满足 2 倍预计 tar：`{status['disk']['free_space_margin_passed']}`。",
        "",
        "## 路径与 Git 忽略",
        "",
    ]
    for key, value in status["git_ignore"].items():
        lines.append(f"- `{key}`：`{value}`。")
    lines.extend(["", "## 建议命令", ""])
    for key, value in status["commands"].items():
        lines.append(f"- `{key}`：`{value}`。")
    lines.extend(["", "## 输入证据", ""])
    for key, value in status["required_inputs"].items():
        lines.append(f"- `{key}`：`{value}`。")
    lines.extend(["", "## Blocking", ""])
    for item in status["blocking"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    status = build_status()
    args.status_path.parent.mkdir(parents=True, exist_ok=True)
    args.status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(status, args.report_path)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
