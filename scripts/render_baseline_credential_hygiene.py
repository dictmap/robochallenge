#!/usr/bin/env python3
"""Render a no-contact credential hygiene packet for the baseline route."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = ROOT / "runs"
LOCAL_ENV_REL = "submission/robochallenge_env.local.sh"
DEFAULT_STATUS = RUNS_DIR / "baseline_credential_hygiene.json"
DEFAULT_REPORT = REPORTS_DIR / "baseline_credential_hygiene.md"
BASELINE_DRY_RUN_GATE_COMMAND = (
    "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_ready_real_submission_template.sh"
)
BASELINE_AUTHORIZED_PREFLIGHT_COMMAND = (
    "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_authorized_preflight_template.sh"
)
BASELINE_REQUIRED_IDS = {
    "SUBMISSION_TARGET_CONFIRMATION",
    "ROBOCHALLENGE_USER_TOKEN",
    "ROBOCHALLENGE_SUBMISSION_ID",
    "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline",
    "ROBOCHALLENGE_REAL_RUN_CONFIRM",
}
LORA_ONLY_IDS = {"CHECKPOINT_ARCHIVE_AUTHORIZATION", "ROBOCHALLENGE_CHECKPOINT_LINK"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成 baseline 凭据卫生证据包；不读取 local env 内容、不联网、不上传。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文报告输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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
    result = run_git(["ls-files", "--error-unmatch", rel])
    return result.returncode == 0


def ids(items: list[dict[str, Any]] | list[str]) -> set[str]:
    output: set[str] = set()
    for item in items:
        value = item.get("id") if isinstance(item, dict) else item
        if value:
            output.add(str(value))
    return output


def build_status() -> dict[str, Any]:
    env_template = read_json(RUNS_DIR / "submission_env_template_audit.json")
    plaintext_scan = read_json(RUNS_DIR / "plaintext_secret_scan.json")
    authorized_preflight = read_json(RUNS_DIR / "authorized_preflight_template_audit.json")
    dry_run_gate = read_json(RUNS_DIR / "baseline_dry_run_gate.json")
    action_packet = read_json(RUNS_DIR / "next_user_action_packet.json")
    route_aware = read_json(RUNS_DIR / "route_aware_submission_blockers.json")
    local_env_path = ROOT / LOCAL_ENV_REL
    baseline_ids = ids(action_packet.get("required_user_decisions", [])) or ids(
        route_aware.get("baseline_current_blocking", [])
    )
    lora_ids = ids(route_aware.get("lora_web_current_blocking", []))
    local_env_ignored = git_check_ignore(LOCAL_ENV_REL)
    local_env_tracked = git_is_tracked(LOCAL_ENV_REL)

    placeholder_values = env_template.get("placeholder_values", {})
    local_secret_paths = env_template.get("local_secret_paths", {})
    evidence = {
        "env_template_passed": env_template.get("passed") is True,
        "template_uses_placeholders_for_secrets": bool(placeholder_values)
        and all(
            placeholder_values.get(key) is True
            for key in [
                "ROBOCHALLENGE_USER_TOKEN",
                "ROBOCHALLENGE_SUBMISSION_ID",
                "ROBOCHALLENGE_LORA_CHECKPOINT_LINK",
                "ROBOCHALLENGE_CHECKPOINT_LINK",
            ]
        ),
        "template_default_variant_baseline": placeholder_values.get("ROBOCHALLENGE_SUBMISSION_VARIANT") is True,
        "local_env_gitignored_by_template_audit": local_secret_paths.get(LOCAL_ENV_REL, {}).get("ignored") is True,
        "local_env_gitignored_now": local_env_ignored,
        "local_env_not_tracked": local_env_tracked is False,
        "plaintext_scan_passed": plaintext_scan.get("passed") is True,
        "plaintext_scan_hit_count_zero": plaintext_scan.get("hit_count") == 0,
        "authorized_preflight_passed": authorized_preflight.get("passed") is True,
        "authorized_preflight_no_credentials_smoke": authorized_preflight.get("no_credentials_smoke", {}).get(
            "passed"
        )
        is True,
        "baseline_dry_run_gate_passed": dry_run_gate.get("passed") is True,
        "baseline_dry_run_gate_command_exact": dry_run_gate.get("dry_run_gate_command")
        == BASELINE_DRY_RUN_GATE_COMMAND,
        "baseline_dry_run_stops_before_real_runner": dry_run_gate.get(
            "stops_before_real_runner_without_confirmation"
        )
        is True,
        "baseline_required_ids_complete": BASELINE_REQUIRED_IDS.issubset(baseline_ids),
        "baseline_required_ids_do_not_include_lora_only": not bool(baseline_ids & LORA_ONLY_IDS),
        "lora_branch_keeps_upload_and_link_ids": LORA_ONLY_IDS.issubset(lora_ids),
    }
    leak_flags = {
        "credentials_printed": any(
            bool(item.get("credentials_printed"))
            for item in [env_template, plaintext_scan, authorized_preflight, dry_run_gate, action_packet, route_aware]
        ),
        "link_values_printed": any(
            bool(item.get("link_values_printed"))
            for item in [env_template, plaintext_scan, authorized_preflight, dry_run_gate, action_packet, route_aware]
        ),
        "secret_values_printed": any(
            bool(item.get("secret_values_printed"))
            for item in [env_template, plaintext_scan, authorized_preflight, dry_run_gate, action_packet, route_aware]
        ),
    }
    contact_flags = {
        "platform_contacted": any(
            bool(item.get("platform_contacted"))
            for item in [env_template, plaintext_scan, authorized_preflight, dry_run_gate, action_packet, route_aware]
        ),
        "uploads_performed": any(
            bool(item.get("uploads_performed") or item.get("upload_performed"))
            for item in [env_template, plaintext_scan, authorized_preflight, dry_run_gate, action_packet, route_aware]
        ),
        "download_host_contacted": False,
    }
    passed = bool(all(evidence.values()) and not any(leak_flags.values()) and not any(contact_flags.values()))
    blocking = []
    if passed:
        blocking.append(
            "baseline 凭据卫生边界已固化；目标确认、真实 token、submission id 和 variant=baseline "
            "只应写入 Git 忽略的 local env 或当前 shell，然后先跑只读预检和 baseline dry-run gate。"
        )
    else:
        for key, ok in evidence.items():
            if not ok:
                blocking.append(f"baseline 凭据卫生证据未通过 `{key}`。")
        if any(leak_flags.values()):
            blocking.append("输入审计显示存在凭据或链接明文泄露风险。")
        if any(contact_flags.values()):
            blocking.append("输入审计显示曾连接平台、上传或接触下载 host。")

    return {
        "kind": "baseline_credential_hygiene",
        "passed": passed,
        "recommended_route": "baseline_official_aloha",
        "recommended_local_env": LOCAL_ENV_REL,
        "local_env_exists_without_reading": local_env_path.exists(),
        "local_env_content_read": False,
        "local_env_gitignored": local_env_ignored,
        "local_env_tracked": local_env_tracked,
        "authorized_preflight_command": BASELINE_AUTHORIZED_PREFLIGHT_COMMAND,
        "dry_run_gate_command": BASELINE_DRY_RUN_GATE_COMMAND,
        "requires_checkpoint_upload": False,
        "requires_checkpoint_link": False,
        "baseline_required_ids": sorted(BASELINE_REQUIRED_IDS),
        "lora_only_ids": sorted(LORA_ONLY_IDS),
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
        "# Baseline 凭据卫生证据包",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 推荐路线：`{status['recommended_route']}`。",
        f"- 建议本地凭据文件：`{status['recommended_local_env']}`。",
        f"- 本地凭据文件是否存在：`{status['local_env_exists_without_reading']}`。",
        f"- 是否读取本地凭据文件内容：`{status['local_env_content_read']}`。",
        f"- 本地凭据文件是否被 Git 忽略：`{status['local_env_gitignored']}`。",
        f"- 本地凭据文件是否被 Git 跟踪：`{status['local_env_tracked']}`。",
        f"- baseline 是否需要 checkpoint upload：`{status['requires_checkpoint_upload']}`。",
        f"- baseline 是否需要 checkpoint link：`{status['requires_checkpoint_link']}`。",
        "",
        "## 凭据到位后的安全顺序",
        "",
        f"1. 只读授权预检：`{status['authorized_preflight_command']}`",
        f"2. baseline dry-run gate：`{status['dry_run_gate_command']}`",
        "",
        "## 边界",
        "",
        "- 真实 token 和 submission id 只能写入 Git 忽略的 local env 或当前 shell。",
        "- 本证据包只检查路径和上游审计结果，不读取 local env 内容。",
        "- LoRA/web checkpoint 的归档、上传和 checkpoint link 仍保留在单独分支，不属于 baseline 前置条件。",
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
