#!/usr/bin/env python3
"""Audit whether the materialized LoRA checkpoint is ready to export/upload."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = ROOT / "runs"
DEFAULT_CHECKPOINT = RUNS_DIR / "openpi_rtc_lora_materialized_policy_checkpoint"
DEFAULT_STATUS = RUNS_DIR / "lora_checkpoint_export_readiness.json"
DEFAULT_REPORT = REPORTS_DIR / "lora_checkpoint_export_readiness.md"


REQUIRED_RELATIVE_FILES = [
    "params/_METADATA",
    "params/_CHECKPOINT_METADATA",
    "params/manifest.ocdbt",
    "params/ocdbt.process_0/manifest.ocdbt",
    "assets/cvpr_multitask_aloha/norm_stats.json",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计 LoRA 完整 checkpoint 是否具备导出/上传前置条件。")
    parser.add_argument(
        "--checkpoint-dir",
        type=Path,
        default=DEFAULT_CHECKPOINT,
        help="本地完整 LoRA policy checkpoint 目录。",
    )
    parser.add_argument(
        "--status-path",
        type=Path,
        default=DEFAULT_STATUS,
        help="机器可读 JSON 输出路径。",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=DEFAULT_REPORT,
        help="中文审计报告输出路径。",
    )
    parser.add_argument(
        "--hash-small-files",
        action="store_true",
        help="计算必要小文件 sha256；不会散列 12GB 参数 shard。",
    )
    return parser.parse_args()


def human_size(num_bytes: int) -> str:
    value = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if value < 1024 or unit == "TB":
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{num_bytes} B"


def git_check_ignore(path: Path) -> dict[str, Any]:
    rel_path = path.relative_to(ROOT)
    result = subprocess.run(
        ["git", "-C", str(ROOT), "check-ignore", "-v", str(rel_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "path": str(rel_path),
        "ignored": result.returncode == 0,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def collect_file_inventory(root: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    dir_count = 0
    total_size = 0
    for path in root.rglob("*"):
        if path.is_dir():
            dir_count += 1
            continue
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        size = path.stat().st_size
        files.append({"path": rel, "size_bytes": size, "size_human": human_size(size)})
        total_size += size
    largest = sorted(files, key=lambda item: item["size_bytes"], reverse=True)[:12]
    params_data_count = sum(1 for item in files if "/d/" in item["path"] or item["path"].startswith("params/d/"))
    return {
        "file_count": len(files),
        "dir_count": dir_count,
        "total_size_bytes": total_size,
        "total_size_human": human_size(total_size),
        "largest_files": largest,
        "params_data_file_count": params_data_count,
    }


def build_status(args: argparse.Namespace) -> dict[str, Any]:
    checkpoint_dir = args.checkpoint_dir.resolve()
    checkpoint_rel = checkpoint_dir.relative_to(ROOT).as_posix()
    required_files = []
    for rel in REQUIRED_RELATIVE_FILES:
        path = checkpoint_dir / rel
        item: dict[str, Any] = {
            "path": f"{checkpoint_rel}/{rel}",
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() and path.is_file() else None,
        }
        if item["size_bytes"] is not None:
            item["size_human"] = human_size(int(item["size_bytes"]))
        if args.hash_small_files and path.exists() and path.is_file() and path.stat().st_size <= 20 * 1024 * 1024:
            item["sha256"] = sha256_file(path)
        required_files.append(item)

    inventory = collect_file_inventory(checkpoint_dir) if checkpoint_dir.exists() else {
        "file_count": 0,
        "dir_count": 0,
        "total_size_bytes": 0,
        "total_size_human": "0.00 B",
        "largest_files": [],
        "params_data_file_count": 0,
    }
    ignore_probe = git_check_ignore(checkpoint_dir / "params/_METADATA") if checkpoint_dir.exists() else {
        "ignored": False,
        "stdout": "",
        "stderr": "checkpoint missing",
    }

    local_export_ready = all(
        [
            checkpoint_dir.exists(),
            checkpoint_dir.is_dir(),
            all(item["exists"] for item in required_files),
            inventory["total_size_bytes"] > 10 * 1024**3,
            inventory["params_data_file_count"] > 0,
            ignore_probe["ignored"],
        ]
    )
    upload_blocking = [
        "需要用户选择并授权可公开或评测端可访问的存储位置。",
        "需要用户提供真实 ROBOCHALLENGE_USER_TOKEN。",
        "需要用户提供真实 ROBOCHALLENGE_SUBMISSION_ID。",
        "上传后需要把真实 checkpoint link 填回 RoboChallenge 网站；本脚本不会伪造链接。",
    ]
    archive_name = "openpi_rtc_lora_materialized_policy_checkpoint.tar"
    return {
        "kind": "lora_checkpoint_export_readiness",
        "passed": local_export_ready,
        "local_export_ready": local_export_ready,
        "web_submission_ready": False,
        "checkpoint_dir": checkpoint_rel,
        "required_files": required_files,
        "inventory": inventory,
        "git_ignore": ignore_probe,
        "recommended_local_archive": {
            "path": f"runs/{archive_name}",
            "git_ignored_by_pattern": "*.tar",
            "create_command": (
                "tar -C runs -cf runs/openpi_rtc_lora_materialized_policy_checkpoint.tar "
                "openpi_rtc_lora_materialized_policy_checkpoint"
            ),
            "hash_command": f"sha256sum runs/{archive_name} > runs/{archive_name}.sha256",
            "note": "默认不自动打包 12GB+ checkpoint；只有需要上传时再手动执行。",
        },
        "upload_blocking": upload_blocking,
    }


def write_report(status: dict[str, Any], report_path: Path) -> None:
    inv = status["inventory"]
    lines = [
        "# LoRA checkpoint 导出就绪审计",
        "",
        "## 结论",
        "",
        f"- 本地导出就绪：`{status['local_export_ready']}`。",
        f"- 网站提交就绪：`{status['web_submission_ready']}`。",
        f"- checkpoint 目录：`{status['checkpoint_dir']}`。",
        f"- 文件数量：`{inv['file_count']}`；目录数量：`{inv['dir_count']}`；总大小：`{inv['total_size_human']}`。",
        f"- 参数数据 shard 数量：`{inv['params_data_file_count']}`。",
        f"- Git 忽略状态：`{status['git_ignore']['ignored']}`。",
        "",
        "## 必需文件",
        "",
    ]
    for item in status["required_files"]:
        size = item.get("size_human", "missing")
        lines.append(f"- `{item['path']}`：exists=`{item['exists']}`，size=`{size}`。")
    lines.extend(
        [
            "",
            "## 最大文件抽样",
            "",
        ]
    )
    for item in inv["largest_files"]:
        lines.append(f"- `{item['path']}`：`{item['size_human']}`。")
    archive = status["recommended_local_archive"]
    lines.extend(
        [
            "",
            "## 建议导出命令",
            "",
            "默认不自动打包大文件。需要上传 checkpoint 时，在 Linux 仓库根目录手动执行：",
            "",
            "```bash",
            archive["create_command"],
            archive["hash_command"],
            "```",
            "",
            "生成的 `.tar` 文件被 `.gitignore` 排除，不应提交到 Git。",
            "",
            "## Blocking",
            "",
        ]
    )
    for item in status["upload_blocking"]:
        lines.append(f"- {item}")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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
