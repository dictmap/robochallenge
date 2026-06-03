#!/usr/bin/env python3
"""Build and audit the RoboChallenge pi0.5 submission preparation package."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
RUNS_DIR = ROOT / "runs"
SUBMISSION_DIR = ROOT / "submission"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成并审计 RoboChallenge pi0.5 提交包清单和最小提交模板。")
    parser.add_argument(
        "--status-path",
        type=Path,
        default=RUNS_DIR / "robochallenge_submission_package_audit.json",
        help="机器可读审计 JSON 输出路径。",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=REPORTS_DIR / "robochallenge_submission_package_checklist.md",
        help="中文提交清单报告输出路径。",
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=SUBMISSION_DIR / "submission_manifest_template.json",
        help="提交包 manifest 模板输出路径。",
    )
    parser.add_argument(
        "--runner-path",
        type=Path,
        default=SUBMISSION_DIR / "run_table30v2_aloha_demo_template.sh",
        help="不含明文凭据的 demo.py 启动模板输出路径。",
    )
    parser.add_argument(
        "--lora-runner-path",
        type=Path,
        default=SUBMISSION_DIR / "run_table30v2_aloha_lora_demo_template.sh",
        help="默认指向本地物化 LoRA checkpoint 的 demo.py 启动模板输出路径。",
    )
    parser.add_argument(
        "--readme-path",
        type=Path,
        default=SUBMISSION_DIR / "README.md",
        help="submission 目录说明输出路径。",
    )
    return parser.parse_args()


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def git_check_ignore(path: Path) -> dict[str, Any]:
    rel_path = path.relative_to(ROOT)
    result = subprocess.run(
        ["git", "-C", str(ROOT), "check-ignore", "-v", str(rel_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "path": str(rel_path),
        "ignored": result.returncode == 0,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def has_arg(source: str, name: str) -> bool:
    pattern = rf"add_argument\(\s*['\"]--{re.escape(name)}['\"]"
    return re.search(pattern, source) is not None


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def bash_syntax_check(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        ["bash", "-n", str(path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "returncode": result.returncode,
        "passed": result.returncode == 0,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def no_credentials_failfast_check(path: Path) -> dict[str, Any]:
    env = os.environ.copy()
    for key in ["ROBOCHALLENGE_USER_TOKEN", "ROBOCHALLENGE_SUBMISSION_ID"]:
        env.pop(key, None)
    result = subprocess.run(
        ["bash", str(path)],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=10,
    )
    output = "\n".join([result.stdout.strip(), result.stderr.strip()]).strip()
    return {
        "returncode": result.returncode,
        "passed": result.returncode != 0 and "ROBOCHALLENGE_USER_TOKEN" in output and "Traceback" not in output,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def placeholder_credentials_failfast_check(path: Path) -> dict[str, Any]:
    env = os.environ.copy()
    env["ROBOCHALLENGE_USER_TOKEN"] = "<真实 user token>"
    env["ROBOCHALLENGE_SUBMISSION_ID"] = "<真实 submission id>"
    result = subprocess.run(
        ["bash", str(path)],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=10,
    )
    output = "\n".join([result.stdout.strip(), result.stderr.strip()]).strip()
    return {
        "returncode": result.returncode,
        "passed": result.returncode != 0 and "占位符" in output and "Traceback" not in output,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def dry_run_no_contact_check(path: Path) -> dict[str, Any]:
    env = os.environ.copy()
    token_value = "local-dry-run-token-value"
    submission_value = "local-dry-run-submission-value"
    checkpoint_value = "https://example.invalid/private-checkpoint-link?dry_run_secret=1"
    env["ROBOCHALLENGE_USER_TOKEN"] = token_value
    env["ROBOCHALLENGE_SUBMISSION_ID"] = submission_value
    env["ROBOCHALLENGE_CHECKPOINT"] = checkpoint_value
    env["ROBOCHALLENGE_DRY_RUN"] = "1"
    result = subprocess.run(
        ["bash", str(path)],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=10,
    )
    output = "\n".join([result.stdout.strip(), result.stderr.strip()]).strip()
    printed_secret = token_value in output or submission_value in output
    printed_checkpoint = checkpoint_value in output
    has_checkpoint_length = "checkpoint_length=" in output
    return {
        "returncode": result.returncode,
        "passed": result.returncode == 0
        and "dry_run=true" in output
        and has_checkpoint_length
        and not printed_secret
        and not printed_checkpoint
        and "Traceback" not in output,
        "printed_secret": printed_secret,
        "printed_checkpoint": printed_checkpoint,
        "has_checkpoint_length": has_checkpoint_length,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def audit_runner_file(path: Path, expected_checkpoint_fragment: str) -> dict[str, Any]:
    exists = path.exists()
    text = path.read_text(encoding="utf-8") if exists else ""
    syntax = bash_syntax_check(path) if exists else {"passed": False, "stderr": "runner missing"}
    failfast = no_credentials_failfast_check(path) if exists else {"passed": False, "stderr": "runner missing"}
    placeholder_failfast = (
        placeholder_credentials_failfast_check(path) if exists else {"passed": False, "stderr": "runner missing"}
    )
    dry_run = dry_run_no_contact_check(path) if exists else {"passed": False, "stderr": "runner missing"}
    return {
        "path": str(path.relative_to(ROOT)),
        "exists": exists,
        "mentions_user_token": "ROBOCHALLENGE_USER_TOKEN" in text,
        "mentions_submission_id": "ROBOCHALLENGE_SUBMISSION_ID" in text,
        "mentions_expected_checkpoint": expected_checkpoint_fragment in text,
        "mentions_placeholder_guard": "reject_placeholder" in text,
        "mentions_dry_run_guard": "ROBOCHALLENGE_DRY_RUN" in text,
        "contains_plaintext_secret_pattern": bool(
            re.search(r"sk-[A-Za-z0-9_-]{20,}|hf_[A-Za-z0-9]{20,}|ROBOCHALLENGE_\w*TOKEN\s*=\s*[A-Za-z0-9_-]{20,}", text)
        ),
        "bash_n": syntax,
        "no_credentials_failfast": failfast,
        "placeholder_credentials_failfast": placeholder_failfast,
        "dry_run_no_contact": dry_run,
    }


def build_manifest(status: dict[str, Any]) -> dict[str, Any]:
    selected = status["selected_target"]
    restore = status["model_restore_materials"]
    return {
        "kind": "robochallenge_submission_manifest_template",
        "status": "template_pending_credentials",
        "language": "zh-CN",
        "target": {
            "benchmark": "Table30v2",
            "robot_type": selected["robot_type"],
            "task_name": selected["task_name"],
            "prompt": selected["prompt"],
            "note": "当前可运行链路是 Table30v2 ALOHA；原始 Table30 数据/配置仍需单独补齐后才能声明 Table30 原榜单提交。",
        },
        "required_runtime_inputs": {
            "ROBOCHALLENGE_USER_TOKEN": "用户登录 RoboChallenge 后提供；不能写入仓库。",
            "ROBOCHALLENGE_SUBMISSION_ID": "在 My Submission/Detail 页面获得；不能伪造。",
            "ROBOCHALLENGE_DRY_RUN": "可选；设为 1 时只打印不含凭据的本地命令摘要，不调用 demo.py。",
            "ROBOCHALLENGE_CHECKPOINT": "baseline runner 默认使用官方 ALOHA checkpoint；LoRA runner 默认使用本地物化 checkpoint，可按需覆盖。",
            "ROBOCHALLENGE_PROMPT": "默认使用当前任务 prompt，可按当前 run prompt 覆盖。",
        },
        "runner_templates": {
            "baseline": status["outputs"]["runner"],
            "lora_materialized": status["outputs"]["lora_runner"],
        },
        "current_verified_entrypoint": status["entrypoint_audit"],
        "model_restore_materials": restore,
        "evidence_files": {
            "mock_smoke": "runs/policy_smoke_aloha_status.json",
            "table30v2_mapping": "runs/table30v2_aloha_mapping_audit.json",
            "lora_restore_audit": "runs/openpi_rtc_lora_checkpoint_restore_audit.json",
            "workspace_validator": "scripts/validate_repro_workspace.py",
            "notebook": "notebooks/robochallenge_pi05_submit_cn.ipynb",
        },
        "links_to_fill_before_web_submission": {
            "checkpoint_link": "需要填真实可访问 checkpoint 链接；baseline 可指向官方模型，LoRA 版本需要先上传本地物化 checkpoint。",
            "inference_code_link": "建议填 GitHub 仓库链接：https://github.com/dictmap/robochallenge/tree/main",
            "fine_tuning_code_link": "建议填同仓库脚本、Notebook 和报告；LoRA 训练/恢复/物化证据已在仓库内记录。",
        },
        "blocking": status["blocking"],
    }


def write_runner(path: Path, selected: dict[str, Any], title: str, default_checkpoint: str) -> None:
    prompt = selected["prompt"]
    quoted_prompt = shell_quote(prompt)
    quoted_checkpoint = shell_quote(default_checkpoint)
    content = f"""#!/usr/bin/env bash
set -euo pipefail

# RoboChallenge Table30v2 ALOHA pi0.5 {title} 提交启动模板。
# 不要把真实 token 写进仓库；运行前在 shell 里 export。
: "${{ROBOCHALLENGE_USER_TOKEN:?请先 export ROBOCHALLENGE_USER_TOKEN}}"
: "${{ROBOCHALLENGE_SUBMISSION_ID:?请先 export ROBOCHALLENGE_SUBMISSION_ID}}"

reject_placeholder() {{
  local name="$1"
  local value="$2"
  case "$value" in
    *"<"*|*">"*|*"真实"*|*"占位"*|*"placeholder"*|*"PLACEHOLDER"*|*"replace_me"*|*"REPLACE_ME"*|*"example"*|*"EXAMPLE"*)
      echo "$name 看起来仍是占位符，请设置真实值。" >&2
      exit 64
      ;;
  esac
}}

reject_placeholder ROBOCHALLENGE_USER_TOKEN "$ROBOCHALLENGE_USER_TOKEN"
reject_placeholder ROBOCHALLENGE_SUBMISSION_ID "$ROBOCHALLENGE_SUBMISSION_ID"

cd "$(dirname "$0")/.."

DEFAULT_CHECKPOINT={quoted_checkpoint}
DEFAULT_PROMPT={quoted_prompt}
CHECKPOINT="${{ROBOCHALLENGE_CHECKPOINT:-$DEFAULT_CHECKPOINT}}"
PROMPT="${{ROBOCHALLENGE_PROMPT:-$DEFAULT_PROMPT}}"

if [[ "${{ROBOCHALLENGE_DRY_RUN:-0}}" == "1" ]]; then
  echo "dry_run=true"
  echo "checkpoint_length=${{#CHECKPOINT}}"
  echo "prompt_length=${{#PROMPT}}"
  echo "user_token_length=${{#ROBOCHALLENGE_USER_TOKEN}}"
  echo "submission_id_length=${{#ROBOCHALLENGE_SUBMISSION_ID}}"
  echo "robot_type=aloha"
  exit 0
fi

python3 demo.py \\
  --user_token "$ROBOCHALLENGE_USER_TOKEN" \\
  --submission_id "$ROBOCHALLENGE_SUBMISSION_ID" \\
  --checkpoint "$CHECKPOINT" \\
  --prompt "$PROMPT" \\
  --action_type joint \\
  --duration 0.033 \\
  --valid_action_num 30 \\
  --image_size "640x480" \\
  --robot_type aloha
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def write_readme(path: Path, manifest_rel: str, runner_rel: str, lora_runner_rel: str) -> None:
    content = f"""# RoboChallenge 提交包模板

本目录只保存提交准备材料，不保存明文 `user_token`、`submission_id` 或大模型权重。

- `{manifest_rel}`：机器可读提交 manifest 模板。
- `{runner_rel}`：Table30v2 ALOHA baseline 的 `demo.py` 启动模板。
- `{lora_runner_rel}`：Table30v2 ALOHA LoRA 完整物化 checkpoint 的 `demo.py` 启动模板。
- `submission/REAL_SUBMISSION_HANDOFF.md`：用户确认 Table30v2/ALOHA/baseline 提交对象并拿到 token、submission id 后的真实提交交接清单；baseline 路线不需要 checkpoint link，LoRA/web checkpoint 路线才需要 link。

当前默认稳妥提交路线仍是官方 pi0.5 Table30v2 ALOHA baseline。该路线使用 Linux 上已有的官方 ALOHA checkpoint，本地 runner 不需要生成 LoRA tar，也不需要 checkpoint link。LoRA scoped checkpoint 已被物化为本地完整 checkpoint，并通过 `create_trained_policy` 加载 smoke；只有选择 LoRA/web checkpoint 路线时，才需要用户提供凭据并把本地 checkpoint 上传成网站可访问链接。

baseline 真实运行前需要用户在 shell 中提供 `ROBOCHALLENGE_SUBMISSION_TARGET_CONFIRMATION=CONFIRM_TABLE30V2_ALOHA_BASELINE`、`ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline` 和 `ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION`；不要把具体值写入仓库、Notebook 或报告。runner 会拒绝 `<真实 ...>`、`example`、`replace_me` 这类占位符。可以先设置 `ROBOCHALLENGE_DRY_RUN=1` 做不连接平台的本地命令摘要检查，输出不会包含 token、submission id 或 checkpoint/link 明文。设置好之后运行：

```bash
bash {runner_rel}
# 或本地 LoRA 物化 checkpoint 路线：
bash {lora_runner_rel}
```
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_report(status: dict[str, Any], report_path: Path) -> None:
    selected = status["selected_target"]
    entry = status["entrypoint_audit"]
    restore = status["model_restore_materials"]
    lines = [
        "# RoboChallenge 提交包清单",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 当前可运行目标：`Table30v2 / {selected['robot_type']} / {selected['task_name']}`。",
        "- 官方 Table30v2 ALOHA baseline 仍是最稳的提交模板。",
        f"- LoRA 完整物化 checkpoint 本地可读：`{restore['direct_demo_checkpoint_ready']}`。",
        "- 真实提交仍不能伪造 token 或 submission_id；checkpoint link 只属于 LoRA/web checkpoint 路线。",
        "",
        "## 已准备材料",
        "",
        f"- 提交 manifest 模板：`{status['outputs']['manifest']}`。",
        f"- 启动脚本模板：`{status['outputs']['runner']}`。",
        f"- LoRA 启动脚本模板：`{status['outputs']['lora_runner']}`。",
        f"- submission 目录说明：`{status['outputs']['readme']}`。",
        f"- `demo.py` 必需参数覆盖：`{entry['required_args_present']}`。",
        f"- baseline runner 语法检查：`{status['runner_audit']['baseline']['bash_n']['passed']}`，无凭据 fail-fast：`{status['runner_audit']['baseline']['no_credentials_failfast']['passed']}`。",
        f"- baseline runner 占位符凭据 fail-fast：`{status['runner_audit']['baseline']['placeholder_credentials_failfast']['passed']}`。",
        f"- baseline runner dry-run 不连接平台：`{status['runner_audit']['baseline']['dry_run_no_contact']['passed']}`，打印凭据：`{status['runner_audit']['baseline']['dry_run_no_contact']['printed_secret']}`，打印 checkpoint/link 明文：`{status['runner_audit']['baseline']['dry_run_no_contact']['printed_checkpoint']}`。",
        f"- LoRA runner 语法检查：`{status['runner_audit']['lora']['bash_n']['passed']}`，无凭据 fail-fast：`{status['runner_audit']['lora']['no_credentials_failfast']['passed']}`。",
        f"- LoRA runner 占位符凭据 fail-fast：`{status['runner_audit']['lora']['placeholder_credentials_failfast']['passed']}`。",
        f"- LoRA runner dry-run 不连接平台：`{status['runner_audit']['lora']['dry_run_no_contact']['passed']}`，打印凭据：`{status['runner_audit']['lora']['dry_run_no_contact']['printed_secret']}`，打印 checkpoint/link 明文：`{status['runner_audit']['lora']['dry_run_no_contact']['printed_checkpoint']}`。",
        f"- mock 验证：`passed={status['evidence']['mock_smoke_passed']}`。",
        f"- Table30v2 ALOHA 映射：`ready={status['evidence']['table30v2_mapping_ready']}`。",
        f"- LoRA restore 审计：`passed={restore['restore_audit_passed']}`，合并后占位 leaf `{restore['placeholder_after_count']}`。",
        f"- LoRA 完整 checkpoint：`{restore['materialized_checkpoint']}`，本地存在 `{restore['materialized_checkpoint_exists']}`，Git 忽略 `{restore['materialized_checkpoint_git_ignored']}`。",
        f"- LoRA policy 加载 smoke：`passed={restore['policy_smoke_passed']}`，模型类型 `{restore['policy_smoke_model_type']}`。",
        "",
        "## 提交时需要用户提供",
        "",
        "- `ROBOCHALLENGE_USER_TOKEN`：用户登录后获得，不能写入仓库。",
        "- `ROBOCHALLENGE_SUBMISSION_ID`：在网站提交详情页获得，不能伪造。",
        "- 如果提交 LoRA 版本，还需要把本地 12GB+ checkpoint 放到网站可访问的 checkpoint link。",
        "- 如果目标切回原始 Table30，需要重新补齐对应数据和配置；当前可运行链路是 Table30v2 ALOHA。",
        "",
        "## 建议填入网站的链接位",
        "",
        "- `Inference Code Link`：`https://github.com/dictmap/robochallenge/tree/main`。",
        "- `Fine-tuning Code Link`：同仓库中的 `scripts/`、`notebooks/`、`reports/`。",
        "- `Checkpoint Link`：baseline 可指向官方 ALOHA checkpoint；LoRA 版本需要上传本地物化 checkpoint 后填可访问链接。",
        "",
        "## Blocking",
        "",
    ]
    for item in status["blocking"]:
        lines.append(f"- {item}")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    demo_source = (ROOT / "demo.py").read_text(encoding="utf-8")
    selected_config = read_json(RUNS_DIR / "selected_robot_config.json", {})
    mapping = read_json(RUNS_DIR / "table30v2_aloha_mapping_audit.json", {})
    mock_smoke = read_json(RUNS_DIR / "policy_smoke_aloha_status.json", {})
    restore = read_json(RUNS_DIR / "openpi_rtc_lora_checkpoint_restore_audit.json", {})
    lora_grad = read_json(RUNS_DIR / "openpi_rtc_lora_numeric_grad_reduced_status.json", {})
    materialize = read_json(RUNS_DIR / "openpi_rtc_lora_inference_checkpoint_materialize_status.json", {})
    policy_smoke = read_json(RUNS_DIR / "openpi_rtc_lora_materialized_policy_smoke_status.json", {})

    selected_target = {
        "benchmark": "Table30v2",
        "robot_type": selected_config.get("robot_type", "aloha"),
        "robot_tag": selected_config.get("robot_tag", "aloha"),
        "task_name": mapping.get("task_info", {}).get("task_desc", {}).get("task_name", "pack_the_toothbrush_holder"),
        "prompt": selected_config.get("prompt", ""),
        "checkpoint": selected_config.get("checkpoint", ""),
        "checkpoint_exists": Path(selected_config.get("checkpoint", "")).exists(),
        "lora_materialized_checkpoint": "runs/openpi_rtc_lora_materialized_policy_checkpoint",
    }
    required_args = [
        "user_token",
        "submission_id",
        "checkpoint",
        "prompt",
        "action_type",
        "duration",
        "valid_action_num",
        "image_size",
        "robot_type",
    ]
    required_args_present = {name: has_arg(demo_source, name) for name in required_args}
    scoped_npz = ROOT / "runs/openpi_rtc_lora_grad_checkpoint/trainable_params_step1.npz"
    checkpoint_ignore = git_check_ignore(scoped_npz)
    materialized_checkpoint = ROOT / "runs/openpi_rtc_lora_materialized_policy_checkpoint"
    materialized_checkpoint_ignore = git_check_ignore(materialized_checkpoint / "params/_METADATA")
    merge = restore.get("merge_audit", {})
    materialize_result = materialize.get("materialize", {})
    policy_load = policy_smoke.get("policy_load_smoke", {})
    materialized_ready = bool(
        materialize.get("passed")
        and materialize.get("direct_demo_checkpoint_ready")
        and materialize_result.get("passed")
        and policy_smoke.get("passed")
        and policy_load.get("passed")
    )

    status: dict[str, Any] = {
        "passed": False,
        "selected_target": selected_target,
        "entrypoint_audit": {
            "demo_py_exists": (ROOT / "demo.py").exists(),
            "test_py_exists": (ROOT / "test.py").exists(),
            "required_args_present": required_args_present,
            "api_base_url_present": "api.robochallenge.cn" in (ROOT / "robot/interface_client.py").read_text(
                encoding="utf-8"
            ),
            "job_loop_uses_submission_id": "get_all_runs(submission_id)" in (
                ROOT / "robot/job_worker.py"
            ).read_text(encoding="utf-8"),
        },
        "evidence": {
            "mock_smoke_passed": bool(mock_smoke.get("smoke") == "passed" or mock_smoke.get("passed")),
            "table30v2_mapping_ready": bool(mapping.get("ready_for_dry_run_converter")),
            "notebook_exists": (ROOT / "notebooks/robochallenge_pi05_submit_cn.ipynb").exists(),
            "validator_exists": (ROOT / "scripts/validate_repro_workspace.py").exists(),
        },
        "model_restore_materials": {
            "official_aloha_checkpoint": selected_target["checkpoint"],
            "official_aloha_checkpoint_exists": selected_target["checkpoint_exists"],
            "pi05_base_params": "/home/yjl/.cache/openpi/openpi-assets/checkpoints/pi05_base/params",
            "scoped_checkpoint_npz": "runs/openpi_rtc_lora_grad_checkpoint/trainable_params_step1.npz",
            "scoped_checkpoint_exists": scoped_npz.exists(),
            "scoped_checkpoint_git_ignored": checkpoint_ignore["ignored"],
            "restore_audit_passed": bool(restore.get("passed")),
            "checkpoint_key_count": merge.get("checkpoint_key_count"),
            "trainable_filter_key_count": merge.get("trainable_filter_key_count"),
            "placeholder_after_count": merge.get("placeholder_after_count"),
            "lora_grad_passed": bool(lora_grad.get("passed")),
            "materialized_checkpoint": "runs/openpi_rtc_lora_materialized_policy_checkpoint",
            "materialized_checkpoint_exists": materialized_checkpoint.exists(),
            "materialized_checkpoint_git_ignored": materialized_checkpoint_ignore["ignored"],
            "materialize_passed": bool(materialize.get("passed") and materialize_result.get("passed")),
            "materialized_restored_leaf_count": materialize_result.get("restored_leaf_count"),
            "policy_smoke_passed": bool(policy_smoke.get("passed") and policy_load.get("passed")),
            "policy_smoke_model_type": policy_load.get("model_type"),
            "direct_demo_checkpoint_ready": materialized_ready,
            "direct_demo_checkpoint_note": "LoRA checkpoint 已本地物化为 demo.py/create_trained_policy 可读的完整 policy checkpoint；只有 LoRA/web checkpoint 网站路线才需要用户授权上传并提供真实可访问 checkpoint link。baseline 官方 ALOHA 路线不需要 checkpoint link。",
        },
        "outputs": {
            "report": str(args.report_path.relative_to(ROOT)),
            "manifest": str(args.manifest_path.relative_to(ROOT)),
            "runner": str(args.runner_path.relative_to(ROOT)),
            "lora_runner": str(args.lora_runner_path.relative_to(ROOT)),
            "readme": str(args.readme_path.relative_to(ROOT)),
        },
        "runner_audit": {},
        "blocking": [
            "baseline 真实提交需要用户确认目标：ROBOCHALLENGE_SUBMISSION_TARGET_CONFIRMATION=CONFIRM_TABLE30V2_ALOHA_BASELINE。",
            "需要用户提供真实 ROBOCHALLENGE_USER_TOKEN。",
            "需要用户提供真实 ROBOCHALLENGE_SUBMISSION_ID。",
            "baseline 真实提交需要 ROBOCHALLENGE_SUBMISSION_VARIANT=baseline 和真实 runner 强确认。",
            "若选择 LoRA/web checkpoint 路线，还需要把本地 12GB+ checkpoint 放到网站可访问的 checkpoint link。",
        ],
    }

    args.status_path.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_path.parent.mkdir(parents=True, exist_ok=True)
    write_runner(args.runner_path, selected_target, "官方 baseline checkpoint", selected_target["checkpoint"])
    write_runner(
        args.lora_runner_path,
        selected_target,
        "LoRA 完整物化 checkpoint",
        selected_target["lora_materialized_checkpoint"],
    )
    write_readme(
        args.readme_path,
        args.manifest_path.relative_to(ROOT).as_posix(),
        args.runner_path.relative_to(ROOT).as_posix(),
        args.lora_runner_path.relative_to(ROOT).as_posix(),
    )
    status["runner_audit"] = {
        "baseline": audit_runner_file(args.runner_path, selected_target["checkpoint"]),
        "lora": audit_runner_file(args.lora_runner_path, selected_target["lora_materialized_checkpoint"]),
    }

    status["passed"] = all(
        [
            status["entrypoint_audit"]["demo_py_exists"],
            status["entrypoint_audit"]["test_py_exists"],
            all(required_args_present.values()),
            status["entrypoint_audit"]["api_base_url_present"],
            status["entrypoint_audit"]["job_loop_uses_submission_id"],
            status["evidence"]["mock_smoke_passed"],
            status["evidence"]["table30v2_mapping_ready"],
            status["model_restore_materials"]["official_aloha_checkpoint_exists"],
            status["model_restore_materials"]["scoped_checkpoint_exists"],
            status["model_restore_materials"]["scoped_checkpoint_git_ignored"],
            status["model_restore_materials"]["restore_audit_passed"],
            status["model_restore_materials"]["placeholder_after_count"] == 0,
            status["model_restore_materials"]["materialized_checkpoint_exists"],
            status["model_restore_materials"]["materialized_checkpoint_git_ignored"],
            status["model_restore_materials"]["materialize_passed"],
            status["model_restore_materials"]["policy_smoke_passed"],
            status["model_restore_materials"]["direct_demo_checkpoint_ready"],
            status["runner_audit"]["baseline"]["exists"],
            status["runner_audit"]["baseline"]["mentions_user_token"],
            status["runner_audit"]["baseline"]["mentions_submission_id"],
            status["runner_audit"]["baseline"]["mentions_expected_checkpoint"],
            status["runner_audit"]["baseline"]["mentions_placeholder_guard"],
            status["runner_audit"]["baseline"]["mentions_dry_run_guard"],
            not status["runner_audit"]["baseline"]["contains_plaintext_secret_pattern"],
            status["runner_audit"]["baseline"]["bash_n"]["passed"],
            status["runner_audit"]["baseline"]["no_credentials_failfast"]["passed"],
            status["runner_audit"]["baseline"]["placeholder_credentials_failfast"]["passed"],
            status["runner_audit"]["baseline"]["dry_run_no_contact"]["passed"],
            not status["runner_audit"]["baseline"]["dry_run_no_contact"]["printed_secret"],
            status["runner_audit"]["lora"]["exists"],
            status["runner_audit"]["lora"]["mentions_user_token"],
            status["runner_audit"]["lora"]["mentions_submission_id"],
            status["runner_audit"]["lora"]["mentions_expected_checkpoint"],
            status["runner_audit"]["lora"]["mentions_placeholder_guard"],
            status["runner_audit"]["lora"]["mentions_dry_run_guard"],
            not status["runner_audit"]["lora"]["contains_plaintext_secret_pattern"],
            status["runner_audit"]["lora"]["bash_n"]["passed"],
            status["runner_audit"]["lora"]["no_credentials_failfast"]["passed"],
            status["runner_audit"]["lora"]["placeholder_credentials_failfast"]["passed"],
            status["runner_audit"]["lora"]["dry_run_no_contact"]["passed"],
            not status["runner_audit"]["lora"]["dry_run_no_contact"]["printed_secret"],
        ]
    )

    args.manifest_path.write_text(
        json.dumps(build_manifest(status), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_report(status, args.report_path)
    args.status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
