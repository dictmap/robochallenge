#!/usr/bin/env python3
"""Smoke-test loading a materialized openpi_rtc LoRA policy checkpoint."""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
from pathlib import Path
import sys
import time
from typing import Any


os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")
os.environ.setdefault("JAX_PLATFORMS", "cpu")

ROOT = Path(__file__).resolve().parents[1]
BASELINE = Path(os.environ.get("BASELINE", "/home/yjl/yjl/RoboChallenge/baseline_pi05_multitask"))
BASELINE_PYTHON = BASELINE / ".venv/bin/python3"
if (
    BASELINE_PYTHON.exists()
    and Path(sys.executable).resolve() != BASELINE_PYTHON.resolve()
    and os.environ.get("OPENPI_RTC_MATERIALIZED_POLICY_SMOKE_REEXEC") != "1"
):
    os.environ["OPENPI_RTC_MATERIALIZED_POLICY_SMOKE_REEXEC"] = "1"
    os.execv(str(BASELINE_PYTHON), [str(BASELINE_PYTHON), *sys.argv])

OPENPI_ROOT = BASELINE / "openpi"
OPENPI_SRC = OPENPI_ROOT / "src"
OPENPI_CLIENT_SRC = OPENPI_ROOT / "packages/openpi-client/src"
LEROBOT_SRC = Path(os.environ.get("LEROBOT_SRC", "/home/yjl/yjl/RoboChallenge/third_party/lerobot"))
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
DEFAULT_CHECKPOINT = RUNS_DIR / "openpi_rtc_lora_materialized_policy_checkpoint"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="加载完整物化 LoRA checkpoint 并构建 openpi_rtc Policy。")
    parser.add_argument("--config-name", default="cvpr_multitask_aloha_rtc", help="OpenPI RTC config 名称。")
    parser.add_argument("--checkpoint-dir", type=Path, default=DEFAULT_CHECKPOINT, help="完整物化 checkpoint 目录。")
    parser.add_argument("--paligemma-variant", default="gemma_2b_lora", help="LoRA PaliGemma variant。")
    parser.add_argument("--action-expert-variant", default="gemma_300m_lora", help="LoRA action expert variant。")
    parser.add_argument("--default-prompt", default="pack the toothbrush holder", help="默认 prompt。")
    parser.add_argument(
        "--status-path",
        type=Path,
        default=RUNS_DIR / "openpi_rtc_lora_materialized_policy_smoke_status.json",
        help="状态 JSON 输出路径。",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=REPORTS_DIR / "openpi_rtc_lora_materialized_policy_smoke.md",
        help="中文 smoke 报告输出路径。",
    )
    return parser.parse_args()


def ensure_import_paths() -> None:
    for path in [OPENPI_SRC, OPENPI_CLIENT_SRC, LEROBOT_SRC]:
        text = str(path)
        if text not in sys.path:
            sys.path.insert(0, text)


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path)


def checkpoint_layout(checkpoint_dir: Path, asset_id: str) -> dict[str, Any]:
    return {
        "checkpoint_dir": rel(checkpoint_dir),
        "exists": checkpoint_dir.exists(),
        "params_metadata_exists": (checkpoint_dir / "params/_METADATA").exists(),
        "params_checkpoint_metadata_exists": (checkpoint_dir / "params/_CHECKPOINT_METADATA").exists(),
        "params_manifest_exists": (checkpoint_dir / "params/manifest.ocdbt").exists(),
        "asset_norm_stats_exists": (checkpoint_dir / "assets" / asset_id / "norm_stats.json").exists(),
    }


def write_report(status: dict[str, Any], report_path: Path) -> None:
    smoke = status["policy_load_smoke"]
    layout = status["checkpoint_layout"]
    lines = [
        "# openpi_rtc LoRA 完整物化 policy 加载 smoke",
        "",
        "## 结论",
        "",
        f"- smoke 状态：`passed={status['passed']}`。",
        f"- checkpoint：`{layout['checkpoint_dir']}`。",
        f"- `create_trained_policy` 加载：`passed={smoke['passed']}`。",
        f"- policy 类型：`{smoke.get('policy_type')}`；模型类型：`{smoke.get('model_type')}`。",
        f"- 加载耗时：`{smoke.get('seconds')}` 秒。",
        "",
        "## checkpoint 结构",
        "",
        f"- `params/_METADATA`：`{layout['params_metadata_exists']}`。",
        f"- `params/manifest.ocdbt`：`{layout['params_manifest_exists']}`。",
        f"- `assets/{status['asset_id']}/norm_stats.json`：`{layout['asset_norm_stats_exists']}`。",
        "",
        "## 边界",
        "",
        "- 本 smoke 只验证 `create_trained_policy` 能构建 policy，不执行真实 RoboChallenge 提交。",
        "- 本 smoke 不评价策略质量；此前 LoRA reduced 训练只证明链路可跑通。",
        "- 真实提交仍需要用户提供 `ROBOCHALLENGE_USER_TOKEN` 和 `ROBOCHALLENGE_SUBMISSION_ID`。",
    ]
    if smoke.get("error"):
        lines.extend(["", "## 错误", "", f"- `{smoke['error']}`"])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    ensure_import_paths()
    args.status_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.parent.mkdir(parents=True, exist_ok=True)

    from openpi_rtc.policies import policy_config
    from openpi_rtc.training import config as train_config

    cfg = train_config.get_config(args.config_name)
    model = dataclasses.replace(
        cfg.model,
        paligemma_variant=args.paligemma_variant,
        action_expert_variant=args.action_expert_variant,
    )
    cfg = dataclasses.replace(cfg, model=model)
    data_config = cfg.data.create(cfg.assets_dirs, cfg.model)
    asset_id = data_config.asset_id

    status: dict[str, Any] = {
        "config_name": args.config_name,
        "checkpoint_dir": rel(args.checkpoint_dir),
        "asset_id": asset_id,
        "model": {
            "paligemma_variant": args.paligemma_variant,
            "action_expert_variant": args.action_expert_variant,
            "pi05": getattr(cfg.model, "pi05", None),
        },
        "checkpoint_layout": checkpoint_layout(args.checkpoint_dir, asset_id),
        "policy_load_smoke": {"passed": False, "error": None},
        "passed": False,
    }

    start = time.time()
    try:
        policy = policy_config.create_trained_policy(
            cfg,
            args.checkpoint_dir,
            default_prompt=args.default_prompt,
        )
        status["policy_load_smoke"] = {
            "passed": True,
            "seconds": round(time.time() - start, 3),
            "policy_type": type(policy).__name__,
            "model_type": type(policy._model).__name__,  # noqa: SLF001 - smoke records concrete runtime class.
            "is_pytorch_model": bool(policy._is_pytorch_model),  # noqa: SLF001
            "metadata_keys": sorted(policy.metadata.keys()),
            "sample_kwargs_keys": sorted(policy._sample_kwargs.keys()),  # noqa: SLF001
        }
    except Exception as exc:  # pragma: no cover - records remote env failure.
        status["policy_load_smoke"] = {
            "passed": False,
            "seconds": round(time.time() - start, 3),
            "error": {"type": type(exc).__name__, "message": str(exc)},
        }

    layout = status["checkpoint_layout"]
    smoke = status["policy_load_smoke"]
    status["passed"] = all(
        [
            status["model"]["pi05"] is True,
            asset_id == "cvpr_multitask_aloha",
            layout["exists"],
            layout["params_metadata_exists"],
            layout["params_manifest_exists"],
            layout["asset_norm_stats_exists"],
            smoke["passed"],
            smoke.get("policy_type") == "Policy",
            smoke.get("is_pytorch_model") is False,
        ]
    )

    args.status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(status, args.report_path)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
