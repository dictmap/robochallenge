#!/usr/bin/env python3
"""Build a no-contact manifest for RoboChallenge submission-prep artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = ROOT / "runs"
DEFAULT_STATUS = RUNS_DIR / "submission_artifact_manifest.json"
DEFAULT_REPORT = REPORTS_DIR / "submission_artifact_manifest.md"

REQUIRED_ARTIFACTS = [
    "README.md",
    "work.md",
    "notebooks/robochallenge_pi05_submit_cn.ipynb",
    "submission/README.md",
    "submission/REAL_SUBMISSION_HANDOFF.md",
    "submission/AUTHORIZED_SUBMISSION_SEQUENCE.md",
    "submission/robochallenge_env_template.sh",
    "submission/submission_manifest_template.json",
    "submission/run_table30v2_aloha_demo_template.sh",
    "submission/run_table30v2_aloha_lora_demo_template.sh",
    "submission/run_authorized_preflight_template.sh",
    "submission/run_ready_real_submission_template.sh",
    "submission/run_authorized_checkpoint_archive_template.sh",
    "reports/pi05_base_repro.md",
    "reports/pi06_pi07_public_release_audit.md",
    "reports/table30_vs_table30v2.md",
    "reports/table30v2_aloha_mapping.md",
    "reports/table30v2_aloha_dry_run_converter.md",
    "reports/openpi_rtc_lora_inference_checkpoint_materialize.md",
    "reports/openpi_rtc_lora_materialized_policy_smoke.md",
    "reports/lora_checkpoint_export_readiness.md",
    "reports/checkpoint_archive_plan.md",
    "reports/checkpoint_split_plan.md",
    "reports/checkpoint_archive_dry_run.md",
    "reports/checkpoint_link_intake.md",
    "reports/checkpoint_link_download_verification.md",
    "reports/checkpoint_upload_channels_audit.md",
    "reports/real_submission_readiness.md",
    "reports/real_submission_readiness_scenarios.md",
    "reports/submission_env_template_audit.md",
    "reports/notebook_structure_audit.md",
    "reports/jupyter_input_template_audit.md",
    "reports/jupyter_authorized_preflight_template_audit.md",
    "reports/jupyter_final_handoff_template_audit.md",
    "reports/historical_notebook_checkpoint_outputs.md",
    "reports/chinese_utf8_artifact_audit.md",
    "reports/authorized_preflight_template_audit.md",
    "reports/ready_real_runner_template_audit.md",
    "reports/authorized_checkpoint_archive_template_audit.md",
    "reports/pi05_aloha_baseline_execution_packet.md",
    "reports/authorized_execution_checklist.md",
    "reports/next_user_action_packet.md",
    "reports/web_form_field_packet.md",
    "reports/submission_variant_route_packet.md",
    "reports/baseline_submission_quickstart.md",
    "reports/baseline_readonly_preflight_entry.md",
    "reports/readonly_preflight_jupyter_shell_parity.md",
    "reports/baseline_dry_run_gate.md",
    "reports/baseline_credential_hygiene.md",
    "reports/local_env_permission_contract.md",
    "reports/local_env_runtime_permission_gate.md",
    "reports/submission_variant_gate.md",
    "reports/boolean_env_gate.md",
    "reports/placeholder_credential_rejection.md",
    "reports/credential_whitespace_guard.md",
    "reports/synthetic_dry_run_redaction.md",
    "reports/shell_xtrace_secret_guard.md",
    "reports/baseline_local_env_smoke.md",
    "reports/baseline_final_handoff_packet.md",
    "reports/baseline_final_handoff_rehearsal.md",
    "reports/route_aware_submission_blockers.md",
    "reports/submission_target_confirmation_packet.md",
    "reports/submission_target_confirmation_gate.md",
    "reports/submission_handoff_docs_audit.md",
    "reports/authorized_submission_sequence_audit.md",
    "reports/submission_preflight_bundle.md",
    "reports/plaintext_secret_scan.md",
    "reports/submission_status_dashboard.html",
    "reports/submission_dashboard_links_audit.md",
    "reports/dashboard_http_static_preview.md",
    "reports/dashboard_gui_access_packet.md",
    "reports/submission_status_dashboard_browser.png",
    "scripts/render_next_user_action_packet.py",
    "scripts/render_web_form_field_packet.py",
    "scripts/render_submission_variant_route_packet.py",
    "scripts/render_baseline_submission_quickstart.py",
    "scripts/render_baseline_readonly_preflight_entry.py",
    "scripts/audit_readonly_preflight_jupyter_shell_parity.py",
    "scripts/render_baseline_dry_run_gate.py",
    "scripts/render_baseline_credential_hygiene.py",
    "scripts/audit_local_env_permission_contract.py",
    "scripts/audit_local_env_runtime_permission_gate.py",
    "scripts/audit_submission_variant_gate.py",
    "scripts/audit_boolean_env_gate.py",
    "scripts/audit_placeholder_credential_rejection.py",
    "scripts/audit_credential_whitespace_guard.py",
    "scripts/audit_synthetic_dry_run_redaction.py",
    "scripts/audit_shell_xtrace_secret_guard.py",
    "scripts/render_baseline_local_env_smoke.py",
    "scripts/render_baseline_final_handoff_packet.py",
    "scripts/render_baseline_final_handoff_rehearsal.py",
    "scripts/render_route_aware_submission_blockers.py",
    "scripts/render_submission_target_confirmation_packet.py",
    "scripts/audit_submission_target_confirmation_gate.py",
    "scripts/audit_submission_dashboard_links.py",
    "scripts/audit_jupyter_input_template.py",
    "scripts/audit_jupyter_authorized_preflight_template.py",
    "scripts/audit_jupyter_final_handoff_template.py",
    "scripts/audit_historical_notebook_checkpoint_outputs.py",
    "scripts/audit_chinese_utf8_artifacts.py",
    "scripts/audit_pi05_aloha_baseline_execution_packet.py",
    "scripts/audit_authorized_execution_checklist.py",
    "scripts/audit_dashboard_http_static_preview.py",
    "scripts/render_dashboard_gui_access_packet.py",
]

LOCAL_SECRET_OR_LARGE_PATHS = [
    "submission/robochallenge_env.local.sh",
    ".env",
    ".env.local",
    "runs/openpi_rtc_lora_materialized_policy_checkpoint",
    "runs/openpi_rtc_lora_materialized_policy_checkpoint.tar",
    "runs/openpi_rtc_lora_materialized_policy_checkpoint.tar.sha256",
    "runs/openpi_rtc_lora_materialized_policy_checkpoint.tar.part-aa",
]

FORBIDDEN_TRACKED_PREFIXES = [
    "submission/robochallenge_env.local.sh",
    ".env",
    ".env.local",
    "runs/openpi_rtc_lora_materialized_policy_checkpoint/",
    "runs/openpi_rtc_lora_materialized_policy_checkpoint.tar",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成提交准备材料 manifest；不读取凭据、不上传、不连接平台。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文审计报告输出路径。")
    return parser.parse_args()


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


def git_tracked_files() -> set[str]:
    result = run_git(["ls-files", "-z"])
    if result.returncode != 0:
        return set()
    return {item for item in result.stdout.split("\0") if item}


def git_check_ignore(rel: str) -> dict[str, Any]:
    result = run_git(["check-ignore", "-q", rel])
    return {"path": rel, "ignored": result.returncode == 0, "returncode": result.returncode}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def artifact_entry(rel: str, tracked: set[str]) -> dict[str, Any]:
    path = ROOT / rel
    exists = path.exists() and path.is_file()
    return {
        "path": rel,
        "exists": exists,
        "tracked": rel in tracked,
        "size_bytes": path.stat().st_size if exists else 0,
        "sha256": sha256_file(path) if exists else "",
    }


def build_status() -> dict[str, Any]:
    tracked = git_tracked_files()
    artifacts = [artifact_entry(rel, tracked) for rel in REQUIRED_ARTIFACTS]
    missing_required = [item["path"] for item in artifacts if not item["exists"]]
    unhashed = [item["path"] for item in artifacts if item["exists"] and len(item["sha256"]) != 64]
    forbidden_tracked = [
        path
        for path in tracked
        if any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in FORBIDDEN_TRACKED_PREFIXES)
    ]
    ignored_paths = {rel: git_check_ignore(rel) for rel in LOCAL_SECRET_OR_LARGE_PATHS}

    preflight = read_json(RUNS_DIR / "submission_preflight_bundle.json")
    pi05_aloha_execution = read_json(RUNS_DIR / "pi05_aloha_baseline_execution_packet.json")
    notebook_structure = read_json(RUNS_DIR / "notebook_structure_audit.json")
    jupyter_input = read_json(RUNS_DIR / "jupyter_input_template_audit.json")
    jupyter_authorized = read_json(RUNS_DIR / "jupyter_authorized_preflight_template_audit.json")
    jupyter_final_handoff = read_json(RUNS_DIR / "jupyter_final_handoff_template_audit.json")
    historical_notebook_outputs = read_json(RUNS_DIR / "historical_notebook_checkpoint_outputs.json")
    chinese_utf8 = read_json(RUNS_DIR / "chinese_utf8_artifact_audit.json")
    authorized_preflight = read_json(RUNS_DIR / "authorized_preflight_template_audit.json")
    ready_real_runner = read_json(RUNS_DIR / "ready_real_runner_template_audit.json")
    authorized_archive = read_json(RUNS_DIR / "authorized_checkpoint_archive_template_audit.json")
    authorized_execution = read_json(RUNS_DIR / "authorized_execution_checklist.json")
    action_packet = read_json(RUNS_DIR / "next_user_action_packet.json")
    web_form_packet = read_json(RUNS_DIR / "web_form_field_packet.json")
    route_packet = read_json(RUNS_DIR / "submission_variant_route_packet.json")
    baseline_quickstart = read_json(RUNS_DIR / "baseline_submission_quickstart.json")
    baseline_readonly_entry = read_json(RUNS_DIR / "baseline_readonly_preflight_entry.json")
    readonly_preflight_parity = read_json(RUNS_DIR / "readonly_preflight_jupyter_shell_parity.json")
    baseline_dry_run_gate = read_json(RUNS_DIR / "baseline_dry_run_gate.json")
    baseline_credential_hygiene = read_json(RUNS_DIR / "baseline_credential_hygiene.json")
    local_env_permission = read_json(RUNS_DIR / "local_env_permission_contract.json")
    local_env_runtime_permission = read_json(RUNS_DIR / "local_env_runtime_permission_gate.json")
    submission_variant_gate = read_json(RUNS_DIR / "submission_variant_gate.json")
    boolean_env_gate = read_json(RUNS_DIR / "boolean_env_gate.json")
    placeholder_credential_rejection = read_json(RUNS_DIR / "placeholder_credential_rejection.json")
    credential_whitespace_guard = read_json(RUNS_DIR / "credential_whitespace_guard.json")
    synthetic_dry_run_redaction = read_json(RUNS_DIR / "synthetic_dry_run_redaction.json")
    shell_xtrace_secret_guard = read_json(RUNS_DIR / "shell_xtrace_secret_guard.json")
    baseline_local_env_smoke = read_json(RUNS_DIR / "baseline_local_env_smoke.json")
    baseline_final_handoff = read_json(RUNS_DIR / "baseline_final_handoff_packet.json")
    baseline_final_handoff_rehearsal = read_json(RUNS_DIR / "baseline_final_handoff_rehearsal.json")
    route_aware_blockers = read_json(RUNS_DIR / "route_aware_submission_blockers.json")
    target_confirmation = read_json(RUNS_DIR / "submission_target_confirmation_packet.json")
    target_confirmation_gate = read_json(RUNS_DIR / "submission_target_confirmation_gate.json")
    readiness = read_json(RUNS_DIR / "real_submission_readiness.json")
    env_template = read_json(RUNS_DIR / "submission_env_template_audit.json")
    secret_scan = read_json(RUNS_DIR / "plaintext_secret_scan.json")
    dashboard_links = read_json(RUNS_DIR / "submission_dashboard_links_audit.json")
    dashboard_http_preview = read_json(RUNS_DIR / "dashboard_http_static_preview.json")
    dashboard_gui_access = read_json(RUNS_DIR / "dashboard_gui_access_packet.json")
    web_form_route_blocking_names = set(web_form_packet.get("recommended_route_blocking_names", []))

    inputs = {
        "preflight_status_available": bool(preflight),
        "preflight_go_no_go_blocked": preflight.get("go_no_go") == "blocked",
        "pi05_aloha_execution_passed": pi05_aloha_execution.get("passed") is True,
        "pi05_aloha_execution_recommended_baseline": pi05_aloha_execution.get("recommended_route")
        == "baseline_official_aloha",
        "pi05_aloha_execution_benchmark_table30v2": pi05_aloha_execution.get("target_benchmark") == "Table30v2",
        "pi05_aloha_execution_robot_aloha": pi05_aloha_execution.get("robot_type") == "aloha",
        "pi05_aloha_execution_task_exact": pi05_aloha_execution.get("task_name") == "pack_the_toothbrush_holder",
        "pi05_aloha_execution_checkpoint_exists": pi05_aloha_execution.get("checkpoint_exists") is True,
        "pi05_aloha_execution_state_shape": pi05_aloha_execution.get("dry_run_padded_state_shape") == [5, 32],
        "pi05_aloha_execution_actions_shape": pi05_aloha_execution.get("dry_run_padded_actions_shape")
        == [5, 50, 32],
        "pi05_aloha_execution_policy_smoke": pi05_aloha_execution.get("policy_smoke_exit_code") == 0
        and pi05_aloha_execution.get("policy_smoke_inference_count", 0) >= 2,
        "pi05_aloha_execution_no_contact": not any(pi05_aloha_execution.get("contact_flags", {}).values()),
        "pi05_aloha_execution_no_leak": not any(pi05_aloha_execution.get("leak_flags", {}).values()),
        "notebook_structure_passed": notebook_structure.get("passed") is True,
        "jupyter_input_template_passed": jupyter_input.get("passed") is True,
        "jupyter_input_recommended_baseline": jupyter_input.get("recommended_route") == "baseline_official_aloha",
        "jupyter_input_baseline_no_upload": jupyter_input.get("baseline_requires_checkpoint_upload") is False,
        "jupyter_input_baseline_no_link": jupyter_input.get("baseline_requires_checkpoint_link") is False,
        "jupyter_input_lora_web_needs_upload": jupyter_input.get("lora_web_requires_checkpoint_upload") is True,
        "jupyter_input_lora_web_needs_link": jupyter_input.get("lora_web_requires_checkpoint_link") is True,
        "jupyter_input_target_confirmation_value_exact": jupyter_input.get("target_confirmation_value")
        == "CONFIRM_TABLE30V2_ALOHA_BASELINE",
        "jupyter_input_target_confirmation_manual_input": jupyter_input.get(
            "target_confirmation_manual_input_required"
        )
        is True,
        "jupyter_input_target_confirmation_exact_match": jupyter_input.get(
            "target_confirmation_exact_match_required"
        )
        is True,
        "jupyter_authorized_preflight_template_passed": jupyter_authorized.get("passed") is True,
        "jupyter_authorized_recommended_baseline": jupyter_authorized.get("recommended_route")
        == "baseline_official_aloha",
        "jupyter_authorized_baseline_no_upload": jupyter_authorized.get("baseline_requires_checkpoint_upload") is False,
        "jupyter_authorized_baseline_no_link": jupyter_authorized.get("baseline_requires_checkpoint_link") is False,
        "jupyter_authorized_lora_web_needs_upload": jupyter_authorized.get("lora_web_requires_checkpoint_upload")
        is True,
        "jupyter_authorized_lora_web_needs_link": jupyter_authorized.get("lora_web_requires_checkpoint_link") is True,
        "jupyter_final_handoff_template_passed": jupyter_final_handoff.get("passed") is True,
        "jupyter_final_handoff_packet_default_true": jupyter_final_handoff.get("packet_default_true") is True,
        "jupyter_final_handoff_real_runner_default_false": jupyter_final_handoff.get(
            "real_runner_default_false"
        )
        is True,
        "jupyter_final_handoff_command_count": jupyter_final_handoff.get("command_count") == 4,
        "jupyter_final_handoff_no_contact_command_count": jupyter_final_handoff.get("no_contact_command_count")
        == 3,
        "jupyter_final_handoff_real_runner_requires_confirmation": jupyter_final_handoff.get(
            "real_runner_requires_confirmation"
        )
        is True,
        "historical_notebook_outputs_passed": historical_notebook_outputs.get("passed") is True,
        "historical_notebook_active_material_clean": historical_notebook_outputs.get(
            "active_material_stale_hit_count"
        )
        == 0,
        "historical_notebook_current_notebook_clean": historical_notebook_outputs.get(
            "current_notebook_stale_hit_count"
        )
        == 0,
        "historical_notebook_executed_outputs_classified": historical_notebook_outputs.get(
            "executed_notebook_historical_hit_count",
            0,
        )
        > 0,
        "historical_notebook_work_log_audit_only": historical_notebook_outputs.get(
            "work_log_mentions_are_audit_only"
        )
        is True,
        "chinese_utf8_artifact_audit_passed": chinese_utf8.get("passed") is True,
        "chinese_utf8_artifact_decode_error_count_zero": chinese_utf8.get("decode_error_count") == 0,
        "chinese_utf8_artifact_bad_marker_hit_count_zero": chinese_utf8.get("bad_marker_hit_count") == 0,
        "chinese_utf8_artifact_scanned_file_count": chinese_utf8.get("scanned_file_count", 0) >= 20,
        "authorized_preflight_template_passed": authorized_preflight.get("passed") is True,
        "ready_real_runner_template_passed": ready_real_runner.get("passed") is True,
        "authorized_checkpoint_archive_template_passed": authorized_archive.get("passed") is True,
        "authorized_execution_checklist_passed": authorized_execution.get("passed") is True,
        "authorized_execution_recommended_baseline": authorized_execution.get("recommended_route")
        == "baseline_official_aloha",
        "authorized_execution_baseline_no_upload": authorized_execution.get("baseline_requires_checkpoint_upload")
        is False,
        "authorized_execution_baseline_no_link": authorized_execution.get("baseline_requires_checkpoint_link") is False,
        "authorized_execution_lora_web_needs_upload": authorized_execution.get("lora_web_requires_checkpoint_upload")
        is True,
        "authorized_execution_lora_web_needs_link": authorized_execution.get("lora_web_requires_checkpoint_link")
        is True,
        "next_user_action_packet_passed": action_packet.get("passed") is True,
        "next_user_action_packet_recommended_baseline": action_packet.get("recommended_route")
        == "baseline_official_aloha",
        "next_user_action_packet_baseline_no_upload": action_packet.get("baseline_requires_checkpoint_upload") is False,
        "next_user_action_packet_baseline_no_link": action_packet.get("baseline_requires_checkpoint_link") is False,
        "next_user_action_packet_lora_web_needs_upload": action_packet.get("lora_web_requires_checkpoint_upload") is True,
        "next_user_action_packet_lora_web_needs_link": action_packet.get("lora_web_requires_checkpoint_link") is True,
        "next_user_action_packet_target_confirmation_value_exact": action_packet.get("target_confirmation_value")
        == "CONFIRM_TABLE30V2_ALOHA_BASELINE",
        "next_user_action_packet_target_not_user_confirmed": action_packet.get("target_user_confirmed") is False,
        "web_form_field_packet_passed": web_form_packet.get("passed") is True,
        "web_form_field_packet_currently_not_ready": web_form_packet.get("web_form_ready") is False,
        "web_form_field_packet_recommended_baseline": web_form_packet.get("recommended_route")
        == "baseline_official_aloha",
        "web_form_field_packet_baseline_excludes_checkpoint_link": web_form_packet.get(
            "baseline_route_excludes_checkpoint_link"
        )
        is True,
        "web_form_field_packet_baseline_excludes_checkpoint_archive": web_form_packet.get(
            "baseline_route_excludes_checkpoint_archive"
        )
        is True,
        "web_form_field_packet_route_blocking_no_checkpoint_link": "Checkpoint Link"
        not in web_form_route_blocking_names,
        "web_form_field_packet_route_blocking_no_checkpoint_archive": "Checkpoint Upload / Archive"
        not in web_form_route_blocking_names,
        "web_form_field_packet_target_confirmation_value_exact": web_form_packet.get("target_confirmation_value")
        == "CONFIRM_TABLE30V2_ALOHA_BASELINE",
        "web_form_field_packet_target_not_user_confirmed": web_form_packet.get("target_user_confirmed") is False,
        "web_form_field_packet_target_field_present": web_form_packet.get("target_confirmation_field_present")
        is True,
        "web_form_field_packet_target_required_for_baseline": web_form_packet.get(
            "target_confirmation_field_required_for_recommended_route"
        )
        is True,
        "web_form_field_packet_target_blocks_until_user_confirmed": web_form_packet.get(
            "target_confirmation_field_ready_for_recommended_route"
        )
        is False,
        "web_form_field_packet_route_blocking_has_target_confirmation": "Submission Target Confirmation"
        in web_form_route_blocking_names,
        "submission_target_confirmation_packet_passed": target_confirmation.get("passed") is True,
        "submission_target_confirmation_recommended_baseline": target_confirmation.get("recommended_route")
        == "baseline_official_aloha",
        "submission_target_confirmation_not_user_confirmed": target_confirmation.get("target_user_confirmed")
        is False,
        "submission_target_confirmation_does_not_confirm_for_user": target_confirmation.get(
            "does_not_confirm_for_user"
        )
        is True,
        "submission_target_confirmation_task_exact": target_confirmation.get("target", {}).get("task_name")
        == "pack_the_toothbrush_holder",
        "submission_target_confirmation_robot_exact": target_confirmation.get("target", {}).get("robot_type")
        == "aloha",
        "submission_target_confirmation_benchmark_exact": target_confirmation.get("target", {}).get("benchmark")
        == "Table30v2",
        "submission_target_confirmation_gate_passed": target_confirmation_gate.get("passed") is True,
        "submission_target_confirmation_gate_bad_rejected": target_confirmation_gate.get(
            "bad_confirmations_rejected"
        )
        is True,
        "submission_target_confirmation_gate_bad_stop_before_preflight": target_confirmation_gate.get(
            "bad_confirmations_stop_before_preflight"
        )
        is True,
        "submission_target_confirmation_gate_correct_accepted": target_confirmation_gate.get(
            "correct_confirmation_accepted"
        )
        is True,
        "submission_target_confirmation_gate_real_runner_not_started": target_confirmation_gate.get(
            "real_runner_started"
        )
        is False,
        "submission_variant_route_packet_passed": route_packet.get("passed") is True,
        "submission_variant_route_packet_baseline_default": route_packet.get("recommended_default")
        == "baseline_official_aloha",
        "submission_variant_route_packet_has_two_routes": route_packet.get("route_count") == 2,
        "submission_variant_route_packet_target_confirmation_value_exact": route_packet.get(
            "target_confirmation_value"
        )
        == "CONFIRM_TABLE30V2_ALOHA_BASELINE",
        "submission_variant_route_packet_baseline_blocking_has_target_confirmation": "SUBMISSION_TARGET_CONFIRMATION"
        in set(route_packet.get("baseline_current_blocking", [])),
        "baseline_submission_quickstart_passed": baseline_quickstart.get("passed") is True,
        "baseline_submission_quickstart_target_confirmation_value_exact": baseline_quickstart.get(
            "target_confirmation_value"
        )
        == "CONFIRM_TABLE30V2_ALOHA_BASELINE",
        "baseline_submission_quickstart_target_confirmation_manual_input": baseline_quickstart.get(
            "target_confirmation_manual_input_required"
        )
        is True,
        "baseline_submission_quickstart_target_confirmation_exact_match": baseline_quickstart.get(
            "target_confirmation_exact_match_required"
        )
        is True,
        "baseline_submission_quickstart_no_upload": baseline_quickstart.get("requires_checkpoint_upload") is False,
        "baseline_submission_quickstart_no_link": baseline_quickstart.get("requires_checkpoint_link") is False,
        "baseline_readonly_entry_passed": baseline_readonly_entry.get("passed") is True,
        "baseline_readonly_entry_command_exact": baseline_readonly_entry.get("readonly_preflight_command")
        == "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_authorized_preflight_template.sh",
        "baseline_readonly_entry_no_upload": baseline_readonly_entry.get("requires_checkpoint_upload") is False,
        "baseline_readonly_entry_no_link": baseline_readonly_entry.get("requires_checkpoint_link") is False,
        "baseline_readonly_entry_real_confirm_not_required": baseline_readonly_entry.get(
            "real_runner_confirm_required_for_readonly_preflight"
        )
        is False,
        "baseline_readonly_entry_real_confirm_required_for_submission": baseline_readonly_entry.get(
            "real_runner_confirm_required_for_real_submission"
        )
        is True,
        "baseline_readonly_entry_target_confirmation_value_exact": baseline_readonly_entry.get(
            "target_confirmation_value"
        )
        == "CONFIRM_TABLE30V2_ALOHA_BASELINE",
        "readonly_preflight_jupyter_shell_parity_passed": readonly_preflight_parity.get("passed") is True,
        "readonly_preflight_routes_converge": readonly_preflight_parity.get("routes_converge_to_same_wrapper")
        is True,
        "readonly_preflight_no_upload": readonly_preflight_parity.get("requires_checkpoint_upload") is False,
        "readonly_preflight_no_link": readonly_preflight_parity.get("requires_checkpoint_link") is False,
        "baseline_dry_run_gate_passed": baseline_dry_run_gate.get("passed") is True,
        "baseline_dry_run_gate_no_upload": baseline_dry_run_gate.get("requires_checkpoint_upload") is False,
        "baseline_dry_run_gate_no_link": baseline_dry_run_gate.get("requires_checkpoint_link") is False,
        "baseline_dry_run_gate_command_exact": baseline_dry_run_gate.get("dry_run_gate_command")
        == "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_ready_real_submission_template.sh",
        "baseline_dry_run_gate_stops_before_real_runner": baseline_dry_run_gate.get(
            "stops_before_real_runner_without_confirmation"
        )
        is True,
        "baseline_dry_run_gate_wrong_confirm_stops_before_real_runner": baseline_dry_run_gate.get(
            "stops_before_real_runner_with_wrong_confirmation"
        )
        is True,
        "baseline_dry_run_gate_malformed_confirm_stops_before_real_runner": baseline_dry_run_gate.get(
            "stops_before_real_runner_with_malformed_confirmation"
        )
        is True,
        "baseline_credential_hygiene_passed": baseline_credential_hygiene.get("passed") is True,
        "baseline_credential_hygiene_local_env_gitignored": baseline_credential_hygiene.get(
            "local_env_gitignored"
        )
        is True,
        "baseline_credential_hygiene_local_env_not_tracked": baseline_credential_hygiene.get(
            "local_env_tracked"
        )
        is False,
        "baseline_credential_hygiene_does_not_read_local_env": baseline_credential_hygiene.get(
            "local_env_content_read"
        )
        is False,
        "baseline_credential_hygiene_no_upload": baseline_credential_hygiene.get("requires_checkpoint_upload")
        is False,
        "baseline_credential_hygiene_no_link": baseline_credential_hygiene.get("requires_checkpoint_link")
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
        "submission_variant_gate_passed": submission_variant_gate.get("passed") is True,
        "submission_variant_bad_rejected": submission_variant_gate.get("bad_variants_rejected") is True,
        "submission_variant_bad_stop_before_preflight": submission_variant_gate.get(
            "bad_variants_stop_before_preflight"
        )
        is True,
        "submission_variant_valid_accepted": submission_variant_gate.get("valid_variants_accepted") is True,
        "submission_variant_real_runner_not_started": submission_variant_gate.get("real_runner_started") is False,
        "submission_variant_values_not_recorded": submission_variant_gate.get("synthetic_values_recorded")
        is False,
        "boolean_env_gate_passed": boolean_env_gate.get("passed") is True,
        "boolean_env_bad_rejected": boolean_env_gate.get("bad_flags_rejected") is True,
        "boolean_env_bad_stop_before_preflight": boolean_env_gate.get("bad_flags_stop_before_preflight") is True,
        "boolean_env_valid_accepted": boolean_env_gate.get("valid_flags_accepted") is True,
        "boolean_env_real_runner_not_started": boolean_env_gate.get("real_runner_started") is False,
        "boolean_env_values_not_recorded": boolean_env_gate.get("synthetic_values_recorded") is False,
        "placeholder_credential_rejection_passed": placeholder_credential_rejection.get("passed") is True,
        "placeholder_credential_rejection_case_count": placeholder_credential_rejection.get("case_count") == 4,
        "placeholder_baseline_rejected_before_dry_run": placeholder_credential_rejection.get(
            "baseline_placeholder_rejected"
        )
        is True
        and placeholder_credential_rejection.get("baseline_stops_before_dry_run") is True,
        "placeholder_lora_rejected_before_dry_run": placeholder_credential_rejection.get(
            "lora_placeholder_rejected"
        )
        is True
        and placeholder_credential_rejection.get("lora_stops_before_dry_run") is True,
        "placeholder_baseline_real_runner_not_started": placeholder_credential_rejection.get(
            "baseline_real_runner_not_started"
        )
        is True,
        "placeholder_lora_real_runner_not_started": placeholder_credential_rejection.get(
            "lora_real_runner_not_started"
        )
        is True,
        "placeholder_values_not_recorded": placeholder_credential_rejection.get("placeholder_values_recorded")
        is False,
        "credential_whitespace_guard_passed": credential_whitespace_guard.get("passed") is True,
        "credential_whitespace_bad_rejected": credential_whitespace_guard.get("bad_credentials_rejected") is True,
        "credential_whitespace_clean_dry_run_passed": credential_whitespace_guard.get(
            "clean_credentials_dry_run_passed"
        )
        is True,
        "credential_whitespace_real_runner_not_started": credential_whitespace_guard.get("real_runner_started")
        is False,
        "credential_whitespace_values_not_recorded": credential_whitespace_guard.get("synthetic_values_recorded")
        is False,
        "synthetic_dry_run_redaction_passed": synthetic_dry_run_redaction.get("passed") is True,
        "synthetic_dry_run_case_count": synthetic_dry_run_redaction.get("case_count") == 2,
        "synthetic_dry_run_baseline_passed": synthetic_dry_run_redaction.get("baseline_dry_run_passed") is True,
        "synthetic_dry_run_lora_passed": synthetic_dry_run_redaction.get("lora_dry_run_passed") is True,
        "synthetic_dry_run_baseline_lengths_only": synthetic_dry_run_redaction.get(
            "baseline_outputs_lengths_only"
        )
        is True,
        "synthetic_dry_run_lora_lengths_only": synthetic_dry_run_redaction.get("lora_outputs_lengths_only")
        is True,
        "synthetic_dry_run_baseline_runner_not_started": synthetic_dry_run_redaction.get(
            "baseline_real_runner_not_started"
        )
        is True,
        "synthetic_dry_run_lora_runner_not_started": synthetic_dry_run_redaction.get(
            "lora_real_runner_not_started"
        )
        is True,
        "synthetic_dry_run_values_not_recorded": synthetic_dry_run_redaction.get("synthetic_values_recorded")
        is False,
        "shell_xtrace_secret_guard_passed": shell_xtrace_secret_guard.get("passed") is True,
        "shell_xtrace_templates_disable_xtrace": shell_xtrace_secret_guard.get("evidence", {}).get(
            "all_templates_disable_xtrace_first"
        )
        is True,
        "shell_xtrace_cases_saw_set_plus_x": shell_xtrace_secret_guard.get("evidence", {}).get(
            "all_cases_saw_set_plus_x_trace"
        )
        is True,
        "shell_xtrace_stops_trace_after_guard": shell_xtrace_secret_guard.get("evidence", {}).get(
            "all_cases_stop_trace_after_guard"
        )
        is True,
        "shell_xtrace_no_protected_values": shell_xtrace_secret_guard.get("evidence", {}).get(
            "all_cases_no_protected_values"
        )
        is True,
        "shell_xtrace_demo_dry_runs_passed": shell_xtrace_secret_guard.get("evidence", {}).get(
            "demo_dry_runs_passed"
        )
        is True,
        "shell_xtrace_ready_runner_blocks_real_runner": shell_xtrace_secret_guard.get("evidence", {}).get(
            "ready_runner_stops_before_real_runner"
        )
        is True,
        "shell_xtrace_values_not_recorded": shell_xtrace_secret_guard.get("synthetic_values_recorded") is False,
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
        "baseline_final_handoff_command_count": baseline_final_handoff.get("command_count") == 4,
        "baseline_final_handoff_no_contact_command_count": baseline_final_handoff.get("no_contact_command_count")
        == 3,
        "baseline_final_handoff_real_runner_requires_confirmation": baseline_final_handoff.get(
            "real_runner_requires_confirmation"
        )
        is True,
        "baseline_final_handoff_does_not_read_local_env": baseline_final_handoff.get("local_env_content_read")
        is False,
        "baseline_final_handoff_target_confirmation_value_exact": baseline_final_handoff.get(
            "target_confirmation_value"
        )
        == "CONFIRM_TABLE30V2_ALOHA_BASELINE",
        "baseline_final_handoff_target_not_user_confirmed": baseline_final_handoff.get("target_user_confirmed")
        is False,
        "baseline_final_handoff_rehearsal_passed": baseline_final_handoff_rehearsal.get("passed") is True,
        "baseline_final_handoff_rehearsal_command_count": baseline_final_handoff_rehearsal.get("command_count")
        == 3,
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
        "baseline_final_handoff_rehearsal_parent_real_confirm_scrubbed": (
            (baseline_final_handoff_rehearsal.get("commands", []) + [{}, {}, {}])[2].get(
                "parent_real_confirm_present_in_subprocess_env"
            )
            is False
        ),
        "baseline_final_handoff_rehearsal_confirmation_absent_after_scrub": (
            (baseline_final_handoff_rehearsal.get("commands", []) + [{}, {}, {}])[2].get("confirmation_absent")
            is True
        ),
        "route_aware_submission_blockers_passed": route_aware_blockers.get("passed") is True,
        "route_aware_recommended_baseline": route_aware_blockers.get("recommended_route") == "baseline_official_aloha",
        "route_aware_baseline_no_upload": route_aware_blockers.get("baseline_requires_checkpoint_upload") is False,
        "route_aware_baseline_no_link": route_aware_blockers.get("baseline_requires_checkpoint_link") is False,
        "route_aware_lora_web_needs_upload": route_aware_blockers.get("lora_web_requires_checkpoint_upload") is True,
        "route_aware_lora_web_needs_link": route_aware_blockers.get("lora_web_requires_checkpoint_link") is True,
        "readiness_currently_blocked": readiness.get("ready_for_real_submission") is False,
        "env_template_passed": env_template.get("passed") is True,
        "dashboard_links_audit_passed": dashboard_links.get("passed") is True,
        "dashboard_links_all_reports_exist": dashboard_links.get("missing_report_count") == 0,
        "dashboard_links_all_local": dashboard_links.get("nonlocal_report_count") == 0,
        "dashboard_links_html_hrefs_rendered": dashboard_links.get("missing_html_href_count") == 0,
        "dashboard_links_card_count": dashboard_links.get("card_count", 0) >= 38,
        "dashboard_http_static_preview_passed": dashboard_http_preview.get("passed") is True,
        "dashboard_http_static_preview_loopback": dashboard_http_preview.get("http_preview_host") == "127.0.0.1",
        "dashboard_http_static_preview_card_count_matches": dashboard_http_preview.get("evidence", {}).get(
            "http_card_count_matches_dashboard"
        )
        is True,
        "dashboard_http_static_preview_no_external_hrefs": dashboard_http_preview.get("external_href_count") == 0,
        "dashboard_gui_access_packet_passed": dashboard_gui_access.get("passed") is True,
        "dashboard_gui_access_html_path_exact": dashboard_gui_access.get("gui_html_path")
        == "reports/submission_status_dashboard.html",
        "dashboard_gui_access_browser_not_blocked": dashboard_gui_access.get("browser_visual_blocked_by_policy")
        is False,
        "dashboard_gui_access_screenshot_created": dashboard_gui_access.get("screenshot_created") is True,
        "dashboard_gui_access_screenshot_path_exact": dashboard_gui_access.get("screenshot_path")
        == "reports/submission_status_dashboard_browser.png",
        "dashboard_gui_access_screenshot_size_current": dashboard_gui_access.get("screenshot_size_bytes", 0)
        > 10_000,
        "dashboard_gui_access_card_count_current": dashboard_gui_access.get("dashboard_card_count", 0) >= 39,
        "secret_scan_passed": secret_scan.get("passed") is True,
        "secret_scan_hit_count_zero": secret_scan.get("hit_count") == 0,
    }
    leak_flags = {
        "credentials_printed": any(
            bool(item.get("credentials_printed"))
            for item in [
                preflight,
                pi05_aloha_execution,
                notebook_structure,
                jupyter_input,
                jupyter_authorized,
                jupyter_final_handoff,
                chinese_utf8,
                authorized_preflight,
                ready_real_runner,
                authorized_archive,
                authorized_execution,
                action_packet,
                web_form_packet,
                route_packet,
                baseline_quickstart,
                baseline_readonly_entry,
                readonly_preflight_parity,
                baseline_dry_run_gate,
                baseline_credential_hygiene,
                local_env_permission,
                local_env_runtime_permission,
                submission_variant_gate,
                boolean_env_gate,
                placeholder_credential_rejection,
                credential_whitespace_guard,
                synthetic_dry_run_redaction,
                shell_xtrace_secret_guard,
                baseline_local_env_smoke,
                baseline_final_handoff,
                baseline_final_handoff_rehearsal,
                route_aware_blockers,
                target_confirmation,
                target_confirmation_gate,
                readiness,
                env_template,
                dashboard_http_preview,
                dashboard_gui_access,
            ]
        ),
        "link_values_printed": bool(preflight.get("leak_flags", {}).get("link_values_printed"))
        or bool(pi05_aloha_execution.get("link_values_printed"))
        or bool(jupyter_input.get("link_values_printed"))
        or bool(jupyter_authorized.get("link_values_printed"))
        or bool(jupyter_final_handoff.get("link_values_printed"))
        or bool(chinese_utf8.get("link_values_printed"))
        or bool(authorized_preflight.get("link_values_printed"))
        or bool(ready_real_runner.get("link_values_printed"))
        or bool(authorized_archive.get("link_values_printed"))
        or bool(authorized_execution.get("link_values_printed"))
        or bool(action_packet.get("link_values_printed"))
        or bool(web_form_packet.get("link_values_printed"))
        or bool(route_packet.get("link_values_printed"))
        or bool(baseline_quickstart.get("link_values_printed"))
        or bool(baseline_readonly_entry.get("link_values_printed"))
        or bool(readonly_preflight_parity.get("link_values_printed"))
        or bool(baseline_dry_run_gate.get("link_values_printed"))
        or bool(baseline_credential_hygiene.get("link_values_printed"))
        or bool(local_env_permission.get("link_values_printed"))
        or bool(local_env_runtime_permission.get("link_values_printed"))
        or bool(submission_variant_gate.get("link_values_printed"))
        or bool(boolean_env_gate.get("link_values_printed"))
        or bool(placeholder_credential_rejection.get("link_values_printed"))
        or bool(credential_whitespace_guard.get("link_values_printed"))
        or bool(synthetic_dry_run_redaction.get("link_values_printed"))
        or bool(shell_xtrace_secret_guard.get("link_values_printed"))
        or bool(baseline_local_env_smoke.get("link_values_printed"))
        or bool(baseline_final_handoff.get("link_values_printed"))
        or bool(baseline_final_handoff_rehearsal.get("link_values_printed"))
        or bool(route_aware_blockers.get("link_values_printed"))
        or bool(target_confirmation.get("link_values_printed"))
        or bool(target_confirmation_gate.get("link_values_printed"))
        or bool(dashboard_http_preview.get("link_values_printed"))
        or bool(dashboard_gui_access.get("link_values_printed")),
        "secret_values_printed": bool(secret_scan.get("secret_values_printed"))
        or bool(pi05_aloha_execution.get("secret_values_printed"))
        or bool(jupyter_input.get("secret_values_printed"))
        or bool(jupyter_authorized.get("secret_values_printed"))
        or bool(jupyter_final_handoff.get("secret_values_printed"))
        or bool(chinese_utf8.get("secret_values_printed"))
        or bool(action_packet.get("secret_values_printed"))
        or bool(web_form_packet.get("secret_values_printed"))
        or bool(route_packet.get("secret_values_printed"))
        or bool(baseline_quickstart.get("secret_values_printed"))
        or bool(baseline_readonly_entry.get("secret_values_printed"))
        or bool(readonly_preflight_parity.get("secret_values_printed"))
        or bool(baseline_dry_run_gate.get("secret_values_printed"))
        or bool(baseline_credential_hygiene.get("secret_values_printed"))
        or bool(local_env_permission.get("secret_values_printed"))
        or bool(local_env_runtime_permission.get("secret_values_printed"))
        or bool(submission_variant_gate.get("secret_values_printed"))
        or bool(boolean_env_gate.get("secret_values_printed"))
        or bool(placeholder_credential_rejection.get("secret_values_printed"))
        or bool(credential_whitespace_guard.get("secret_values_printed"))
        or bool(synthetic_dry_run_redaction.get("secret_values_printed"))
        or bool(shell_xtrace_secret_guard.get("secret_values_printed"))
        or bool(baseline_local_env_smoke.get("secret_values_printed"))
        or bool(baseline_final_handoff.get("secret_values_printed"))
        or bool(baseline_final_handoff_rehearsal.get("secret_values_printed"))
        or bool(route_aware_blockers.get("secret_values_printed"))
        or bool(target_confirmation.get("secret_values_printed"))
        or bool(target_confirmation_gate.get("secret_values_printed"))
        or bool(dashboard_http_preview.get("secret_values_printed"))
        or bool(dashboard_gui_access.get("secret_values_printed")),
    }
    contact_flags = {
        "platform_contacted": any(
            bool(item.get("platform_contacted"))
            for item in [
                preflight,
                pi05_aloha_execution,
                notebook_structure,
                jupyter_input,
                jupyter_authorized,
                jupyter_final_handoff,
                chinese_utf8,
                authorized_preflight,
                ready_real_runner,
                authorized_archive,
                authorized_execution,
                action_packet,
                web_form_packet,
                route_packet,
                baseline_quickstart,
                baseline_readonly_entry,
                readonly_preflight_parity,
                baseline_dry_run_gate,
                baseline_credential_hygiene,
                local_env_permission,
                local_env_runtime_permission,
                submission_variant_gate,
                boolean_env_gate,
                placeholder_credential_rejection,
                credential_whitespace_guard,
                synthetic_dry_run_redaction,
                shell_xtrace_secret_guard,
                baseline_local_env_smoke,
                baseline_final_handoff,
                baseline_final_handoff_rehearsal,
                route_aware_blockers,
                target_confirmation,
                target_confirmation_gate,
                readiness,
                env_template,
                secret_scan,
                dashboard_http_preview,
                dashboard_gui_access,
            ]
        ),
        "uploads_performed": any(
            bool(item.get("uploads_performed") or item.get("upload_performed"))
            for item in [
                preflight,
                pi05_aloha_execution,
                notebook_structure,
                jupyter_input,
                jupyter_authorized,
                jupyter_final_handoff,
                chinese_utf8,
                authorized_preflight,
                ready_real_runner,
                authorized_archive,
                authorized_execution,
                action_packet,
                web_form_packet,
                route_packet,
                baseline_quickstart,
                baseline_readonly_entry,
                readonly_preflight_parity,
                baseline_dry_run_gate,
                baseline_credential_hygiene,
                local_env_permission,
                local_env_runtime_permission,
                submission_variant_gate,
                boolean_env_gate,
                placeholder_credential_rejection,
                credential_whitespace_guard,
                synthetic_dry_run_redaction,
                shell_xtrace_secret_guard,
                baseline_local_env_smoke,
                baseline_final_handoff,
                baseline_final_handoff_rehearsal,
                route_aware_blockers,
                target_confirmation,
                target_confirmation_gate,
                readiness,
                env_template,
                secret_scan,
                dashboard_http_preview,
                dashboard_gui_access,
            ]
        ),
        "download_host_contacted": bool(preflight.get("contact_flags", {}).get("download_host_contacted"))
        or bool(pi05_aloha_execution.get("contact_flags", {}).get("download_host_contacted"))
        or bool(baseline_readonly_entry.get("contact_flags", {}).get("download_host_contacted"))
        or bool(readonly_preflight_parity.get("contact_flags", {}).get("download_host_contacted"))
        or bool(dashboard_http_preview.get("contact_flags", {}).get("download_host_contacted"))
        or bool(dashboard_gui_access.get("contact_flags", {}).get("download_host_contacted")),
        "external_network_contacted": bool(
            dashboard_http_preview.get("contact_flags", {}).get("external_network_contacted")
        )
        or bool(pi05_aloha_execution.get("contact_flags", {}).get("external_network_contacted")),
    }
    blocking = []
    if missing_required:
        blocking.append("提交准备材料 manifest 缺少必需文件。")
    if unhashed:
        blocking.append("部分提交准备材料未生成 sha256。")
    if forbidden_tracked:
        blocking.append("检测到禁止进入 Git 的本地凭据或大 checkpoint 路径已被跟踪。")
    if not all(item["ignored"] for item in ignored_paths.values()):
        blocking.append("部分本地凭据或大文件路径未被 Git 忽略。")
    for name, ok in inputs.items():
        if not ok:
            blocking.append(f"输入审计证据未通过 `{name}`。")
    if any(leak_flags.values()):
        blocking.append("输入审计显示存在凭据或链接明文泄露风险。")
    if any(contact_flags.values()):
        blocking.append("输入审计显示曾连接平台、上传或接触下载 host。")
    if not blocking:
        blocking.append(
            "提交准备材料 manifest 已完整；baseline runner 仍需要用户目标确认、token、submission id、"
            "variant=baseline 和真实 runner 强确认；LoRA 或网页 checkpoint 路线仍需要上传授权和 checkpoint link。"
        )

    passed = bool(
        not missing_required
        and not unhashed
        and not forbidden_tracked
        and all(item["ignored"] for item in ignored_paths.values())
        and all(inputs.values())
        and not any(leak_flags.values())
        and not any(contact_flags.values())
    )
    return {
        "kind": "submission_artifact_manifest",
        "passed": passed,
        "platform_contacted": False,
        "uploads_performed": False,
        "credentials_read": False,
        "credentials_printed": False,
        "link_values_printed": False,
        "secret_values_printed": False,
        "pi05_aloha_execution_passed": pi05_aloha_execution.get("passed") is True,
        "pi05_aloha_policy_smoke_inference_count": pi05_aloha_execution.get("policy_smoke_inference_count"),
        "pi05_aloha_no_contact": not any(pi05_aloha_execution.get("contact_flags", {}).values()),
        "pi05_aloha_no_leak": not any(pi05_aloha_execution.get("leak_flags", {}).values()),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "missing_required_artifacts": missing_required,
        "unhashed_artifacts": unhashed,
        "forbidden_tracked_paths": forbidden_tracked,
        "ignored_local_secret_or_large_paths": ignored_paths,
        "inputs": inputs,
        "leak_flags": leak_flags,
        "contact_flags": contact_flags,
        "blocking": blocking,
    }


def write_report(status: dict[str, Any], path: Path) -> None:
    lines = [
        "# 提交准备材料 manifest 审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 材料数量：`{status['artifact_count']}`。",
        f"- 缺失材料数量：`{len(status['missing_required_artifacts'])}`。",
        f"- 禁止跟踪路径数量：`{len(status['forbidden_tracked_paths'])}`。",
        f"- 是否连接平台：`{status['platform_contacted']}`。",
        f"- 是否执行上传：`{status['uploads_performed']}`。",
        f"- 是否读取真实凭据：`{status['credentials_read']}`。",
        f"- 是否打印真实凭据或链接：`{status['credentials_printed'] or status['link_values_printed'] or status['secret_values_printed']}`。",
        "",
        "## 材料清单",
        "",
    ]
    for item in status["artifacts"]:
        lines.append(
            f"- `{item['path']}`：exists=`{item['exists']}`，tracked=`{item['tracked']}`，"
            f"size=`{item['size_bytes']}`，sha256=`{item['sha256']}`。"
        )
    lines.extend(["", "## 本地凭据与大文件忽略检查", ""])
    for rel, item in status["ignored_local_secret_or_large_paths"].items():
        lines.append(f"- `{rel}`：ignored=`{item['ignored']}`。")
    lines.extend(["", "## 输入证据", ""])
    for key, ok in status["inputs"].items():
        lines.append(f"- `{key}`：`{ok}`。")
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
