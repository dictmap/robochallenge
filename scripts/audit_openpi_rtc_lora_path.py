#!/usr/bin/env python3
"""Audit the low-memory LoRA path for openpi_rtc pi0.5 Table30v2 ALOHA."""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
from pathlib import Path
import sys
import time
from typing import Any

import numpy as np


os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")

ROOT = Path(__file__).resolve().parents[1]
BASELINE = Path(os.environ.get("BASELINE", "/home/yjl/yjl/RoboChallenge/baseline_pi05_multitask"))
BASELINE_PYTHON = BASELINE / ".venv/bin/python3"
if (
    BASELINE_PYTHON.exists()
    and Path(sys.executable).resolve() != BASELINE_PYTHON.resolve()
    and os.environ.get("OPENPI_RTC_LORA_AUDIT_REEXEC") != "1"
):
    os.environ["OPENPI_RTC_LORA_AUDIT_REEXEC"] = "1"
    os.execv(str(BASELINE_PYTHON), [str(BASELINE_PYTHON), *sys.argv])

OPENPI_ROOT = BASELINE / "openpi"
OPENPI_SRC = OPENPI_ROOT / "src"
OPENPI_CLIENT_SRC = OPENPI_ROOT / "packages/openpi-client/src"
LEROBOT_SRC = Path(os.environ.get("LEROBOT_SRC", "/home/yjl/yjl/RoboChallenge/third_party/lerobot"))
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
DEFAULT_PARAMS = Path("/home/yjl/.cache/openpi/openpi-assets/checkpoints/pi05_base/params")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计 openpi_rtc pi0.5 LoRA 低显存训练路线。")
    parser.add_argument("--config-name", default="cvpr_multitask_aloha_rtc", help="OpenPI RTC config 名称。")
    parser.add_argument("--params-path", type=Path, default=DEFAULT_PARAMS, help="pi05_base params 路径。")
    parser.add_argument("--paligemma-variant", default="gemma_2b_lora", help="LoRA PaliGemma variant。")
    parser.add_argument("--action-expert-variant", default="gemma_300m_lora", help="LoRA action expert variant。")
    parser.add_argument(
        "--status-path",
        type=Path,
        default=RUNS_DIR / "openpi_rtc_lora_path_audit.json",
        help="状态 JSON 输出路径。",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=REPORTS_DIR / "openpi_rtc_lora_path_audit.md",
        help="中文报告输出路径。",
    )
    return parser.parse_args()


def ensure_import_paths() -> None:
    for path in [OPENPI_SRC, OPENPI_CLIENT_SRC, LEROBOT_SRC]:
        text = str(path)
        if text not in sys.path:
            sys.path.insert(0, text)


def summarize_state(state: Any, limit: int = 12) -> dict[str, Any]:
    flat = state.flat_state()
    dtype_counts: dict[str, int] = {}
    total_elements = 0
    samples = []
    for key, variable in flat.items():
        value = getattr(variable, "value", variable)
        shape = list(getattr(value, "shape", ()))
        dtype = str(getattr(value, "dtype", type(value).__name__))
        dtype_counts[dtype] = dtype_counts.get(dtype, 0) + 1
        total_elements += int(np.prod(shape, dtype=np.int64))
        if len(samples) < limit:
            samples.append({"path": "/".join(map(str, key)), "shape": shape, "dtype": dtype})
    return {
        "leaf_count": len(flat),
        "total_elements": total_elements,
        "dtype_counts": dtype_counts,
        "sample_leaves": samples,
    }


def write_report(status: dict[str, Any], report_path: Path) -> None:
    model = status["model"]
    counts = status["param_counts"]
    weight = status["weight_preflight"]
    lines = [
        "# openpi_rtc LoRA 低显存路线审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 基础配置：`{status['config_name']}`。",
        f"- LoRA 变体：`{model['paligemma_variant']}` + `{model['action_expert_variant']}`。",
        f"- `pi05` 标志保持：`{model['pi05']}`。",
        "- 本轮只做配置、参数树和权重合并预检，没有跑真实 forward/grad，也没有写训练 checkpoint。",
        "",
        "## 参数规模",
        "",
        f"- 总参数 leaf：`{counts['all']['leaf_count']}`，元素数：`{counts['all']['total_elements']}`。",
        f"- LoRA leaf：`{counts['lora']['leaf_count']}`，元素数：`{counts['lora']['total_elements']}`。",
        f"- 冻结 leaf：`{counts['frozen']['leaf_count']}`，元素数：`{counts['frozen']['total_elements']}`。",
        f"- 可训练 leaf：`{counts['trainable']['leaf_count']}`，元素数：`{counts['trainable']['total_elements']}`。",
        "",
        "## 权重合并",
        "",
        f"- `pi05_base` 路径：`{weight['params_path']}`。",
        f"- 合并校验：`passed={weight['passed']}`。",
        f"- 加载并合并耗时：`{weight['load_seconds']}` 秒。",
        f"- 合并后 leaf：`{weight['loaded_leaf_count']}`。",
        f"- 从模型初始化补入的 LoRA leaf：`{weight['loaded_lora_leaf_count']}`。",
        f"- 从模型初始化补入的 knob leaf：`{weight['loaded_knob_leaf_count']}`。",
        "",
        "## 边界",
        "",
        "- LoRA 路线能接上 `pi05_base` 权重，不等于已经完成数值训练。",
        "- 当前真实 `forward/head_grad/full grad` 仍受 GPU 显存与 XLA 执行阻塞影响。",
        "- 下一步若不释放 GPU，需要把 LoRA 路线接入数值 dry-run，并优先尝试更短序列、CPU/offload 或分布式训练。",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    ensure_import_paths()
    args.status_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.parent.mkdir(parents=True, exist_ok=True)

    import flax.traverse_util
    from flax import nnx
    import jax
    import jax.numpy as jnp

    import openpi_rtc.shared.array_typing as at
    from openpi_rtc.shared import nnx_utils
    from openpi_rtc.training import config as train_config
    from openpi_rtc.training import weight_loaders

    status: dict[str, Any] = {
        "config_name": args.config_name,
        "baseline": str(BASELINE),
        "passed": False,
        "model": {
            "paligemma_variant": args.paligemma_variant,
            "action_expert_variant": args.action_expert_variant,
            "pi05": None,
        },
    }

    cfg = train_config.get_config(args.config_name)
    model = dataclasses.replace(
        cfg.model,
        paligemma_variant=args.paligemma_variant,
        action_expert_variant=args.action_expert_variant,
    )
    freeze_filter = model.get_freeze_filter()
    cfg = dataclasses.replace(
        cfg,
        model=model,
        freeze_filter=freeze_filter,
        ema_decay=None,
        weight_loader=weight_loaders.CheckpointWeightLoader(str(args.params_path)),
    )
    status["model"]["pi05"] = getattr(cfg.model, "pi05", None)
    status["ema_decay"] = cfg.ema_decay

    abstract_model = nnx.eval_shape(cfg.model.create, jax.random.key(cfg.seed))
    all_params = nnx.state(abstract_model, nnx.Param)
    lora_params = nnx.state(abstract_model, nnx.All(nnx.Param, nnx_utils.PathRegex(".*lora.*")))
    frozen_params = nnx.state(abstract_model, nnx.All(nnx.Param, cfg.freeze_filter))
    trainable_params = nnx.state(abstract_model, cfg.trainable_filter)
    status["param_counts"] = {
        "all": summarize_state(all_params),
        "lora": summarize_state(lora_params),
        "frozen": summarize_state(frozen_params),
        "trainable": summarize_state(trainable_params),
    }

    def cast_bf16_if_array(param):
        value = param.value
        if hasattr(value, "astype"):
            return param.replace(value.astype(jnp.bfloat16))
        return param

    start = time.time()
    params_shape = nnx_utils.state_map(all_params, cfg.freeze_filter, cast_bf16_if_array)
    loaded = cfg.weight_loader.load(params_shape.to_pure_dict())
    at.check_pytree_equality(expected=params_shape.to_pure_dict(), got=loaded, check_shapes=True, check_dtypes=True)
    flat_loaded = flax.traverse_util.flatten_dict(loaded)
    loaded_lora = [key for key in flat_loaded if "lora" in "/".join(map(str, key))]
    loaded_knob = [key for key in flat_loaded if "knob_" in "/".join(map(str, key))]
    status["weight_preflight"] = {
        "passed": True,
        "params_path": str(args.params_path),
        "load_seconds": round(time.time() - start, 3),
        "loaded_leaf_count": len(flat_loaded),
        "loaded_lora_leaf_count": len(loaded_lora),
        "loaded_knob_leaf_count": len(loaded_knob),
        "loaded_lora_sample": ["/".join(map(str, key)) for key in loaded_lora[:12]],
    }
    status["passed"] = True
    args.status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(status, args.report_path)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
