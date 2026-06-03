#!/usr/bin/env python3
"""Run a no-contact submission preflight bundle and summarize go/no-go state."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
DEFAULT_STATUS = RUNS_DIR / "submission_preflight_bundle.json"
DEFAULT_REPORT = REPORTS_DIR / "submission_preflight_bundle.md"

SUBCOMMANDS = [
    ("checkpoint_link_intake", "scripts/audit_checkpoint_link_intake.py"),
    ("checkpoint_link_download_verification", "scripts/audit_checkpoint_link_download_verification.py"),
    ("submission_env_template", "scripts/audit_submission_env_template.py"),
    ("notebook_structure", "scripts/audit_notebook_structure.py"),
    ("jupyter_input_template", "scripts/audit_jupyter_input_template.py"),
    ("jupyter_authorized_preflight_template", "scripts/audit_jupyter_authorized_preflight_template.py"),
    ("jupyter_final_handoff_template", "scripts/audit_jupyter_final_handoff_template.py"),
    ("historical_notebook_checkpoint_outputs", "scripts/audit_historical_notebook_checkpoint_outputs.py"),
    ("chinese_utf8_artifacts", "scripts/audit_chinese_utf8_artifacts.py"),
    ("real_submission_readiness", "scripts/audit_real_submission_readiness.py"),
    ("authorized_preflight_template", "scripts/audit_authorized_preflight_template.py"),
    ("ready_real_runner_template", "scripts/audit_ready_real_runner_template.py"),
    ("authorized_checkpoint_archive_template", "scripts/audit_authorized_checkpoint_archive_template.py"),
    ("plaintext_secret_scan", "scripts/audit_plaintext_secrets.py"),
    ("submission_variant_route_packet", "scripts/render_submission_variant_route_packet.py"),
    ("baseline_submission_quickstart", "scripts/render_baseline_submission_quickstart.py"),
    ("baseline_readonly_preflight_entry", "scripts/render_baseline_readonly_preflight_entry.py"),
    ("readonly_preflight_jupyter_shell_parity", "scripts/audit_readonly_preflight_jupyter_shell_parity.py"),
    ("submission_target_confirmation_packet", "scripts/render_submission_target_confirmation_packet.py"),
    ("submission_target_confirmation_gate", "scripts/audit_submission_target_confirmation_gate.py"),
    ("authorized_execution_checklist", "scripts/audit_authorized_execution_checklist.py"),
    ("next_user_action_packet", "scripts/render_next_user_action_packet.py"),
    ("web_form_field_packet", "scripts/render_web_form_field_packet.py"),
    ("route_aware_submission_blockers", "scripts/render_route_aware_submission_blockers.py"),
    ("baseline_dry_run_gate", "scripts/render_baseline_dry_run_gate.py"),
    ("baseline_credential_hygiene", "scripts/render_baseline_credential_hygiene.py"),
    ("local_env_permission_contract", "scripts/audit_local_env_permission_contract.py"),
    ("local_env_runtime_permission_gate", "scripts/audit_local_env_runtime_permission_gate.py"),
    ("submission_variant_gate", "scripts/audit_submission_variant_gate.py"),
    ("boolean_env_gate", "scripts/audit_boolean_env_gate.py"),
    ("placeholder_credential_rejection", "scripts/audit_placeholder_credential_rejection.py"),
    ("credential_whitespace_guard", "scripts/audit_credential_whitespace_guard.py"),
    ("synthetic_dry_run_redaction", "scripts/audit_synthetic_dry_run_redaction.py"),
    ("shell_xtrace_secret_guard", "scripts/audit_shell_xtrace_secret_guard.py"),
    ("baseline_local_env_smoke", "scripts/render_baseline_local_env_smoke.py"),
    ("baseline_final_handoff_packet", "scripts/render_baseline_final_handoff_packet.py"),
    ("baseline_final_handoff_rehearsal", "scripts/render_baseline_final_handoff_rehearsal.py"),
    ("submission_handoff_docs", "scripts/audit_submission_handoff_docs.py"),
    ("dashboard_gui_access_packet", "scripts/render_dashboard_gui_access_packet.py"),
    ("submission_artifact_manifest", "scripts/audit_submission_artifact_manifest.py"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行真实提交前只读预检汇总；不上传、不连接平台、不打印凭据。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文审计报告输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def run_subcommand(name: str, script: str) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, script],
        cwd=ROOT,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=600,
    )
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    if name == "historical_notebook_checkpoint_outputs":
        stdout_tail = "[historical notebook checkpoint output audit summarized; see runs/historical_notebook_checkpoint_outputs.json]"
    else:
        stdout_tail = stdout[-1000:]
    return {
        "script": script,
        "returncode": result.returncode,
        "passed": result.returncode == 0,
        "stdout_tail": stdout_tail,
        "stderr_tail": stderr[-1000:],
    }


def build_status() -> dict[str, Any]:
    subcommands = {name: run_subcommand(name, script) for name, script in SUBCOMMANDS}
    link_intake = read_json(RUNS_DIR / "checkpoint_link_intake.json")
    link_download = read_json(RUNS_DIR / "checkpoint_link_download_verification.json")
    artifact_manifest = read_json(RUNS_DIR / "submission_artifact_manifest.json")
    notebook_structure = read_json(RUNS_DIR / "notebook_structure_audit.json")
    jupyter_input = read_json(RUNS_DIR / "jupyter_input_template_audit.json")
    jupyter_authorized = read_json(RUNS_DIR / "jupyter_authorized_preflight_template_audit.json")
    jupyter_final_handoff = read_json(RUNS_DIR / "jupyter_final_handoff_template_audit.json")
    historical_notebook_outputs = read_json(RUNS_DIR / "historical_notebook_checkpoint_outputs.json")
    chinese_utf8 = read_json(RUNS_DIR / "chinese_utf8_artifact_audit.json")
    readiness = read_json(RUNS_DIR / "real_submission_readiness.json")
    authorized_preflight = read_json(RUNS_DIR / "authorized_preflight_template_audit.json")
    ready_real_runner = read_json(RUNS_DIR / "ready_real_runner_template_audit.json")
    authorized_archive = read_json(RUNS_DIR / "authorized_checkpoint_archive_template_audit.json")
    handoff = read_json(RUNS_DIR / "submission_handoff_docs_audit.json")
    dashboard_gui_access = read_json(RUNS_DIR / "dashboard_gui_access_packet.json")
    secret_scan = read_json(RUNS_DIR / "plaintext_secret_scan.json")
    action_packet = read_json(RUNS_DIR / "next_user_action_packet.json")
    web_form_packet = read_json(RUNS_DIR / "web_form_field_packet.json")
    target_confirmation = read_json(RUNS_DIR / "submission_target_confirmation_packet.json")
    target_confirmation_gate = read_json(RUNS_DIR / "submission_target_confirmation_gate.json")
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

    leak_flags = {
        "credentials_printed": any(
            bool(item.get("credentials_printed"))
            for item in [
                link_intake,
                link_download,
                artifact_manifest,
                notebook_structure,
                jupyter_input,
                jupyter_authorized,
                jupyter_final_handoff,
                historical_notebook_outputs,
                chinese_utf8,
                readiness,
                authorized_preflight,
                ready_real_runner,
                authorized_archive,
                handoff,
                dashboard_gui_access,
                secret_scan,
                action_packet,
                web_form_packet,
                target_confirmation,
                target_confirmation_gate,
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
            ]
        ),
        "link_values_printed": bool(link_intake.get("link_values_printed"))
        or bool(link_download.get("link_value_printed"))
        or bool(artifact_manifest.get("link_values_printed"))
        or bool(notebook_structure.get("link_values_printed"))
        or bool(jupyter_input.get("link_values_printed"))
        or bool(jupyter_authorized.get("link_values_printed"))
        or bool(jupyter_final_handoff.get("link_values_printed"))
        or bool(historical_notebook_outputs.get("link_values_printed"))
        or bool(chinese_utf8.get("link_values_printed"))
        or bool(authorized_preflight.get("link_values_printed"))
        or bool(ready_real_runner.get("link_values_printed"))
        or bool(authorized_archive.get("link_values_printed"))
        or bool(action_packet.get("link_values_printed"))
        or bool(web_form_packet.get("link_values_printed"))
        or bool(target_confirmation.get("link_values_printed"))
        or bool(target_confirmation_gate.get("link_values_printed"))
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
        or bool(dashboard_gui_access.get("link_values_printed")),
        "secret_values_printed": bool(secret_scan.get("secret_values_printed"))
        or bool(artifact_manifest.get("secret_values_printed"))
        or bool(notebook_structure.get("secret_values_printed"))
        or bool(jupyter_input.get("secret_values_printed"))
        or bool(jupyter_authorized.get("secret_values_printed"))
        or bool(jupyter_final_handoff.get("secret_values_printed"))
        or bool(historical_notebook_outputs.get("secret_values_printed"))
        or bool(chinese_utf8.get("secret_values_printed"))
        or bool(authorized_preflight.get("secret_values_printed"))
        or bool(ready_real_runner.get("secret_values_printed"))
        or bool(authorized_archive.get("secret_values_printed"))
        or bool(action_packet.get("secret_values_printed"))
        or bool(web_form_packet.get("secret_values_printed"))
        or bool(target_confirmation.get("secret_values_printed"))
        or bool(target_confirmation_gate.get("secret_values_printed"))
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
        or bool(dashboard_gui_access.get("secret_values_printed")),
    }
    contact_flags = {
        "platform_contacted": any(
            bool(item.get("platform_contacted"))
            for item in [
                link_intake,
                link_download,
                artifact_manifest,
                notebook_structure,
                jupyter_input,
                jupyter_authorized,
                jupyter_final_handoff,
                historical_notebook_outputs,
                chinese_utf8,
                readiness,
                authorized_preflight,
                ready_real_runner,
                authorized_archive,
                handoff,
                dashboard_gui_access,
                secret_scan,
                action_packet,
                web_form_packet,
                target_confirmation,
                target_confirmation_gate,
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
            ]
        ),
        "uploads_performed": any(
            bool(item.get(key))
            for item in [
                link_intake,
                link_download,
                artifact_manifest,
                notebook_structure,
                jupyter_input,
                jupyter_authorized,
                jupyter_final_handoff,
                historical_notebook_outputs,
                chinese_utf8,
                readiness,
                authorized_preflight,
                ready_real_runner,
                authorized_archive,
                handoff,
                dashboard_gui_access,
                secret_scan,
                action_packet,
                web_form_packet,
                target_confirmation,
                target_confirmation_gate,
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
            ]
            for key in ["uploads_performed", "upload_performed"]
        ),
        "download_host_contacted": bool(
            link_download.get("verification", {}).get("download_host_contacted")
        )
        or bool(baseline_readonly_entry.get("contact_flags", {}).get("download_host_contacted"))
        or bool(readonly_preflight_parity.get("contact_flags", {}).get("download_host_contacted"))
        or bool(dashboard_gui_access.get("contact_flags", {}).get("download_host_contacted")),
    }
    readiness_blocking = readiness.get("blocking", [])
    link_blocking = link_intake.get("current_env", {}).get("blocking", [])
    download_blocking = link_download.get("blocking", [])
    legacy_global_blocking = []
    for source in [readiness_blocking, link_blocking, download_blocking]:
        for item in source:
            if item not in legacy_global_blocking:
                legacy_global_blocking.append(item)
    blocking = list(route_aware_blockers.get("baseline_current_blocking", [])) or legacy_global_blocking
    go_no_go = "ready" if readiness.get("ready_for_real_submission") is True else "blocked"
    rehearsal_commands = baseline_final_handoff_rehearsal.get("commands", [])
    rehearsal_step3 = rehearsal_commands[2] if len(rehearsal_commands) >= 3 else {}
    passed = all(item["passed"] for item in subcommands.values()) and not any(leak_flags.values()) and not any(
        contact_flags.values()
    )
    return {
        "kind": "submission_preflight_bundle",
        "passed": passed,
        "go_no_go": go_no_go,
        "ready_for_real_submission": readiness.get("ready_for_real_submission"),
        "web_form_ready": readiness.get("web_form_ready"),
        "web_form_recommended_route": web_form_packet.get("recommended_route"),
        "web_form_recommended_route_ready": web_form_packet.get("recommended_route_ready"),
        "web_form_recommended_route_required_field_count": web_form_packet.get(
            "recommended_route_required_field_count"
        ),
        "web_form_recommended_route_ready_field_count": web_form_packet.get("recommended_route_ready_field_count"),
        "web_form_recommended_route_missing_field_count": web_form_packet.get(
            "recommended_route_missing_field_count"
        ),
        "web_form_baseline_excludes_checkpoint_link": web_form_packet.get("baseline_route_excludes_checkpoint_link")
        is True,
        "web_form_baseline_excludes_checkpoint_archive": web_form_packet.get(
            "baseline_route_excludes_checkpoint_archive"
        )
        is True,
        "web_form_recommended_route_blocking_names": web_form_packet.get("recommended_route_blocking_names", []),
        "web_form_target_confirmation_value": web_form_packet.get("target_confirmation_value"),
        "web_form_target_user_confirmed": web_form_packet.get("target_user_confirmed"),
        "web_form_target_confirmation_field_present": web_form_packet.get("target_confirmation_field_present")
        is True,
        "web_form_target_confirmation_required": web_form_packet.get(
            "target_confirmation_field_required_for_recommended_route"
        )
        is True,
        "web_form_target_confirmation_ready": web_form_packet.get(
            "target_confirmation_field_ready_for_recommended_route"
        )
        is True,
        "local_baseline_runner_ready": readiness.get("local_baseline_runner_ready"),
        "local_lora_runner_ready": readiness.get("local_lora_runner_ready"),
        "verify_download_requested": link_download.get("verify_download_requested"),
        "download_verified": link_download.get("verification", {}).get("download_verified"),
        "link_shape_ready": link_intake.get("current_env", {}).get("link_shape_ready"),
        "recommended_route": route_aware_blockers.get("recommended_route"),
        "submission_target_confirmation_packet_passed": target_confirmation.get("passed") is True,
        "submission_target_confirmation_value": target_confirmation.get("recommended_confirmation_value"),
        "submission_target_user_confirmed": target_confirmation.get("target_user_confirmed"),
        "submission_target_does_not_confirm_for_user": target_confirmation.get("does_not_confirm_for_user")
        is True,
        "submission_target_target_task": target_confirmation.get("target", {}).get("task_name"),
        "submission_target_target_robot": target_confirmation.get("target", {}).get("robot_type"),
        "submission_target_target_benchmark": target_confirmation.get("target", {}).get("benchmark"),
        "submission_target_confirmation_gate_passed": target_confirmation_gate.get("passed") is True,
        "submission_target_confirmation_gate_case_count": target_confirmation_gate.get("case_count"),
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
        "submission_variant_target_confirmation_value": route_packet.get("target_confirmation_value"),
        "submission_variant_baseline_blocking": route_packet.get("baseline_current_blocking", []),
        "jupyter_input_target_confirmation_value": jupyter_input.get("target_confirmation_value"),
        "jupyter_input_target_confirmation_manual_input": jupyter_input.get(
            "target_confirmation_manual_input_required"
        )
        is True,
        "jupyter_input_target_confirmation_exact_match": jupyter_input.get(
            "target_confirmation_exact_match_required"
        )
        is True,
        "next_user_action_target_confirmation_value": action_packet.get("target_confirmation_value"),
        "next_user_action_target_user_confirmed": action_packet.get("target_user_confirmed"),
        "baseline_submission_quickstart_passed": baseline_quickstart.get("passed") is True,
        "baseline_submission_quickstart_target_confirmation_value": baseline_quickstart.get(
            "target_confirmation_value"
        ),
        "baseline_submission_quickstart_target_confirmation_manual_input": baseline_quickstart.get(
            "target_confirmation_manual_input_required"
        )
        is True,
        "baseline_submission_quickstart_target_confirmation_exact_match": baseline_quickstart.get(
            "target_confirmation_exact_match_required"
        )
        is True,
        "baseline_readonly_preflight_entry_passed": baseline_readonly_entry.get("passed") is True,
        "baseline_readonly_preflight_entry_command": baseline_readonly_entry.get("readonly_preflight_command"),
        "baseline_readonly_preflight_entry_target_confirmation_value": baseline_readonly_entry.get(
            "target_confirmation_value"
        ),
        "baseline_readonly_preflight_entry_no_upload": baseline_readonly_entry.get(
            "requires_checkpoint_upload"
        )
        is False,
        "baseline_readonly_preflight_entry_no_link": baseline_readonly_entry.get("requires_checkpoint_link")
        is False,
        "baseline_readonly_preflight_entry_real_confirm_required_for_readonly": baseline_readonly_entry.get(
            "real_runner_confirm_required_for_readonly_preflight"
        ),
        "baseline_readonly_preflight_entry_real_confirm_required_for_submission": baseline_readonly_entry.get(
            "real_runner_confirm_required_for_real_submission"
        ),
        "baseline_readonly_preflight_entry_required_ids": baseline_readonly_entry.get(
            "required_user_inputs_for_readonly_preflight",
            [],
        ),
        "baseline_readonly_preflight_entry_excluded_ids": baseline_readonly_entry.get(
            "excluded_from_readonly_preflight",
            [],
        ),
        "readonly_preflight_jupyter_shell_parity_passed": readonly_preflight_parity.get("passed") is True,
        "readonly_preflight_routes_converge": readonly_preflight_parity.get("routes_converge_to_same_wrapper")
        is True,
        "readonly_preflight_shell_command": readonly_preflight_parity.get("shell_readonly_command"),
        "readonly_preflight_jupyter_command": readonly_preflight_parity.get("jupyter_authorized_command"),
        "readonly_preflight_wrapper_template": readonly_preflight_parity.get("wrapper_template"),
        "readonly_preflight_no_upload": readonly_preflight_parity.get("requires_checkpoint_upload") is False,
        "readonly_preflight_no_link": readonly_preflight_parity.get("requires_checkpoint_link") is False,
        "readonly_preflight_real_confirm_required_for_readonly": readonly_preflight_parity.get(
            "real_runner_confirm_required_for_readonly_preflight"
        ),
        "dashboard_gui_access_packet_passed": dashboard_gui_access.get("passed") is True,
        "dashboard_gui_access_html_path": dashboard_gui_access.get("gui_html_path"),
        "dashboard_gui_access_card_count": dashboard_gui_access.get("dashboard_card_count"),
        "dashboard_gui_access_browser_blocked": dashboard_gui_access.get("browser_visual_blocked_by_policy"),
        "dashboard_gui_access_screenshot_created": dashboard_gui_access.get("screenshot_created"),
        "baseline_requires_checkpoint_link": route_aware_blockers.get("baseline_requires_checkpoint_link"),
        "baseline_requires_checkpoint_upload": route_aware_blockers.get("baseline_requires_checkpoint_upload"),
        "chinese_utf8_artifact_audit_passed": chinese_utf8.get("passed") is True,
        "chinese_utf8_artifact_scanned_file_count": chinese_utf8.get("scanned_file_count"),
        "chinese_utf8_artifact_decode_error_count": chinese_utf8.get("decode_error_count"),
        "chinese_utf8_artifact_bad_marker_hit_count": chinese_utf8.get("bad_marker_hit_count"),
        "baseline_dry_run_gate_passed": baseline_dry_run_gate.get("passed") is True,
        "baseline_dry_run_gate_command": baseline_dry_run_gate.get("dry_run_gate_command"),
        "baseline_dry_run_gate_stops_before_real_runner": baseline_dry_run_gate.get(
            "stops_before_real_runner_without_confirmation"
        ),
        "baseline_dry_run_gate_wrong_confirm_stops_before_real_runner": baseline_dry_run_gate.get(
            "stops_before_real_runner_with_wrong_confirmation"
        ),
        "baseline_dry_run_gate_malformed_confirm_stops_before_real_runner": baseline_dry_run_gate.get(
            "stops_before_real_runner_with_malformed_confirmation"
        ),
        "baseline_credential_hygiene_passed": baseline_credential_hygiene.get("passed") is True,
        "baseline_credential_hygiene_local_env_gitignored": baseline_credential_hygiene.get(
            "local_env_gitignored"
        )
        is True,
        "baseline_credential_hygiene_local_env_content_read": baseline_credential_hygiene.get(
            "local_env_content_read"
        ),
        "local_env_permission_contract_passed": local_env_permission.get("passed") is True,
        "local_env_permission_chmod_600_recommended": local_env_permission.get("recommended_chmod_command")
        == "chmod 600 submission/robochallenge_env.local.sh",
        "local_env_permission_gitignored": local_env_permission.get("evidence", {}).get("local_env_gitignored")
        is True,
        "local_env_permission_not_tracked": local_env_permission.get("evidence", {}).get("local_env_not_tracked")
        is True,
        "local_env_permission_template_recommends_chmod": local_env_permission.get("evidence", {}).get(
            "env_template_recommends_chmod_600"
        )
        is True,
        "local_env_permission_owner_only": local_env_permission.get("local_env_owner_only_permissions") is True,
        "local_env_permission_content_not_read": local_env_permission.get("local_env_content_read") is False,
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
        "synthetic_dry_run_baseline_passed": synthetic_dry_run_redaction.get("baseline_dry_run_passed") is True,
        "synthetic_dry_run_lora_passed": synthetic_dry_run_redaction.get("lora_dry_run_passed") is True,
        "synthetic_dry_run_baseline_lengths_only": synthetic_dry_run_redaction.get(
            "baseline_outputs_lengths_only"
        )
        is True,
        "synthetic_dry_run_lora_lengths_only": synthetic_dry_run_redaction.get("lora_outputs_lengths_only")
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
        "baseline_local_env_smoke_authorized_preflight_variant_baseline": baseline_local_env_smoke.get(
            "authorized_preflight", {}
        ).get("variant_baseline")
        is True,
        "baseline_local_env_smoke_ready_runner_stops_before_real_runner": baseline_local_env_smoke.get(
            "ready_runner", {}
        ).get("stops_before_real_runner")
        is True,
        "baseline_local_env_smoke_parent_real_confirm_scrubbed": baseline_local_env_smoke.get(
            "ready_runner", {}
        ).get("parent_real_confirm_present_in_subprocess_env")
        is False,
        "baseline_local_env_smoke_confirmation_absent_after_scrub": baseline_local_env_smoke.get(
            "ready_runner", {}
        ).get("confirmation_absent")
        is True,
        "jupyter_final_handoff_passed": jupyter_final_handoff.get("passed") is True,
        "jupyter_final_handoff_packet_default_true": jupyter_final_handoff.get("packet_default_true") is True,
        "jupyter_final_handoff_real_runner_default_false": jupyter_final_handoff.get(
            "real_runner_default_false"
        )
        is True,
        "jupyter_final_handoff_command_count": jupyter_final_handoff.get("command_count"),
        "jupyter_final_handoff_no_contact_command_count": jupyter_final_handoff.get("no_contact_command_count"),
        "jupyter_final_handoff_real_runner_requires_confirmation": jupyter_final_handoff.get(
            "real_runner_requires_confirmation"
        )
        is True,
        "historical_notebook_outputs_passed": historical_notebook_outputs.get("passed") is True,
        "historical_notebook_active_material_stale_hit_count": historical_notebook_outputs.get(
            "active_material_stale_hit_count"
        ),
        "historical_notebook_current_notebook_stale_hit_count": historical_notebook_outputs.get(
            "current_notebook_stale_hit_count"
        ),
        "historical_notebook_executed_hit_count": historical_notebook_outputs.get(
            "executed_notebook_historical_hit_count"
        ),
        "historical_notebook_work_log_audit_only": historical_notebook_outputs.get(
            "work_log_mentions_are_audit_only"
        ),
        "baseline_final_handoff_passed": baseline_final_handoff.get("passed") is True,
        "baseline_final_handoff_command_count": baseline_final_handoff.get("command_count"),
        "baseline_final_handoff_no_contact_command_count": baseline_final_handoff.get("no_contact_command_count"),
        "baseline_final_handoff_real_runner_requires_confirmation": baseline_final_handoff.get(
            "real_runner_requires_confirmation"
        )
        is True,
        "baseline_final_handoff_no_upload": baseline_final_handoff.get("requires_checkpoint_upload") is False,
        "baseline_final_handoff_no_link": baseline_final_handoff.get("requires_checkpoint_link") is False,
        "baseline_final_handoff_does_not_read_local_env": baseline_final_handoff.get("local_env_content_read") is False,
        "baseline_final_handoff_target_confirmation_value": baseline_final_handoff.get(
            "target_confirmation_value"
        ),
        "baseline_final_handoff_target_user_confirmed": baseline_final_handoff.get("target_user_confirmed"),
        "baseline_final_handoff_rehearsal_passed": baseline_final_handoff_rehearsal.get("passed") is True,
        "baseline_final_handoff_rehearsal_command_count": baseline_final_handoff_rehearsal.get("command_count"),
        "baseline_final_handoff_rehearsal_ready_runner_stops": rehearsal_step3.get("stops_before_real_runner")
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
        "lora_web_requires_checkpoint_link": route_aware_blockers.get("lora_web_requires_checkpoint_link"),
        "lora_web_requires_checkpoint_upload": route_aware_blockers.get("lora_web_requires_checkpoint_upload"),
        "baseline_current_blocking": route_aware_blockers.get("baseline_current_blocking", []),
        "lora_web_current_blocking": route_aware_blockers.get("lora_web_current_blocking", []),
        "secret_scan_hit_count": secret_scan.get("hit_count"),
        "secret_scan_scanned_files": secret_scan.get("scanned_files"),
        "subcommands": subcommands,
        "leak_flags": leak_flags,
        "contact_flags": contact_flags,
        "legacy_global_blocking": legacy_global_blocking,
        "blocking": blocking,
    }


def write_report(status: dict[str, Any], path: Path) -> None:
    lines = [
        "# 真实提交前预检汇总",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- go/no-go：`{status['go_no_go']}`。",
        f"- 真实提交就绪：`{status['ready_for_real_submission']}`。",
        f"- Web 表单就绪：`{status['web_form_ready']}`。",
        f"- Web 表单推荐路线：`{status['web_form_recommended_route']}`。",
        f"- Web 表单推荐路线必填字段：`{status['web_form_recommended_route_required_field_count']}`，已就绪 `{status['web_form_recommended_route_ready_field_count']}`，待补 `{status['web_form_recommended_route_missing_field_count']}`。",
        f"- baseline Web 表单是否排除 checkpoint link：`{status['web_form_baseline_excludes_checkpoint_link']}`。",
        f"- baseline Web 表单是否排除 checkpoint archive/upload：`{status['web_form_baseline_excludes_checkpoint_archive']}`。",
        f"- Web 表单目标确认值：`{status['web_form_target_confirmation_value']}`。",
        f"- Web 表单目标确认是否已由用户确认：`{status['web_form_target_user_confirmed']}`。",
        f"- Web 表单目标确认字段是否必填：`{status['web_form_target_confirmation_required']}`。",
        f"- baseline runner 就绪：`{status['local_baseline_runner_ready']}`。",
        f"- LoRA runner 就绪：`{status['local_lora_runner_ready']}`。",
        f"- checkpoint link 形态就绪：`{status['link_shape_ready']}`。",
        f"- 推荐提交路线：`{status['recommended_route']}`。",
        f"- 提交对象确认包：`{status['submission_target_confirmation_packet_passed']}`。",
        f"- 推荐目标确认值：`{status['submission_target_confirmation_value']}`。",
        f"- 是否已经替用户确认目标：`{status['submission_target_user_confirmed']}`。",
        f"- 确认包目标：`{status['submission_target_target_benchmark']} / {status['submission_target_target_robot']} / {status['submission_target_target_task']}`。",
        f"- 提交对象确认 gate：`{status['submission_target_confirmation_gate_passed']}`。",
        f"- 确认 gate case 数量：`{status['submission_target_confirmation_gate_case_count']}`。",
        f"- 错误确认值是否停在预检前：`{status['submission_target_confirmation_gate_bad_stop_before_preflight']}`。",
        f"- 正确确认值是否被接受：`{status['submission_target_confirmation_gate_correct_accepted']}`。",
        f"- 确认 gate 是否未启动真实 runner：`{status['submission_target_confirmation_gate_real_runner_not_started']}`。",
        f"- Jupyter 第 44 节确认值：`{status['jupyter_input_target_confirmation_value']}`。",
        f"- Jupyter 第 44 节是否要求手动输入确认：`{status['jupyter_input_target_confirmation_manual_input']}`。",
        f"- Jupyter 第 44 节是否精确匹配确认：`{status['jupyter_input_target_confirmation_exact_match']}`。",
        f"- 下一步动作包透传确认值：`{status['next_user_action_target_confirmation_value']}`。",
        f"- 下一步动作包是否替用户确认：`{status['next_user_action_target_user_confirmed']}`。",
        f"- baseline 最短路径：`{status['baseline_submission_quickstart_passed']}`。",
        f"- baseline 最短路径确认值：`{status['baseline_submission_quickstart_target_confirmation_value']}`。",
        f"- baseline 最短路径是否要求手动目标确认：`{status['baseline_submission_quickstart_target_confirmation_manual_input']}`。",
        f"- baseline 最短路径是否精确匹配目标确认：`{status['baseline_submission_quickstart_target_confirmation_exact_match']}`。",
        f"- baseline 只读预检入口：`{status['baseline_readonly_preflight_entry_passed']}`。",
        f"- baseline 只读预检命令：`{status['baseline_readonly_preflight_entry_command']}`。",
        f"- baseline 只读预检是否需要真实 runner 强确认：`{status['baseline_readonly_preflight_entry_real_confirm_required_for_readonly']}`。",
        f"- baseline 真实提交是否仍需要强确认：`{status['baseline_readonly_preflight_entry_real_confirm_required_for_submission']}`。",
        f"- baseline 只读预检目标确认值：`{status['baseline_readonly_preflight_entry_target_confirmation_value']}`。",
        f"- Jupyter/shell 只读预检一致性：`{status['readonly_preflight_jupyter_shell_parity_passed']}`。",
        f"- Jupyter/shell 是否收敛到同一 wrapper：`{status['readonly_preflight_routes_converge']}`。",
        f"- shell 只读预检入口：`{status['readonly_preflight_shell_command']}`。",
        f"- Jupyter 只读预检入口：`{status['readonly_preflight_jupyter_command']}`。",
        f"- 共同 wrapper：`{status['readonly_preflight_wrapper_template']}`。",
        f"- GUI 展示入口审计：`{status['dashboard_gui_access_packet_passed']}`。",
        f"- GUI HTML 路径：`{status['dashboard_gui_access_html_path']}`。",
        f"- GUI 卡片数量：`{status['dashboard_gui_access_card_count']}`。",
        f"- 浏览器 file URL 预览是否被策略阻止：`{status['dashboard_gui_access_browser_blocked']}`。",
        f"- 本轮是否生成 GUI 截图：`{status['dashboard_gui_access_screenshot_created']}`。",
        f"- baseline 是否需要 checkpoint link：`{status['baseline_requires_checkpoint_link']}`。",
        f"- baseline 是否需要 checkpoint upload：`{status['baseline_requires_checkpoint_upload']}`。",
        f"- 中文 UTF-8 产物审计：`{status['chinese_utf8_artifact_audit_passed']}`。",
        f"- 中文 UTF-8 扫描文件数：`{status['chinese_utf8_artifact_scanned_file_count']}`。",
        f"- 中文 UTF-8 解码错误数：`{status['chinese_utf8_artifact_decode_error_count']}`。",
        f"- 中文乱码哨兵命中数：`{status['chinese_utf8_artifact_bad_marker_hit_count']}`。",
        f"- baseline dry-run gate：`{status['baseline_dry_run_gate_passed']}`。",
        f"- baseline dry-run 命令：`{status['baseline_dry_run_gate_command']}`。",
        f"- dry-run 是否停在真实 runner 前：`{status['baseline_dry_run_gate_stops_before_real_runner']}`。",
        f"- 畸形确认短语是否停在真实 runner 前：`{status['baseline_dry_run_gate_malformed_confirm_stops_before_real_runner']}`。",
        f"- baseline 凭据卫生：`{status['baseline_credential_hygiene_passed']}`。",
        f"- local env 是否被 Git 忽略：`{status['baseline_credential_hygiene_local_env_gitignored']}`。",
        f"- 是否读取 local env 内容：`{status['baseline_credential_hygiene_local_env_content_read']}`。",
        f"- local env 权限契约：`{status['local_env_permission_contract_passed']}`。",
        f"- local env 是否建议 chmod 600：`{status['local_env_permission_chmod_600_recommended']}`。",
        f"- local env 权限审计是否 Git 忽略：`{status['local_env_permission_gitignored']}`。",
        f"- local env 权限审计是否未跟踪：`{status['local_env_permission_not_tracked']}`。",
        f"- local env 权限审计是否未读取内容：`{status['local_env_permission_content_not_read']}`。",
        f"- local env 是否 owner-only：`{status['local_env_permission_owner_only']}`。",
        f"- local env synthetic chmod smoke：`{status['local_env_permission_synthetic_chmod_passed']}`。",
        f"- local env runtime 权限 gate：`{status['local_env_runtime_permission_gate_passed']}`。",
        f"- runtime gate 是否拒绝 0644：`{status['local_env_runtime_bad_permissions_rejected']}`。",
        f"- runtime gate 是否放行 0600：`{status['local_env_runtime_owner_only_accepted']}`。",
        f"- runtime gate 是否在权限检查前不读内容：`{status['local_env_runtime_content_not_read_before_gate']}`。",
        f"- runtime gate 是否未启动真实 runner：`{status['local_env_runtime_real_runner_not_started']}`。",
        f"- 提交 variant gate：`{status['submission_variant_gate_passed']}`。",
        f"- 错误 variant 是否被拒绝：`{status['submission_variant_bad_rejected']}`。",
        f"- 错误 variant 是否停在预检前：`{status['submission_variant_bad_stop_before_preflight']}`。",
        f"- 合法 variant 是否被接受：`{status['submission_variant_valid_accepted']}`。",
        f"- variant gate 是否未启动真实 runner：`{status['submission_variant_real_runner_not_started']}`。",
        f"- 布尔环境变量 gate：`{status['boolean_env_gate_passed']}`。",
        f"- 错误布尔值是否被拒绝：`{status['boolean_env_bad_rejected']}`。",
        f"- 错误布尔值是否停在预检前：`{status['boolean_env_bad_stop_before_preflight']}`。",
        f"- 合法布尔值是否被接受：`{status['boolean_env_valid_accepted']}`。",
        f"- 布尔环境变量 gate 是否未启动真实 runner：`{status['boolean_env_real_runner_not_started']}`。",
        f"- 占位符凭据拒绝：`{status['placeholder_credential_rejection_passed']}`。",
        f"- baseline 占位符是否在 dry-run 前被拒绝：`{status['placeholder_baseline_rejected_before_dry_run']}`。",
        f"- LoRA 占位符是否在 dry-run 前被拒绝：`{status['placeholder_lora_rejected_before_dry_run']}`。",
        f"- baseline 占位符是否未启动真实 runner：`{status['placeholder_baseline_real_runner_not_started']}`。",
        f"- LoRA 占位符是否未启动真实 runner：`{status['placeholder_lora_real_runner_not_started']}`。",
        f"- 是否未记录占位符明文：`{status['placeholder_values_not_recorded']}`。",
        f"- 凭据空白字符 gate：`{status['credential_whitespace_guard_passed']}`。",
        f"- 空白字符坏输入是否被拒绝：`{status['credential_whitespace_bad_rejected']}`。",
        f"- 干净凭据 dry-run 是否通过：`{status['credential_whitespace_clean_dry_run_passed']}`。",
        f"- 空白字符 gate 是否未启动真实 runner：`{status['credential_whitespace_real_runner_not_started']}`。",
        f"- synthetic dry-run 脱敏：`{status['synthetic_dry_run_redaction_passed']}`。",
        f"- baseline synthetic dry-run 是否通过：`{status['synthetic_dry_run_baseline_passed']}`。",
        f"- LoRA synthetic dry-run 是否通过：`{status['synthetic_dry_run_lora_passed']}`。",
        f"- baseline synthetic dry-run 是否只输出长度：`{status['synthetic_dry_run_baseline_lengths_only']}`。",
        f"- LoRA synthetic dry-run 是否只输出长度：`{status['synthetic_dry_run_lora_lengths_only']}`。",
        f"- 是否未记录 synthetic 明文：`{status['synthetic_dry_run_values_not_recorded']}`。",
        f"- bash xtrace 防泄漏：`{status['shell_xtrace_secret_guard_passed']}`。",
        f"- xtrace 首条命令是否关闭：`{status['shell_xtrace_templates_disable_xtrace']}`。",
        f"- bash -x 是否看到 set +x 防护：`{status['shell_xtrace_cases_saw_set_plus_x']}`。",
        f"- set +x 后是否停止 trace：`{status['shell_xtrace_stops_trace_after_guard']}`。",
        f"- bash -x 是否未打印 synthetic 凭据：`{status['shell_xtrace_no_protected_values']}`。",
        f"- bash -x demo dry-run 是否通过：`{status['shell_xtrace_demo_dry_runs_passed']}`。",
        f"- bash -x ready runner 是否停在真实 runner 前：`{status['shell_xtrace_ready_runner_blocks_real_runner']}`。",
        f"- bash -x 是否未记录 synthetic 明文：`{status['shell_xtrace_values_not_recorded']}`。",
        f"- synthetic local env smoke：`{status['baseline_local_env_smoke_passed']}`。",
        f"- synthetic 授权预检是否走 baseline：`{status['baseline_local_env_smoke_authorized_preflight_variant_baseline']}`。",
        f"- synthetic ready runner 是否停在真实 runner 前：`{status['baseline_local_env_smoke_ready_runner_stops_before_real_runner']}`。",
        f"- synthetic 父环境确认短语是否已清理：`{status['baseline_local_env_smoke_parent_real_confirm_scrubbed']}`。",
        f"- synthetic ready runner 是否未看到确认短语：`{status['baseline_local_env_smoke_confirmation_absent_after_scrub']}`。",
        f"- Jupyter final handoff：`{status['jupyter_final_handoff_passed']}`。",
        f"- Jupyter final handoff 默认生成包：`{status['jupyter_final_handoff_packet_default_true']}`。",
        f"- Jupyter final handoff 真实 runner 默认关闭：`{status['jupyter_final_handoff_real_runner_default_false']}`。",
        f"- Notebook 历史输出审计：`{status['historical_notebook_outputs_passed']}`。",
        f"- 当前材料旧 checkpoint 口径命中数：`{status['historical_notebook_active_material_stale_hit_count']}`。",
        f"- 当前 Notebook 旧 checkpoint 口径命中数：`{status['historical_notebook_current_notebook_stale_hit_count']}`。",
        f"- executed Notebook 历史旧口径命中数：`{status['historical_notebook_executed_hit_count']}`。",
        f"- work.md 旧短语是否仅为审计记录：`{status['historical_notebook_work_log_audit_only']}`。",
        f"- baseline final handoff：`{status['baseline_final_handoff_passed']}`。",
        f"- final handoff 命令数：`{status['baseline_final_handoff_command_count']}`。",
        f"- final handoff no-contact 命令数：`{status['baseline_final_handoff_no_contact_command_count']}`。",
        f"- final handoff 真实 runner 是否需要强确认：`{status['baseline_final_handoff_real_runner_requires_confirmation']}`。",
        f"- final handoff 透传确认值：`{status['baseline_final_handoff_target_confirmation_value']}`。",
        f"- final handoff 是否替用户确认：`{status['baseline_final_handoff_target_user_confirmed']}`。",
        f"- final handoff 前三步演练：`{status['baseline_final_handoff_rehearsal_passed']}`。",
        f"- rehearsal 命令数：`{status['baseline_final_handoff_rehearsal_command_count']}`。",
        f"- rehearsal 是否 no-contact：`{status['baseline_final_handoff_rehearsal_no_contact']}`。",
        f"- rehearsal 是否 no-leak：`{status['baseline_final_handoff_rehearsal_no_leak']}`。",
        f"- rehearsal 父环境确认短语是否已清理：`{status['baseline_final_handoff_rehearsal_parent_real_confirm_scrubbed']}`。",
        f"- rehearsal ready runner 是否未看到确认短语：`{status['baseline_final_handoff_rehearsal_confirmation_absent_after_scrub']}`。",
        f"- LoRA/web 是否需要 checkpoint link：`{status['lora_web_requires_checkpoint_link']}`。",
        f"- LoRA/web 是否需要 checkpoint upload：`{status['lora_web_requires_checkpoint_upload']}`。",
        f"- 下载已验证：`{status['download_verified']}`。",
        f"- secret scan 命中数：`{status['secret_scan_hit_count']}`。",
        "",
        "## 只读边界",
        "",
        f"- 是否连接 RoboChallenge 平台：`{status['contact_flags']['platform_contacted']}`。",
        f"- 是否上传：`{status['contact_flags']['uploads_performed']}`。",
        f"- 是否接触下载 host：`{status['contact_flags']['download_host_contacted']}`。",
        f"- 是否打印凭据：`{status['leak_flags']['credentials_printed']}`。",
        f"- 是否打印链接明文：`{status['leak_flags']['link_values_printed']}`。",
        f"- 是否打印 secret 明文：`{status['leak_flags']['secret_values_printed']}`。",
        "",
        "## 子审计",
        "",
    ]
    for name, item in status["subcommands"].items():
        lines.append(f"- `{name}`：returncode=`{item['returncode']}`，passed=`{item['passed']}`。")
    lines.extend(["", "## Baseline 最短路线当前只差", ""])
    for item in status["baseline_current_blocking"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## LoRA / 网页 checkpoint 路线当前只差", ""])
    for item in status["lora_web_current_blocking"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Blocking", ""])
    for item in status["blocking"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 旧全局阻塞（兼容 readiness/web/LoRA）", ""])
    for item in status["legacy_global_blocking"]:
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
