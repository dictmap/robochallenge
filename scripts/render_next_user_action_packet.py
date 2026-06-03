#!/usr/bin/env python3
"""Render the next user-action packet without reading credentials."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = ROOT / "runs"
DEFAULT_STATUS = RUNS_DIR / "next_user_action_packet.json"
DEFAULT_REPORT = REPORTS_DIR / "next_user_action_packet.md"

EXPECTED_DECISIONS = [
    "SUBMISSION_TARGET_CONFIRMATION",
    "ROBOCHALLENGE_USER_TOKEN",
    "ROBOCHALLENGE_SUBMISSION_ID",
    "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline",
    "ROBOCHALLENGE_REAL_RUN_CONFIRM",
]

BASELINE_REQUIRED_IDS = [
    "SUBMISSION_TARGET_CONFIRMATION",
    "ROBOCHALLENGE_USER_TOKEN",
    "ROBOCHALLENGE_SUBMISSION_ID",
    "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline",
    "ROBOCHALLENGE_REAL_RUN_CONFIRM",
]

LORA_WEB_REQUIRED_IDS = [
    "SUBMISSION_TARGET_CONFIRMATION",
    "ROBOCHALLENGE_USER_TOKEN",
    "ROBOCHALLENGE_SUBMISSION_ID",
    "ROBOCHALLENGE_SUBMISSION_VARIANT=lora",
    "CHECKPOINT_ARCHIVE_AUTHORIZATION",
    "ROBOCHALLENGE_CHECKPOINT_LINK",
    "ROBOCHALLENGE_REAL_RUN_CONFIRM",
]

NOTEBOOK_PATH = "notebooks/robochallenge_pi05_submit_cn.ipynb"
LOCAL_ENV_PATH = "submission/robochallenge_env.local.sh"
EXPECTED_TARGET_CONFIRMATION_VALUE = "CONFIRM_TABLE30V2_ALOHA_BASELINE"
EXPECTED_TARGET = {
    "benchmark": "Table30v2",
    "robot_type": "aloha",
    "task_name": "pack_the_toothbrush_holder",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成下一步用户动作包；不读取凭据、不联网、不上传。")
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


def route_by_id(packet: dict[str, Any], route_id: str) -> dict[str, Any]:
    for item in packet.get("routes", []):
        if item.get("id") == route_id:
            return item
    return {}


def build_status() -> dict[str, Any]:
    readiness = read_json(RUNS_DIR / "real_submission_readiness.json")
    blockers = read_json(RUNS_DIR / "submission_blockers_summary.json")
    authorized_execution = read_json(RUNS_DIR / "authorized_execution_checklist.json")
    jupyter_input = read_json(RUNS_DIR / "jupyter_input_template_audit.json")
    jupyter_authorized = read_json(RUNS_DIR / "jupyter_authorized_preflight_template_audit.json")
    env_template = read_json(RUNS_DIR / "submission_env_template_audit.json")
    handoff = read_json(RUNS_DIR / "submission_handoff_docs_audit.json")
    sequence = read_json(RUNS_DIR / "authorized_submission_sequence_audit.json")
    route_packet = read_json(RUNS_DIR / "submission_variant_route_packet.json")
    baseline_quickstart = read_json(RUNS_DIR / "baseline_submission_quickstart.json")
    target_confirmation = read_json(RUNS_DIR / "submission_target_confirmation_packet.json")
    secret_scan = read_json(RUNS_DIR / "plaintext_secret_scan.json")

    decisions = authorized_execution.get("required_user_decisions", [])
    decision_ids = [item.get("id") for item in decisions]
    lora_web_decisions = authorized_execution.get("lora_web_user_decisions", [])
    lora_web_decision_ids = authorized_execution.get("lora_web_user_decision_ids", [])
    authorized_steps = authorized_execution.get("authorized_steps", [])
    first_notebook_steps = [
        item
        for item in authorized_steps
        if str(item.get("command", "")).startswith("Notebook 第 44 节")
        or str(item.get("command", "")).startswith("Notebook 第 45 节")
    ]
    legacy_global_blocking = unique(
        list(readiness.get("blocking", []))
        + list(blockers.get("blocking", []))
        + list(authorized_execution.get("blocking", []))
    )
    baseline_route = route_by_id(route_packet, "baseline_official_aloha")
    lora_route = route_by_id(route_packet, "lora_materialized")
    baseline_current_blocking = unique(
        list(baseline_route.get("current_blocking", []))
        or [item.get("id", "") for item in baseline_quickstart.get("required_user_inputs", [])]
        or BASELINE_REQUIRED_IDS
    )
    lora_web_current_blocking = unique(list(lora_route.get("current_blocking", [])) or LORA_WEB_REQUIRED_IDS)
    target_confirmation_target = target_confirmation.get("target", {})
    first_user_confirmation_step = {
        "id": "SUBMISSION_TARGET_CONFIRMATION",
        "recommended_confirmation_value": target_confirmation.get("recommended_confirmation_value"),
        "target": dict(EXPECTED_TARGET),
        "source": "reports/submission_target_confirmation_packet.md",
        "user_action": "确认本次提交对象是 Table30v2 / aloha / pack_the_toothbrush_holder baseline。",
    }

    local_env_ignored = (
        env_template.get("local_secret_paths", {})
        .get(LOCAL_ENV_PATH, {})
        .get("ignored")
        is True
    )
    evidence = {
        "readiness_gate_passed": readiness.get("passed") is True,
        "ready_for_real_submission_false": readiness.get("ready_for_real_submission") is False,
        "web_form_ready_false": readiness.get("web_form_ready") is False,
        "authorized_execution_checklist_passed": authorized_execution.get("passed") is True,
        "authorized_execution_go_no_go_blocked": authorized_execution.get("go_no_go") == "blocked_by_user_inputs",
        "authorized_execution_recommends_baseline": authorized_execution.get("recommended_route")
        == "baseline_official_aloha",
        "all_expected_decisions_listed": set(EXPECTED_DECISIONS).issubset(set(decision_ids)),
        "baseline_decisions_have_no_checkpoint_link": "ROBOCHALLENGE_CHECKPOINT_LINK" not in set(decision_ids),
        "baseline_decisions_have_no_archive_authorization": "CHECKPOINT_ARCHIVE_AUTHORIZATION" not in set(decision_ids),
        "lora_web_expected_decisions_listed": set(LORA_WEB_REQUIRED_IDS).issubset(set(lora_web_decision_ids)),
        "jupyter_input_template_passed": jupyter_input.get("passed") is True,
        "jupyter_input_default_false": jupyter_input.get("run_flag_default_false") is True,
        "jupyter_authorized_preflight_template_passed": jupyter_authorized.get("passed") is True,
        "jupyter_authorized_preflight_execution_default_false": jupyter_authorized.get("execution_default_false")
        is True,
        "local_env_ignored": local_env_ignored,
        "handoff_docs_available": bool(handoff),
        "authorized_sequence_available": bool(sequence),
        "route_packet_passed": route_packet.get("passed") is True,
        "route_packet_recommends_baseline": route_packet.get("recommended_default") == "baseline_official_aloha",
        "baseline_quickstart_passed": baseline_quickstart.get("passed") is True,
        "baseline_quickstart_no_link": baseline_quickstart.get("requires_checkpoint_link") is False,
        "baseline_quickstart_no_upload": baseline_quickstart.get("requires_checkpoint_upload") is False,
        "target_confirmation_packet_passed": target_confirmation.get("passed") is True,
        "target_confirmation_value_exact": target_confirmation.get("recommended_confirmation_value")
        == EXPECTED_TARGET_CONFIRMATION_VALUE,
        "target_confirmation_not_user_confirmed": target_confirmation.get("target_user_confirmed") is False,
        "target_confirmation_does_not_confirm_for_user": target_confirmation.get("does_not_confirm_for_user")
        is True,
        "target_confirmation_target_exact": all(
            target_confirmation_target.get(key) == value for key, value in EXPECTED_TARGET.items()
        ),
        "baseline_blocking_has_no_checkpoint_link": "ROBOCHALLENGE_CHECKPOINT_LINK" not in baseline_current_blocking,
        "baseline_blocking_has_no_archive_authorization": "CHECKPOINT_ARCHIVE_AUTHORIZATION"
        not in baseline_current_blocking,
        "baseline_required_ids_complete": set(BASELINE_REQUIRED_IDS).issubset(set(baseline_current_blocking)),
        "lora_web_requires_checkpoint_link": "ROBOCHALLENGE_CHECKPOINT_LINK" in lora_web_current_blocking,
        "lora_web_requires_archive_authorization": "CHECKPOINT_ARCHIVE_AUTHORIZATION" in lora_web_current_blocking,
        "lora_web_required_ids_complete": set(LORA_WEB_REQUIRED_IDS).issubset(set(lora_web_current_blocking)),
        "secret_scan_clean": secret_scan.get("passed") is True and secret_scan.get("hit_count") == 0,
    }
    leak_flags = {
        "credentials_printed": any(
            bool(item.get("credentials_printed"))
            for item in [
                readiness,
                blockers,
                authorized_execution,
                jupyter_input,
                jupyter_authorized,
                env_template,
                handoff,
                sequence,
                route_packet,
                baseline_quickstart,
                target_confirmation,
                secret_scan,
            ]
        ),
        "link_values_printed": any(
            bool(item.get("link_values_printed"))
            for item in [
                blockers,
                authorized_execution,
                jupyter_input,
                jupyter_authorized,
                handoff,
                sequence,
                route_packet,
                baseline_quickstart,
                target_confirmation,
                secret_scan,
            ]
        ),
        "secret_values_printed": any(
            bool(item.get("secret_values_printed"))
            for item in [
                blockers,
                authorized_execution,
                jupyter_input,
                jupyter_authorized,
                env_template,
                handoff,
                sequence,
                route_packet,
                baseline_quickstart,
                target_confirmation,
                secret_scan,
            ]
        ),
    }
    contact_flags = {
        "platform_contacted": any(
            bool(item.get("platform_contacted"))
            for item in [
                readiness,
                blockers,
                authorized_execution,
                jupyter_input,
                jupyter_authorized,
                env_template,
                handoff,
                sequence,
                route_packet,
                baseline_quickstart,
                target_confirmation,
                secret_scan,
            ]
        ),
        "uploads_performed": any(
            bool(item.get("uploads_performed") or item.get("upload_performed"))
            for item in [
                readiness,
                blockers,
                authorized_execution,
                jupyter_input,
                jupyter_authorized,
                env_template,
                handoff,
                sequence,
                route_packet,
                baseline_quickstart,
                target_confirmation,
                secret_scan,
            ]
        ),
        "download_host_contacted": False,
    }
    passed = bool(
        all(evidence.values())
        and not any(leak_flags.values())
        and not any(contact_flags.values())
        and len(first_notebook_steps) >= 2
        and baseline_current_blocking
        and lora_web_current_blocking
    )
    blocking = []
    if not passed:
        for name, ok in evidence.items():
            if not ok:
                blocking.append(f"动作包输入证据未通过 `{name}`。")
        if any(leak_flags.values()):
            blocking.append("输入审计显示存在凭据或链接明文泄露风险。")
        if any(contact_flags.values()):
            blocking.append("输入审计显示曾连接平台、接触下载 host 或执行上传。")
        if len(first_notebook_steps) < 2:
            blocking.append("授权执行清单未同时列出 Notebook 第 44/45 节。")
        if not baseline_current_blocking:
            blocking.append("baseline 当前阻塞项为空，动作包无法说明最短路线需要用户补齐什么。")
        if not lora_web_current_blocking:
            blocking.append("LoRA/web 当前阻塞项为空，动作包无法说明 checkpoint 路线需要用户补齐什么。")
    else:
        blocking.append(
            "动作包已生成；baseline 仍等待用户 token、submission id 和真实 runner 强确认，"
            "LoRA/web checkpoint 路线额外等待授权上传和真实 checkpoint link。"
        )

    return {
        "kind": "next_user_action_packet",
        "passed": passed,
        "go_no_go": "blocked_by_user_inputs",
        "ready_for_real_submission": readiness.get("ready_for_real_submission"),
        "web_form_ready": readiness.get("web_form_ready"),
        "notebook_path": NOTEBOOK_PATH,
        "local_env_path": LOCAL_ENV_PATH,
        "local_env_ignored": local_env_ignored,
        "recommended_route": "baseline_official_aloha",
        "target_confirmation_value": target_confirmation.get("recommended_confirmation_value"),
        "target_user_confirmed": target_confirmation.get("target_user_confirmed"),
        "target_confirmation_target": dict(EXPECTED_TARGET),
        "first_user_confirmation_step": first_user_confirmation_step,
        "baseline_requires_checkpoint_link": False,
        "baseline_requires_checkpoint_upload": False,
        "baseline_current_blocking": baseline_current_blocking,
        "lora_web_requires_checkpoint_link": True,
        "lora_web_requires_checkpoint_upload": True,
        "lora_web_current_blocking": lora_web_current_blocking,
        "legacy_global_blocking": legacy_global_blocking,
        "required_user_decisions": decisions,
        "required_decision_ids": decision_ids,
        "lora_web_user_decisions": lora_web_decisions,
        "lora_web_decision_ids": lora_web_decision_ids,
        "first_notebook_steps": first_notebook_steps,
        "current_blocking": baseline_current_blocking,
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
        "# 下一步用户动作包",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- go/no-go：`{status['go_no_go']}`。",
        f"- 真实提交就绪：`{status['ready_for_real_submission']}`。",
        f"- Web 表单就绪：`{status['web_form_ready']}`。",
        f"- Notebook：`{status['notebook_path']}`。",
        f"- 本地 env：`{status['local_env_path']}`，Git 忽略：`{status['local_env_ignored']}`。",
        f"- 推荐路线：`{status['recommended_route']}`。",
        f"- baseline 是否需要 checkpoint link：`{status['baseline_requires_checkpoint_link']}`。",
        f"- baseline 是否需要 checkpoint upload：`{status['baseline_requires_checkpoint_upload']}`。",
        f"- LoRA/web 是否需要 checkpoint link：`{status['lora_web_requires_checkpoint_link']}`。",
        f"- LoRA/web 是否需要 checkpoint upload：`{status['lora_web_requires_checkpoint_upload']}`。",
        f"- 推荐目标确认值：`{status['target_confirmation_value']}`。",
        f"- 是否已经替用户确认目标：`{status['target_user_confirmed']}`。",
        "",
        "## 提交对象确认",
        "",
        f"- 目标：`{status['target_confirmation_target']['benchmark']} / {status['target_confirmation_target']['robot_type']} / {status['target_confirmation_target']['task_name']}`。",
        f"- 用户需要确认的短语：`{status['first_user_confirmation_step']['recommended_confirmation_value']}`。",
        f"- 证据来源：`{status['first_user_confirmation_step']['source']}`。",
        f"- 本包只给出推荐确认值，不替用户确认、不联系平台：`target_user_confirmed={status['target_user_confirmed']}`。",
        "",
        "## Baseline 最短路线当前只差",
        "",
    ]
    for item in status["baseline_current_blocking"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## LoRA / 网页 checkpoint 路线当前只差",
            "",
        ]
    )
    for item in status["lora_web_current_blocking"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
        "",
        "## Baseline 主决策清单",
        "",
        ]
    )
    for item in status["required_user_decisions"]:
        lines.append(f"- `{item.get('id')}`：{item.get('label')}。{item.get('detail')}")
    lines.extend(["", "## LoRA/web checkpoint 分支决策清单", ""])
    for item in status["lora_web_user_decisions"]:
        lines.append(f"- `{item.get('id')}`：{item.get('label')}。{item.get('detail')}")
    lines.extend(
        [
            "",
            "## 推荐入口",
            "",
            "1. 打开 `notebooks/robochallenge_pi05_submit_cn.ipynb`。",
            (
                "2. 在第 44 节手动设置 `RUN_SAFE_LOCAL_ENV_INPUT_TEMPLATE=True`，"
                f"输入目标确认值 `{status['target_confirmation_value']}`，"
                "再把真实 token、submission id 和 `baseline` variant 写入被 Git 忽略的 local env。"
            ),
            "3. 在第 45 节手动设置 `RUN_JUPYTER_AUTHORIZED_PREFLIGHT=True`，优先运行 baseline 授权预检。",
            "4. 先按 `reports/baseline_submission_quickstart.md` 跑 baseline dry-run gate；只有明确选择 LoRA/web checkpoint 路线时，才进入 checkpoint 归档、上传和 link 回填。",
            "",
            "## 当前阻塞（baseline 默认路线）",
            "",
        ]
    )
    for item in status["current_blocking"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 旧全局阻塞（兼容 readiness/web/LoRA）", ""])
    for item in status["legacy_global_blocking"]:
        lines.append(f"- {item}")
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
