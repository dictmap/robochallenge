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
    ("real_submission_readiness", "scripts/audit_real_submission_readiness.py"),
    ("authorized_preflight_template", "scripts/audit_authorized_preflight_template.py"),
    ("ready_real_runner_template", "scripts/audit_ready_real_runner_template.py"),
    ("authorized_checkpoint_archive_template", "scripts/audit_authorized_checkpoint_archive_template.py"),
    ("plaintext_secret_scan", "scripts/audit_plaintext_secrets.py"),
    ("submission_variant_route_packet", "scripts/render_submission_variant_route_packet.py"),
    ("baseline_submission_quickstart", "scripts/render_baseline_submission_quickstart.py"),
    ("authorized_execution_checklist", "scripts/audit_authorized_execution_checklist.py"),
    ("next_user_action_packet", "scripts/render_next_user_action_packet.py"),
    ("web_form_field_packet", "scripts/render_web_form_field_packet.py"),
    ("route_aware_submission_blockers", "scripts/render_route_aware_submission_blockers.py"),
    ("baseline_dry_run_gate", "scripts/render_baseline_dry_run_gate.py"),
    ("baseline_credential_hygiene", "scripts/render_baseline_credential_hygiene.py"),
    ("baseline_local_env_smoke", "scripts/render_baseline_local_env_smoke.py"),
    ("baseline_final_handoff_packet", "scripts/render_baseline_final_handoff_packet.py"),
    ("submission_handoff_docs", "scripts/audit_submission_handoff_docs.py"),
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
    return {
        "script": script,
        "returncode": result.returncode,
        "passed": result.returncode == 0,
        "stdout_tail": stdout[-1000:],
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
    readiness = read_json(RUNS_DIR / "real_submission_readiness.json")
    authorized_preflight = read_json(RUNS_DIR / "authorized_preflight_template_audit.json")
    ready_real_runner = read_json(RUNS_DIR / "ready_real_runner_template_audit.json")
    authorized_archive = read_json(RUNS_DIR / "authorized_checkpoint_archive_template_audit.json")
    handoff = read_json(RUNS_DIR / "submission_handoff_docs_audit.json")
    secret_scan = read_json(RUNS_DIR / "plaintext_secret_scan.json")
    action_packet = read_json(RUNS_DIR / "next_user_action_packet.json")
    web_form_packet = read_json(RUNS_DIR / "web_form_field_packet.json")
    route_packet = read_json(RUNS_DIR / "submission_variant_route_packet.json")
    baseline_quickstart = read_json(RUNS_DIR / "baseline_submission_quickstart.json")
    baseline_dry_run_gate = read_json(RUNS_DIR / "baseline_dry_run_gate.json")
    baseline_credential_hygiene = read_json(RUNS_DIR / "baseline_credential_hygiene.json")
    baseline_local_env_smoke = read_json(RUNS_DIR / "baseline_local_env_smoke.json")
    baseline_final_handoff = read_json(RUNS_DIR / "baseline_final_handoff_packet.json")
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
                readiness,
                authorized_preflight,
                ready_real_runner,
                authorized_archive,
                handoff,
                secret_scan,
                action_packet,
                web_form_packet,
                route_packet,
                baseline_quickstart,
                baseline_dry_run_gate,
                baseline_credential_hygiene,
                baseline_local_env_smoke,
                baseline_final_handoff,
                route_aware_blockers,
            ]
        ),
        "link_values_printed": bool(link_intake.get("link_values_printed"))
        or bool(link_download.get("link_value_printed"))
        or bool(artifact_manifest.get("link_values_printed"))
        or bool(notebook_structure.get("link_values_printed"))
        or bool(jupyter_input.get("link_values_printed"))
        or bool(jupyter_authorized.get("link_values_printed"))
        or bool(authorized_preflight.get("link_values_printed"))
        or bool(ready_real_runner.get("link_values_printed"))
        or bool(authorized_archive.get("link_values_printed"))
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
        or bool(artifact_manifest.get("secret_values_printed"))
        or bool(notebook_structure.get("secret_values_printed"))
        or bool(jupyter_input.get("secret_values_printed"))
        or bool(jupyter_authorized.get("secret_values_printed"))
        or bool(authorized_preflight.get("secret_values_printed"))
        or bool(ready_real_runner.get("secret_values_printed"))
        or bool(authorized_archive.get("secret_values_printed"))
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
                link_intake,
                link_download,
                artifact_manifest,
                notebook_structure,
                jupyter_input,
                jupyter_authorized,
                readiness,
                authorized_preflight,
                ready_real_runner,
                authorized_archive,
                handoff,
                secret_scan,
                action_packet,
                web_form_packet,
                route_packet,
                baseline_quickstart,
                baseline_dry_run_gate,
                baseline_credential_hygiene,
                baseline_local_env_smoke,
                baseline_final_handoff,
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
                readiness,
                authorized_preflight,
                ready_real_runner,
                authorized_archive,
                handoff,
                secret_scan,
                action_packet,
                web_form_packet,
                route_packet,
                baseline_quickstart,
                baseline_dry_run_gate,
                baseline_credential_hygiene,
                baseline_local_env_smoke,
                baseline_final_handoff,
                route_aware_blockers,
            ]
            for key in ["uploads_performed", "upload_performed"]
        ),
        "download_host_contacted": bool(
            link_download.get("verification", {}).get("download_host_contacted")
        ),
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
    passed = all(item["passed"] for item in subcommands.values()) and not any(leak_flags.values()) and not any(
        contact_flags.values()
    )
    return {
        "kind": "submission_preflight_bundle",
        "passed": passed,
        "go_no_go": go_no_go,
        "ready_for_real_submission": readiness.get("ready_for_real_submission"),
        "web_form_ready": readiness.get("web_form_ready"),
        "local_baseline_runner_ready": readiness.get("local_baseline_runner_ready"),
        "local_lora_runner_ready": readiness.get("local_lora_runner_ready"),
        "verify_download_requested": link_download.get("verify_download_requested"),
        "download_verified": link_download.get("verification", {}).get("download_verified"),
        "link_shape_ready": link_intake.get("current_env", {}).get("link_shape_ready"),
        "recommended_route": route_aware_blockers.get("recommended_route"),
        "baseline_requires_checkpoint_link": route_aware_blockers.get("baseline_requires_checkpoint_link"),
        "baseline_requires_checkpoint_upload": route_aware_blockers.get("baseline_requires_checkpoint_upload"),
        "baseline_dry_run_gate_passed": baseline_dry_run_gate.get("passed") is True,
        "baseline_dry_run_gate_command": baseline_dry_run_gate.get("dry_run_gate_command"),
        "baseline_dry_run_gate_stops_before_real_runner": baseline_dry_run_gate.get(
            "stops_before_real_runner_without_confirmation"
        ),
        "baseline_credential_hygiene_passed": baseline_credential_hygiene.get("passed") is True,
        "baseline_credential_hygiene_local_env_gitignored": baseline_credential_hygiene.get(
            "local_env_gitignored"
        )
        is True,
        "baseline_credential_hygiene_local_env_content_read": baseline_credential_hygiene.get(
            "local_env_content_read"
        ),
        "baseline_local_env_smoke_passed": baseline_local_env_smoke.get("passed") is True,
        "baseline_local_env_smoke_authorized_preflight_variant_baseline": baseline_local_env_smoke.get(
            "authorized_preflight", {}
        ).get("variant_baseline")
        is True,
        "baseline_local_env_smoke_ready_runner_stops_before_real_runner": baseline_local_env_smoke.get(
            "ready_runner", {}
        ).get("stops_before_real_runner")
        is True,
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
        f"- baseline runner 就绪：`{status['local_baseline_runner_ready']}`。",
        f"- LoRA runner 就绪：`{status['local_lora_runner_ready']}`。",
        f"- checkpoint link 形态就绪：`{status['link_shape_ready']}`。",
        f"- 推荐提交路线：`{status['recommended_route']}`。",
        f"- baseline 是否需要 checkpoint link：`{status['baseline_requires_checkpoint_link']}`。",
        f"- baseline 是否需要 checkpoint upload：`{status['baseline_requires_checkpoint_upload']}`。",
        f"- baseline dry-run gate：`{status['baseline_dry_run_gate_passed']}`。",
        f"- baseline dry-run 命令：`{status['baseline_dry_run_gate_command']}`。",
        f"- dry-run 是否停在真实 runner 前：`{status['baseline_dry_run_gate_stops_before_real_runner']}`。",
        f"- baseline 凭据卫生：`{status['baseline_credential_hygiene_passed']}`。",
        f"- local env 是否被 Git 忽略：`{status['baseline_credential_hygiene_local_env_gitignored']}`。",
        f"- 是否读取 local env 内容：`{status['baseline_credential_hygiene_local_env_content_read']}`。",
        f"- synthetic local env smoke：`{status['baseline_local_env_smoke_passed']}`。",
        f"- synthetic 授权预检是否走 baseline：`{status['baseline_local_env_smoke_authorized_preflight_variant_baseline']}`。",
        f"- synthetic ready runner 是否停在真实 runner 前：`{status['baseline_local_env_smoke_ready_runner_stops_before_real_runner']}`。",
        f"- baseline final handoff：`{status['baseline_final_handoff_passed']}`。",
        f"- final handoff 命令数：`{status['baseline_final_handoff_command_count']}`。",
        f"- final handoff no-contact 命令数：`{status['baseline_final_handoff_no_contact_command_count']}`。",
        f"- final handoff 真实 runner 是否需要强确认：`{status['baseline_final_handoff_real_runner_requires_confirmation']}`。",
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
