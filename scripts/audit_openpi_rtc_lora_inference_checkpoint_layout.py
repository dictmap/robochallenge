#!/usr/bin/env python3
"""Audit the path from scoped LoRA params to a demo-loadable inference checkpoint."""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
from pathlib import Path
import shutil
import subprocess
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
    and os.environ.get("OPENPI_RTC_LORA_INFERENCE_LAYOUT_REEXEC") != "1"
):
    os.environ["OPENPI_RTC_LORA_INFERENCE_LAYOUT_REEXEC"] = "1"
    os.execv(str(BASELINE_PYTHON), [str(BASELINE_PYTHON), *sys.argv])

OPENPI_ROOT = BASELINE / "openpi"
OPENPI_SRC = OPENPI_ROOT / "src"
OPENPI_CLIENT_SRC = OPENPI_ROOT / "packages/openpi-client/src"
LEROBOT_SRC = Path(os.environ.get("LEROBOT_SRC", "/home/yjl/yjl/RoboChallenge/third_party/lerobot"))
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
DEFAULT_PARAMS = Path("/home/yjl/.cache/openpi/openpi-assets/checkpoints/pi05_base/params")
DEFAULT_OFFICIAL_ALOHA = Path("/home/yjl/yjl/RoboChallenge/checkpoints/table30v2_multitask_baseline_aloha")
DEFAULT_SCOPED_NPZ = RUNS_DIR / "openpi_rtc_lora_grad_checkpoint/trainable_params_step1.npz"
DEFAULT_SCOPED_METADATA = RUNS_DIR / "openpi_rtc_lora_grad_checkpoint/metadata.json"
DEFAULT_TARGET = RUNS_DIR / "openpi_rtc_lora_materialized_policy_checkpoint"
DEFAULT_SMOKE = RUNS_DIR / "openpi_rtc_lora_checkpoint_layout_smoke"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审计 LoRA scoped 参数物化为 openpi_rtc 推理 checkpoint 的可行性。")
    parser.add_argument("--config-name", default="cvpr_multitask_aloha_rtc", help="OpenPI RTC config 名称。")
    parser.add_argument("--params-path", type=Path, default=DEFAULT_PARAMS, help="pi05_base params 路径。")
    parser.add_argument("--official-checkpoint-dir", type=Path, default=DEFAULT_OFFICIAL_ALOHA, help="官方 ALOHA checkpoint。")
    parser.add_argument("--checkpoint-npz", type=Path, default=DEFAULT_SCOPED_NPZ, help="scoped trainable npz。")
    parser.add_argument("--metadata-path", type=Path, default=DEFAULT_SCOPED_METADATA, help="scoped checkpoint metadata。")
    parser.add_argument("--target-checkpoint-dir", type=Path, default=DEFAULT_TARGET, help="可选完整物化 checkpoint 输出目录。")
    parser.add_argument("--smoke-dir", type=Path, default=DEFAULT_SMOKE, help="tiny Orbax save/restore smoke 输出目录。")
    parser.add_argument("--paligemma-variant", default="gemma_2b_lora", help="LoRA PaliGemma variant。")
    parser.add_argument("--action-expert-variant", default="gemma_300m_lora", help="LoRA action expert variant。")
    parser.add_argument("--materialize", action="store_true", help="显式写出完整推理 checkpoint。默认不写大文件。")
    parser.add_argument("--force", action="store_true", help="物化或 smoke 时允许覆盖目标目录。")
    parser.add_argument("--skip-tiny-save-smoke", action="store_true", help="跳过 tiny Orbax 写入/读取 smoke。")
    parser.add_argument(
        "--status-path",
        type=Path,
        default=RUNS_DIR / "openpi_rtc_lora_inference_checkpoint_layout_audit.json",
        help="状态 JSON 输出路径。",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=REPORTS_DIR / "openpi_rtc_lora_inference_checkpoint_layout.md",
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


def is_under(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def file_count(path: Path, limit: int = 10000) -> int:
    if not path.exists():
        return 0
    count = 0
    for item in path.rglob("*"):
        if item.is_file():
            count += 1
            if count >= limit:
                return count
    return count


def git_check_ignore(path: Path) -> dict[str, Any]:
    try:
        rel_path = path.relative_to(ROOT)
    except ValueError:
        rel_path = path
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


def git_check_ignore_checkpoint_contents(path: Path) -> dict[str, Any]:
    probe = path / "params/_METADATA"
    status = git_check_ignore(probe)
    status["checkpoint_dir"] = str(path)
    return status


def summarize_checkpoint_dir(path: Path, asset_id: str | None) -> dict[str, Any]:
    params = path / "params"
    assets = path / "assets"
    asset_norm = assets / asset_id / "norm_stats.json" if asset_id else None
    return {
        "path": str(path),
        "exists": path.exists(),
        "params_dir_exists": params.exists(),
        "params_metadata_exists": (params / "_METADATA").exists(),
        "params_manifest_exists": (params / "manifest.ocdbt").exists(),
        "params_array_metadata_exists": (params / "array_metadatas/process_0").exists(),
        "params_file_count": file_count(params),
        "checkpoint_metadata_exists": (path / "_CHECKPOINT_METADATA").exists(),
        "assets_dir_exists": assets.exists(),
        "asset_id": asset_id,
        "asset_norm_stats": str(asset_norm) if asset_norm else None,
        "asset_norm_stats_exists": asset_norm.exists() if asset_norm else False,
    }


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def checkpoint_npz_summary(path: Path) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "path": rel(path),
        "exists": path.exists(),
        "leaf_count": 0,
        "dtype_counts": {},
        "sample_leaves": [],
    }
    if not path.exists():
        return summary
    with np.load(path) as npz:
        summary["leaf_count"] = len(npz.files)
        for key in sorted(npz.files):
            arr = npz[key]
            dtype = str(arr.dtype)
            summary["dtype_counts"][dtype] = summary["dtype_counts"].get(dtype, 0) + 1
            if len(summary["sample_leaves"]) < 12:
                summary["sample_leaves"].append({"path": key, "shape": list(arr.shape), "dtype": dtype})
    return summary


def run_tiny_save_smoke(smoke_dir: Path, *, force: bool) -> dict[str, Any]:
    import openpi_rtc.models.model as _model
    import orbax.checkpoint as ocp

    params_dir = smoke_dir / "params"
    status: dict[str, Any] = {
        "attempted": True,
        "smoke_dir": rel(smoke_dir),
        "params_dir": rel(params_dir),
        "passed": False,
        "error": None,
    }
    if smoke_dir.exists():
        if not force and not is_under(smoke_dir, RUNS_DIR):
            raise ValueError(f"refuse to overwrite smoke dir outside runs/: {smoke_dir}")
        shutil.rmtree(smoke_dir)
    smoke_dir.mkdir(parents=True, exist_ok=True)
    tiny = {"params": {"tiny_weight": np.arange(6, dtype=np.float32).reshape(2, 3)}}
    try:
        with ocp.PyTreeCheckpointer() as ckptr:
            ckptr.save(params_dir, tiny, force=True)
        restored = _model.restore_params(params_dir, restore_type=np.ndarray)
        arr = restored["tiny_weight"]
        status.update(
            {
                "passed": bool(arr.shape == (2, 3) and str(arr.dtype) == "float32" and float(arr.sum()) == 15.0),
                "restored_shape": list(arr.shape),
                "restored_dtype": str(arr.dtype),
                "restored_sum": float(arr.sum()),
                "metadata_exists": (params_dir / "_METADATA").exists(),
                "manifest_exists": (params_dir / "manifest.ocdbt").exists(),
                "array_metadata_exists": (params_dir / "array_metadatas/process_0").exists(),
            }
        )
    except Exception as exc:  # pragma: no cover - report path for remote environment drift.
        status["error"] = {"type": type(exc).__name__, "message": str(exc)}
    return status


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


def load_checkpoint_arrays(npz_path: Path, flat_expected: dict[str, Any]) -> dict[str, Any]:
    arrays: dict[str, Any] = {}
    with np.load(npz_path) as npz:
        for key in npz.files:
            if key not in flat_expected:
                continue
            raw = npz[key]
            expected = flat_expected[key]
            if list(raw.shape) != list(getattr(expected, "shape", ())):
                continue
            arrays[key] = coerce_checkpoint_array(raw, expected)
    return arrays


def materialize_full_checkpoint(
    *,
    cfg: Any,
    expected: dict[str, Any],
    flat_expected: dict[str, Any],
    checkpoint_npz: Path,
    official_checkpoint_dir: Path,
    target_dir: Path,
    asset_id: str,
    force: bool,
) -> dict[str, Any]:
    import flax.traverse_util
    import jax
    import orbax.checkpoint as ocp
    from flax import nnx
    import openpi_rtc.models.model as _model
    import openpi_rtc.shared.array_typing as at

    status: dict[str, Any] = {
        "attempted": True,
        "target_dir": rel(target_dir),
        "safe_target_under_runs": is_under(target_dir, RUNS_DIR),
        "passed": False,
        "error": None,
    }
    if not is_under(target_dir, RUNS_DIR):
        raise ValueError(f"refuse to materialize outside runs/: {target_dir}")
    if target_dir.exists():
        if not force:
            raise FileExistsError(f"target exists; pass --force to replace: {target_dir}")
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    start = time.time()
    try:
        base_loaded = cfg.weight_loader.load(expected)
        flat_base = flax.traverse_util.flatten_dict(base_loaded, sep="/")
        checkpoint_arrays = load_checkpoint_arrays(checkpoint_npz, flat_expected)
        merged_flat = dict(flat_base)
        merged_flat.update(checkpoint_arrays)
        merged = flax.traverse_util.unflatten_dict(merged_flat, sep="/")
        at.check_pytree_equality(expected=expected, got=merged, check_shapes=True, check_dtypes=True)

        params_dir = target_dir / "params"
        with ocp.PyTreeCheckpointer() as ckptr:
            ckptr.save(params_dir, {"params": merged}, force=True)

        source_asset = official_checkpoint_dir / "assets" / asset_id
        target_asset = target_dir / "assets" / asset_id
        target_asset.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_asset, target_asset)

        restored = _model.restore_params(params_dir, restore_type=np.ndarray)
        restored_flat = flax.traverse_util.flatten_dict(restored, sep="/")
        graphdef, state = nnx.split(nnx.eval_shape(cfg.model.create, jax.random.key(cfg.seed)))
        state.replace_by_pure_dict(restored)
        del graphdef

        status.update(
            {
                "passed": True,
                "seconds": round(time.time() - start, 3),
                "params_metadata_exists": (params_dir / "_METADATA").exists(),
                "params_manifest_exists": (params_dir / "manifest.ocdbt").exists(),
                "asset_norm_stats_exists": (target_asset / "norm_stats.json").exists(),
                "restored_leaf_count": len(restored_flat),
                "restored_tree_check_passed": True,
                "state_replace_passed": True,
            }
        )
    except Exception as exc:  # pragma: no cover - records heavyweight materialization failure.
        status["error"] = {"type": type(exc).__name__, "message": str(exc)}
    return status


def write_report(status: dict[str, Any], report_path: Path) -> None:
    layout = status["layout"]
    target = layout["target_checkpoint"]
    materialize = status["materialize"]
    if materialize.get("attempted") and materialize.get("passed"):
        materialize_summary = "本次已显式写出完整 12GB+ checkpoint，并完成恢复 smoke。"
        materialize_next = "如需重建完整 checkpoint，可重新运行 `python3 scripts/audit_openpi_rtc_lora_inference_checkpoint_layout.py --materialize --force`。"
    else:
        materialize_summary = "当前默认只完成目录形态、源材料和 tiny Orbax 写入/读取 smoke；没有自动写出 12GB+ 完整权重目录。"
        materialize_next = "如需物化完整 checkpoint，需要显式运行 `python3 scripts/audit_openpi_rtc_lora_inference_checkpoint_layout.py --materialize --force`。"
    lines = [
        "# openpi_rtc LoRA 推理 checkpoint 物化审计",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 当前是否已有 `demo.py --checkpoint` 可直接消费的 LoRA 完整 checkpoint：`{status['direct_demo_checkpoint_ready']}`。",
        f"- {materialize_summary}",
        f"- {materialize_next}",
        "",
        "## 已确认的推理 checkpoint 目录形态",
        "",
        "- `create_trained_policy` 对 JAX/NNX checkpoint 的读取路径是 `<checkpoint>/params`。",
        "- `<checkpoint>/params` 需要是 Orbax PyTree checkpoint，顶层 item 形态为 `{\"params\": full_params}`。",
        f"- norm stats 需要放在 `<checkpoint>/assets/{layout['asset_id']}/norm_stats.json`。",
        f"- tiny 保存/读取 smoke：`passed={status['tiny_save_smoke']['passed']}`，目录 `{status['tiny_save_smoke'].get('smoke_dir')}`。",
        "",
        "## 源材料",
        "",
        f"- `pi05_base` params：`{layout['pi05_base_params']['path']}`，`_METADATA={layout['pi05_base_params']['params_metadata_exists']}`。",
        f"- 官方 ALOHA checkpoint：`{layout['official_aloha_checkpoint']['path']}`，norm stats 存在：`{layout['official_aloha_checkpoint']['asset_norm_stats_exists']}`。",
        f"- LoRA scoped checkpoint：`{status['scoped_checkpoint']['path']}`，leaf 数：`{status['scoped_checkpoint']['leaf_count']}`。",
        f"- restore/merge 审计：`passed={status['restore_audit']['passed']}`，合并后占位 leaf：`{status['restore_audit']['placeholder_after_count']}`。",
        "",
        "## 目标目录",
        "",
        f"- 目标目录：`{target['path']}`。",
        f"- Git ignore：`ignored={target['git_ignore']['ignored']}`，规则：`{target['git_ignore']['stdout']}`。",
        f"- 物化执行：`attempted={materialize['attempted']}`，`passed={materialize.get('passed')}`。",
        "",
        "## 边界",
        "",
        "- 本轮没有声明 LoRA 策略质量提升；已有 loss/grad smoke 只说明链路能跑通。",
        "- 未提供 RoboChallenge `user_token` 和 `submission_id` 前，不会运行真实提交。",
        "- 如果后续选择 `--materialize`，生成的大 checkpoint 必须留在 ignored 目录，不能提交到 Git。",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
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
    data_config = cfg.data.create(cfg.assets_dirs, cfg.model)
    asset_id = data_config.asset_id

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

    restore_status = read_json(RUNS_DIR / "openpi_rtc_lora_checkpoint_restore_audit.json")
    restore_merge = restore_status.get("merge_audit", {})
    scoped_summary = checkpoint_npz_summary(args.checkpoint_npz)
    metadata = read_json(args.metadata_path) if args.metadata_path.exists() else {}
    target_ignore = git_check_ignore_checkpoint_contents(args.target_checkpoint_dir)

    tiny_smoke = {"attempted": False, "passed": None}
    if not args.skip_tiny_save_smoke:
        tiny_smoke = run_tiny_save_smoke(args.smoke_dir, force=True)

    materialize_status: dict[str, Any] = {"attempted": False, "passed": None}
    if args.materialize:
        materialize_status = materialize_full_checkpoint(
            cfg=cfg,
            expected=expected,
            flat_expected=flat_expected,
            checkpoint_npz=args.checkpoint_npz,
            official_checkpoint_dir=args.official_checkpoint_dir,
            target_dir=args.target_checkpoint_dir,
            asset_id=asset_id,
            force=args.force,
        )

    status: dict[str, Any] = {
        "config_name": args.config_name,
        "baseline": str(BASELINE),
        "passed": False,
        "direct_demo_checkpoint_ready": bool(materialize_status.get("passed")),
        "model": {
            "paligemma_variant": args.paligemma_variant,
            "action_expert_variant": args.action_expert_variant,
            "pi05": getattr(cfg.model, "pi05", None),
            "ema_decay": cfg.ema_decay,
            "expected_leaf_count": len(flat_expected),
            "trainable_filter_key_count": len(flat_trainable),
        },
        "layout": {
            "asset_id": asset_id,
            "use_quantile_norm": getattr(data_config, "use_quantile_norm", None),
            "pi05_base_params": summarize_checkpoint_dir(args.params_path.parent, asset_id),
            "official_aloha_checkpoint": summarize_checkpoint_dir(args.official_checkpoint_dir, asset_id),
            "target_checkpoint": {
                "path": rel(args.target_checkpoint_dir),
                "safe_target_under_runs": is_under(args.target_checkpoint_dir, RUNS_DIR),
                "git_ignore": target_ignore,
            },
        },
        "scoped_checkpoint": {
            **scoped_summary,
            "metadata_path": rel(args.metadata_path),
            "metadata_exists": args.metadata_path.exists(),
            "metadata_kind": metadata.get("kind"),
            "metadata_scope": metadata.get("scope"),
        },
        "restore_audit": {
            "passed": restore_status.get("passed"),
            "checkpoint_key_count": restore_merge.get("checkpoint_key_count"),
            "trainable_filter_key_count": restore_merge.get("trainable_filter_key_count"),
            "placeholder_after_count": restore_merge.get("placeholder_after_count"),
            "tree_check_passed": restore_merge.get("tree_check_passed"),
            "state_replace_passed": restore_merge.get("state_replace_passed"),
        },
        "tiny_save_smoke": tiny_smoke,
        "materialize": materialize_status,
    }

    base_layout = status["layout"]["pi05_base_params"]
    official_layout = status["layout"]["official_aloha_checkpoint"]
    status["passed"] = all(
        [
            status["model"]["pi05"] is True,
            status["model"]["ema_decay"] is None,
            status["model"]["expected_leaf_count"] == 73,
            status["model"]["trainable_filter_key_count"] == 53,
            asset_id == "cvpr_multitask_aloha",
            base_layout["params_dir_exists"],
            base_layout["params_metadata_exists"],
            base_layout["params_manifest_exists"],
            official_layout["params_dir_exists"],
            official_layout["params_metadata_exists"],
            official_layout["asset_norm_stats_exists"],
            scoped_summary["exists"],
            scoped_summary["leaf_count"] == 53,
            status["scoped_checkpoint"]["metadata_kind"] == "scoped_trainable_checkpoint",
            status["scoped_checkpoint"]["metadata_scope"] == "cfg.trainable_filter",
            status["restore_audit"]["passed"],
            status["restore_audit"]["placeholder_after_count"] == 0,
            target_ignore["ignored"],
            is_under(args.target_checkpoint_dir, RUNS_DIR),
            args.skip_tiny_save_smoke or tiny_smoke.get("passed"),
            (not args.materialize) or materialize_status.get("passed"),
        ]
    )

    args.status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(status, args.report_path)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
