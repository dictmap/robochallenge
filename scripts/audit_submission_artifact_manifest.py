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
    "reports/authorized_preflight_template_audit.md",
    "reports/ready_real_runner_template_audit.md",
    "reports/authorized_checkpoint_archive_template_audit.md",
    "reports/authorized_execution_checklist.md",
    "reports/next_user_action_packet.md",
    "reports/web_form_field_packet.md",
    "reports/submission_variant_route_packet.md",
    "reports/baseline_submission_quickstart.md",
    "reports/baseline_dry_run_gate.md",
    "reports/baseline_credential_hygiene.md",
    "reports/baseline_local_env_smoke.md",
    "reports/baseline_final_handoff_packet.md",
    "reports/route_aware_submission_blockers.md",
    "reports/submission_handoff_docs_audit.md",
    "reports/authorized_submission_sequence_audit.md",
    "reports/submission_preflight_bundle.md",
    "reports/plaintext_secret_scan.md",
    "reports/submission_status_dashboard.html",
    "scripts/render_next_user_action_packet.py",
    "scripts/render_web_form_field_packet.py",
    "scripts/render_submission_variant_route_packet.py",
    "scripts/render_baseline_submission_quickstart.py",
    "scripts/render_baseline_dry_run_gate.py",
    "scripts/render_baseline_credential_hygiene.py",
    "scripts/render_baseline_local_env_smoke.py",
    "scripts/render_baseline_final_handoff_packet.py",
    "scripts/render_route_aware_submission_blockers.py",
    "scripts/audit_jupyter_input_template.py",
    "scripts/audit_jupyter_authorized_preflight_template.py",
    "scripts/audit_jupyter_final_handoff_template.py",
    "scripts/audit_authorized_execution_checklist.py",
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
    notebook_structure = read_json(RUNS_DIR / "notebook_structure_audit.json")
    jupyter_input = read_json(RUNS_DIR / "jupyter_input_template_audit.json")
    jupyter_authorized = read_json(RUNS_DIR / "jupyter_authorized_preflight_template_audit.json")
    jupyter_final_handoff = read_json(RUNS_DIR / "jupyter_final_handoff_template_audit.json")
    authorized_preflight = read_json(RUNS_DIR / "authorized_preflight_template_audit.json")
    ready_real_runner = read_json(RUNS_DIR / "ready_real_runner_template_audit.json")
    authorized_archive = read_json(RUNS_DIR / "authorized_checkpoint_archive_template_audit.json")
    authorized_execution = read_json(RUNS_DIR / "authorized_execution_checklist.json")
    action_packet = read_json(RUNS_DIR / "next_user_action_packet.json")
    web_form_packet = read_json(RUNS_DIR / "web_form_field_packet.json")
    route_packet = read_json(RUNS_DIR / "submission_variant_route_packet.json")
    baseline_quickstart = read_json(RUNS_DIR / "baseline_submission_quickstart.json")
    baseline_dry_run_gate = read_json(RUNS_DIR / "baseline_dry_run_gate.json")
    baseline_credential_hygiene = read_json(RUNS_DIR / "baseline_credential_hygiene.json")
    baseline_local_env_smoke = read_json(RUNS_DIR / "baseline_local_env_smoke.json")
    baseline_final_handoff = read_json(RUNS_DIR / "baseline_final_handoff_packet.json")
    route_aware_blockers = read_json(RUNS_DIR / "route_aware_submission_blockers.json")
    readiness = read_json(RUNS_DIR / "real_submission_readiness.json")
    env_template = read_json(RUNS_DIR / "submission_env_template_audit.json")
    secret_scan = read_json(RUNS_DIR / "plaintext_secret_scan.json")

    inputs = {
        "preflight_status_available": bool(preflight),
        "preflight_go_no_go_blocked": preflight.get("go_no_go") == "blocked",
        "notebook_structure_passed": notebook_structure.get("passed") is True,
        "jupyter_input_template_passed": jupyter_input.get("passed") is True,
        "jupyter_input_recommended_baseline": jupyter_input.get("recommended_route") == "baseline_official_aloha",
        "jupyter_input_baseline_no_upload": jupyter_input.get("baseline_requires_checkpoint_upload") is False,
        "jupyter_input_baseline_no_link": jupyter_input.get("baseline_requires_checkpoint_link") is False,
        "jupyter_input_lora_web_needs_upload": jupyter_input.get("lora_web_requires_checkpoint_upload") is True,
        "jupyter_input_lora_web_needs_link": jupyter_input.get("lora_web_requires_checkpoint_link") is True,
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
        "web_form_field_packet_passed": web_form_packet.get("passed") is True,
        "web_form_field_packet_currently_not_ready": web_form_packet.get("web_form_ready") is False,
        "submission_variant_route_packet_passed": route_packet.get("passed") is True,
        "submission_variant_route_packet_baseline_default": route_packet.get("recommended_default")
        == "baseline_official_aloha",
        "submission_variant_route_packet_has_two_routes": route_packet.get("route_count") == 2,
        "baseline_submission_quickstart_passed": baseline_quickstart.get("passed") is True,
        "baseline_submission_quickstart_no_upload": baseline_quickstart.get("requires_checkpoint_upload") is False,
        "baseline_submission_quickstart_no_link": baseline_quickstart.get("requires_checkpoint_link") is False,
        "baseline_dry_run_gate_passed": baseline_dry_run_gate.get("passed") is True,
        "baseline_dry_run_gate_no_upload": baseline_dry_run_gate.get("requires_checkpoint_upload") is False,
        "baseline_dry_run_gate_no_link": baseline_dry_run_gate.get("requires_checkpoint_link") is False,
        "baseline_dry_run_gate_command_exact": baseline_dry_run_gate.get("dry_run_gate_command")
        == "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_ready_real_submission_template.sh",
        "baseline_dry_run_gate_stops_before_real_runner": baseline_dry_run_gate.get(
            "stops_before_real_runner_without_confirmation"
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
        "route_aware_submission_blockers_passed": route_aware_blockers.get("passed") is True,
        "route_aware_recommended_baseline": route_aware_blockers.get("recommended_route") == "baseline_official_aloha",
        "route_aware_baseline_no_upload": route_aware_blockers.get("baseline_requires_checkpoint_upload") is False,
        "route_aware_baseline_no_link": route_aware_blockers.get("baseline_requires_checkpoint_link") is False,
        "route_aware_lora_web_needs_upload": route_aware_blockers.get("lora_web_requires_checkpoint_upload") is True,
        "route_aware_lora_web_needs_link": route_aware_blockers.get("lora_web_requires_checkpoint_link") is True,
        "readiness_currently_blocked": readiness.get("ready_for_real_submission") is False,
        "env_template_passed": env_template.get("passed") is True,
        "secret_scan_passed": secret_scan.get("passed") is True,
        "secret_scan_hit_count_zero": secret_scan.get("hit_count") == 0,
    }
    leak_flags = {
        "credentials_printed": any(
            bool(item.get("credentials_printed"))
            for item in [
                preflight,
                notebook_structure,
                jupyter_input,
                jupyter_authorized,
                jupyter_final_handoff,
                authorized_preflight,
                ready_real_runner,
                authorized_archive,
                authorized_execution,
                action_packet,
                web_form_packet,
                route_packet,
                baseline_quickstart,
                baseline_dry_run_gate,
                baseline_credential_hygiene,
                baseline_local_env_smoke,
                baseline_final_handoff,
                route_aware_blockers,
                readiness,
                env_template,
            ]
        ),
        "link_values_printed": bool(preflight.get("leak_flags", {}).get("link_values_printed"))
        or bool(jupyter_input.get("link_values_printed"))
        or bool(jupyter_authorized.get("link_values_printed"))
        or bool(jupyter_final_handoff.get("link_values_printed"))
        or bool(authorized_preflight.get("link_values_printed"))
        or bool(ready_real_runner.get("link_values_printed"))
        or bool(authorized_archive.get("link_values_printed"))
        or bool(authorized_execution.get("link_values_printed"))
        or bool(action_packet.get("link_values_printed"))
        or bool(web_form_packet.get("link_values_printed"))
        or bool(route_packet.get("link_values_printed"))
        or bool(baseline_quickstart.get("link_values_printed"))
        or bool(baseline_dry_run_gate.get("link_values_printed"))
        or bool(baseline_credential_hygiene.get("link_values_printed"))
        or bool(baseline_local_env_smoke.get("link_values_printed"))
        or bool(baseline_final_handoff.get("link_values_printed"))
        or bool(route_aware_blockers.get("link_values_printed")),
        "secret_values_printed": bool(secret_scan.get("secret_values_printed"))
        or bool(jupyter_input.get("secret_values_printed"))
        or bool(jupyter_authorized.get("secret_values_printed"))
        or bool(jupyter_final_handoff.get("secret_values_printed"))
        or bool(action_packet.get("secret_values_printed"))
        or bool(web_form_packet.get("secret_values_printed"))
        or bool(route_packet.get("secret_values_printed"))
        or bool(baseline_quickstart.get("secret_values_printed"))
        or bool(baseline_dry_run_gate.get("secret_values_printed"))
        or bool(baseline_credential_hygiene.get("secret_values_printed"))
        or bool(baseline_local_env_smoke.get("secret_values_printed"))
        or bool(baseline_final_handoff.get("secret_values_printed"))
        or bool(route_aware_blockers.get("secret_values_printed")),
    }
    contact_flags = {
        "platform_contacted": any(
            bool(item.get("platform_contacted"))
            for item in [
                preflight,
                notebook_structure,
                jupyter_input,
                jupyter_authorized,
                jupyter_final_handoff,
                authorized_preflight,
                ready_real_runner,
                authorized_archive,
                authorized_execution,
                action_packet,
                web_form_packet,
                route_packet,
                baseline_quickstart,
                baseline_dry_run_gate,
                baseline_credential_hygiene,
                baseline_local_env_smoke,
                baseline_final_handoff,
                route_aware_blockers,
                readiness,
                env_template,
                secret_scan,
            ]
        ),
        "uploads_performed": any(
            bool(item.get("uploads_performed") or item.get("upload_performed"))
            for item in [
                preflight,
                notebook_structure,
                jupyter_input,
                jupyter_authorized,
                jupyter_final_handoff,
                authorized_preflight,
                ready_real_runner,
                authorized_archive,
                authorized_execution,
                action_packet,
                web_form_packet,
                route_packet,
                baseline_quickstart,
                baseline_dry_run_gate,
                baseline_credential_hygiene,
                baseline_local_env_smoke,
                baseline_final_handoff,
                route_aware_blockers,
                readiness,
                env_template,
                secret_scan,
            ]
        ),
        "download_host_contacted": bool(preflight.get("contact_flags", {}).get("download_host_contacted")),
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
            "提交准备材料 manifest 已完整；baseline runner 仍需要用户凭据和 submission id，"
            "LoRA 或网页 checkpoint 路线仍需要上传授权和 checkpoint link。"
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
