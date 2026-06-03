#!/usr/bin/env python3
"""Audit and smoke-test the authorized preflight template without real credentials."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = ROOT / "runs"
TEMPLATE = ROOT / "submission" / "run_authorized_preflight_template.sh"
DEFAULT_STATUS = RUNS_DIR / "authorized_preflight_template_audit.json"
DEFAULT_REPORT = REPORTS_DIR / "authorized_preflight_template_audit.md"
TARGET_CONFIRMATION_VALUE = "CONFIRM_TABLE30V2_ALOHA_BASELINE"

SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9_-]{30,}",
    r"hf_[A-Za-z0-9]{20,}",
    r"ghp_[A-Za-z0-9]{30,}",
    r"github_pat_[A-Za-z0-9_]{20,}",
    r"ROBOCHALLENGE_(?:USER_)?TOKEN\s*=\s*[A-Za-z0-9_-]{20,}",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计授权后安全预检模板；不读取真实凭据、不上传、不运行真实 runner。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文审计报告输出路径。")
    return parser.parse_args()


def run_command(args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    merged_env["PYTHONIOENCODING"] = "utf-8"
    if env:
        merged_env.update(env)
    return subprocess.run(
        args,
        cwd=ROOT,
        env=merged_env,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=900,
    )


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def synthetic_no_credentials_smoke() -> dict[str, Any]:
    env = {
        "ROBOCHALLENGE_ENV_FILE": str(ROOT / "submission" / "__missing_env_for_audit__.sh"),
        "ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD": "0",
        "ROBOCHALLENGE_REQUIRE_READY": "0",
        "ROBOCHALLENGE_SUBMISSION_VARIANT": "lora",
        "ROBOCHALLENGE_SUBMISSION_TARGET_CONFIRMATION": TARGET_CONFIRMATION_VALUE,
    }
    for key in [
        "ROBOCHALLENGE_USER_TOKEN",
        "ROBOCHALLENGE_SUBMISSION_ID",
        "ROBOCHALLENGE_CHECKPOINT_LINK",
        "ROBOCHALLENGE_LORA_CHECKPOINT_LINK",
    ]:
        env[key] = ""
    result = run_command(["bash", str(TEMPLATE)], env=env)
    output = (result.stdout or "") + "\n" + (result.stderr or "")
    return {
        "returncode": result.returncode,
        "passed": result.returncode == 0,
        "stdout_tail": (result.stdout or "")[-2000:],
        "stderr_tail": (result.stderr or "")[-1000:],
        "env_file_present_false": "env_file_present=false" in output,
        "verify_download_disabled": "verify_download=0" in output,
        "target_confirmation_present": "target_confirmation_present=true" in output,
        "stops_before_runner": "stop before runner dry-run" in output,
        "ready_false": "ready_for_real_submission=false" in output,
        "real_runner_not_called": "dry-run passed; real runner" not in output,
    }


def build_status() -> dict[str, Any]:
    exists = TEMPLATE.exists()
    text = TEMPLATE.read_text(encoding="utf-8") if exists else ""
    bash_n = run_command(["bash", "-n", str(TEMPLATE)]) if exists else None
    smoke = synthetic_no_credentials_smoke() if exists else {}
    readiness = read_json(RUNS_DIR / "real_submission_readiness.json")
    blockers = read_json(RUNS_DIR / "submission_blockers_summary.json")
    secret_hits = [pattern for pattern in SECRET_PATTERNS if re.search(pattern, text)]
    source_index = text.find('source "$ENV_FILE"')
    variant_index = text.find('VARIANT="${ROBOCHALLENGE_SUBMISSION_VARIANT:-baseline}"')
    required_fragments = {
        "sources_local_env_file": "source \"$ENV_FILE\"" in text,
        "reads_variant_after_local_env_source": source_index >= 0 and variant_index > source_index,
        "default_variant_baseline": 'VARIANT="${ROBOCHALLENGE_SUBMISSION_VARIANT:-baseline}"' in text,
        "requires_target_confirmation": "ROBOCHALLENGE_SUBMISSION_TARGET_CONFIRMATION" in text
        and TARGET_CONFIRMATION_VALUE in text
        and "validate_target_confirmation" in text,
        "runs_link_intake": "python3 scripts/audit_checkpoint_link_intake.py" in text,
        "runs_link_download_default": "python3 scripts/audit_checkpoint_link_download_verification.py" in text,
        "download_verify_guarded": "ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD" in text
        and "--verify-download" in text,
        "runs_readiness": "python3 scripts/audit_real_submission_readiness.py" in text,
        "runs_blockers_summary": "python3 scripts/audit_submission_blockers_summary.py" in text,
        "reads_readiness_json": "runs/real_submission_readiness.json" in text,
        "lora_dry_run_only": "ROBOCHALLENGE_DRY_RUN=1 bash submission/run_table30v2_aloha_lora_demo_template.sh"
        in text,
        "baseline_dry_run_only": "ROBOCHALLENGE_DRY_RUN=1 bash submission/run_table30v2_aloha_demo_template.sh"
        in text,
        "blockers_warning_continues_dry_run_only": "continuing dry-run only" in text,
        "requires_explicit_real_authorization": "real runner still requires explicit user authorization" in text,
    }
    forbidden_fragments = {
        "calls_lora_real_runner": "bash submission/run_table30v2_aloha_lora_demo_template.sh" in text
        and "ROBOCHALLENGE_DRY_RUN=1 bash submission/run_table30v2_aloha_lora_demo_template.sh" not in text,
        "calls_baseline_real_runner": "bash submission/run_table30v2_aloha_demo_template.sh" in text
        and "ROBOCHALLENGE_DRY_RUN=1 bash submission/run_table30v2_aloha_demo_template.sh" not in text,
    }
    passed = bool(
        exists
        and bash_n is not None
        and bash_n.returncode == 0
        and all(required_fragments.values())
        and not any(forbidden_fragments.values())
        and not secret_hits
        and smoke.get("passed")
        and smoke.get("env_file_present_false")
        and smoke.get("verify_download_disabled")
        and smoke.get("target_confirmation_present")
        and smoke.get("stops_before_runner")
        and smoke.get("ready_false")
        and smoke.get("real_runner_not_called")
        and readiness.get("ready_for_real_submission") is False
        and blockers.get("current_state", {}).get("go_no_go") == "blocked"
    )
    blocking: list[str] = []
    if not exists:
        blocking.append("缺少授权后安全预检模板。")
    if bash_n is None or bash_n.returncode != 0:
        blocking.append("授权后安全预检模板 bash 语法检查未通过。")
    for key, ok in required_fragments.items():
        if not ok:
            blocking.append(f"模板缺少必要片段：{key}。")
    for key, found in forbidden_fragments.items():
        if found:
            blocking.append(f"模板疑似包含真实 runner 直接调用：{key}。")
    if secret_hits:
        blocking.append("模板疑似包含明文 token 或密钥模式。")
    for key in [
        "passed",
        "env_file_present_false",
        "verify_download_disabled",
        "target_confirmation_present",
        "stops_before_runner",
        "ready_false",
    ]:
        if not smoke.get(key):
            blocking.append(f"无凭据 smoke 未满足：{key}。")
    if not blocking:
        blocking.append("授权后安全预检模板已通过；默认不联网、不上传、不运行真实 runner。")
    return {
        "kind": "authorized_preflight_template_audit",
        "passed": passed,
        "platform_contacted": False,
        "uploads_performed": False,
        "credentials_read": False,
        "credentials_printed": False,
        "link_values_printed": False,
        "secret_values_printed": False,
        "template_path": "submission/run_authorized_preflight_template.sh",
        "bash_n": {
            "returncode": bash_n.returncode if bash_n else None,
            "passed": bash_n.returncode == 0 if bash_n else False,
            "stderr": (bash_n.stderr or "").strip() if bash_n else "missing",
        },
        "required_fragments": required_fragments,
        "forbidden_fragments": forbidden_fragments,
        "secret_patterns_found": secret_hits,
        "no_credentials_smoke": smoke,
        "input_evidence": {
            "readiness_currently_blocked": readiness.get("ready_for_real_submission") is False,
            "blockers_summary_go_no_go_blocked": blockers.get("current_state", {}).get("go_no_go") == "blocked",
        },
        "blocking": blocking,
    }


def write_report(status: dict[str, Any], path: Path) -> None:
    lines = [
        "# 授权后安全预检模板审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 模板路径：`{status['template_path']}`。",
        f"- bash 语法检查：`{status['bash_n']['passed']}`。",
        f"- 无凭据 smoke：`{status['no_credentials_smoke'].get('passed')}`。",
        f"- 是否连接平台：`{status['platform_contacted']}`。",
        f"- 是否上传：`{status['uploads_performed']}`。",
        f"- 是否读取或打印凭据：`{status['credentials_read'] or status['credentials_printed']}`。",
        "",
        "## 必要片段",
        "",
    ]
    for key, value in status["required_fragments"].items():
        lines.append(f"- `{key}`：`{value}`。")
    lines.extend(["", "## 禁止片段", ""])
    for key, value in status["forbidden_fragments"].items():
        lines.append(f"- `{key}`：`{value}`。")
    lines.extend(["", "## 无凭据 smoke", ""])
    for key, value in status["no_credentials_smoke"].items():
        if key.endswith("_tail"):
            continue
        lines.append(f"- `{key}`：`{value}`。")
    lines.extend(["", "## Blocking", ""])
    for item in status["blocking"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args()
    status = build_status()
    args.status_path.parent.mkdir(parents=True, exist_ok=True)
    with args.status_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(status, ensure_ascii=False, indent=2) + "\n")
    write_report(status, args.report_path)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
