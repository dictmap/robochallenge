#!/usr/bin/env python3
"""Audit the guarded real-runner wrapper without contacting RoboChallenge."""

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
TEMPLATE = ROOT / "submission" / "run_ready_real_submission_template.sh"
DEFAULT_STATUS = RUNS_DIR / "ready_real_runner_template_audit.json"
DEFAULT_REPORT = REPORTS_DIR / "ready_real_runner_template_audit.md"
CONFIRM_PHRASE = "RUN_REAL_ROBOCHALLENGE_SUBMISSION"
WRONG_CONFIRM_PHRASE = "RUN_REAL_ROBOCHALLENGE_SUBMISSION_WRONG"
MALFORMED_CONFIRM_CASES = [
    ("trailing_space", CONFIRM_PHRASE + " "),
    ("leading_space", " " + CONFIRM_PHRASE),
    ("lowercase", CONFIRM_PHRASE.lower()),
    ("newline", CONFIRM_PHRASE + "\n"),
]
SYNTHETIC_TOKEN = "audit-token-shape-only"
SYNTHETIC_SUBMISSION_ID = "audit-submission-shape-only"

SECRET_PATTERNS = [
    r"sk-[A-Za-z0-9_-]{30,}",
    r"hf_[A-Za-z0-9]{20,}",
    r"ghp_[A-Za-z0-9]{30,}",
    r"github_pat_[A-Za-z0-9_]{20,}",
]

REQUIRED_FRAGMENTS = {
    "sources_local_env_file": "source \"$ENV_FILE\"",
    "runs_link_intake": "python3 scripts/audit_checkpoint_link_intake.py --scenario-only",
    "runs_download_default": "python3 scripts/audit_checkpoint_link_download_verification.py",
    "download_verify_guarded": "--verify-download",
    "runs_readiness": "python3 scripts/audit_real_submission_readiness.py",
    "reads_readiness_json": "runs/real_submission_readiness.json",
    "default_variant_baseline": 'VARIANT="${ROBOCHALLENGE_SUBMISSION_VARIANT:-baseline}"',
    "checks_lora_ready": "local_lora_runner_ready",
    "checks_baseline_ready": "local_baseline_runner_ready",
    "lora_dry_run_first": "ROBOCHALLENGE_DRY_RUN=1 bash submission/run_table30v2_aloha_lora_demo_template.sh",
    "baseline_dry_run_first": "ROBOCHALLENGE_DRY_RUN=1 bash submission/run_table30v2_aloha_demo_template.sh",
    "requires_confirmation": "ROBOCHALLENGE_REAL_RUN_CONFIRM",
    "confirmation_phrase": CONFIRM_PHRASE,
    "lora_real_runner_available": "bash submission/run_table30v2_aloha_lora_demo_template.sh",
    "baseline_real_runner_available": "bash submission/run_table30v2_aloha_demo_template.sh",
}

FORBIDDEN_FRAGMENTS = {
    "creates_large_archive": "--confirm-create-large-archive",
    "uploads_with_rclone": "rclone copy",
    "uploads_with_aws": "aws s3 cp",
    "uploads_with_curl": "curl -T",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计强确认真实 runner 模板；不连接平台、不上传、不打印凭据。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文审计报告输出路径。")
    return parser.parse_args()


def bash_syntax(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        ["bash", "-n", str(path)],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {"returncode": result.returncode, "passed": result.returncode == 0, "stderr": (result.stderr or "").strip()}


def clean_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    for key in [
        "ROBOCHALLENGE_USER_TOKEN",
        "ROBOCHALLENGE_SUBMISSION_ID",
        "ROBOCHALLENGE_CHECKPOINT_LINK",
        "ROBOCHALLENGE_LORA_CHECKPOINT_LINK",
        "ROBOCHALLENGE_CHECKPOINT",
        "ROBOCHALLENGE_REAL_RUN_CONFIRM",
        "ROBOCHALLENGE_ENV_FILE",
        "ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD",
        "ROBOCHALLENGE_SUBMISSION_VARIANT",
        "ROBOCHALLENGE_DRY_RUN",
    ]:
        env.pop(key, None)
    if extra:
        env.update(extra)
    return env


def run_template(extra_env: dict[str, str]) -> dict[str, Any]:
    env = clean_env(extra_env)
    protected_keys = {
        "ROBOCHALLENGE_USER_TOKEN",
        "ROBOCHALLENGE_SUBMISSION_ID",
        "ROBOCHALLENGE_CHECKPOINT_LINK",
        "ROBOCHALLENGE_LORA_CHECKPOINT_LINK",
    }
    values_to_protect = [value for key, value in extra_env.items() if key in protected_keys and value]
    result = subprocess.run(
        ["bash", "submission/run_ready_real_submission_template.sh"],
        cwd=ROOT,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=120,
    )
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    combined = stdout + "\n" + stderr
    leaked_values = [value for value in values_to_protect if value in combined]
    variant = ""
    for line in combined.splitlines():
        if line.startswith("[ready-real-runner] variant="):
            variant = line.split("=", 1)[1].strip()
    return {
        "returncode": result.returncode,
        "stdout_tail": stdout[-3000:],
        "stderr_tail": stderr[-3000:],
        "variant": variant,
        "printed_protected_values": bool(leaked_values),
        "leaked_value_count": len(leaked_values),
        "ready_false": "ready_for_real_submission=false" in combined,
        "dry_run_called": "dry_run=true" in combined,
        "missing_confirmation": "missing explicit real-run confirmation" in combined,
        "confirmation_present": "confirmation_present=true" in combined,
        "stops_before_real_runner": "stop before real runner" in combined,
        "real_runner_started": "confirmation accepted; starting real runner" in combined,
        "demo_mentioned": "demo.py" in combined,
    }


def restore_clean_submission_state() -> dict[str, Any]:
    env = clean_env()
    commands = [
        ["python3", "scripts/audit_checkpoint_link_intake.py"],
        ["python3", "scripts/audit_checkpoint_link_download_verification.py"],
        ["python3", "scripts/audit_real_submission_readiness.py"],
    ]
    results = []
    for command in commands:
        result = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=120,
        )
        results.append({"command": " ".join(command), "returncode": result.returncode})
    return {"passed": all(item["returncode"] == 0 for item in results), "commands": results}


def scan_secret_patterns(text: str) -> list[str]:
    return [pattern for pattern in SECRET_PATTERNS if re.search(pattern, text)]


def build_status() -> dict[str, Any]:
    text = TEMPLATE.read_text(encoding="utf-8") if TEMPLATE.exists() else ""
    required = {name: fragment in text for name, fragment in REQUIRED_FRAGMENTS.items()}
    forbidden = {name: fragment in text for name, fragment in FORBIDDEN_FRAGMENTS.items()}
    bash_n = bash_syntax(TEMPLATE)

    no_credentials = run_template(
        {
            "ROBOCHALLENGE_ENV_FILE": str(ROOT / "submission" / "__missing_env_for_real_runner_audit__.sh"),
            "ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD": "0",
        }
    )
    synthetic_no_confirm = run_template(
        {
            "ROBOCHALLENGE_ENV_FILE": str(ROOT / "submission" / "__missing_env_for_real_runner_audit__.sh"),
            "ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD": "0",
            "ROBOCHALLENGE_USER_TOKEN": SYNTHETIC_TOKEN,
            "ROBOCHALLENGE_SUBMISSION_ID": SYNTHETIC_SUBMISSION_ID,
        }
    )
    synthetic_wrong_confirm = run_template(
        {
            "ROBOCHALLENGE_ENV_FILE": str(ROOT / "submission" / "__missing_env_for_real_runner_audit__.sh"),
            "ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD": "0",
            "ROBOCHALLENGE_USER_TOKEN": SYNTHETIC_TOKEN,
            "ROBOCHALLENGE_SUBMISSION_ID": SYNTHETIC_SUBMISSION_ID,
            "ROBOCHALLENGE_REAL_RUN_CONFIRM": WRONG_CONFIRM_PHRASE,
        }
    )
    malformed_confirmation_cases = []
    for name, confirm_value in MALFORMED_CONFIRM_CASES:
        item = run_template(
            {
                "ROBOCHALLENGE_ENV_FILE": str(ROOT / "submission" / "__missing_env_for_real_runner_audit__.sh"),
                "ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD": "0",
                "ROBOCHALLENGE_USER_TOKEN": SYNTHETIC_TOKEN,
                "ROBOCHALLENGE_SUBMISSION_ID": SYNTHETIC_SUBMISSION_ID,
                "ROBOCHALLENGE_REAL_RUN_CONFIRM": confirm_value,
            }
        )
        item["name"] = name
        item["confirm_value_length"] = len(confirm_value)
        malformed_confirmation_cases.append(item)
    restore = restore_clean_submission_state()

    no_credentials["passed"] = all(
        [
            no_credentials["returncode"] != 0,
            no_credentials["ready_false"],
            not no_credentials["dry_run_called"],
            not no_credentials["real_runner_started"],
            not no_credentials["demo_mentioned"],
            not no_credentials["printed_protected_values"],
        ]
    )
    synthetic_no_confirm["passed"] = all(
        [
            synthetic_no_confirm["returncode"] != 0,
            synthetic_no_confirm["variant"] == "baseline",
            synthetic_no_confirm["dry_run_called"],
            not synthetic_no_confirm["confirmation_present"],
            synthetic_no_confirm["missing_confirmation"],
            synthetic_no_confirm["stops_before_real_runner"],
            not synthetic_no_confirm["real_runner_started"],
            not synthetic_no_confirm["demo_mentioned"],
            not synthetic_no_confirm["printed_protected_values"],
        ]
    )
    synthetic_wrong_confirm["passed"] = all(
        [
            synthetic_wrong_confirm["returncode"] != 0,
            synthetic_wrong_confirm["variant"] == "baseline",
            synthetic_wrong_confirm["dry_run_called"],
            synthetic_wrong_confirm["confirmation_present"],
            synthetic_wrong_confirm["missing_confirmation"],
            synthetic_wrong_confirm["stops_before_real_runner"],
            not synthetic_wrong_confirm["real_runner_started"],
            not synthetic_wrong_confirm["demo_mentioned"],
            not synthetic_wrong_confirm["printed_protected_values"],
        ]
    )
    for item in malformed_confirmation_cases:
        item["passed"] = all(
            [
                item["returncode"] != 0,
                item["variant"] == "baseline",
                item["dry_run_called"],
                item["confirmation_present"],
                item["missing_confirmation"],
                item["stops_before_real_runner"],
                not item["real_runner_started"],
                not item["demo_mentioned"],
                not item["printed_protected_values"],
            ]
        )
    malformed_confirmation_cases_rejected = all(item["passed"] for item in malformed_confirmation_cases)

    secret_hits = scan_secret_patterns(text)
    passed = bool(
        TEMPLATE.exists()
        and bash_n["passed"]
        and all(required.values())
        and not any(forbidden.values())
        and not secret_hits
        and no_credentials["passed"]
        and synthetic_no_confirm["passed"]
        and synthetic_wrong_confirm["passed"]
        and malformed_confirmation_cases_rejected
        and restore["passed"]
    )
    return {
        "kind": "ready_real_runner_template_audit",
        "passed": passed,
        "platform_contacted": False,
        "uploads_performed": False,
        "credentials_read": False,
        "credentials_printed": False,
        "link_values_printed": False,
        "secret_values_printed": False,
        "template_path": "submission/run_ready_real_submission_template.sh",
        "confirmation_phrase": CONFIRM_PHRASE,
        "wrong_confirmation_phrase": WRONG_CONFIRM_PHRASE,
        "malformed_confirmation_case_count": len(malformed_confirmation_cases),
        "malformed_confirmation_cases_rejected": malformed_confirmation_cases_rejected,
        "malformed_confirmation_real_runner_started": any(
            item["real_runner_started"] for item in malformed_confirmation_cases
        ),
        "default_variant": "baseline" if REQUIRED_FRAGMENTS["default_variant_baseline"] in text else "",
        "bash_n": bash_n,
        "required_fragments": required,
        "forbidden_fragments": forbidden,
        "secret_patterns_found": secret_hits,
        "no_credentials_smoke": no_credentials,
        "synthetic_no_confirm_smoke": synthetic_no_confirm,
        "synthetic_wrong_confirm_smoke": synthetic_wrong_confirm,
        "malformed_confirmation_cases": malformed_confirmation_cases,
        "clean_state_restore": restore,
        "blocking": [
            "强确认真实 runner 模板已通过；没有确认短语或确认短语写错时都不会启动真实 runner。"
            if passed
            else "强确认真实 runner 模板仍存在阻塞，请查看 JSON 字段。"
        ],
    }


def write_report(status: dict[str, Any], path: Path) -> None:
    lines = [
        "# 强确认真实 runner 模板审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 模板路径：`{status['template_path']}`。",
        f"- 默认提交路线：`{status['default_variant']}`。",
        f"- 确认短语：`{status['confirmation_phrase']}`。",
        f"- 错误确认短语 smoke：`{status['synthetic_wrong_confirm_smoke']['passed']}`。",
        f"- bash 语法检查：`{status['bash_n']['passed']}`。",
        f"- 无凭据 smoke：`{status['no_credentials_smoke']['passed']}`。",
        f"- synthetic 无确认 smoke：`{status['synthetic_no_confirm_smoke']['passed']}`。",
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
    lines.extend(["", "## Smoke 结果", ""])
    lines.append(f"- 无凭据返回码：`{status['no_credentials_smoke']['returncode']}`。")
    lines.append(f"- 无凭据是否停在真实 runner 前：`{not status['no_credentials_smoke']['real_runner_started']}`。")
    lines.append(f"- synthetic 是否先 dry-run：`{status['synthetic_no_confirm_smoke']['dry_run_called']}`。")
    lines.append(f"- synthetic 默认路线：`{status['synthetic_no_confirm_smoke']['variant']}`。")
    lines.append(f"- synthetic 是否因缺少确认停止：`{status['synthetic_no_confirm_smoke']['missing_confirmation']}`。")
    lines.append(f"- synthetic 是否启动真实 runner：`{status['synthetic_no_confirm_smoke']['real_runner_started']}`。")
    lines.append(
        f"- synthetic 错误确认是否仍停在真实 runner 前：`{status['synthetic_wrong_confirm_smoke']['stops_before_real_runner']}`。"
    )
    lines.append(
        f"- synthetic 错误确认是否启动真实 runner：`{status['synthetic_wrong_confirm_smoke']['real_runner_started']}`。"
    )
    lines.append(f"- clean state restore：`{status['clean_state_restore']['passed']}`。")
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
