#!/usr/bin/env python3
"""Audit restoring a scoped openpi_rtc LoRA checkpoint on top of pi05_base."""

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
os.environ.setdefault("JAX_PLATFORMS", "cpu")

ROOT = Path(__file__).resolve().parents[1]
BASELINE = Path(os.environ.get("BASELINE", "/home/yjl/yjl/RoboChallenge/baseline_pi05_multitask"))
BASELINE_PYTHON = BASELINE / ".venv/bin/python3"
if (
    BASELINE_PYTHON.exists()
    and Path(sys.executable).resolve() != BASELINE_PYTHON.resolve()
    and os.environ.get("OPENPI_RTC_LORA_RESTORE_AUDIT_REEXEC") != "1"
):
    os.environ["OPENPI_RTC_LORA_RESTORE_AUDIT_REEXEC"] = "1"
    os.execv(str(BASELINE_PYTHON), [str(BASELINE_PYTHON), *sys.argv])

OPENPI_ROOT = BASELINE / "openpi"
OPENPI_SRC = OPENPI_ROOT / "src"
OPENPI_CLIENT_SRC = OPENPI_ROOT / "packages/openpi-client/src"
LEROBOT_SRC = Path(os.environ.get("LEROBOT_SRC", "/home/yjl/yjl/RoboChallenge/third_party/lerobot"))
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
DEFAULT_PARAMS = Path("/home/yjl/.cache/openpi/openpi-assets/checkpoints/pi05_base/params")
DEFAULT_CHECKPOINT = RUNS_DIR / "openpi_rtc_lora_grad_checkpoint/trainable_params_step1.npz"
DEFAULT_METADATA = RUNS_DIR / "openpi_rtc_lora_grad_checkpoint/metadata.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计 openpi_rtc LoRA scoped checkpoint 的恢复/合并链路。")
    parser.add_argument("--config-name", default="cvpr_multitask_aloha_rtc", help="OpenPI RTC config 名称。")
    parser.add_argument("--params-path", type=Path, default=DEFAULT_PARAMS, help="pi05_base params 路径。")
    parser.add_argument("--checkpoint-npz", type=Path, default=DEFAULT_CHECKPOINT, help="scoped trainable npz。")
    parser.add_argument("--metadata-path", type=Path, default=DEFAULT_METADATA, help="scoped checkpoint metadata。")
    parser.add_argument("--paligemma-variant", default="gemma_2b_lora", help="LoRA PaliGemma variant。")
    parser.add_argument("--action-expert-variant", default="gemma_300m_lora", help="LoRA action expert variant。")
    parser.add_argument(
        "--status-path",
        type=Path,
        default=RUNS_DIR / "openpi_rtc_lora_checkpoint_restore_audit.json",
        help="状态 JSON 输出路径。",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=REPORTS_DIR / "openpi_rtc_lora_checkpoint_restore_audit.md",
        help="中文审计报告输出路径。",
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


def summarize_flat(flat: dict[str, Any], limit: int = 16) -> dict[str, Any]:
    dtype_counts: dict[str, int] = {}
    total_elements = 0
    samples = []
    for key in sorted(flat):
        value = flat[key]
        shape = list(getattr(value, "shape", ()))
        dtype = str(getattr(value, "dtype", type(value).__name__))
        dtype_counts[dtype] = dtype_counts.get(dtype, 0) + 1
        if shape:
            total_elements += int(np.prod(shape, dtype=np.int64))
        if len(samples) < limit:
            samples.append({"path": key, "shape": shape, "dtype": dtype})
    return {
        "leaf_count": len(flat),
        "total_elements": total_elements,
        "dtype_counts": dtype_counts,
        "sample_leaves": samples,
    }


def expected_dtype_name(value: Any) -> str:
    return str(getattr(value, "dtype", ""))


def coerce_checkpoint_array(raw: np.ndarray, expected_value: Any) -> np.ndarray:
    expected_dtype = expected_dtype_name(expected_value)
    if raw.dtype.kind == "V":
        import ml_dtypes

        raw = raw.view(ml_dtypes.bfloat16)
    if expected_dtype == "bfloat16":
        return raw
    if expected_dtype:
        return raw.astype(expected_dtype, copy=False)
    return raw


def load_checkpoint_arrays(npz_path: Path, flat_expected: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    arrays: dict[str, Any] = {}
    shape_mismatches = []
    dtype_conversions = []
    with np.load(npz_path) as npz:
        for key in npz.files:
            if key not in flat_expected:
                continue
            raw = npz[key]
            expected = flat_expected[key]
            expected_shape = list(getattr(expected, "shape", ()))
            raw_shape = list(raw.shape)
            if raw_shape != expected_shape:
                shape_mismatches.append({"path": key, "expected": expected_shape, "actual": raw_shape})
                continue
            converted = coerce_checkpoint_array(raw, expected)
            arrays[key] = converted
            raw_dtype = str(raw.dtype)
            converted_dtype = str(getattr(converted, "dtype", raw.dtype))
            expected_dtype = expected_dtype_name(expected)
            if raw_dtype != converted_dtype or converted_dtype != expected_dtype:
                dtype_conversions.append(
                    {
                        "path": key,
                        "raw_dtype": raw_dtype,
                        "converted_dtype": converted_dtype,
                        "expected_dtype": expected_dtype,
                    }
                )
    return arrays, {
        "shape_mismatches": shape_mismatches,
        "dtype_conversions": dtype_conversions[:24],
        "dtype_conversion_count": len(dtype_conversions),
    }


def write_report(status: dict[str, Any], report_path: Path) -> None:
    ckpt = status["checkpoint"]
    merge = status["merge_audit"]
    lines = [
        "# openpi_rtc LoRA checkpoint 恢复/合并审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 基础权重：`{ckpt['base_params_path']}`。",
        f"- scoped checkpoint：`{ckpt['checkpoint_npz']}`。",
        f"- checkpoint 范围：`{ckpt.get('metadata', {}).get('scope')}`，不是完整 policy checkpoint。",
        f"- 恢复方式：先加载 `pi05_base` 到 LoRA 参数树，再用 scoped trainable params 覆盖对应 leaf。",
        "",
        "## 关键证据",
        "",
        f"- LoRA 模型 leaf 数：`{merge['expected_leaf_count']}`。",
        f"- `pi05_base` 合并后 leaf 数：`{merge['base_loaded_leaf_count']}`。",
        f"- scoped checkpoint key 数：`{merge['checkpoint_key_count']}`。",
        f"- `cfg.trainable_filter` key 数：`{merge['trainable_filter_key_count']}`。",
        f"- checkpoint 中 LoRA key 数：`{merge['checkpoint_lora_key_count']}`。",
        f"- checkpoint 中 `knob_*` key 数：`{merge['checkpoint_knob_key_count']}`。",
        f"- 合并前 `ShapeDtypeStruct` 占位 leaf：`{merge['placeholder_before_count']}`。",
        f"- scoped 覆盖 leaf：`{merge['overwritten_leaf_count']}`。",
        f"- 合并后剩余 `ShapeDtypeStruct` 占位 leaf：`{merge['placeholder_after_count']}`。",
        f"- 参数树 shape/dtype 校验：`{merge['tree_check_passed']}`。",
        f"- NNX state 恢复 smoke：`{merge['state_replace_passed']}`。",
        "",
        "## 边界",
        "",
        "- 这个 scoped checkpoint 只能和相同 config、相同 LoRA variant、相同 `pi05_base` 一起恢复。",
        "- 本轮只验证恢复/合并链路，没有声明策略质量，也没有完成 RoboChallenge 真实提交。",
        "- 真实提交仍需要网站 `user_token` 和 `submission_id`，不能伪造。",
    ]
    if merge.get("missing_checkpoint_keys"):
        lines.extend(["", "## 缺失 key", "", f"- `{merge['missing_checkpoint_keys'][:20]}`"])
    if merge.get("unexpected_checkpoint_keys"):
        lines.extend(["", "## 额外 key", "", f"- `{merge['unexpected_checkpoint_keys'][:20]}`"])
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
        "checkpoint": {
            "base_params_path": str(args.params_path),
            "base_params_exists": args.params_path.exists(),
            "checkpoint_npz": rel(args.checkpoint_npz),
            "checkpoint_npz_exists": args.checkpoint_npz.exists(),
            "metadata_path": rel(args.metadata_path),
            "metadata_exists": args.metadata_path.exists(),
        },
    }

    if not args.params_path.exists():
        raise FileNotFoundError(f"params path does not exist: {args.params_path}")
    if not args.checkpoint_npz.exists():
        raise FileNotFoundError(f"checkpoint npz does not exist: {args.checkpoint_npz}")
    if args.metadata_path.exists():
        status["checkpoint"]["metadata"] = json.loads(args.metadata_path.read_text(encoding="utf-8"))

    cfg = train_config.get_config(args.config_name)
    model = dataclasses.replace(
        cfg.model,
        paligemma_variant=args.paligemma_variant,
        action_expert_variant=args.action_expert_variant,
    )
    cfg = dataclasses.replace(
        cfg,
        model=model,
        freeze_filter=model.get_freeze_filter(),
        ema_decay=None,
        weight_loader=weight_loaders.CheckpointWeightLoader(str(args.params_path)),
    )
    status["model"]["pi05"] = getattr(cfg.model, "pi05", None)
    status["ema_decay"] = cfg.ema_decay

    abstract_model = nnx.eval_shape(cfg.model.create, jax.random.key(cfg.seed))
    all_params = nnx.state(abstract_model, nnx.Param)
    trainable_params = nnx.state(abstract_model, cfg.trainable_filter)

    def cast_bf16_if_array(param):
        value = param.value
        if hasattr(value, "astype"):
            return param.replace(value.astype(jnp.bfloat16))
        return param

    params_shape = nnx_utils.state_map(all_params, cfg.freeze_filter, cast_bf16_if_array)
    expected = params_shape.to_pure_dict()
    trainable_expected = trainable_params.to_pure_dict()
    flat_expected = flax.traverse_util.flatten_dict(expected, sep="/")
    flat_trainable = flax.traverse_util.flatten_dict(trainable_expected, sep="/")

    start = time.time()
    base_loaded = cfg.weight_loader.load(expected)
    at.check_pytree_equality(expected=expected, got=base_loaded, check_shapes=True, check_dtypes=True)
    base_load_seconds = round(time.time() - start, 3)
    flat_base = flax.traverse_util.flatten_dict(base_loaded, sep="/")
    placeholder_before = sorted(key for key, value in flat_base.items() if isinstance(value, jax.ShapeDtypeStruct))

    with np.load(args.checkpoint_npz) as npz:
        checkpoint_keys = sorted(npz.files)
        raw_checkpoint_summary = {
            "leaf_count": len(checkpoint_keys),
            "dtype_counts": {},
            "sample_leaves": [],
        }
        for key in checkpoint_keys:
            raw = npz[key]
            raw_checkpoint_summary["dtype_counts"][str(raw.dtype)] = (
                raw_checkpoint_summary["dtype_counts"].get(str(raw.dtype), 0) + 1
            )
            if len(raw_checkpoint_summary["sample_leaves"]) < 16:
                raw_checkpoint_summary["sample_leaves"].append(
                    {"path": key, "shape": list(raw.shape), "dtype": str(raw.dtype)}
                )

    checkpoint_arrays, checkpoint_cast = load_checkpoint_arrays(args.checkpoint_npz, flat_expected)
    checkpoint_key_set = set(checkpoint_keys)
    trainable_key_set = set(flat_trainable)
    expected_key_set = set(flat_expected)
    missing_checkpoint_keys = sorted(trainable_key_set - checkpoint_key_set)
    unexpected_checkpoint_keys = sorted(checkpoint_key_set - expected_key_set)
    checkpoint_not_trainable = sorted(checkpoint_key_set - trainable_key_set)

    merged_flat = dict(flat_base)
    overwritten = []
    for key in checkpoint_keys:
        if key in checkpoint_arrays:
            merged_flat[key] = checkpoint_arrays[key]
            overwritten.append(key)
    placeholder_after = sorted(key for key, value in merged_flat.items() if isinstance(value, jax.ShapeDtypeStruct))
    merged = flax.traverse_util.unflatten_dict(merged_flat, sep="/")
    at.check_pytree_equality(expected=expected, got=merged, check_shapes=True, check_dtypes=True)

    graphdef, state = nnx.split(abstract_model)
    state.replace_by_pure_dict(merged)

    status["merge_audit"] = {
        "base_load_seconds": base_load_seconds,
        "expected_leaf_count": len(flat_expected),
        "base_loaded_leaf_count": len(flat_base),
        "trainable_filter_key_count": len(flat_trainable),
        "checkpoint_key_count": len(checkpoint_keys),
        "checkpoint_lora_key_count": sum("lora" in key for key in checkpoint_keys),
        "checkpoint_knob_key_count": sum("knob_" in key for key in checkpoint_keys),
        "placeholder_before_count": len(placeholder_before),
        "placeholder_before_sample": placeholder_before[:20],
        "overwritten_leaf_count": len(overwritten),
        "overwritten_leaf_sample": overwritten[:20],
        "placeholder_after_count": len(placeholder_after),
        "placeholder_after_sample": placeholder_after[:20],
        "missing_checkpoint_keys": missing_checkpoint_keys,
        "unexpected_checkpoint_keys": unexpected_checkpoint_keys,
        "checkpoint_not_trainable_keys": checkpoint_not_trainable,
        "shape_mismatches": checkpoint_cast["shape_mismatches"],
        "dtype_conversion_count": checkpoint_cast["dtype_conversion_count"],
        "dtype_conversions_sample": checkpoint_cast["dtype_conversions"],
        "expected_summary": summarize_flat(flat_expected),
        "base_loaded_summary": summarize_flat(flat_base),
        "raw_checkpoint_summary": raw_checkpoint_summary,
        "merged_summary": summarize_flat(merged_flat),
        "tree_check_passed": True,
        "state_replace_passed": True,
    }
    status["passed"] = all(
        [
            status["model"]["pi05"] is True,
            status["ema_decay"] is None,
            len(flat_expected) == 73,
            len(flat_base) == 73,
            len(flat_trainable) == 53,
            len(checkpoint_keys) == 53,
            len(missing_checkpoint_keys) == 0,
            len(unexpected_checkpoint_keys) == 0,
            len(checkpoint_not_trainable) == 0,
            len(placeholder_before) == 22,
            len(overwritten) == 53,
            len(placeholder_after) == 0,
            len(checkpoint_cast["shape_mismatches"]) == 0,
        ]
    )

    args.status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(status, args.report_path)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
