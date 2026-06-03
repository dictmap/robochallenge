#!/usr/bin/env python3
"""Render the shortest no-contact quickstart for the official ALOHA baseline route."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = ROOT / "runs"
DEFAULT_STATUS = RUNS_DIR / "baseline_submission_quickstart.json"
DEFAULT_REPORT = REPORTS_DIR / "baseline_submission_quickstart.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成官方 ALOHA baseline 最短提交路径；不读取凭据、不联网、不上传。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文报告输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def find_route(route_packet: dict[str, Any], route_id: str) -> dict[str, Any]:
    for item in route_packet.get("routes", []):
        if item.get("id") == route_id:
            return item
    return {}


def command(step: int, name: str, shell: str, guard: str) -> dict[str, Any]:
    return {"step": step, "name": name, "command": shell, "guard": guard}


def build_status() -> dict[str, Any]:
    route_packet = read_json(RUNS_DIR / "submission_variant_route_packet.json")
    ready_runner = read_json(RUNS_DIR / "ready_real_runner_template_audit.json")
    package = read_json(RUNS_DIR / "robochallenge_submission_package_audit.json")
    readiness = read_json(RUNS_DIR / "real_submission_readiness.json")
    secret_scan = read_json(RUNS_DIR / "plaintext_secret_scan.json")
    jupyter_input = read_json(RUNS_DIR / "jupyter_input_template_audit.json")
    target_confirmation = read_json(RUNS_DIR / "submission_target_confirmation_packet.json")
    baseline_route = find_route(route_packet, "baseline_official_aloha")
    synthetic = ready_runner.get("synthetic_no_confirm_smoke", {})
    target_confirmation_value = target_confirmation.get(
        "recommended_confirmation_value", "CONFIRM_TABLE30V2_ALOHA_BASELINE"
    )

    required_user_inputs = [
        {
            "id": "SUBMISSION_TARGET_CONFIRMATION",
            "detail": "确认提交对象是 Table30v2 ALOHA baseline，不是原始 Table30，也不是 LoRA 网页 checkpoint 路线。",
        },
        {
            "id": "ROBOCHALLENGE_USER_TOKEN",
            "detail": "从 RoboChallenge 页面获得，只写入本地 shell 或被 Git 忽略的 local env。",
        },
        {
            "id": "ROBOCHALLENGE_SUBMISSION_ID",
            "detail": "从 RoboChallenge 提交页面获得，不能伪造。",
        },
        {
            "id": "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline",
            "detail": "当前 wrapper 已默认 baseline；显式设置可避免误走 LoRA。",
        },
        {
            "id": "ROBOCHALLENGE_REAL_RUN_CONFIRM",
            "detail": "只有用户确认启动真实 runner 后，才设置 RUN_REAL_ROBOCHALLENGE_SUBMISSION。",
        },
    ]
    commands = [
        command(
            1,
            "写入本地 env",
            (
                "Notebook 第 44 节：RUN_SAFE_LOCAL_ENV_INPUT_TEMPLATE=True；"
                f"确认值填 {target_confirmation_value}；variant 填 baseline。"
            ),
            "只写 submission/robochallenge_env.local.sh；不把真实值写入 Notebook 源码或 tracked 文件。",
        ),
        command(
            2,
            "授权前只读预检",
            "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_authorized_preflight_template.sh",
            "只读检查；ready=false 时停止。",
        ),
        command(
            3,
            "baseline wrapper dry-run gate",
            "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_ready_real_submission_template.sh",
            "未设置真实确认短语时，最多跑 baseline dry-run，然后停在真实 runner 前。",
        ),
        command(
            4,
            "真实 runner 强确认",
            (
                "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline "
                "ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION "
                "bash submission/run_ready_real_submission_template.sh"
            ),
            "只有用户明确授权真实提交时运行；该命令会启动 demo.py 并连接 RoboChallenge。",
        ),
    ]

    evidence = {
        "route_packet_passed": route_packet.get("passed") is True,
        "baseline_is_recommended_default": route_packet.get("recommended_default") == "baseline_official_aloha",
        "baseline_route_ready_without_credentials": baseline_route.get("local_runner_ready_without_credentials")
        is True,
        "baseline_checkpoint_ready": baseline_route.get("local_checkpoint_ready") is True,
        "baseline_does_not_need_upload": baseline_route.get("requires_checkpoint_upload") is False,
        "baseline_does_not_need_checkpoint_link": baseline_route.get("requires_checkpoint_link_for_local_runner")
        is False,
        "ready_runner_template_passed": ready_runner.get("passed") is True,
        "ready_runner_default_baseline": ready_runner.get("default_variant") == "baseline",
        "target_confirmation_packet_passed": target_confirmation.get("passed") is True,
        "target_confirmation_value_exact": target_confirmation_value == "CONFIRM_TABLE30V2_ALOHA_BASELINE",
        "jupyter_input_requires_manual_target_confirmation": jupyter_input.get(
            "target_confirmation_manual_input_required"
        )
        is True,
        "jupyter_input_requires_exact_target_confirmation": jupyter_input.get(
            "target_confirmation_exact_match_required"
        )
        is True,
        "synthetic_baseline_no_confirm_dry_run": synthetic.get("passed") is True
        and synthetic.get("variant") == "baseline"
        and synthetic.get("dry_run_called") is True
        and synthetic.get("missing_confirmation") is True
        and synthetic.get("real_runner_started") is False,
        "package_audit_passed": package.get("passed") is True,
        "readiness_gate_passed": readiness.get("passed") is True,
        "secret_scan_clean": secret_scan.get("passed") is True and secret_scan.get("hit_count") == 0,
    }
    leak_flags = {
        "credentials_printed": bool(route_packet.get("credentials_printed"))
        or bool(ready_runner.get("credentials_printed"))
        or bool(readiness.get("credentials_printed")),
        "link_values_printed": bool(route_packet.get("link_values_printed")) or bool(ready_runner.get("link_values_printed")),
        "secret_values_printed": bool(route_packet.get("secret_values_printed"))
        or bool(ready_runner.get("secret_values_printed"))
        or bool(secret_scan.get("secret_values_printed")),
    }
    contact_flags = {
        "platform_contacted": bool(route_packet.get("platform_contacted"))
        or bool(ready_runner.get("platform_contacted"))
        or bool(readiness.get("platform_contacted")),
        "uploads_performed": bool(route_packet.get("uploads_performed")) or bool(ready_runner.get("uploads_performed")),
        "download_host_contacted": False,
    }
    passed = bool(all(evidence.values()) and not any(leak_flags.values()) and not any(contact_flags.values()))
    blocking = []
    if not passed:
        for name, ok in evidence.items():
            if not ok:
                blocking.append(f"baseline 最短路径输入证据未通过 `{name}`。")
        if any(leak_flags.values()):
            blocking.append("输入审计显示存在凭据或链接明文泄露风险。")
        if any(contact_flags.values()):
            blocking.append("输入审计显示曾连接平台、接触下载 host 或执行上传。")
    else:
        blocking.append(
            "baseline 最短路径已固化；真实提交仍等待用户目标确认、token、submission id、"
            "variant=baseline 和真实 runner 强确认。"
        )

    return {
        "kind": "baseline_submission_quickstart",
        "passed": passed,
        "recommended_route": "baseline_official_aloha",
        "target_confirmation_value": target_confirmation_value,
        "target_confirmation_manual_input_required": jupyter_input.get("target_confirmation_manual_input_required")
        is True,
        "target_confirmation_exact_match_required": jupyter_input.get("target_confirmation_exact_match_required")
        is True,
        "requires_checkpoint_upload": False,
        "requires_checkpoint_link": False,
        "required_user_inputs": required_user_inputs,
        "commands": commands,
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
        "# 官方 ALOHA baseline 最短提交路径",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 推荐路线：`{status['recommended_route']}`。",
        f"- 目标确认值：`{status['target_confirmation_value']}`。",
        f"- 是否要求手动输入目标确认：`{status['target_confirmation_manual_input_required']}`。",
        f"- 是否要求精确匹配目标确认：`{status['target_confirmation_exact_match_required']}`。",
        f"- 是否需要 checkpoint upload：`{status['requires_checkpoint_upload']}`。",
        f"- 是否需要 checkpoint link：`{status['requires_checkpoint_link']}`。",
        "",
        "## 用户需要补齐",
        "",
    ]
    for item in status["required_user_inputs"]:
        lines.append(f"- `{item['id']}`：{item['detail']}")
    lines.extend(["", "## 最短命令顺序", ""])
    for item in status["commands"]:
        lines.append(f"{item['step']}. {item['name']}：`{item['command']}`")
        lines.append(f"   - 边界：{item['guard']}")
    lines.extend(["", "## 只读边界", ""])
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
