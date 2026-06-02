#!/usr/bin/env python3
"""Render a static GUI dashboard for RoboChallenge submission readiness."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
DEFAULT_HTML = REPORTS_DIR / "submission_status_dashboard.html"
DEFAULT_STATUS = RUNS_DIR / "submission_status_dashboard.json"


SOURCE_FILES = {
    "pi05": RUNS_DIR / "pi05_base_probe_status.json",
    "pi06_pi07": RUNS_DIR / "pi06_pi07_public_audit.json",
    "mapping": RUNS_DIR / "table30v2_aloha_mapping_audit.json",
    "lora_policy": RUNS_DIR / "openpi_rtc_lora_materialized_policy_smoke_status.json",
    "lora_export": RUNS_DIR / "lora_checkpoint_export_readiness.json",
    "archive_dry_run": RUNS_DIR / "checkpoint_archive_dry_run.json",
    "authorized_archive": RUNS_DIR / "authorized_checkpoint_archive_template_audit.json",
    "authorized_execution": RUNS_DIR / "authorized_execution_checklist.json",
    "next_user_action_packet": RUNS_DIR / "next_user_action_packet.json",
    "web_form_field_packet": RUNS_DIR / "web_form_field_packet.json",
    "submission_variant_route_packet": RUNS_DIR / "submission_variant_route_packet.json",
    "baseline_submission_quickstart": RUNS_DIR / "baseline_submission_quickstart.json",
    "baseline_dry_run_gate": RUNS_DIR / "baseline_dry_run_gate.json",
    "baseline_credential_hygiene": RUNS_DIR / "baseline_credential_hygiene.json",
    "local_env_permission": RUNS_DIR / "local_env_permission_contract.json",
    "local_env_runtime_permission": RUNS_DIR / "local_env_runtime_permission_gate.json",
    "submission_variant_gate": RUNS_DIR / "submission_variant_gate.json",
    "boolean_env_gate": RUNS_DIR / "boolean_env_gate.json",
    "placeholder_credentials": RUNS_DIR / "placeholder_credential_rejection.json",
    "credential_whitespace_guard": RUNS_DIR / "credential_whitespace_guard.json",
    "synthetic_dry_run_redaction": RUNS_DIR / "synthetic_dry_run_redaction.json",
    "shell_xtrace_secret_guard": RUNS_DIR / "shell_xtrace_secret_guard.json",
    "baseline_local_env_smoke": RUNS_DIR / "baseline_local_env_smoke.json",
    "baseline_final_handoff": RUNS_DIR / "baseline_final_handoff_packet.json",
    "baseline_final_handoff_rehearsal": RUNS_DIR / "baseline_final_handoff_rehearsal.json",
    "route_aware_submission_blockers": RUNS_DIR / "route_aware_submission_blockers.json",
    "jupyter_input": RUNS_DIR / "jupyter_input_template_audit.json",
    "jupyter_authorized": RUNS_DIR / "jupyter_authorized_preflight_template_audit.json",
    "jupyter_final_handoff": RUNS_DIR / "jupyter_final_handoff_template_audit.json",
    "chinese_utf8_artifacts": RUNS_DIR / "chinese_utf8_artifact_audit.json",
    "link_intake": RUNS_DIR / "checkpoint_link_intake.json",
    "readiness": RUNS_DIR / "real_submission_readiness.json",
    "preflight_bundle": RUNS_DIR / "submission_preflight_bundle.json",
    "authorized_sequence": RUNS_DIR / "authorized_submission_sequence_audit.json",
    "plaintext_scan": RUNS_DIR / "plaintext_secret_scan.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成 RoboChallenge 提交状态静态 GUI 面板。")
    parser.add_argument("--html-path", type=Path, default=DEFAULT_HTML, help="HTML 面板输出路径。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def yes(value: Any) -> str:
    return "是" if bool(value) else "否"


def state_label(state: str) -> str:
    return {
        "done": "已完成",
        "blocked": "待授权",
        "watch": "需关注",
    }.get(state, state)


def card(title: str, state: str, value: str, detail: str, report: str) -> dict[str, str]:
    return {
        "title": title,
        "state": state,
        "state_label": state_label(state),
        "value": value,
        "detail": detail,
        "report": report,
    }


def build_cards(data: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    pi05 = data["pi05"]
    pi06_pi07 = data["pi06_pi07"]
    mapping = data["mapping"]
    lora_policy = data["lora_policy"]
    lora_export = data["lora_export"]
    archive_dry_run = data["archive_dry_run"]
    authorized_archive = data["authorized_archive"]
    authorized_execution = data["authorized_execution"]
    action_packet = data["next_user_action_packet"]
    web_form_packet = data["web_form_field_packet"]
    route_packet = data["submission_variant_route_packet"]
    baseline_quickstart = data["baseline_submission_quickstart"]
    baseline_dry_run_gate = data["baseline_dry_run_gate"]
    baseline_credential_hygiene = data["baseline_credential_hygiene"]
    local_env_permission = data["local_env_permission"]
    local_env_runtime_permission = data["local_env_runtime_permission"]
    submission_variant_gate = data["submission_variant_gate"]
    boolean_env_gate = data["boolean_env_gate"]
    placeholder_credentials = data["placeholder_credentials"]
    credential_whitespace_guard = data["credential_whitespace_guard"]
    synthetic_dry_run = data["synthetic_dry_run_redaction"]
    shell_xtrace = data["shell_xtrace_secret_guard"]
    baseline_local_env_smoke = data["baseline_local_env_smoke"]
    baseline_final_handoff = data["baseline_final_handoff"]
    baseline_final_handoff_rehearsal = data["baseline_final_handoff_rehearsal"]
    route_aware_blockers = data["route_aware_submission_blockers"]
    jupyter_input = data["jupyter_input"]
    jupyter_authorized = data["jupyter_authorized"]
    jupyter_final_handoff = data["jupyter_final_handoff"]
    chinese_utf8 = data["chinese_utf8_artifacts"]
    link_intake = data["link_intake"]
    readiness = data["readiness"]
    preflight = data["preflight_bundle"]
    sequence = data["authorized_sequence"]
    plaintext = data["plaintext_scan"]

    gcs_zero = all(item.get("object_count") == 0 for item in pi06_pi07.get("gcs_prefixes", []))
    current_link_ready = link_intake.get("current_env", {}).get("link_shape_ready")
    ready_for_real = readiness.get("ready_for_real_submission")
    preflight_contacts = preflight.get("contact_flags", {})
    preflight_leaks = preflight.get("leak_flags", {})
    preflight_no_contact = not any(preflight_contacts.values())
    preflight_no_leak = not any(preflight_leaks.values())
    archive_created = archive_dry_run.get("archive_created")
    archive_confirm_smoke = authorized_archive.get("no_confirm_smoke", {})
    archive_confirm_gate_passed = bool(
        authorized_archive.get("passed")
        and archive_confirm_smoke.get("passed")
        and archive_confirm_smoke.get("stops_before_creating_tar")
        and archive_confirm_smoke.get("archive_created") is False
    )
    authorized_execution_ready = bool(
        authorized_execution.get("passed")
        and authorized_execution.get("go_no_go") == "blocked_by_user_inputs"
        and authorized_execution.get("ready_for_real_submission") is False
        and authorized_execution.get("recommended_route") == "baseline_official_aloha"
        and authorized_execution.get("baseline_requires_checkpoint_link") is False
        and authorized_execution.get("lora_web_requires_checkpoint_link") is True
    )
    action_packet_ready = bool(
        action_packet.get("passed")
        and action_packet.get("go_no_go") == "blocked_by_user_inputs"
        and action_packet.get("local_env_ignored") is True
        and len(action_packet.get("required_user_decisions", [])) >= 5
        and action_packet.get("recommended_route") == "baseline_official_aloha"
        and action_packet.get("baseline_requires_checkpoint_link") is False
        and action_packet.get("lora_web_requires_checkpoint_link") is True
    )
    web_form_packet_ready = bool(
        web_form_packet.get("passed")
        and web_form_packet.get("field_count", 0) >= 10
        and web_form_packet.get("web_form_ready") is False
    )
    route_packet_ready = bool(
        route_packet.get("passed")
        and route_packet.get("recommended_default") == "baseline_official_aloha"
        and route_packet.get("route_count") == 2
    )
    baseline_quickstart_ready = bool(
        baseline_quickstart.get("passed")
        and baseline_quickstart.get("recommended_route") == "baseline_official_aloha"
        and baseline_quickstart.get("requires_checkpoint_upload") is False
        and baseline_quickstart.get("requires_checkpoint_link") is False
    )
    baseline_dry_run_gate_ready = bool(
        baseline_dry_run_gate.get("passed")
        and baseline_dry_run_gate.get("recommended_route") == "baseline_official_aloha"
        and baseline_dry_run_gate.get("requires_checkpoint_upload") is False
        and baseline_dry_run_gate.get("requires_checkpoint_link") is False
        and baseline_dry_run_gate.get("stops_before_real_runner_without_confirmation") is True
        and baseline_dry_run_gate.get("stops_before_real_runner_with_wrong_confirmation") is True
    )
    baseline_credential_hygiene_ready = bool(
        baseline_credential_hygiene.get("passed")
        and baseline_credential_hygiene.get("recommended_route") == "baseline_official_aloha"
        and baseline_credential_hygiene.get("local_env_gitignored") is True
        and baseline_credential_hygiene.get("local_env_tracked") is False
        and baseline_credential_hygiene.get("local_env_content_read") is False
    )
    local_env_permission_ready = bool(
        local_env_permission.get("passed")
        and local_env_permission.get("recommended_chmod_command") == "chmod 600 submission/robochallenge_env.local.sh"
        and local_env_permission.get("local_env_content_read") is False
        and local_env_permission.get("local_env_owner_only_permissions") is True
        and local_env_permission.get("evidence", {}).get("local_env_gitignored") is True
        and local_env_permission.get("evidence", {}).get("local_env_not_tracked") is True
        and local_env_permission.get("synthetic_chmod_smoke", {}).get("owner_only_permissions") is True
        and not any(local_env_permission.get("leak_flags", {}).values())
        and not any(local_env_permission.get("contact_flags", {}).values())
    )
    local_env_runtime_permission_ready = bool(
        local_env_runtime_permission.get("passed")
        and local_env_runtime_permission.get("bad_permissions_rejected") is True
        and local_env_runtime_permission.get("owner_only_permissions_accepted") is True
        and local_env_runtime_permission.get("content_read_before_permission_check") is False
        and local_env_runtime_permission.get("real_runner_started") is False
        and local_env_runtime_permission.get("synthetic_values_recorded") is False
        and local_env_runtime_permission.get("evidence", {}).get("bad_permissions_stop_before_dry_run") is True
        and local_env_runtime_permission.get("evidence", {}).get("real_runner_not_started") is True
        and not any(local_env_runtime_permission.get("leak_flags", {}).values())
        and not any(local_env_runtime_permission.get("contact_flags", {}).values())
    )
    submission_variant_ready = bool(
        submission_variant_gate.get("passed")
        and submission_variant_gate.get("bad_variants_rejected") is True
        and submission_variant_gate.get("bad_variants_stop_before_preflight") is True
        and submission_variant_gate.get("valid_variants_accepted") is True
        and submission_variant_gate.get("real_runner_started") is False
        and submission_variant_gate.get("synthetic_values_recorded") is False
        and submission_variant_gate.get("evidence", {}).get("all_cases_no_protected_values") is True
        and submission_variant_gate.get("evidence", {}).get("real_runner_not_started") is True
        and not any(submission_variant_gate.get("leak_flags", {}).values())
        and not any(submission_variant_gate.get("contact_flags", {}).values())
    )
    boolean_env_ready = bool(
        boolean_env_gate.get("passed")
        and boolean_env_gate.get("bad_flags_rejected") is True
        and boolean_env_gate.get("bad_flags_stop_before_preflight") is True
        and boolean_env_gate.get("valid_flags_accepted") is True
        and boolean_env_gate.get("real_runner_started") is False
        and boolean_env_gate.get("synthetic_values_recorded") is False
        and boolean_env_gate.get("evidence", {}).get("all_cases_no_protected_values") is True
        and boolean_env_gate.get("evidence", {}).get("real_runner_not_started") is True
        and not any(boolean_env_gate.get("leak_flags", {}).values())
        and not any(boolean_env_gate.get("contact_flags", {}).values())
    )
    placeholder_credentials_ready = bool(
        placeholder_credentials.get("passed")
        and placeholder_credentials.get("baseline_placeholder_rejected") is True
        and placeholder_credentials.get("lora_placeholder_rejected") is True
        and placeholder_credentials.get("baseline_stops_before_dry_run") is True
        and placeholder_credentials.get("lora_stops_before_dry_run") is True
        and placeholder_credentials.get("baseline_real_runner_not_started") is True
        and placeholder_credentials.get("lora_real_runner_not_started") is True
        and placeholder_credentials.get("placeholder_values_recorded") is False
        and not any(placeholder_credentials.get("leak_flags", {}).values())
        and not any(placeholder_credentials.get("contact_flags", {}).values())
    )
    credential_whitespace_ready = bool(
        credential_whitespace_guard.get("passed")
        and credential_whitespace_guard.get("bad_credentials_rejected") is True
        and credential_whitespace_guard.get("clean_credentials_dry_run_passed") is True
        and credential_whitespace_guard.get("real_runner_started") is False
        and credential_whitespace_guard.get("synthetic_values_recorded") is False
        and credential_whitespace_guard.get("evidence", {}).get("bad_credentials_stop_before_dry_run") is True
        and credential_whitespace_guard.get("evidence", {}).get("all_cases_no_protected_values") is True
        and not any(credential_whitespace_guard.get("leak_flags", {}).values())
        and not any(credential_whitespace_guard.get("contact_flags", {}).values())
    )
    synthetic_dry_run_ready = bool(
        synthetic_dry_run.get("passed")
        and synthetic_dry_run.get("baseline_dry_run_passed") is True
        and synthetic_dry_run.get("lora_dry_run_passed") is True
        and synthetic_dry_run.get("baseline_outputs_lengths_only") is True
        and synthetic_dry_run.get("lora_outputs_lengths_only") is True
        and synthetic_dry_run.get("baseline_real_runner_not_started") is True
        and synthetic_dry_run.get("lora_real_runner_not_started") is True
        and synthetic_dry_run.get("synthetic_values_recorded") is False
        and not any(synthetic_dry_run.get("leak_flags", {}).values())
        and not any(synthetic_dry_run.get("contact_flags", {}).values())
    )
    shell_xtrace_ready = bool(
        shell_xtrace.get("passed")
        and shell_xtrace.get("synthetic_values_recorded") is False
        and shell_xtrace.get("evidence", {}).get("all_templates_disable_xtrace_first") is True
        and shell_xtrace.get("evidence", {}).get("all_cases_saw_set_plus_x_trace") is True
        and shell_xtrace.get("evidence", {}).get("all_cases_stop_trace_after_guard") is True
        and shell_xtrace.get("evidence", {}).get("all_cases_no_protected_values") is True
        and shell_xtrace.get("evidence", {}).get("demo_dry_runs_passed") is True
        and shell_xtrace.get("evidence", {}).get("ready_runner_stops_before_real_runner") is True
        and not any(shell_xtrace.get("leak_flags", {}).values())
        and not any(shell_xtrace.get("contact_flags", {}).values())
    )
    baseline_local_env_smoke_ready = bool(
        baseline_local_env_smoke.get("passed")
        and baseline_local_env_smoke.get("recommended_route") == "baseline_official_aloha"
        and baseline_local_env_smoke.get("synthetic_values_recorded") is False
        and baseline_local_env_smoke.get("synthetic_env_file_removed_after_run") is True
        and baseline_local_env_smoke.get("authorized_preflight", {}).get("variant_baseline") is True
        and baseline_local_env_smoke.get("ready_runner", {}).get("stops_before_real_runner") is True
        and baseline_local_env_smoke.get("ready_runner", {}).get("parent_real_confirm_present_in_subprocess_env")
        is False
        and baseline_local_env_smoke.get("ready_runner", {}).get("confirmation_absent") is True
    )
    baseline_final_handoff_ready = bool(
        baseline_final_handoff.get("passed")
        and baseline_final_handoff.get("recommended_route") == "baseline_official_aloha"
        and baseline_final_handoff.get("requires_checkpoint_upload") is False
        and baseline_final_handoff.get("requires_checkpoint_link") is False
        and baseline_final_handoff.get("local_env_content_read") is False
        and baseline_final_handoff.get("command_count") == 4
        and baseline_final_handoff.get("no_contact_command_count") == 3
        and baseline_final_handoff.get("real_runner_requires_confirmation") is True
    )
    rehearsal_commands = baseline_final_handoff_rehearsal.get("commands", [])
    rehearsal_step3 = rehearsal_commands[2] if len(rehearsal_commands) >= 3 else {}
    baseline_final_handoff_rehearsal_ready = bool(
        baseline_final_handoff_rehearsal.get("passed")
        and baseline_final_handoff_rehearsal.get("recommended_route") == "baseline_official_aloha"
        and baseline_final_handoff_rehearsal.get("command_count") == 3
        and baseline_final_handoff_rehearsal.get("synthetic_values_recorded") is False
        and baseline_final_handoff_rehearsal.get("synthetic_env_file_removed_after_run") is True
        and baseline_final_handoff_rehearsal.get("workspace_state_restored_after_rehearsal") is True
        and rehearsal_step3.get("stops_before_real_runner") is True
        and rehearsal_step3.get("parent_real_confirm_present_in_subprocess_env") is False
        and rehearsal_step3.get("confirmation_absent") is True
        and not any(baseline_final_handoff_rehearsal.get("contact_flags", {}).values())
        and not any(baseline_final_handoff_rehearsal.get("leak_flags", {}).values())
    )
    route_aware_blockers_ready = bool(
        route_aware_blockers.get("passed")
        and route_aware_blockers.get("recommended_route") == "baseline_official_aloha"
        and route_aware_blockers.get("baseline_requires_checkpoint_upload") is False
        and route_aware_blockers.get("baseline_requires_checkpoint_link") is False
        and route_aware_blockers.get("lora_web_requires_checkpoint_upload") is True
        and route_aware_blockers.get("lora_web_requires_checkpoint_link") is True
    )
    jupyter_input_ready = bool(
        jupyter_input.get("passed")
        and jupyter_input.get("run_flag_default_false")
        and jupyter_input.get("local_env_ignored", {}).get("ignored")
        and jupyter_input.get("recommended_route") == "baseline_official_aloha"
        and jupyter_input.get("baseline_requires_checkpoint_link") is False
        and jupyter_input.get("lora_web_requires_checkpoint_link") is True
    )
    jupyter_authorized_ready = bool(
        jupyter_authorized.get("passed")
        and jupyter_authorized.get("audit_default_true")
        and jupyter_authorized.get("execution_default_false")
        and jupyter_authorized.get("recommended_route") == "baseline_official_aloha"
        and jupyter_authorized.get("baseline_requires_checkpoint_link") is False
        and jupyter_authorized.get("lora_web_requires_checkpoint_link") is True
    )
    jupyter_final_handoff_ready = bool(
        jupyter_final_handoff.get("passed")
        and jupyter_final_handoff.get("audit_default_true")
        and jupyter_final_handoff.get("packet_default_true")
        and jupyter_final_handoff.get("real_runner_default_false")
        and jupyter_final_handoff.get("command_count") == 4
        and jupyter_final_handoff.get("no_contact_command_count") == 3
        and jupyter_final_handoff.get("real_runner_requires_confirmation") is True
    )
    chinese_utf8_ready = bool(
        chinese_utf8.get("passed")
        and chinese_utf8.get("scanned_file_count", 0) >= 20
        and chinese_utf8.get("decode_error_count") == 0
        and chinese_utf8.get("bad_marker_hit_count") == 0
        and all(item.get("present") is True for item in chinese_utf8.get("required_phrase_checks", {}).values())
    )
    uploads_performed = readiness.get("inputs", {}).get("uploads_performed")
    plaintext_clean = plaintext.get("hit_count") == 0 and plaintext.get("secret_values_printed") is False

    return [
        card(
            "pi0.5 基模",
            "done" if pi05.get("local_complete") and pi05.get("load_params_smoke_preserved") else "watch",
            f"{pi05.get('remote_object_count', 0)} 个对象",
            f"本地缓存完整，匹配字节 {pi05.get('local_matched_bytes', 0):,}。",
            "reports/pi05_base_repro.md",
        ),
        card(
            "pi0.6 / pi0.7",
            "watch" if gcs_zero else "done",
            "未发现公开 checkpoint",
            "公开 OpenPI/GCS 审计未找到可直接复现 checkpoint；当前只能记录为 release gap。",
            "reports/pi06_pi07_public_release_audit.md",
        ),
        card(
            "Table30v2 ALOHA",
            "done" if mapping.get("ready_for_dry_run_converter") and mapping.get("lengths_match") else "watch",
            "1100 帧任务链",
            "pack_the_toothbrush_holder 映射、转换、短 episode dataloader 已完成。",
            "reports/table30v2_aloha_mapping.md",
        ),
        card(
            "LoRA 物化 policy",
            "done" if lora_policy.get("passed") else "watch",
            lora_policy.get("policy_load_smoke", {}).get("model_type", "Pi0"),
            "完整物化 checkpoint 已通过 create_trained_policy 加载 smoke。",
            "reports/openpi_rtc_lora_materialized_policy_smoke.md",
        ),
        card(
            "Checkpoint 导出",
            "done" if lora_export.get("local_export_ready") else "watch",
            f"{lora_export.get('inventory', {}).get('total_size_gb', 11.064)} GB",
            "目录结构、必需文件、tar stream smoke 已就绪。",
            "reports/lora_checkpoint_export_readiness.md",
        ),
        card(
            "归档生成",
            "blocked" if not archive_created else "done",
            "dry-run 已通过",
            "默认不生成 tar；真实生成必须先通过归档强确认入口。",
            "reports/checkpoint_archive_dry_run.md",
        ),
        card(
            "归档强确认入口",
            "done" if archive_confirm_gate_passed else "watch",
            "无确认不生成 tar",
            (
                "模板要求 ROBOCHALLENGE_ARCHIVE_CONFIRM=CREATE_ROBOCHALLENGE_CHECKPOINT_ARCHIVE；"
                "未确认时停在 creating tar 前。"
            ),
            "reports/authorized_checkpoint_archive_template_audit.md",
        ),
        card(
            "上传与链接",
            "blocked" if not current_link_ready else "done",
            "缺少真实链接" if not current_link_ready else "链接形态就绪",
            "仅 LoRA/web checkpoint 路线需要上传和真实 link；baseline 本地 runner 不等这个前置。",
            "reports/checkpoint_link_intake.md",
        ),
        card(
            "真实提交 gate",
            "blocked" if not ready_for_real else "done",
            "ready=false" if not ready_for_real else "ready=true",
            "baseline 仍缺 token、submission id、variant=baseline 和真实 runner 强确认；checkpoint link 只属于 LoRA/web 分支。",
            "reports/real_submission_readiness.md",
        ),
        card(
            "提交前预检汇总",
            "blocked" if preflight.get("go_no_go") == "blocked" else "done",
            f"go/no-go={preflight.get('go_no_go', 'unknown')}",
            (
                "一键预检已串联 link、下载协议、readiness、handoff 和明文扫描；"
                f"no-contact={yes(preflight_no_contact)}，no-leak={yes(preflight_no_leak)}。"
            ),
            "reports/submission_preflight_bundle.md",
        ),
        card(
            "授权后顺序",
            "done" if sequence.get("passed") and sequence.get("commands", {}).get("critical_order_passed") else "watch",
            "顺序已固化",
            "默认先选 baseline 路线，再做授权预检和 dry-run gate；LoRA/web link/upload 分支单独保留。",
            "reports/authorized_submission_sequence_audit.md",
        ),
        card(
            "授权执行清单",
            "done" if authorized_execution_ready else "watch",
            "baseline 输入",
            "baseline 主清单只等目标确认、token、submission id、variant=baseline 和真实 runner 确认；LoRA/web 另列 link/upload。",
            "reports/authorized_execution_checklist.md",
        ),
        card(
            "下一步动作包",
            "done" if action_packet_ready else "watch",
            "baseline 优先",
            "默认只列 baseline 最短缺口；LoRA/web checkpoint 的上传和 link 阻塞单独保留。",
            "reports/next_user_action_packet.md",
        ),
        card(
            "网页表单字段",
            "done" if web_form_packet_ready else "watch",
            f"{web_form_packet.get('ready_field_count', 0)}/{web_form_packet.get('field_count', 0)} 已就绪",
            "baseline 表单先补 token、submission id 和 variant；checkpoint link 只在选择 LoRA/web checkpoint 路线时补齐。",
            "reports/web_form_field_packet.md",
        ),
        card(
            "提交路线拆分",
            "done" if route_packet_ready else "watch",
            "baseline 优先",
            "官方 ALOHA baseline 本地 runner 不需要 LoRA tar/link；LoRA 网页 checkpoint 路线仍需上传和 link。",
            "reports/submission_variant_route_packet.md",
        ),
        card(
            "Baseline 最短路径",
            "done" if baseline_quickstart_ready else "watch",
            "无 link 前置",
            "token 和 submission id 到位后先跑 baseline 授权预检；缺真实确认短语时只到 dry-run，不启动 runner。",
            "reports/baseline_submission_quickstart.md",
        ),
        card(
            "Baseline dry-run gate",
            "done" if baseline_dry_run_gate_ready else "watch",
            "先 dry-run",
            "拿到 token/submission id 后先跑授权前只读预检，再跑 baseline wrapper dry-run gate；无强确认时停在真实 runner 前。",
            "reports/baseline_dry_run_gate.md",
        ),
        card(
            "Baseline 凭据卫生",
            "done" if baseline_credential_hygiene_ready else "watch",
            "local env 安全",
            "真实值只写 Git 忽略的 local env 或当前 shell；本检查只验证路径和上游审计，不读取 local env 内容。",
            "reports/baseline_credential_hygiene.md",
        ),
        card(
            "Local env 权限",
            "done" if local_env_permission_ready else "watch",
            "chmod 600",
            "真实 token/submission id 写入 local env 后，文件必须 Git 忽略、未跟踪且权限收敛到 owner-only；本审计不读取内容。",
            "reports/local_env_permission_contract.md",
        ),
        card(
            "Local env runtime gate",
            "done" if local_env_runtime_permission_ready else "watch",
            "source 前拦截",
            "两个授权入口会在 source local env 前检查权限；0644 会被拒绝，0600 synthetic 文件可进入授权边界且不启动真实 runner。",
            "reports/local_env_runtime_permission_gate.md",
        ),
        card(
            "提交 variant gate",
            "done" if submission_variant_ready else "watch",
            f"{submission_variant_gate.get('case_count', 0)} 个场景",
            "授权入口只接受 baseline 或 lora；拼写错误、大小写错误或带空白字符会在 checkpoint/readiness 预检前被拒绝。",
            "reports/submission_variant_gate.md",
        ),
        card(
            "布尔环境变量 gate",
            "done" if boolean_env_ready else "watch",
            f"{boolean_env_gate.get('case_count', 0)} 个场景",
            "授权入口只接受 0/1；true/false/yes/no 或空白会在 checkpoint/readiness 预检前被拒绝。",
            "reports/boolean_env_gate.md",
        ),
        card(
            "占位符凭据拒绝",
            "done" if placeholder_credentials_ready else "watch",
            f"{placeholder_credentials.get('case_count', 0)} 个场景",
            "token 和 submission id 的占位符会在 baseline/LoRA wrapper 的 dry-run 与真实 runner 前被拒绝。",
            "reports/placeholder_credential_rejection.md",
        ),
        card(
            "凭据空白字符 gate",
            "done" if credential_whitespace_ready else "watch",
            f"{credential_whitespace_guard.get('case_count', 0)} 个场景",
            "token/submission id 带空格、tab 或换行时会在 dry-run 前被拒绝；干净 synthetic 值仍可走 dry-run 且只输出长度。",
            "reports/credential_whitespace_guard.md",
        ),
        card(
            "Synthetic dry-run 脱敏",
            "done" if synthetic_dry_run_ready else "watch",
            f"{synthetic_dry_run.get('case_count', 0)} 个场景",
            "非占位假值 dry-run 会返回长度字段和 robot_type，不打印 token/submission id 明文，也不启动真实 runner。",
            "reports/synthetic_dry_run_redaction.md",
        ),
        card(
            "bash xtrace 防泄漏",
            "done" if shell_xtrace_ready else "watch",
            f"{shell_xtrace.get('case_count', 0)} 个入口",
            "四个提交 shell 入口在 bash -x 下会先关闭 xtrace，合成 token/submission id 不进入日志。",
            "reports/shell_xtrace_secret_guard.md",
        ),
        card(
            "Baseline local env smoke",
            "done" if baseline_local_env_smoke_ready else "watch",
            "synthetic 已跑通",
            "临时 fake local env 已验证授权预检会按 baseline 读取；父环境确认短语会被清理，ready runner 仍停在真实 runner 前。",
            "reports/baseline_local_env_smoke.md",
        ),
        card(
            "Baseline final handoff",
            "done" if baseline_final_handoff_ready else "watch",
            "凭据后执行",
            "最终交接包把凭据卫生、授权前只读预检、dry-run gate 和真实 runner 强确认命令按顺序固化。",
            "reports/baseline_final_handoff_packet.md",
        ),
        card(
            "Baseline handoff rehearsal",
            "done" if baseline_final_handoff_rehearsal_ready else "watch",
            "前三步已演练",
            "临时 synthetic local env 已按 final handoff 前三条命令顺序跑通；父环境确认短语会被清理，第三步仍停在 runner 前。",
            "reports/baseline_final_handoff_rehearsal.md",
        ),
        card(
            "路线感知阻塞",
            "done" if route_aware_blockers_ready else "watch",
            "baseline 不等 link",
            "底部当前阻塞按 baseline 最短路线显示；LoRA/web checkpoint 的上传和 link 阻塞单独保留。",
            "reports/route_aware_submission_blockers.md",
        ),
        card(
            "Jupyter 安全填空",
            "done" if jupyter_input_ready else "watch",
            "baseline 默认",
            "Notebook 第 44 节默认关闭；baseline 只填 token/submission id，checkpoint link 留空不会进入 LoRA 上传流程。",
            "reports/jupyter_input_template_audit.md",
        ),
        card(
            "Jupyter 授权预检",
            "done" if jupyter_authorized_ready else "watch",
            "baseline 预检",
            "Notebook 第 45 节默认按 baseline_official_aloha 预检；LoRA/web checkpoint 的归档、上传和 link 回填另走手动授权。",
            "reports/jupyter_authorized_preflight_template_audit.md",
        ),
        card(
            "Jupyter final handoff",
            "done" if jupyter_final_handoff_ready else "watch",
            "第 46 节已接入",
            "Notebook 默认生成 final handoff 包并展示命令顺序；真实 runner 标志默认关闭，只能手动强确认。",
            "reports/jupyter_final_handoff_template_audit.md",
        ),
        card(
            "中文 UTF-8",
            "done" if chinese_utf8_ready else "watch",
            f"{chinese_utf8.get('scanned_file_count', 0)} 个文件",
            "关键报告、GUI、Notebook 和交接文档已做 UTF-8 解码与常见乱码哨兵扫描。",
            "reports/chinese_utf8_artifact_audit.md",
        ),
        card(
            "明文凭据扫描",
            "done" if plaintext_clean else "watch",
            f"hit_count={plaintext.get('hit_count')}",
            "仓库跟踪文件和未忽略文件未发现明文凭据模式。",
            "reports/plaintext_secret_scan.md",
        ),
    ]


def build_status(cards: list[dict[str, str]], data: dict[str, dict[str, Any]], html_path: Path) -> dict[str, Any]:
    readiness = data["readiness"]
    link_intake = data["link_intake"]
    archive = data["archive_dry_run"]
    authorized_archive = data["authorized_archive"]
    authorized_execution = data["authorized_execution"]
    action_packet = data["next_user_action_packet"]
    web_form_packet = data["web_form_field_packet"]
    route_packet = data["submission_variant_route_packet"]
    baseline_quickstart = data["baseline_submission_quickstart"]
    baseline_dry_run_gate = data["baseline_dry_run_gate"]
    baseline_credential_hygiene = data["baseline_credential_hygiene"]
    local_env_permission = data["local_env_permission"]
    local_env_runtime_permission = data["local_env_runtime_permission"]
    submission_variant_gate = data["submission_variant_gate"]
    boolean_env_gate = data["boolean_env_gate"]
    placeholder_credentials = data["placeholder_credentials"]
    credential_whitespace_guard = data["credential_whitespace_guard"]
    synthetic_dry_run = data["synthetic_dry_run_redaction"]
    shell_xtrace = data["shell_xtrace_secret_guard"]
    baseline_local_env_smoke = data["baseline_local_env_smoke"]
    baseline_final_handoff = data["baseline_final_handoff"]
    baseline_final_handoff_rehearsal = data["baseline_final_handoff_rehearsal"]
    route_aware_blockers = data["route_aware_submission_blockers"]
    jupyter_input = data["jupyter_input"]
    jupyter_authorized = data["jupyter_authorized"]
    jupyter_final_handoff = data["jupyter_final_handoff"]
    chinese_utf8 = data["chinese_utf8_artifacts"]
    sequence = data["authorized_sequence"]
    preflight = data["preflight_bundle"]
    plaintext = data["plaintext_scan"]
    preflight_contacts = preflight.get("contact_flags", {})
    preflight_leaks = preflight.get("leak_flags", {})
    blocked_cards = [item for item in cards if item["state"] == "blocked"]
    watch_cards = [item for item in cards if item["state"] == "watch"]
    done_cards = [item for item in cards if item["state"] == "done"]
    rehearsal_commands = baseline_final_handoff_rehearsal.get("commands", [])
    rehearsal_step3 = rehearsal_commands[2] if len(rehearsal_commands) >= 3 else {}
    return {
        "kind": "submission_status_dashboard",
        "passed": True,
        "html_path": html_path.relative_to(ROOT).as_posix(),
        "source_count": len(SOURCE_FILES),
        "card_count": len(cards),
        "done_count": len(done_cards),
        "blocked_count": len(blocked_cards),
        "watch_count": len(watch_cards),
        "ready_for_real_submission": readiness.get("ready_for_real_submission"),
        "web_form_ready": readiness.get("web_form_ready"),
        "preflight_passed": preflight.get("passed"),
        "preflight_go_no_go": preflight.get("go_no_go"),
        "preflight_no_contact": not any(preflight_contacts.values()),
        "preflight_no_secret_leak": not any(preflight_leaks.values()),
        "link_shape_ready": link_intake.get("current_env", {}).get("link_shape_ready"),
        "archive_created": archive.get("archive_created"),
        "archive_confirm_gate_passed": authorized_archive.get("passed") is True,
        "archive_confirm_phrase": authorized_archive.get("confirmation_phrase"),
        "archive_no_confirm_blocks": authorized_archive.get("no_confirm_smoke", {}).get("passed") is True,
        "authorized_execution_checklist_passed": authorized_execution.get("passed") is True,
        "authorized_execution_go_no_go": authorized_execution.get("go_no_go"),
        "next_user_action_packet_passed": action_packet.get("passed") is True,
        "next_user_action_packet_decision_count": len(action_packet.get("required_user_decisions", [])),
        "next_user_action_packet_local_env_ignored": action_packet.get("local_env_ignored") is True,
        "next_user_action_packet_recommended_route": action_packet.get("recommended_route"),
        "next_user_action_packet_baseline_no_upload": action_packet.get("baseline_requires_checkpoint_upload") is False,
        "next_user_action_packet_baseline_no_link": action_packet.get("baseline_requires_checkpoint_link") is False,
        "next_user_action_packet_lora_web_needs_upload": action_packet.get("lora_web_requires_checkpoint_upload") is True,
        "next_user_action_packet_lora_web_needs_link": action_packet.get("lora_web_requires_checkpoint_link") is True,
        "web_form_field_packet_passed": web_form_packet.get("passed") is True,
        "web_form_field_count": web_form_packet.get("field_count"),
        "web_form_ready_field_count": web_form_packet.get("ready_field_count"),
        "web_form_packet_currently_not_ready": web_form_packet.get("web_form_ready") is False,
        "submission_variant_route_packet_passed": route_packet.get("passed") is True,
        "submission_variant_recommended_default": route_packet.get("recommended_default"),
        "submission_variant_route_count": route_packet.get("route_count"),
        "baseline_submission_quickstart_passed": baseline_quickstart.get("passed") is True,
        "baseline_submission_quickstart_no_upload": baseline_quickstart.get("requires_checkpoint_upload") is False,
        "baseline_submission_quickstart_no_link": baseline_quickstart.get("requires_checkpoint_link") is False,
        "baseline_dry_run_gate_passed": baseline_dry_run_gate.get("passed") is True,
        "baseline_dry_run_gate_no_upload": baseline_dry_run_gate.get("requires_checkpoint_upload") is False,
        "baseline_dry_run_gate_no_link": baseline_dry_run_gate.get("requires_checkpoint_link") is False,
        "baseline_dry_run_gate_stops_before_real_runner": baseline_dry_run_gate.get(
            "stops_before_real_runner_without_confirmation"
        )
        is True,
        "baseline_dry_run_gate_wrong_confirm_stops_before_real_runner": baseline_dry_run_gate.get(
            "stops_before_real_runner_with_wrong_confirmation"
        )
        is True,
        "baseline_dry_run_gate_command": baseline_dry_run_gate.get("dry_run_gate_command"),
        "baseline_credential_hygiene_passed": baseline_credential_hygiene.get("passed") is True,
        "baseline_credential_hygiene_local_env_gitignored": baseline_credential_hygiene.get(
            "local_env_gitignored"
        )
        is True,
        "baseline_credential_hygiene_local_env_not_tracked": baseline_credential_hygiene.get("local_env_tracked")
        is False,
        "baseline_credential_hygiene_does_not_read_local_env": baseline_credential_hygiene.get(
            "local_env_content_read"
        )
        is False,
        "local_env_permission_contract_passed": local_env_permission.get("passed") is True,
        "local_env_permission_chmod_600_recommended": local_env_permission.get("recommended_chmod_command")
        == "chmod 600 submission/robochallenge_env.local.sh",
        "local_env_permission_gitignored": local_env_permission.get("evidence", {}).get("local_env_gitignored")
        is True,
        "local_env_permission_not_tracked": local_env_permission.get("evidence", {}).get("local_env_not_tracked")
        is True,
        "local_env_permission_content_not_read": local_env_permission.get("local_env_content_read") is False,
        "local_env_permission_owner_only": local_env_permission.get("local_env_owner_only_permissions") is True,
        "local_env_permission_synthetic_chmod_passed": local_env_permission.get(
            "synthetic_chmod_smoke", {}
        ).get("owner_only_permissions")
        is True,
        "local_env_permission_no_contact": not any(local_env_permission.get("contact_flags", {}).values()),
        "local_env_permission_no_leak": not any(local_env_permission.get("leak_flags", {}).values()),
        "local_env_runtime_permission_gate_passed": local_env_runtime_permission.get("passed") is True,
        "local_env_runtime_bad_permissions_rejected": local_env_runtime_permission.get(
            "bad_permissions_rejected"
        )
        is True,
        "local_env_runtime_owner_only_accepted": local_env_runtime_permission.get(
            "owner_only_permissions_accepted"
        )
        is True,
        "local_env_runtime_content_not_read_before_gate": local_env_runtime_permission.get(
            "content_read_before_permission_check"
        )
        is False,
        "local_env_runtime_real_runner_not_started": local_env_runtime_permission.get("real_runner_started")
        is False,
        "local_env_runtime_values_not_recorded": local_env_runtime_permission.get("synthetic_values_recorded")
        is False,
        "local_env_runtime_no_contact": not any(
            local_env_runtime_permission.get("contact_flags", {}).values()
        ),
        "local_env_runtime_no_leak": not any(local_env_runtime_permission.get("leak_flags", {}).values()),
        "submission_variant_gate_passed": submission_variant_gate.get("passed") is True,
        "submission_variant_case_count": submission_variant_gate.get("case_count"),
        "submission_variant_bad_rejected": submission_variant_gate.get("bad_variants_rejected") is True,
        "submission_variant_bad_stop_before_preflight": submission_variant_gate.get(
            "bad_variants_stop_before_preflight"
        )
        is True,
        "submission_variant_valid_accepted": submission_variant_gate.get("valid_variants_accepted") is True,
        "submission_variant_real_runner_not_started": submission_variant_gate.get("real_runner_started")
        is False,
        "submission_variant_values_not_recorded": submission_variant_gate.get("synthetic_values_recorded")
        is False,
        "submission_variant_no_contact": not any(submission_variant_gate.get("contact_flags", {}).values()),
        "submission_variant_no_leak": not any(submission_variant_gate.get("leak_flags", {}).values()),
        "boolean_env_gate_passed": boolean_env_gate.get("passed") is True,
        "boolean_env_case_count": boolean_env_gate.get("case_count"),
        "boolean_env_bad_rejected": boolean_env_gate.get("bad_flags_rejected") is True,
        "boolean_env_bad_stop_before_preflight": boolean_env_gate.get("bad_flags_stop_before_preflight")
        is True,
        "boolean_env_valid_accepted": boolean_env_gate.get("valid_flags_accepted") is True,
        "boolean_env_real_runner_not_started": boolean_env_gate.get("real_runner_started") is False,
        "boolean_env_values_not_recorded": boolean_env_gate.get("synthetic_values_recorded") is False,
        "boolean_env_no_contact": not any(boolean_env_gate.get("contact_flags", {}).values()),
        "boolean_env_no_leak": not any(boolean_env_gate.get("leak_flags", {}).values()),
        "placeholder_credential_rejection_passed": placeholder_credentials.get("passed") is True,
        "placeholder_credential_rejection_case_count": placeholder_credentials.get("case_count"),
        "placeholder_baseline_rejected_before_dry_run": placeholder_credentials.get("baseline_placeholder_rejected")
        is True
        and placeholder_credentials.get("baseline_stops_before_dry_run") is True,
        "placeholder_lora_rejected_before_dry_run": placeholder_credentials.get("lora_placeholder_rejected")
        is True
        and placeholder_credentials.get("lora_stops_before_dry_run") is True,
        "placeholder_baseline_real_runner_not_started": placeholder_credentials.get(
            "baseline_real_runner_not_started"
        )
        is True,
        "placeholder_lora_real_runner_not_started": placeholder_credentials.get("lora_real_runner_not_started")
        is True,
        "placeholder_values_not_recorded": placeholder_credentials.get("placeholder_values_recorded") is False,
        "placeholder_credentials_no_contact": not any(placeholder_credentials.get("contact_flags", {}).values()),
        "placeholder_credentials_no_leak": not any(placeholder_credentials.get("leak_flags", {}).values()),
        "credential_whitespace_guard_passed": credential_whitespace_guard.get("passed") is True,
        "credential_whitespace_case_count": credential_whitespace_guard.get("case_count"),
        "credential_whitespace_bad_rejected": credential_whitespace_guard.get("bad_credentials_rejected") is True,
        "credential_whitespace_clean_dry_run_passed": credential_whitespace_guard.get(
            "clean_credentials_dry_run_passed"
        )
        is True,
        "credential_whitespace_real_runner_not_started": credential_whitespace_guard.get("real_runner_started")
        is False,
        "credential_whitespace_values_not_recorded": credential_whitespace_guard.get("synthetic_values_recorded")
        is False,
        "credential_whitespace_no_contact": not any(
            credential_whitespace_guard.get("contact_flags", {}).values()
        ),
        "credential_whitespace_no_leak": not any(credential_whitespace_guard.get("leak_flags", {}).values()),
        "synthetic_dry_run_redaction_passed": synthetic_dry_run.get("passed") is True,
        "synthetic_dry_run_redaction_case_count": synthetic_dry_run.get("case_count"),
        "synthetic_dry_run_baseline_passed": synthetic_dry_run.get("baseline_dry_run_passed") is True,
        "synthetic_dry_run_lora_passed": synthetic_dry_run.get("lora_dry_run_passed") is True,
        "synthetic_dry_run_baseline_lengths_only": synthetic_dry_run.get("baseline_outputs_lengths_only")
        is True,
        "synthetic_dry_run_lora_lengths_only": synthetic_dry_run.get("lora_outputs_lengths_only") is True,
        "synthetic_dry_run_baseline_runner_not_started": synthetic_dry_run.get(
            "baseline_real_runner_not_started"
        )
        is True,
        "synthetic_dry_run_lora_runner_not_started": synthetic_dry_run.get("lora_real_runner_not_started")
        is True,
        "synthetic_dry_run_values_not_recorded": synthetic_dry_run.get("synthetic_values_recorded") is False,
        "synthetic_dry_run_no_contact": not any(synthetic_dry_run.get("contact_flags", {}).values()),
        "synthetic_dry_run_no_leak": not any(synthetic_dry_run.get("leak_flags", {}).values()),
        "shell_xtrace_secret_guard_passed": shell_xtrace.get("passed") is True,
        "shell_xtrace_case_count": shell_xtrace.get("case_count"),
        "shell_xtrace_templates_disable_xtrace": shell_xtrace.get("evidence", {}).get(
            "all_templates_disable_xtrace_first"
        )
        is True,
        "shell_xtrace_cases_saw_set_plus_x": shell_xtrace.get("evidence", {}).get(
            "all_cases_saw_set_plus_x_trace"
        )
        is True,
        "shell_xtrace_stops_trace_after_guard": shell_xtrace.get("evidence", {}).get(
            "all_cases_stop_trace_after_guard"
        )
        is True,
        "shell_xtrace_no_protected_values": shell_xtrace.get("evidence", {}).get(
            "all_cases_no_protected_values"
        )
        is True,
        "shell_xtrace_demo_dry_runs_passed": shell_xtrace.get("evidence", {}).get("demo_dry_runs_passed")
        is True,
        "shell_xtrace_ready_runner_blocks_real_runner": shell_xtrace.get("evidence", {}).get(
            "ready_runner_stops_before_real_runner"
        )
        is True,
        "shell_xtrace_values_not_recorded": shell_xtrace.get("synthetic_values_recorded") is False,
        "shell_xtrace_no_contact": not any(shell_xtrace.get("contact_flags", {}).values()),
        "shell_xtrace_no_leak": not any(shell_xtrace.get("leak_flags", {}).values()),
        "baseline_local_env_smoke_passed": baseline_local_env_smoke.get("passed") is True,
        "baseline_local_env_smoke_synthetic_values_not_recorded": baseline_local_env_smoke.get(
            "synthetic_values_recorded"
        )
        is False,
        "baseline_local_env_smoke_temp_env_removed": baseline_local_env_smoke.get(
            "synthetic_env_file_removed_after_run"
        )
        is True,
        "baseline_local_env_smoke_authorized_preflight_baseline": baseline_local_env_smoke.get(
            "authorized_preflight", {}
        ).get("variant_baseline")
        is True,
        "baseline_local_env_smoke_ready_runner_stops": baseline_local_env_smoke.get("ready_runner", {}).get(
            "stops_before_real_runner"
        )
        is True,
        "baseline_local_env_smoke_parent_real_confirm_scrubbed": baseline_local_env_smoke.get(
            "ready_runner", {}
        ).get("parent_real_confirm_present_in_subprocess_env")
        is False,
        "baseline_local_env_smoke_confirmation_absent_after_scrub": baseline_local_env_smoke.get(
            "ready_runner", {}
        ).get("confirmation_absent")
        is True,
        "baseline_final_handoff_passed": baseline_final_handoff.get("passed") is True,
        "baseline_final_handoff_no_upload": baseline_final_handoff.get("requires_checkpoint_upload") is False,
        "baseline_final_handoff_no_link": baseline_final_handoff.get("requires_checkpoint_link") is False,
        "baseline_final_handoff_no_archive_authorization": baseline_final_handoff.get(
            "requires_checkpoint_archive_authorization"
        )
        is False,
        "baseline_final_handoff_command_count": baseline_final_handoff.get("command_count"),
        "baseline_final_handoff_no_contact_command_count": baseline_final_handoff.get("no_contact_command_count"),
        "baseline_final_handoff_real_runner_requires_confirmation": baseline_final_handoff.get(
            "real_runner_requires_confirmation"
        )
        is True,
        "baseline_final_handoff_does_not_read_local_env": baseline_final_handoff.get("local_env_content_read") is False,
        "baseline_final_handoff_rehearsal_passed": baseline_final_handoff_rehearsal.get("passed") is True,
        "baseline_final_handoff_rehearsal_command_count": baseline_final_handoff_rehearsal.get("command_count"),
        "baseline_final_handoff_rehearsal_synthetic_values_not_recorded": baseline_final_handoff_rehearsal.get(
            "synthetic_values_recorded"
        )
        is False,
        "baseline_final_handoff_rehearsal_temp_env_removed": baseline_final_handoff_rehearsal.get(
            "synthetic_env_file_removed_after_run"
        )
        is True,
        "baseline_final_handoff_rehearsal_workspace_restored": baseline_final_handoff_rehearsal.get(
            "workspace_state_restored_after_rehearsal"
        )
        is True,
        "baseline_final_handoff_rehearsal_parent_real_confirm_scrubbed": rehearsal_step3.get(
            "parent_real_confirm_present_in_subprocess_env"
        )
        is False,
        "baseline_final_handoff_rehearsal_confirmation_absent_after_scrub": rehearsal_step3.get(
            "confirmation_absent"
        )
        is True,
        "baseline_final_handoff_rehearsal_no_contact": not any(
            baseline_final_handoff_rehearsal.get("contact_flags", {}).values()
        ),
        "baseline_final_handoff_rehearsal_no_leak": not any(
            baseline_final_handoff_rehearsal.get("leak_flags", {}).values()
        ),
        "route_aware_submission_blockers_passed": route_aware_blockers.get("passed") is True,
        "route_aware_recommended_route": route_aware_blockers.get("recommended_route"),
        "route_aware_baseline_no_upload": route_aware_blockers.get("baseline_requires_checkpoint_upload") is False,
        "route_aware_baseline_no_link": route_aware_blockers.get("baseline_requires_checkpoint_link") is False,
        "route_aware_lora_web_needs_upload": route_aware_blockers.get("lora_web_requires_checkpoint_upload") is True,
        "route_aware_lora_web_needs_link": route_aware_blockers.get("lora_web_requires_checkpoint_link") is True,
        "route_aware_baseline_blocking_count": len(route_aware_blockers.get("baseline_current_blocking", [])),
        "jupyter_input_template_passed": jupyter_input.get("passed") is True,
        "jupyter_input_default_off": jupyter_input.get("run_flag_default_false") is True,
        "jupyter_local_env_ignored": jupyter_input.get("local_env_ignored", {}).get("ignored") is True,
        "jupyter_input_recommended_route": jupyter_input.get("recommended_route"),
        "jupyter_input_baseline_no_upload": jupyter_input.get("baseline_requires_checkpoint_upload") is False,
        "jupyter_input_baseline_no_link": jupyter_input.get("baseline_requires_checkpoint_link") is False,
        "jupyter_input_lora_web_needs_upload": jupyter_input.get("lora_web_requires_checkpoint_upload") is True,
        "jupyter_input_lora_web_needs_link": jupyter_input.get("lora_web_requires_checkpoint_link") is True,
        "jupyter_authorized_preflight_template_passed": jupyter_authorized.get("passed") is True,
        "jupyter_authorized_preflight_default_off": jupyter_authorized.get("execution_default_false") is True,
        "jupyter_authorized_preflight_audit_on": jupyter_authorized.get("audit_default_true") is True,
        "jupyter_authorized_recommended_route": jupyter_authorized.get("recommended_route"),
        "jupyter_authorized_baseline_no_upload": jupyter_authorized.get("baseline_requires_checkpoint_upload") is False,
        "jupyter_authorized_baseline_no_link": jupyter_authorized.get("baseline_requires_checkpoint_link") is False,
        "jupyter_authorized_lora_web_needs_upload": jupyter_authorized.get("lora_web_requires_checkpoint_upload")
        is True,
        "jupyter_authorized_lora_web_needs_link": jupyter_authorized.get("lora_web_requires_checkpoint_link")
        is True,
        "jupyter_final_handoff_template_passed": jupyter_final_handoff.get("passed") is True,
        "jupyter_final_handoff_audit_on": jupyter_final_handoff.get("audit_default_true") is True,
        "jupyter_final_handoff_packet_default_on": jupyter_final_handoff.get("packet_default_true") is True,
        "jupyter_final_handoff_real_runner_default_off": jupyter_final_handoff.get("real_runner_default_false")
        is True,
        "jupyter_final_handoff_command_count": jupyter_final_handoff.get("command_count"),
        "jupyter_final_handoff_no_contact_command_count": jupyter_final_handoff.get("no_contact_command_count"),
        "jupyter_final_handoff_real_runner_requires_confirmation": jupyter_final_handoff.get(
            "real_runner_requires_confirmation"
        )
        is True,
        "chinese_utf8_artifact_audit_passed": chinese_utf8.get("passed") is True,
        "chinese_utf8_artifact_scanned_file_count": chinese_utf8.get("scanned_file_count"),
        "chinese_utf8_artifact_decode_error_count": chinese_utf8.get("decode_error_count"),
        "chinese_utf8_artifact_bad_marker_hit_count": chinese_utf8.get("bad_marker_hit_count"),
        "chinese_utf8_artifact_required_phrases_present": all(
            item.get("present") is True for item in chinese_utf8.get("required_phrase_checks", {}).values()
        ),
        "authorized_execution_recommended_route": authorized_execution.get("recommended_route"),
        "authorized_execution_baseline_no_upload": authorized_execution.get("baseline_requires_checkpoint_upload") is False,
        "authorized_execution_baseline_no_link": authorized_execution.get("baseline_requires_checkpoint_link") is False,
        "authorized_execution_lora_web_needs_upload": authorized_execution.get("lora_web_requires_checkpoint_upload")
        is True,
        "authorized_execution_lora_web_needs_link": authorized_execution.get("lora_web_requires_checkpoint_link")
        is True,
        "uploads_performed": readiness.get("inputs", {}).get("uploads_performed"),
        "platform_contacted": False,
        "credentials_printed": False,
        "link_values_printed": False,
        "secret_values_printed": plaintext.get("secret_values_printed"),
        "critical_order_passed": sequence.get("commands", {}).get("critical_order_passed"),
        "blocking": route_aware_blockers.get("baseline_current_blocking") or readiness.get("blocking", []),
        "cards": cards,
    }


def render_html(status: dict[str, Any]) -> str:
    cards_html = []
    for item in status["cards"]:
        cards_html.append(
            f"""
            <article class="card {escape(item['state'])}">
              <div class="card-top">
                <span class="state">{escape(item['state_label'])}</span>
                <a href="../{escape(item['report'])}">报告</a>
              </div>
              <h2>{escape(item['title'])}</h2>
              <p class="value">{escape(item['value'])}</p>
              <p>{escape(item['detail'])}</p>
            </article>
            """
        )
    blocking_html = "".join(f"<li>{escape(item)}</li>" for item in status["blocking"])
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>RoboChallenge pi0.5 提交状态面板</title>
  <style>
    :root {{
      --ink: #16201b;
      --muted: #657067;
      --paper: #f2f5f1;
      --line: #cbd5cf;
      --done: #2f7d5b;
      --blocked: #b64b34;
      --watch: #8a6d24;
      --panel: #ffffff;
      --shadow: 0 16px 42px rgba(34, 54, 44, .12);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      font-family: "Aptos", "Segoe UI", "Microsoft YaHei", sans-serif;
      letter-spacing: 0;
    }}
    .shell {{ max-width: 1180px; margin: 0 auto; padding: 28px 22px 44px; }}
    header {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 18px;
      align-items: end;
      border-bottom: 2px solid var(--ink);
      padding-bottom: 18px;
    }}
    h1 {{ margin: 0; font-size: 30px; line-height: 1.1; font-weight: 800; }}
    .sub {{ margin: 10px 0 0; color: var(--muted); font-size: 14px; max-width: 760px; }}
    .stamp {{ font-size: 12px; color: var(--muted); text-align: right; }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 10px;
      margin: 18px 0;
    }}
    .metric {{
      background: var(--panel);
      border: 1px solid var(--line);
      padding: 12px;
      min-height: 86px;
    }}
    .metric b {{ display: block; font-size: 24px; margin-bottom: 8px; }}
    .metric span {{ color: var(--muted); font-size: 12px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin-top: 14px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-left: 6px solid var(--muted);
      padding: 14px 16px 16px;
      box-shadow: var(--shadow);
      min-height: 150px;
    }}
    .card.done {{ border-left-color: var(--done); }}
    .card.blocked {{ border-left-color: var(--blocked); }}
    .card.watch {{ border-left-color: var(--watch); }}
    .card-top {{ display: flex; justify-content: space-between; align-items: center; gap: 10px; }}
    .state {{
      font-size: 12px;
      font-weight: 700;
      padding: 4px 7px;
      border: 1px solid currentColor;
      color: var(--muted);
    }}
    .done .state {{ color: var(--done); }}
    .blocked .state {{ color: var(--blocked); }}
    .watch .state {{ color: var(--watch); }}
    a {{ color: var(--ink); text-decoration: underline; text-underline-offset: 3px; }}
    h2 {{ margin: 14px 0 8px; font-size: 18px; line-height: 1.2; }}
    p {{ margin: 0; color: var(--muted); line-height: 1.55; font-size: 14px; overflow-wrap: anywhere; }}
    .value {{ color: var(--ink); font-size: 21px; font-weight: 800; margin-bottom: 8px; overflow-wrap: anywhere; }}
    .blockers {{
      margin-top: 18px;
      background: #1f2924;
      color: #f5fff8;
      padding: 18px;
    }}
    .blockers h2 {{ margin-top: 0; color: #f5fff8; }}
    .blockers li {{ margin: 7px 0; line-height: 1.45; }}
    @media (max-width: 820px) {{
      header {{ grid-template-columns: 1fr; }}
      .stamp {{ text-align: left; }}
      .summary {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <header>
      <div>
        <h1>RoboChallenge pi0.5 提交状态面板</h1>
        <p class="sub">静态 GUI 汇总当前复现、LoRA checkpoint、上传/link/readiness 阻塞和授权后执行顺序。面板由 JSON 审计结果生成，不读取或显示真实凭据。</p>
      </div>
      <div class="stamp">生成时间<br>{escape(generated_at)}</div>
    </header>
    <section class="summary">
      <div class="metric"><b>{status['done_count']}</b><span>已完成项</span></div>
      <div class="metric"><b>{status['blocked_count']}</b><span>待授权项</span></div>
      <div class="metric"><b>{yes(status['ready_for_real_submission'])}</b><span>真实提交就绪</span></div>
      <div class="metric"><b>{yes(status['link_shape_ready'])}</b><span>checkpoint link 就绪</span></div>
      <div class="metric"><b>{yes(status['archive_created'])}</b><span>本地 tar 已生成</span></div>
    </section>
    <section class="grid">
      {''.join(cards_html)}
    </section>
    <section class="blockers">
      <h2>当前阻塞</h2>
      <ul>{blocking_html}</ul>
    </section>
  </main>
</body>
</html>
"""
    return "\n".join(line.rstrip() for line in html.splitlines()) + "\n"


def main() -> int:
    args = parse_args()
    data = {key: read_json(path) for key, path in SOURCE_FILES.items()}
    cards = build_cards(data)
    status = build_status(cards, data, args.html_path)
    args.html_path.parent.mkdir(parents=True, exist_ok=True)
    args.html_path.write_text(render_html(status), encoding="utf-8")
    args.status_path.parent.mkdir(parents=True, exist_ok=True)
    args.status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
