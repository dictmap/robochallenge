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
            "ROBOCHALLENGE_CHECKPOINT": "默认使用本机已验证 ALOHA baseline checkpoint，可按需覆盖。",
            "ROBOCHALLENGE_PROMPT": "默认使用当前任务 prompt，可按当前 run prompt 覆盖。",
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
            "checkpoint_link": "需要填真实可访问 checkpoint 链接；baseline 可指向 Hugging Face 官方模型，LoRA scoped 需要先打包完整恢复流程。",
            "inference_code_link": "建议填 GitHub 仓库链接：https://github.com/dictmap/robochallenge/tree/main",
            "fine_tuning_code_link": "建议填同仓库脚本和报告；若提交 LoRA 版本，需补完整训练/恢复脚本入口。",
        },
        "blocking": status["blocking"],
    }


def write_runner(path: Path, selected: dict[str, Any]) -> None:
    prompt = selected["prompt"]
    checkpoint = selected["checkpoint"]
    content = f"""#!/usr/bin/env bash
set -euo pipefail

# RoboChallenge Table30v2 ALOHA pi0.5 baseline 提交启动模板。
# 不要把真实 token 写进仓库；运行前在 shell 里 export。
: "${{ROBOCHALLENGE_USER_TOKEN:?请先 export ROBOCHALLENGE_USER_TOKEN}}"
: "${{ROBOCHALLENGE_SUBMISSION_ID:?请先 export ROBOCHALLENGE_SUBMISSION_ID}}"

CHECKPOINT="${{ROBOCHALLENGE_CHECKPOINT:-{checkpoint}}}"
PROMPT="${{ROBOCHALLENGE_PROMPT:-{prompt}}}"

cd "$(dirname "$0")/.."

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


def write_readme(path: Path, manifest_rel: str, runner_rel: str) -> None:
    content = f"""# RoboChallenge 提交包模板

本目录只保存提交准备材料，不保存明文 `user_token`、`submission_id` 或大模型权重。

- `{manifest_rel}`：机器可读提交 manifest 模板。
- `{runner_rel}`：Table30v2 ALOHA baseline 的 `demo.py` 启动模板。

当前默认可运行提交路线是官方 pi0.5 Table30v2 ALOHA baseline。LoRA scoped checkpoint 已通过恢复/合并审计，但它不是 `demo.py` 可直接消费的完整 checkpoint，不能单独作为 checkpoint 提交。

运行前需要用户在 shell 中提供 `ROBOCHALLENGE_USER_TOKEN` 和 `ROBOCHALLENGE_SUBMISSION_ID` 两个环境变量；不要把具体值写入仓库、Notebook 或报告。设置好之后运行：

```bash
bash {runner_rel}
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
        "- 当前最小提交模板走官方 pi0.5 Table30v2 ALOHA baseline；不会伪造网站 token 或 submission_id。",
        "- LoRA scoped checkpoint 已完成恢复/合并审计，但仍不是完整 policy checkpoint，不能单独给 `demo.py --checkpoint` 使用。",
        "",
        "## 已准备材料",
        "",
        f"- 提交 manifest 模板：`{status['outputs']['manifest']}`。",
        f"- 启动脚本模板：`{status['outputs']['runner']}`。",
        f"- submission 目录说明：`{status['outputs']['readme']}`。",
        f"- 入口脚本：`demo.py`，必需参数覆盖情况：`{entry['required_args_present']}`。",
        f"- mock 验证：`passed={status['evidence']['mock_smoke_passed']}`。",
        f"- Table30v2 ALOHA 映射：`ready={status['evidence']['table30v2_mapping_ready']}`。",
        f"- LoRA 恢复审计：`passed={restore['restore_audit_passed']}`，合并后占位 leaf `{restore['placeholder_after_count']}`。",
        "",
        "## 提交时需要用户提供",
        "",
        "- `ROBOCHALLENGE_USER_TOKEN`：用户登录后获得，不能写入仓库。",
        "- `ROBOCHALLENGE_SUBMISSION_ID`：在网站提交详情页获得，不能伪造。",
        "- 当前评测 run 的 prompt/robot/benchmark 是否仍为 Table30v2 ALOHA；若目标切回原始 Table30，需要重新补齐对应数据和配置。",
        "",
        "## 建议填入网站的链接位",
        "",
        "- `Inference Code Link`：`https://github.com/dictmap/robochallenge/tree/main`。",
        "- `Fine-tuning Code Link`：同仓库中的 `scripts/`、`notebooks/`、`reports/`。",
        "- `Checkpoint Link`：baseline 路线可指向官方 ALOHA baseline checkpoint；LoRA scoped 路线必须先打包为完整可恢复 checkpoint 或提供完整恢复说明。",
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

    selected_target = {
        "benchmark": "Table30v2",
        "robot_type": selected_config.get("robot_type", "aloha"),
        "robot_tag": selected_config.get("robot_tag", "aloha"),
        "task_name": mapping.get("task_info", {}).get("task_desc", {}).get("task_name", "pack_the_toothbrush_holder"),
        "prompt": selected_config.get("prompt", ""),
        "checkpoint": selected_config.get("checkpoint", ""),
        "checkpoint_exists": Path(selected_config.get("checkpoint", "")).exists(),
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
    merge = restore.get("merge_audit", {})

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
            "direct_demo_checkpoint_ready": False,
            "direct_demo_checkpoint_note": "scoped checkpoint 不是完整 checkpoint；demo.py 当前可直接使用的是官方 ALOHA baseline checkpoint。",
        },
        "outputs": {
            "report": str(args.report_path.relative_to(ROOT)),
            "manifest": str(args.manifest_path.relative_to(ROOT)),
            "runner": str(args.runner_path.relative_to(ROOT)),
            "readme": str(args.readme_path.relative_to(ROOT)),
        },
        "blocking": [
            "需要用户提供真实 ROBOCHALLENGE_USER_TOKEN。",
            "需要用户提供真实 ROBOCHALLENGE_SUBMISSION_ID。",
            "需要确认本次要提交的是 Table30v2 ALOHA 还是原始 Table30；当前可运行链路是 Table30v2 ALOHA。",
            "若要提交 LoRA scoped 路线，还需要把 scoped params 打包成 demo.py 可直接恢复的完整 policy 入口。",
        ],
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
        ]
    )

    args.status_path.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_path.parent.mkdir(parents=True, exist_ok=True)
    write_runner(args.runner_path, selected_target)
    write_readme(
        args.readme_path,
        args.manifest_path.relative_to(ROOT).as_posix(),
        args.runner_path.relative_to(ROOT).as_posix(),
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
