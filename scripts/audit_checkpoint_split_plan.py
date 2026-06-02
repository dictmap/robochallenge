#!/usr/bin/env python3
"""Audit checkpoint split/reassemble commands without creating files."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
DEFAULT_STATUS = RUNS_DIR / "checkpoint_split_plan.json"
DEFAULT_REPORT = REPORTS_DIR / "checkpoint_split_plan.md"
ARCHIVE_PLAN_STATUS = RUNS_DIR / "checkpoint_archive_plan.json"
EXPORT_STATUS = RUNS_DIR / "lora_checkpoint_export_readiness.json"
ARCHIVE_PATH = RUNS_DIR / "openpi_rtc_lora_materialized_policy_checkpoint.tar"
SHA256_PATH = RUNS_DIR / "openpi_rtc_lora_materialized_policy_checkpoint.tar.sha256"
PART_PREFIX = RUNS_DIR / "openpi_rtc_lora_materialized_policy_checkpoint.tar.part-"
PART_SIZE_BYTES = 4 * 1024**3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计 LoRA checkpoint 分片上传计划，不生成分片、不上传。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文审计报告输出路径。")
    parser.add_argument("--part-size-gb", type=int, default=4, help="建议分片大小，单位 GiB。默认 4。")
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


def expected_archive_bytes() -> int:
    archive_plan = read_json(ARCHIVE_PLAN_STATUS)
    export_status = read_json(EXPORT_STATUS)
    tar_smoke = export_status.get("tar_stream_smoke", {})
    inventory = export_status.get("inventory", {})
    return int(
        archive_plan.get("expected_archive_bytes")
        or tar_smoke.get("archive_stream_bytes")
        or inventory.get("total_size_bytes")
        or 0
    )


def build_parts(total_bytes: int, part_size_bytes: int) -> list[dict[str, Any]]:
    if total_bytes <= 0 or part_size_bytes <= 0:
        return []
    part_count = math.ceil(total_bytes / part_size_bytes)
    parts = []
    for index in range(part_count):
        remaining = total_bytes - index * part_size_bytes
        expected_size = min(part_size_bytes, remaining)
        part_path = RUNS_DIR / f"openpi_rtc_lora_materialized_policy_checkpoint.tar.part-{index:03d}"
        parts.append(
            {
                "index": index,
                "path": part_path.relative_to(ROOT).as_posix(),
                "expected_size_bytes": expected_size,
                "expected_size_gib": round(expected_size / 1024**3, 3),
                "exists": part_path.exists(),
                "git_ignored": git_check_ignore(part_path)["ignored"],
            }
        )
    return parts


def build_status(part_size_gb: int) -> dict[str, Any]:
    archive_plan = read_json(ARCHIVE_PLAN_STATUS)
    total_bytes = expected_archive_bytes()
    part_size_bytes = part_size_gb * 1024**3
    parts = build_parts(total_bytes, part_size_bytes)
    existing_parts = sorted(PART_PREFIX.parent.glob(PART_PREFIX.name + "*"))
    split_command = (
        f"split -b {part_size_gb}G -d -a 3 {ARCHIVE_PATH.relative_to(ROOT).as_posix()} "
        f"{PART_PREFIX.relative_to(ROOT).as_posix()}"
    )
    reassemble_command = (
        f"cat {PART_PREFIX.relative_to(ROOT).as_posix()}* > {ARCHIVE_PATH.relative_to(ROOT).as_posix()}"
    )
    verify_command = f"sha256sum -c {SHA256_PATH.relative_to(ROOT).as_posix()}"
    list_parts_command = f"ls -lh {PART_PREFIX.relative_to(ROOT).as_posix()}*"
    commands_safe = all(
        [
            split_command.startswith("split -b "),
            " /" not in split_command,
            reassemble_command.startswith("cat runs/"),
            ">" in reassemble_command,
            verify_command.startswith("sha256sum -c runs/"),
            "rm " not in split_command + reassemble_command + verify_command,
        ]
    )
    passed = all(
        [
            archive_plan.get("passed") is True,
            archive_plan.get("archive_created") is False,
            archive_plan.get("upload_performed") is False,
            archive_plan.get("credentials_read") is False,
            total_bytes > 10 * 1024**3,
            part_size_gb == 4,
            len(parts) == 3,
            all(part["git_ignored"] for part in parts),
            not ARCHIVE_PATH.exists(),
            not SHA256_PATH.exists(),
            len(existing_parts) == 0,
            commands_safe,
        ]
    )
    return {
        "kind": "checkpoint_split_plan",
        "passed": passed,
        "archive_created": False,
        "parts_created": False,
        "upload_performed": False,
        "credentials_read": False,
        "platform_contacted": False,
        "archive_path": ARCHIVE_PATH.relative_to(ROOT).as_posix(),
        "sha256_path": SHA256_PATH.relative_to(ROOT).as_posix(),
        "part_prefix": PART_PREFIX.relative_to(ROOT).as_posix(),
        "expected_archive_bytes": total_bytes,
        "expected_archive_gib": round(total_bytes / 1024**3, 3),
        "part_size_bytes": part_size_bytes,
        "part_size_gib": part_size_gb,
        "expected_part_count": len(parts),
        "parts": parts,
        "archive_absent": not ARCHIVE_PATH.exists(),
        "sha256_absent": not SHA256_PATH.exists(),
        "existing_part_count": len(existing_parts),
        "all_parts_git_ignored": all(part["git_ignored"] for part in parts),
        "commands": {
            "split_archive": split_command,
            "list_parts": list_parts_command,
            "verify_reassembled_archive": verify_command,
            "reassemble_archive": reassemble_command,
            "commands_safe": commands_safe,
        },
        "blocking": [
            "本审计不生成 tar、不生成分片、不上传 checkpoint。",
            "真实分片上传仍需要用户先授权生成 tar/sha256，并选择存储通道。",
            "拿到真实可访问 checkpoint link 后，仍需运行 checkpoint link intake 和 readiness gate。",
        ],
    }


def write_report(status: dict[str, Any], path: Path) -> None:
    lines = [
        "# Checkpoint 分片上传计划审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 是否生成 tar：`{status['archive_created']}`。",
        f"- 是否生成分片：`{status['parts_created']}`。",
        f"- 是否上传：`{status['upload_performed']}`。",
        f"- 是否读取凭据：`{status['credentials_read']}`。",
        f"- 预计 tar 大小：`{status['expected_archive_gib']}` GiB。",
        f"- 建议分片大小：`{status['part_size_gib']}` GiB。",
        f"- 预计分片数量：`{status['expected_part_count']}`。",
        f"- 当前已存在分片数量：`{status['existing_part_count']}`。",
        "",
        "## 预计分片",
        "",
    ]
    for part in status["parts"]:
        lines.append(
            f"- `{part['path']}`：预计 `{part['expected_size_gib']}` GiB，"
            f"exists=`{part['exists']}`，git_ignored=`{part['git_ignored']}`。"
        )
    lines.extend(["", "## 授权后命令", ""])
    for key, value in status["commands"].items():
        lines.append(f"- `{key}`：`{value}`。")
    lines.extend(["", "## Blocking", ""])
    for item in status["blocking"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    status = build_status(args.part_size_gb)
    args.status_path.parent.mkdir(parents=True, exist_ok=True)
    args.status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(status, args.report_path)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
