#!/usr/bin/env python3
"""Audit checkpoint-link intake without printing link values or contacting hosts."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = ROOT / "runs"
DEFAULT_STATUS = RUNS_DIR / "checkpoint_link_intake.json"
DEFAULT_REPORT = REPORTS_DIR / "checkpoint_link_intake.md"

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
SYNTHETIC_LINK = "https://download.shape-ok.invalid/robochallenge/openpi_lora_checkpoint.tar"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="离线审计 checkpoint link 回填形态，不打印链接明文。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文审计报告输出路径。")
    parser.add_argument("--scenario-only", action="store_true", help="只输出当前环境判定，供场景 smoke 调用。")
    return parser.parse_args()


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


def current_env_status() -> dict[str, Any]:
    links = {key: classify_link(os.environ.get(key, "")) for key in LINK_KEYS}
    accepted_keys = [key for key, item in links.items() if item["accepted_shape"]]
    any_present = any(item["present"] for item in links.values())
    link_shape_ready = bool(accepted_keys)
    blocking = []
    if not any_present:
        blocking.append("缺少 checkpoint link；请设置 ROBOCHALLENGE_CHECKPOINT_LINK 或 ROBOCHALLENGE_LORA_CHECKPOINT_LINK。")
    elif not link_shape_ready:
        blocking.append("checkpoint link 形态未通过；请使用真实 HTTPS 下载链接，且不要保留占位符文本。")
    else:
        blocking.append("checkpoint link 形态已通过；本审计未联网验证链接是否可下载。")
    return {
        "links": links,
        "accepted_link_keys": accepted_keys,
        "link_shape_ready": link_shape_ready,
        "download_verified": False,
        "blocking": blocking,
    }


def run_current_status_with_env(env_updates: dict[str, str]) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    for key in LINK_KEYS:
        env.pop(key, None)
    env.update(env_updates)
    with tempfile.TemporaryDirectory(prefix="robochallenge_link_intake_") as tmp:
        tmp_dir = Path(tmp)
        status_path = tmp_dir / "status.json"
        report_path = tmp_dir / "report.md"
        result = subprocess.run(
            [
                sys.executable,
                "scripts/audit_checkpoint_link_intake.py",
                "--scenario-only",
                "--status-path",
                str(status_path),
                "--report-path",
                str(report_path),
            ],
            cwd=ROOT,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.exists() else {}
        combined_output = "\n".join(
            [
                stdout,
                stderr,
                status_path.read_text(encoding="utf-8") if status_path.exists() else "",
                report_path.read_text(encoding="utf-8") if report_path.exists() else "",
            ]
        )
        leaked = [key for key, value in env_updates.items() if value and value in combined_output]
        return {
            "returncode": result.returncode,
            "link_shape_ready": status.get("current_env", {}).get("link_shape_ready"),
            "download_verified": status.get("current_env", {}).get("download_verified"),
            "platform_contacted": status.get("platform_contacted"),
            "credentials_printed": status.get("credentials_printed"),
            "link_values_printed": bool(leaked),
            "leaked_value_keys": leaked,
            "accepted_link_keys": status.get("current_env", {}).get("accepted_link_keys", []),
        }


def build_status(scenario_only: bool) -> dict[str, Any]:
    current = current_env_status()
    status: dict[str, Any] = {
        "kind": "checkpoint_link_intake",
        "passed": True,
        "platform_contacted": False,
        "uploads_performed": False,
        "archive_created": False,
        "credentials_printed": False,
        "link_values_printed": False,
        "synthetic_values_recorded": False,
        "current_env": current,
        "blocking": [
            "本审计只检查 checkpoint link 回填形态，不联网验证下载有效性。",
            "真实提交仍需要用户提供 token、submission id 和真实可访问 checkpoint link。",
        ],
    }
    if scenario_only:
        return status

    missing = run_current_status_with_env({})
    placeholder = run_current_status_with_env({"ROBOCHALLENGE_LORA_CHECKPOINT_LINK": "<真实 checkpoint link>"})
    synthetic = run_current_status_with_env({"ROBOCHALLENGE_LORA_CHECKPOINT_LINK": SYNTHETIC_LINK})

    scenarios = {
        "missing_link_expected_blocked": missing,
        "placeholder_link_expected_rejected": placeholder,
        "synthetic_https_shape_expected_accepted": synthetic,
    }
    expectations = {
        "missing_link_expected_blocked": all(
            [
                missing["returncode"] == 0,
                missing["link_shape_ready"] is False,
                missing["download_verified"] is False,
                missing["platform_contacted"] is False,
                missing["credentials_printed"] is False,
                missing["link_values_printed"] is False,
            ]
        ),
        "placeholder_link_expected_rejected": all(
            [
                placeholder["returncode"] == 0,
                placeholder["link_shape_ready"] is False,
                placeholder["download_verified"] is False,
                placeholder["platform_contacted"] is False,
                placeholder["credentials_printed"] is False,
                placeholder["link_values_printed"] is False,
            ]
        ),
        "synthetic_https_shape_expected_accepted": all(
            [
                synthetic["returncode"] == 0,
                synthetic["link_shape_ready"] is True,
                synthetic["download_verified"] is False,
                synthetic["platform_contacted"] is False,
                synthetic["credentials_printed"] is False,
                synthetic["link_values_printed"] is False,
            ]
        ),
    }
    status["scenarios"] = scenarios
    status["expectations"] = expectations
    status["passed"] = all(expectations.values()) and current["link_shape_ready"] is False
    return status


def write_report(status: dict[str, Any], path: Path) -> None:
    current = status["current_env"]
    lines = [
        "# Checkpoint Link 回填审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 当前环境 link 形态就绪：`{current['link_shape_ready']}`。",
        f"- 是否联网验证下载：`{current['download_verified']}`。",
        f"- 是否连接平台：`{status['platform_contacted']}`。",
        f"- 是否上传：`{status['uploads_performed']}`。",
        f"- 是否打印凭据或链接明文：`{status['credentials_printed'] or status['link_values_printed']}`。",
        "",
        "## 当前环境变量形态",
        "",
    ]
    for key, item in current["links"].items():
        lines.append(
            f"- `{key}`：present=`{item['present']}`，length=`{item['length']}`，"
            f"https=`{item['looks_like_https_url']}`，archive_hint=`{item['has_archive_hint']}`，"
            f"placeholder_like=`{item['placeholder_like']}`，accepted_shape=`{item['accepted_shape']}`。"
        )
    if "scenarios" in status:
        lines.extend(["", "## 场景 Smoke", ""])
        for name, item in status["scenarios"].items():
            lines.extend(
                [
                    f"### {name}",
                    "",
                    f"- returncode：`{item['returncode']}`。",
                    f"- link_shape_ready：`{item['link_shape_ready']}`。",
                    f"- download_verified：`{item['download_verified']}`。",
                    f"- platform_contacted：`{item['platform_contacted']}`。",
                    f"- credentials_printed：`{item['credentials_printed']}`。",
                    f"- link_values_printed：`{item['link_values_printed']}`。",
                    "",
                ]
            )
    lines.extend(["## Blocking", ""])
    for item in current["blocking"]:
        lines.append(f"- {item}")
    for item in status["blocking"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args()
    status = build_status(args.scenario_only)
    args.status_path.parent.mkdir(parents=True, exist_ok=True)
    args.status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(status, args.report_path)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
