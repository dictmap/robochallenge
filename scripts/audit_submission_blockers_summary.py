#!/usr/bin/env python3
"""Summarize current real-submission blockers without reading credentials."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = ROOT / "runs"
DEFAULT_STATUS = RUNS_DIR / "submission_blockers_summary.json"
DEFAULT_REPORT = REPORTS_DIR / "submission_blockers_summary.md"

REQUIRED_USER_INPUTS = [
    {
        "id": "ROBOCHALLENGE_USER_TOKEN",
        "label": "RoboChallenge user token",
        "source": "用户登录 RoboChallenge 后提供；只能放入本地 shell 或被 Git 忽略的 local env 文件。",
    },
    {
        "id": "ROBOCHALLENGE_SUBMISSION_ID",
        "label": "RoboChallenge submission id",
        "source": "用户在 RoboChallenge My Submission/Detail 页面确认；不能伪造。",
    },
    {
        "id": "CHECKPOINT_UPLOAD_AUTHORIZATION",
        "label": "checkpoint 上传授权",
        "source": "如果提交 LoRA 物化 checkpoint，用户需要确认是否生成 12GB+ tar 并选择上传通道。",
    },
    {
        "id": "ROBOCHALLENGE_CHECKPOINT_LINK",
        "label": "真实可访问 checkpoint link",
        "source": "由用户授权上传后得到；只做脱敏形态检查，默认不联网验证。",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="汇总真实提交前阻塞项；不读取凭据、不上传、不连接平台。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文报告输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = " ".join(str(item).split())
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def build_status() -> dict[str, Any]:
    preflight = read_json(RUNS_DIR / "submission_preflight_bundle.json")
    readiness = read_json(RUNS_DIR / "real_submission_readiness.json")
    link_intake = read_json(RUNS_DIR / "checkpoint_link_intake.json")
    link_download = read_json(RUNS_DIR / "checkpoint_link_download_verification.json")
    upload_channels = read_json(RUNS_DIR / "checkpoint_upload_channels_audit.json")
    env_template = read_json(RUNS_DIR / "submission_env_template_audit.json")
    notebook_structure = read_json(RUNS_DIR / "notebook_structure_audit.json")
    authorized_preflight = read_json(RUNS_DIR / "authorized_preflight_template_audit.json")
    artifact_manifest = read_json(RUNS_DIR / "submission_artifact_manifest.json")
    package = read_json(RUNS_DIR / "robochallenge_submission_package_audit.json")
    secret_scan = read_json(RUNS_DIR / "plaintext_secret_scan.json")

    blocking = unique(
        list(preflight.get("blocking", []))
        + list(readiness.get("blocking", []))
        + list(link_intake.get("current_env", {}).get("blocking", []))
        + list(link_download.get("blocking", []))
        + list(package.get("blocking", []))
    )
    local_ready = {
        "submission_package_ready": package.get("passed") is True,
        "artifact_manifest_ready": artifact_manifest.get("passed") is True,
        "env_template_ready": env_template.get("passed") is True,
        "notebook_structure_ready": notebook_structure.get("passed") is True,
        "authorized_preflight_template_ready": authorized_preflight.get("passed") is True,
        "upload_channels_audited": upload_channels.get("passed") is True,
        "preflight_bundle_ready": preflight.get("passed") is True,
        "secret_scan_clean": secret_scan.get("passed") is True and secret_scan.get("hit_count") == 0,
    }
    leak_flags = {
        "credentials_printed": bool(preflight.get("leak_flags", {}).get("credentials_printed"))
        or bool(readiness.get("credentials_printed")),
        "link_values_printed": bool(preflight.get("leak_flags", {}).get("link_values_printed"))
        or bool(link_intake.get("link_values_printed"))
        or bool(link_download.get("link_value_printed")),
        "secret_values_printed": bool(preflight.get("leak_flags", {}).get("secret_values_printed"))
        or bool(secret_scan.get("secret_values_printed")),
    }
    contact_flags = {
        "platform_contacted": bool(preflight.get("contact_flags", {}).get("platform_contacted"))
        or bool(readiness.get("platform_contacted")),
        "uploads_performed": bool(preflight.get("contact_flags", {}).get("uploads_performed"))
        or bool(upload_channels.get("uploads_performed")),
        "download_host_contacted": bool(preflight.get("contact_flags", {}).get("download_host_contacted"))
        or bool(link_download.get("verification", {}).get("download_host_contacted")),
    }
    current_state = {
        "go_no_go": preflight.get("go_no_go"),
        "ready_for_real_submission": readiness.get("ready_for_real_submission"),
        "web_form_ready": readiness.get("web_form_ready"),
        "link_shape_ready": link_intake.get("current_env", {}).get("link_shape_ready"),
        "download_verified": link_download.get("verification", {}).get("download_verified"),
    }
    passed = bool(
        preflight.get("passed")
        and readiness.get("passed")
        and preflight.get("go_no_go") == "blocked"
        and readiness.get("ready_for_real_submission") is False
        and len(blocking) >= 4
        and all(local_ready.values())
        and not any(leak_flags.values())
        and not any(contact_flags.values())
    )
    return {
        "kind": "submission_blockers_summary",
        "passed": passed,
        "platform_contacted": False,
        "uploads_performed": False,
        "credentials_read": False,
        "credentials_printed": False,
        "link_values_printed": False,
        "secret_values_printed": False,
        "current_state": current_state,
        "local_ready": local_ready,
        "required_user_inputs": REQUIRED_USER_INPUTS,
        "blocking": blocking,
        "blocking_count": len(blocking),
        "leak_flags": leak_flags,
        "contact_flags": contact_flags,
        "next_command_after_user_inputs": "python3 scripts/audit_real_submission_readiness.py",
    }


def write_report(status: dict[str, Any], path: Path) -> None:
    lines = [
        "# 真实提交阻塞项摘要",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- go/no-go：`{status['current_state']['go_no_go']}`。",
        f"- 真实提交就绪：`{status['current_state']['ready_for_real_submission']}`。",
        f"- Web 表单就绪：`{status['current_state']['web_form_ready']}`。",
        f"- checkpoint link 形态就绪：`{status['current_state']['link_shape_ready']}`。",
        f"- 下载已验证：`{status['current_state']['download_verified']}`。",
        f"- 阻塞项数量：`{status['blocking_count']}`。",
        f"- 是否连接平台：`{status['platform_contacted']}`。",
        f"- 是否上传：`{status['uploads_performed']}`。",
        f"- 是否读取真实凭据：`{status['credentials_read']}`。",
        "",
        "## 本地材料状态",
        "",
    ]
    for key, value in status["local_ready"].items():
        lines.append(f"- `{key}`：`{value}`。")
    lines.extend(["", "## 需要用户提供或授权", ""])
    for item in status["required_user_inputs"]:
        lines.append(f"- `{item['id']}`：{item['source']}")
    lines.extend(["", "## 当前阻塞项", ""])
    for item in status["blocking"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## 拿到用户输入后的下一步",
            "",
            f"- 先运行 `{status['next_command_after_user_inputs']}`。",
            "- 如果 readiness 仍为 false，停止，不启动真实 runner。",
            "- 如果需要联网验证 checkpoint link，必须由用户显式授权后再运行 `python3 scripts/audit_checkpoint_link_download_verification.py --verify-download`。",
        ]
    )
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
