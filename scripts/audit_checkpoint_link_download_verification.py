#!/usr/bin/env python3
"""Audit checkpoint-link download verification without leaking link values."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
DEFAULT_STATUS = RUNS_DIR / "checkpoint_link_download_verification.json"
DEFAULT_REPORT = REPORTS_DIR / "checkpoint_link_download_verification.md"
LINK_INTAKE_STATUS = RUNS_DIR / "checkpoint_link_intake.json"
SPLIT_PLAN_STATUS = RUNS_DIR / "checkpoint_split_plan.json"

LINK_KEYS = ["ROBOCHALLENGE_CHECKPOINT_LINK", "ROBOCHALLENGE_LORA_CHECKPOINT_LINK"]
PLACEHOLDER_MARKERS = [
    "<",
    ">",
    "真实",
    "example",
    "replace_me",
    "placeholder",
    "checkpoint link",
    "todo",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计 checkpoint link 下载校验协议，不打印链接明文。")
    parser.add_argument("--verify-download", action="store_true", help="真实联网校验当前 checkpoint link。默认不联网。")
    parser.add_argument("--range-bytes", type=int, default=1024 * 1024, help="Range smoke 读取字节数，默认 1MiB。")
    parser.add_argument("--timeout-seconds", type=int, default=30, help="curl 超时时间。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文审计报告输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def classify_link(value: str) -> dict[str, Any]:
    parsed = urlparse(value) if value else None
    lowered = value.lower()
    placeholder_like = any(marker.lower() in lowered for marker in PLACEHOLDER_MARKERS)
    looks_like_https_url = bool(parsed and parsed.scheme == "https" and parsed.netloc)
    has_archive_hint = lowered.endswith((".tar", ".tar.gz", ".tgz", ".zip")) or "checkpoint" in lowered
    accepted_shape = bool(value and looks_like_https_url and has_archive_hint and not placeholder_like)
    return {
        "present": bool(value),
        "length": len(value) if value else 0,
        "looks_like_https_url": looks_like_https_url,
        "has_archive_hint": has_archive_hint,
        "placeholder_like": placeholder_like,
        "accepted_shape": accepted_shape,
    }


def current_link_status() -> dict[str, Any]:
    raw_values = {key: os.environ.get(key, "") for key in LINK_KEYS}
    links = {key: classify_link(value) for key, value in raw_values.items()}
    accepted = [key for key, item in links.items() if item["accepted_shape"]]
    selected_key = accepted[0] if accepted else ""
    return {
        "links": links,
        "accepted_link_keys": accepted,
        "selected_link_key": selected_key,
        "selected_link_value": raw_values.get(selected_key, ""),
        "link_shape_ready": bool(selected_key),
    }


def command_available(name: str) -> dict[str, Any]:
    result = subprocess.run(
        [name, "--version"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    first_line = (result.stdout.strip() or result.stderr.strip()).splitlines()
    return {
        "available": result.returncode == 0,
        "version": first_line[0] if first_line else "",
    }


def sanitize(text: str, secret: str) -> str:
    if secret:
        text = text.replace(secret, "<redacted_checkpoint_link>")
    return text[-1200:]


def parse_content_length(headers: str) -> int:
    matches = re.findall(r"(?im)^content-length:\s*(\d+)\s*$", headers)
    return int(matches[-1]) if matches else 0


def run_curl_checks(link: str, range_bytes: int, timeout_seconds: int) -> dict[str, Any]:
    head_cmd = ["curl", "-L", "--fail", "--head", "--max-time", str(timeout_seconds), link]
    range_cmd = [
        "curl",
        "-L",
        "--fail",
        "--range",
        f"0-{range_bytes - 1}",
        "--output",
        "/dev/null",
        "--max-time",
        str(timeout_seconds),
        link,
    ]
    head = subprocess.run(head_cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    range_smoke = subprocess.run(range_cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    head_combined = sanitize(head.stdout + "\n" + head.stderr, link)
    range_combined = sanitize(range_smoke.stdout + "\n" + range_smoke.stderr, link)
    leaked = bool(link and (link in head_combined or link in range_combined))
    content_length = parse_content_length(head.stdout)
    return {
        "head": {
            "returncode": head.returncode,
            "passed": head.returncode == 0,
            "content_length": content_length,
            "sanitized_output_tail": head_combined,
        },
        "range_smoke": {
            "returncode": range_smoke.returncode,
            "passed": range_smoke.returncode == 0,
            "requested_bytes": range_bytes,
            "sanitized_output_tail": range_combined,
        },
        "download_verified": head.returncode == 0 and range_smoke.returncode == 0,
        "link_value_printed": leaked,
    }


def build_status(args: argparse.Namespace) -> dict[str, Any]:
    link_intake = read_json(LINK_INTAKE_STATUS)
    split_plan = read_json(SPLIT_PLAN_STATUS)
    current = current_link_status()
    curl = command_available("curl")
    planned_commands = {
        "head": (
            "curl -L --fail --head --max-time "
            f"{args.timeout_seconds} [REDACTED_CHECKPOINT_LINK]"
        ),
        "range_smoke": (
            "curl -L --fail --range 0-"
            f"{args.range_bytes - 1} --output /dev/null --max-time {args.timeout_seconds} [REDACTED_CHECKPOINT_LINK]"
        ),
    }
    no_contact_mode = not args.verify_download
    checks = {
        "link_intake_passed": link_intake.get("passed") is True,
        "split_plan_passed": split_plan.get("passed") is True,
        "curl_available": curl["available"],
        "commands_redacted": "[REDACTED_CHECKPOINT_LINK]" in planned_commands["head"]
        and "[REDACTED_CHECKPOINT_LINK]" in planned_commands["range_smoke"],
        "commands_no_shell_redirection": ">" not in planned_commands["head"] + planned_commands["range_smoke"],
    }
    verification = {
        "attempted": False,
        "download_verified": False,
        "download_host_contacted": False,
        "link_value_printed": False,
        "head": {},
        "range_smoke": {},
    }
    blocking: list[str] = []
    if not current["link_shape_ready"]:
        blocking.append("缺少真实 checkpoint link；当前只能审计下载校验协议，不能联网验证。")
    if not args.verify_download:
        blocking.append("未请求 --verify-download；本轮不联网、不下载、不接触 checkpoint link host。")
    if args.verify_download and current["link_shape_ready"] and curl["available"]:
        verification.update(run_curl_checks(current["selected_link_value"], args.range_bytes, args.timeout_seconds))
        verification["attempted"] = True
        verification["download_host_contacted"] = True
        if not verification["download_verified"]:
            blocking.append("真实 checkpoint link 下载校验未通过；请检查链接权限、有效期和 Range 支持。")
    elif args.verify_download and not current["link_shape_ready"]:
        blocking.append("已请求联网校验，但没有形态合格的 checkpoint link。")
    elif args.verify_download and not curl["available"]:
        blocking.append("已请求联网校验，但当前环境没有 curl。")

    passed = all(checks.values()) and not verification["link_value_printed"]
    if args.verify_download:
        passed = passed and verification["download_verified"]
    else:
        passed = passed and not verification["attempted"] and not verification["download_host_contacted"]
    return {
        "kind": "checkpoint_link_download_verification",
        "passed": passed,
        "verify_download_requested": args.verify_download,
        "platform_contacted": False,
        "upload_performed": False,
        "credentials_read": False,
        "credentials_printed": False,
        "link_value_printed": verification["link_value_printed"],
        "current_env": {
            "links": current["links"],
            "accepted_link_keys": current["accepted_link_keys"],
            "selected_link_key": current["selected_link_key"],
            "link_shape_ready": current["link_shape_ready"],
        },
        "tooling": {"curl": curl},
        "planned_commands": planned_commands,
        "checks": checks,
        "verification": verification,
        "expected_archive_gib": split_plan.get("expected_archive_gib"),
        "expected_part_count": split_plan.get("expected_part_count"),
        "blocking": blocking,
    }


def write_report(status: dict[str, Any], path: Path) -> None:
    current = status["current_env"]
    verification = status["verification"]
    lines = [
        "# Checkpoint Link 下载校验审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 是否请求联网校验：`{status['verify_download_requested']}`。",
        f"- 是否接触下载 host：`{verification['download_host_contacted']}`。",
        f"- 下载是否已验证：`{verification['download_verified']}`。",
        f"- 是否连接 RoboChallenge 平台：`{status['platform_contacted']}`。",
        f"- 是否上传：`{status['upload_performed']}`。",
        f"- 是否读取凭据：`{status['credentials_read']}`。",
        f"- 是否打印链接明文：`{status['link_value_printed']}`。",
        f"- curl 可用：`{status['tooling']['curl']['available']}`。",
        "",
        "## 当前链接状态",
        "",
    ]
    for key, item in current["links"].items():
        lines.append(
            f"- `{key}`：present=`{item['present']}`，length=`{item['length']}`，"
            f"https=`{item['looks_like_https_url']}`，archive_hint=`{item['has_archive_hint']}`，"
            f"placeholder_like=`{item['placeholder_like']}`，accepted_shape=`{item['accepted_shape']}`。"
        )
    lines.extend(["", "## 授权后校验命令", ""])
    for key, value in status["planned_commands"].items():
        lines.append(f"- `{key}`：`{value}`。")
    lines.extend(
        [
            "",
            "## 输入证据",
            "",
            f"- link intake passed：`{status['checks']['link_intake_passed']}`。",
            f"- split plan passed：`{status['checks']['split_plan_passed']}`。",
            f"- expected archive GiB：`{status['expected_archive_gib']}`。",
            f"- expected part count：`{status['expected_part_count']}`。",
            "",
            "## Blocking",
            "",
        ]
    )
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
