#!/usr/bin/env python3
"""Audit local upload-channel readiness for the materialized LoRA checkpoint."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = ROOT / "runs"
EXPORT_STATUS = RUNS_DIR / "lora_checkpoint_export_readiness.json"
DEFAULT_STATUS = RUNS_DIR / "checkpoint_upload_channels_audit.json"
DEFAULT_REPORT = REPORTS_DIR / "checkpoint_upload_channels_audit.md"


COMMANDS = {
    "hf": [["hf", "--version"]],
    "huggingface-cli": [["huggingface-cli", "--version"]],
    "gh": [["gh", "--version"]],
    "git-lfs": [["git", "lfs", "version"]],
    "rclone": [["rclone", "version"]],
    "ossutil": [["ossutil", "version"], ["ossutil", "--version"]],
    "aws": [["aws", "--version"]],
    "gsutil": [["gsutil", "version"]],
    "gcloud": [["gcloud", "--version"]],
    "azcopy": [["azcopy", "--version"]],
    "curl": [["curl", "--version"]],
}


AUTH_PROBES = {
    "huggingface": {
        "env": ["HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"],
        "files": ["~/.cache/huggingface/token"],
    },
    "github_cli": {
        "env": ["GH_TOKEN", "GITHUB_TOKEN"],
        "files": ["~/.config/gh/hosts.yml"],
    },
    "rclone": {
        "env": ["RCLONE_CONFIG"],
        "files": ["~/.config/rclone/rclone.conf"],
    },
    "aliyun_oss": {
        "env": ["OSS_ACCESS_KEY_ID", "OSS_ACCESS_KEY_SECRET", "ALIBABA_CLOUD_ACCESS_KEY_ID"],
        "files": ["~/.ossutilconfig", "~/.ossutilconfig.aliyuncs"],
    },
    "aws_s3": {
        "env": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_PROFILE"],
        "files": ["~/.aws/credentials", "~/.aws/config"],
    },
    "google_cloud": {
        "env": ["GOOGLE_APPLICATION_CREDENTIALS", "CLOUDSDK_CONFIG"],
        "files": ["~/.boto", "~/.config/gcloud/application_default_credentials.json"],
    },
    "azure_blob": {
        "env": ["AZURE_STORAGE_CONNECTION_STRING", "AZCOPY_AUTO_LOGIN_TYPE"],
        "files": ["~/.azure"],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计 LoRA checkpoint 可用上传通道，不上传、不读取凭据明文。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文审计报告输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def run_version(command_variants: list[list[str]]) -> dict[str, Any]:
    executable = command_variants[0][0]
    path = shutil.which(executable)
    if path is None:
        return {"available": False, "path": None, "version": "", "returncode": None}
    for command in command_variants:
        try:
            result = subprocess.run(
                command,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=8,
            )
        except Exception as exc:  # pragma: no cover - defensive local audit path.
            return {"available": True, "path": path, "version": "", "returncode": None, "error": repr(exc)}
        text = (result.stdout.strip() or result.stderr.strip()).splitlines()
        if result.returncode == 0 and text:
            return {"available": True, "path": path, "version": text[0][:240], "returncode": result.returncode}
    return {"available": True, "path": path, "version": "", "returncode": result.returncode}


def redact_env_probe(keys: list[str]) -> dict[str, bool]:
    return {key: bool(os.environ.get(key)) for key in keys}


def probe_files(paths: list[str]) -> dict[str, bool]:
    result = {}
    for raw in paths:
        path = Path(raw).expanduser()
        result[raw] = path.exists()
    return result


def disk_status(path: Path) -> dict[str, Any]:
    usage = shutil.disk_usage(path)
    return {
        "path": str(path),
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "free_gb": round(usage.free / 1024**3, 3),
    }


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


def build_status() -> dict[str, Any]:
    export_status = read_json(EXPORT_STATUS)
    archive_path = RUNS_DIR / "openpi_rtc_lora_materialized_policy_checkpoint.tar"
    sha_path = RUNS_DIR / "openpi_rtc_lora_materialized_policy_checkpoint.tar.sha256"
    command_status = {name: run_version(variants) for name, variants in COMMANDS.items()}
    auth_status = {
        name: {
            "env_present": redact_env_probe(spec["env"]),
            "config_file_present": probe_files(spec["files"]),
        }
        for name, spec in AUTH_PROBES.items()
    }
    local_archive = export_status.get("recommended_local_archive", {})
    local_tar_ready = bool(
        export_status.get("local_export_ready")
        and export_status.get("tar_stream_smoke", {}).get("passed")
        and not archive_path.exists()
    )
    channels = {
        "huggingface_hub": {
            "tool_available": command_status["hf"]["available"] or command_status["huggingface-cli"]["available"],
            "credential_hint_present": any(auth_status["huggingface"]["env_present"].values())
            or any(auth_status["huggingface"]["config_file_present"].values()),
            "selected": False,
            "blocking": "需要用户确认 Hugging Face 仓库、可见性、许可和 token 后才能上传。",
        },
        "github_release_or_lfs": {
            "tool_available": command_status["gh"]["available"] or command_status["git-lfs"]["available"],
            "credential_hint_present": any(auth_status["github_cli"]["env_present"].values())
            or any(auth_status["github_cli"]["config_file_present"].values()),
            "selected": False,
            "blocking": "需要用户确认 GitHub 资产大小限制、仓库策略和 token 后才能上传。",
        },
        "rclone_remote": {
            "tool_available": command_status["rclone"]["available"],
            "credential_hint_present": any(auth_status["rclone"]["env_present"].values())
            or any(auth_status["rclone"]["config_file_present"].values()),
            "selected": False,
            "blocking": "需要用户指定 rclone remote 和可公开/评测端可访问路径。",
        },
        "object_storage": {
            "tool_available": any(
                command_status[name]["available"] for name in ["ossutil", "aws", "gsutil", "gcloud", "azcopy"]
            ),
            "credential_hint_present": any(
                any(auth_status[name]["env_present"].values()) or any(auth_status[name]["config_file_present"].values())
                for name in ["aliyun_oss", "aws_s3", "google_cloud", "azure_blob"]
            ),
            "selected": False,
            "blocking": "需要用户指定对象存储 bucket/path、访问权限和凭据。",
        },
        "manual_download": {
            "tool_available": command_status["curl"]["available"],
            "credential_hint_present": False,
            "selected": False,
            "blocking": "需要用户给出可由 RoboChallenge 评测端访问的下载 URL。",
        },
    }
    passed = bool(export_status.get("local_export_ready") and export_status.get("tar_stream_smoke", {}).get("passed"))
    return {
        "kind": "checkpoint_upload_channels_audit",
        "passed": passed,
        "uploads_performed": False,
        "plaintext_credentials_read": False,
        "export_status_path": str(EXPORT_STATUS.relative_to(ROOT)),
        "local_tar_ready": local_tar_ready,
        "archive_path": str(archive_path.relative_to(ROOT)),
        "archive_exists": archive_path.exists(),
        "archive_git_ignored": git_check_ignore(archive_path)["ignored"],
        "sha256_path": str(sha_path.relative_to(ROOT)),
        "sha256_exists": sha_path.exists(),
        "disk": disk_status(RUNS_DIR),
        "recommended_local_archive": local_archive,
        "commands": command_status,
        "auth_probes": auth_status,
        "channels": channels,
        "blocking": [
            "需要用户选择上传通道和存储位置。",
            "需要用户授权相应存储凭据；本审计只检查是否存在凭据迹象，不读取明文。",
            "需要生成真实 checkpoint link 后回填 RoboChallenge 网站。",
            "真实提交仍需要 ROBOCHALLENGE_USER_TOKEN 和 ROBOCHALLENGE_SUBMISSION_ID。",
        ],
    }


def write_report(status: dict[str, Any], path: Path) -> None:
    lines = [
        "# Checkpoint 上传通道审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 是否执行上传：`{status['uploads_performed']}`。",
        f"- 是否读取明文凭据：`{status['plaintext_credentials_read']}`。",
        f"- 本地 tar 前置条件：`{status['local_tar_ready']}`。",
        f"- tar 文件已存在：`{status['archive_exists']}`；Git 忽略：`{status['archive_git_ignored']}`。",
        f"- runs 目录剩余空间：`{status['disk']['free_gb']}` GB。",
        "",
        "## 本地命令可用性",
        "",
    ]
    for name, item in status["commands"].items():
        lines.append(f"- `{name}`：available=`{item['available']}`，version=`{item.get('version', '')}`。")
    lines.extend(["", "## 凭据迹象", ""])
    for name, item in status["auth_probes"].items():
        env_count = sum(1 for present in item["env_present"].values() if present)
        file_count = sum(1 for present in item["config_file_present"].values() if present)
        lines.append(f"- `{name}`：env_present_count=`{env_count}`，config_file_present_count=`{file_count}`。")
    lines.extend(["", "## 候选上传通道", ""])
    for name, item in status["channels"].items():
        lines.append(
            f"- `{name}`：tool_available=`{item['tool_available']}`，credential_hint_present=`{item['credential_hint_present']}`，selected=`{item['selected']}`。"
        )
        lines.append(f"  - 阻塞：{item['blocking']}")
    lines.extend(["", "## 建议下一步", ""])
    archive = status["recommended_local_archive"]
    if archive:
        lines.extend(
            [
                "用户确认上传通道后，在 Linux 仓库根目录执行本地打包命令：",
                "",
                "```bash",
                archive.get("create_command", ""),
                archive.get("hash_command", ""),
                "```",
            ]
        )
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
