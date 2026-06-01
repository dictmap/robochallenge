#!/usr/bin/env python3
"""Run numeric preflight steps for openpi_rtc Table30v2 ALOHA training."""

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
import traceback
from typing import Any

import numpy as np


os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")

ROOT = Path(__file__).resolve().parents[1]
BASELINE = Path(os.environ.get("BASELINE", "/home/yjl/yjl/RoboChallenge/baseline_pi05_multitask"))
BASELINE_PYTHON = BASELINE / ".venv/bin/python3"
if (
    BASELINE_PYTHON.exists()
    and Path(sys.executable).resolve() != BASELINE_PYTHON.resolve()
    and os.environ.get("OPENPI_RTC_NUMERIC_REEXEC") != "1"
):
    os.environ["OPENPI_RTC_NUMERIC_REEXEC"] = "1"
    os.execv(str(BASELINE_PYTHON), [str(BASELINE_PYTHON), *sys.argv])


OPENPI_ROOT = BASELINE / "openpi"
OPENPI_SRC = OPENPI_ROOT / "src"
OPENPI_CLIENT_SRC = OPENPI_ROOT / "packages/openpi-client/src"
LEROBOT_SRC = Path(os.environ.get("LEROBOT_SRC", "/home/yjl/yjl/RoboChallenge/third_party/lerobot"))
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
DEFAULT_PARAMS = Path("/home/yjl/.cache/openpi/openpi-assets/checkpoints/pi05_base/params")
DEFAULT_STATUS = RUNS_DIR / "openpi_rtc_numeric_dry_run_status.json"
DEFAULT_REPORT = REPORTS_DIR / "openpi_rtc_numeric_dry_run.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="对 openpi_rtc + Table30v2 ALOHA 做数值训练 dry-run 的分阶段预检。"
    )
    parser.add_argument("--config-name", default="cvpr_multitask_aloha_rtc", help="OpenPI RTC config 名称。")
    parser.add_argument("--repo-id", default="robochallenge_table30v2_aloha_short", help="本地 LeRobot repo_id。")
    parser.add_argument("--batch-size", type=int, default=1, help="batch size。")
    parser.add_argument("--num-workers", type=int, default=1, help="dataloader worker 数。")
    parser.add_argument("--paligemma-variant", default=None, help="覆盖 model.paligemma_variant，例如 gemma_2b_lora。")
    parser.add_argument(
        "--action-expert-variant",
        default=None,
        help="覆盖 model.action_expert_variant，例如 gemma_300m_lora。",
    )
    parser.add_argument("--max-token-len", type=int, default=None, help="覆盖 model.max_token_len，用于低显存 smoke。")
    parser.add_argument("--action-horizon", type=int, default=None, help="覆盖 model.action_horizon，用于低显存 smoke。")
    parser.add_argument(
        "--random-action-offset-copies",
        type=int,
        default=None,
        help="覆盖 DataConfig.random_action_offset_copies；默认保留 config 原值。",
    )
    parser.add_argument("--params-path", type=Path, default=DEFAULT_PARAMS, help="pi05_base params 路径。")
    parser.add_argument(
        "--mode",
        choices=["weight_preflight", "forward", "grad", "head_grad"],
        default="weight_preflight",
        help="weight_preflight 只加载并校验权重；forward 算一次 loss；grad 算全量梯度；head_grad 只训练小头部参数。",
    )
    parser.add_argument(
        "--compute-param-dtype",
        choices=["float32", "bfloat16"],
        default="float32",
        help="forward/grad 计算时注入模型的参数 dtype；weight_preflight 始终先按原 dtype 校验。",
    )
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="状态 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文报告输出路径。")
    parser.add_argument(
        "--checkpoint-dir",
        type=Path,
        default=RUNS_DIR / "openpi_rtc_head_grad_checkpoint",
        help="head_grad scoped checkpoint 输出目录。",
    )
    return parser.parse_args()


def ensure_import_paths() -> None:
    for path in [OPENPI_SRC, OPENPI_CLIENT_SRC, LEROBOT_SRC]:
        text = str(path)
        if text not in sys.path:
            sys.path.insert(0, text)


def run_text(cmd: list[str]) -> dict[str, Any]:
    exe = shutil.which(cmd[0])
    if exe is None:
        return {"available": False, "cmd": cmd, "stdout": "", "stderr": f"{cmd[0]} not found"}
    result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return {
        "available": True,
        "cmd": cmd,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def summarize_tree(tree: Any, limit: int = 16) -> dict[str, Any]:
    import jax

    leaves = jax.tree_util.tree_leaves(tree)
    dtype_counts: dict[str, int] = {}
    total_elements = 0
    samples = []
    for leaf in leaves:
        if hasattr(leaf, "shape") and hasattr(leaf, "dtype"):
            shape = list(leaf.shape)
            dtype = str(leaf.dtype)
            dtype_counts[dtype] = dtype_counts.get(dtype, 0) + 1
            total_elements += int(np.prod(shape, dtype=np.int64))
            if len(samples) < limit:
                samples.append({"shape": shape, "dtype": dtype})
        elif len(samples) < limit:
            samples.append({"type": type(leaf).__name__})
    return {
        "leaf_count": len(leaves),
        "total_elements": total_elements,
        "dtype_counts": dtype_counts,
        "sample_leaves": samples,
    }


def make_config(
    config_name: str,
    repo_id: str,
    batch_size: int,
    num_workers: int,
    params_path: Path,
    random_action_offset_copies: int | None,
    paligemma_variant: str | None,
    action_expert_variant: str | None,
    max_token_len: int | None,
    action_horizon: int | None,
):
    from openpi_rtc.training import config as train_config
    from openpi_rtc.training import weight_loaders

    cfg = train_config.get_config(config_name)
    model = cfg.model
    variant_overridden = paligemma_variant is not None or action_expert_variant is not None
    if paligemma_variant is not None:
        model = dataclasses.replace(model, paligemma_variant=paligemma_variant)
    if action_expert_variant is not None:
        model = dataclasses.replace(model, action_expert_variant=action_expert_variant)
    if max_token_len is not None:
        model = dataclasses.replace(model, max_token_len=max_token_len)
    if action_horizon is not None:
        model = dataclasses.replace(model, action_horizon=action_horizon)
    freeze_filter = model.get_freeze_filter() if variant_overridden else cfg.freeze_filter
    ema_decay = None if variant_overridden and "lora" in f"{model.paligemma_variant} {model.action_expert_variant}" else cfg.ema_decay
    data = dataclasses.replace(cfg.data, repo_id=repo_id)
    if random_action_offset_copies is not None:
        data = dataclasses.replace(
            data,
            base_config=dataclasses.replace(
                data.base_config,
                random_action_offset_copies=random_action_offset_copies,
            ),
        )

    cfg = dataclasses.replace(
        cfg,
        exp_name=f"robochallenge_{repo_id}_numeric_dry_run",
        model=model,
        freeze_filter=freeze_filter,
        ema_decay=ema_decay,
        data=data,
        weight_loader=weight_loaders.CheckpointWeightLoader(str(params_path)),
        batch_size=batch_size,
        num_workers=num_workers,
        num_train_steps=1,
        log_interval=1,
        save_interval=1,
        keep_period=None,
        overwrite=True,
        resume=False,
        wandb_enabled=False,
        checkpoint_base_dir=str(RUNS_DIR / "openpi_rtc_numeric_checkpoints"),
        assets_base_dir=str(RUNS_DIR / "openpi_rtc_numeric_assets"),
    )
    return cfg


def load_batch(cfg) -> tuple[Any, Any, dict[str, Any]]:
    from openpi_rtc.training import data_loader

    data_config = cfg.data.create(cfg.assets_dirs, cfg.model)
    loader = data_loader.create_torch_data_loader(
        data_config,
        model_config=cfg.model,
        action_horizon=cfg.model.action_horizon,
        batch_size=cfg.batch_size,
        shuffle=False,
        num_batches=1,
        num_workers=cfg.num_workers,
        skip_norm_stats=True,
        framework="numpy",
    )
    observation, actions = next(iter(loader))
    return observation, actions, {
        "state_shape": list(observation.state.shape),
        "actions_shape": list(actions.shape),
        "tokenized_prompt_shape": list(observation.tokenized_prompt.shape),
        "tokenized_prompt_mask_shape": list(observation.tokenized_prompt_mask.shape),
        "image_keys": sorted(observation.images.keys()),
    }


def expected_param_shape(cfg):
    import jax
    import jax.numpy as jnp
    from flax import nnx

    from openpi_rtc.shared import nnx_utils

    def init(rng):
        _, model_rng = jax.random.split(rng)
        model = cfg.model.create(model_rng)
        params = nnx.state(model)

        def cast_bf16_if_array(param):
            value = param.value
            if hasattr(value, "astype"):
                return param.replace(value.astype(jnp.bfloat16))
            return param

        return nnx_utils.state_map(params, cfg.freeze_filter, cast_bf16_if_array)

    return jax.eval_shape(init, jax.random.key(cfg.seed))


def load_and_validate_weights(cfg, params_shape) -> tuple[Any, dict[str, Any]]:
    import jax
    import flax.traverse_util

    import openpi_rtc.shared.array_typing as at

    start = time.time()
    loaded = cfg.weight_loader.load(params_shape.to_pure_dict())
    load_seconds = round(time.time() - start, 3)
    at.check_pytree_equality(expected=params_shape.to_pure_dict(), got=loaded, check_shapes=True, check_dtypes=True)
    jax.tree_util.tree_leaves(loaded)
    flat_loaded = flax.traverse_util.flatten_dict(loaded)
    removed_shape_dtype = {
        "/".join(key): value
        for key, value in flat_loaded.items()
        if isinstance(value, jax.ShapeDtypeStruct)
    }
    partial_params = flax.traverse_util.unflatten_dict(
        {key: value for key, value in flat_loaded.items() if not isinstance(value, jax.ShapeDtypeStruct)}
    )
    return partial_params, {
        "passed": True,
        "params_path": str(cfg.weight_loader.params_path),
        "load_seconds": load_seconds,
        "expected": summarize_tree(params_shape),
        "loaded": summarize_tree(loaded),
        "partial_params": summarize_tree(partial_params),
        "removed_shape_dtype_struct_count": len(removed_shape_dtype),
        "removed_shape_dtype_struct_sample": sorted(removed_shape_dtype)[:16],
    }


def build_loaded_graph(cfg, loaded_params):
    import jax
    from flax import nnx

    _, model_rng = jax.random.split(jax.random.key(cfg.seed))
    model = cfg.model.create(model_rng)
    graphdef, state = nnx.split(model)
    state.replace_by_pure_dict(loaded_params)
    return graphdef, state


def cast_float_tree(tree: Any, dtype_name: str) -> Any:
    if dtype_name == "float32":
        return tree
    import jax
    import ml_dtypes

    target = ml_dtypes.bfloat16

    def cast_leaf(value):
        if hasattr(value, "dtype") and np.issubdtype(value.dtype, np.floating):
            return np.asarray(value).astype(target)
        return value

    return jax.tree.map(cast_leaf, tree)


def numeric_forward(cfg, loaded_params, observation, actions) -> dict[str, Any]:
    import jax
    import jax.numpy as jnp
    from flax import nnx

    import openpi_rtc.shared.array_typing as at

    graphdef, state = build_loaded_graph(cfg, loaded_params)
    obs = jax.tree.map(jnp.asarray, observation)
    act = jax.tree.map(jnp.asarray, actions)

    def loss_fn(params, rng, obs_value, act_value):
        model = nnx.merge(graphdef, params)
        model.train()
        return jnp.mean(model.compute_loss(rng, obs_value, act_value, train=True))

    start = time.time()
    with at.disable_typechecking():
        loss = jax.jit(loss_fn)(state, jax.random.key(cfg.seed + 1), obs, act)
    loss.block_until_ready()
    return {
        "passed": bool(np.isfinite(np.asarray(loss))),
        "loss": float(np.asarray(loss)),
        "seconds": round(time.time() - start, 3),
    }


def numeric_grad(cfg, loaded_params, observation, actions) -> dict[str, Any]:
    import jax
    import jax.numpy as jnp
    from flax import nnx
    import optax

    import openpi_rtc.shared.array_typing as at

    graphdef, state = build_loaded_graph(cfg, loaded_params)
    obs = jax.tree.map(jnp.asarray, observation)
    act = jax.tree.map(jnp.asarray, actions)

    def loss_fn(params, rng, obs_value, act_value):
        model = nnx.merge(graphdef, params)
        model.train()
        return jnp.mean(model.compute_loss(rng, obs_value, act_value, train=True))

    start = time.time()
    with at.disable_typechecking():
        loss, grads = jax.jit(jax.value_and_grad(loss_fn))(state, jax.random.key(cfg.seed + 2), obs, act)
    loss.block_until_ready()
    grad_norm = optax.global_norm(grads)
    grad_norm.block_until_ready()
    return {
        "passed": bool(np.isfinite(np.asarray(loss)) and np.isfinite(np.asarray(grad_norm))),
        "loss": float(np.asarray(loss)),
        "grad_norm": float(np.asarray(grad_norm)),
        "seconds": round(time.time() - start, 3),
    }


def numeric_head_grad(cfg, loaded_params, observation, actions, checkpoint_dir: Path) -> dict[str, Any]:
    import jax
    import jax.numpy as jnp
    from flax import nnx
    from flax import traverse_util
    import optax

    import openpi_rtc.models.model as _model
    import openpi_rtc.shared.array_typing as at
    import openpi_rtc.shared.nnx_utils as nnx_utils

    graphdef, state = build_loaded_graph(cfg, loaded_params)
    model = nnx.merge(graphdef, state)
    model.train()
    obs = jax.tree.map(jnp.asarray, observation)
    act = jax.tree.map(jnp.asarray, actions)
    trainable_filter = nnx.All(
        nnx.Param,
        nnx_utils.PathRegex(r".*(action_in_proj|action_out_proj|knob_).*"),
    )

    @at.typecheck
    def loss_fn(model: _model.BaseModel, rng, obs_value: _model.Observation, act_value: _model.Actions):
        return jnp.mean(model.compute_loss(rng, obs_value, act_value, train=True))

    start = time.time()
    diff_state = nnx.DiffState(0, trainable_filter)
    with at.disable_typechecking():
        loss, grads = nnx.value_and_grad(loss_fn, argnums=diff_state)(model, jax.random.key(cfg.seed + 3), obs, act)
    loss.block_until_ready()
    grad_norm = optax.global_norm(grads)
    grad_norm.block_until_ready()

    trainable_params = nnx.state(model, trainable_filter)
    tx = optax.sgd(1e-6)
    updates, _ = tx.update(grads, tx.init(trainable_params), trainable_params)
    updated_params = optax.apply_updates(trainable_params, updates)
    nnx.update(model, updated_params)

    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    flat_params = traverse_util.flatten_dict(updated_params.to_pure_dict(), sep="/")
    npz_path = checkpoint_dir / "trainable_params_step1.npz"
    np.savez(
        npz_path,
        **{key: np.asarray(value) for key, value in flat_params.items() if hasattr(value, "shape")},
    )
    metadata = {
        "kind": "scoped_trainable_checkpoint",
        "scope": "action_in_proj|action_out_proj|knob_",
        "step": 1,
        "loss": float(np.asarray(loss)),
        "grad_norm": float(np.asarray(grad_norm)),
        "trainable_param_summary": summarize_tree(updated_params),
        "npz_path": str(npz_path),
    }
    metadata_path = checkpoint_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "passed": bool(np.isfinite(np.asarray(loss)) and np.isfinite(np.asarray(grad_norm)) and npz_path.exists()),
        "loss": float(np.asarray(loss)),
        "grad_norm": float(np.asarray(grad_norm)),
        "seconds": round(time.time() - start, 3),
        "checkpoint_dir": str(checkpoint_dir),
        "checkpoint_npz": str(npz_path),
        "checkpoint_metadata": str(metadata_path),
        "trainable_param_summary": summarize_tree(updated_params),
    }


def write_report(status: dict[str, Any], report_path: Path) -> None:
    lines = [
        "# openpi_rtc 数值训练 dry-run",
        "",
        "## 结论",
        "",
        f"- 本轮模式：`{status['mode']}`。",
        f"- 本轮状态：`passed={status['passed']}`。",
        f"- 使用权重：`{status['checkpoint']['params_path']}`。",
        f"- 模型变体：`{status.get('effective_model', {}).get('paligemma_variant', 'unknown')}` + "
        f"`{status.get('effective_model', {}).get('action_expert_variant', 'unknown')}`。",
        f"- GPU 状态：`{status['gpu_before'].get('stdout', '').splitlines()[0] if status['gpu_before'].get('stdout') else 'unknown'}`。",
        "",
        "## 已验证",
        "",
        f"- dataloader state shape：`{status['dataloader']['state_shape']}`。",
        f"- dataloader actions shape：`{status['dataloader']['actions_shape']}`。",
        f"- tokenized prompt shape：`{status['dataloader']['tokenized_prompt_shape']}`。",
        f"- 权重结构校验：`passed={status['weight_preflight'].get('passed')}`。",
        f"- 权重加载耗时：`{status['weight_preflight'].get('load_seconds')}` 秒。",
        f"- 权重 leaf 数：`{status['weight_preflight'].get('loaded', {}).get('leaf_count')}`。",
        f"- 可实际注入的 partial params leaf 数：`{status['weight_preflight'].get('partial_params', {}).get('leaf_count')}`。",
        f"- 已过滤 `ShapeDtypeStruct` leaf 数：`{status['weight_preflight'].get('removed_shape_dtype_struct_count')}`。",
        f"- 权重元素数：`{status['weight_preflight'].get('loaded', {}).get('total_elements')}`。",
        f"- 权重 dtype 分布：`{status['weight_preflight'].get('loaded', {}).get('dtype_counts')}`。",
    ]
    if status.get("forward"):
        lines.extend(["", "## 数值前向", "", f"- 结果：`{status['forward']}`。"])
    if status.get("grad"):
        lines.extend(["", "## 数值反向", "", f"- 结果：`{status['grad']}`。"])
    if status.get("head_grad"):
        lines.extend(
            [
                "",
                "## 小头部反向",
                "",
                f"- 结果：`{status['head_grad']}`。",
                "- 该 checkpoint 只包含 `action_in_proj`、`action_out_proj`、`knob_*` 的 scoped trainable params，不是完整 OpenPI 发布 checkpoint。",
            ]
        )
    if status.get("error"):
        lines.extend(["", "## 错误", "", f"- 类型：`{status['error']['type']}`。", f"- 信息：`{status['error']['message']}`。"])
    lines.extend(
        [
            "",
            "## 边界",
            "",
            "- `weight_preflight` 只证明 `openpi_rtc` 参数结构能接上 `pi05_base` 权重，不代表已经完成训练。",
            "- `forward` 才代表真实数值 loss 前向；`grad` 才代表真实反向梯度。",
            "- `head_grad` 是冻结大模型、只更新小头部参数的低显存 dry-run，用于验证反向和 checkpoint 写出链路。",
            "- 全量 `grad` 可能超过 24GB 显存；失败时应优先改成 LoRA/冻结层 dry-run，而不是假装完成。",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    ensure_import_paths()
    args.status_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.parent.mkdir(parents=True, exist_ok=True)

    status: dict[str, Any] = {
        "mode": args.mode,
        "config_name": args.config_name,
        "repo_id": args.repo_id,
        "checkpoint": {
            "params_path": str(args.params_path),
            "params_exists": args.params_path.exists(),
            "params_size_bytes": None,
        },
        "compute_param_dtype": args.compute_param_dtype,
        "random_action_offset_copies_override": args.random_action_offset_copies,
        "paligemma_variant_override": args.paligemma_variant,
        "action_expert_variant_override": args.action_expert_variant,
        "max_token_len_override": args.max_token_len,
        "action_horizon_override": args.action_horizon,
        "gpu_before": run_text(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free", "--format=csv,noheader"]
        ),
        "passed": False,
    }
    try:
        if not args.params_path.exists():
            raise FileNotFoundError(f"params path does not exist: {args.params_path}")
        status["checkpoint"]["params_size_bytes"] = sum(
            path.stat().st_size for path in args.params_path.rglob("*") if path.is_file()
        )
        cfg = make_config(
            args.config_name,
            args.repo_id,
            args.batch_size,
            args.num_workers,
            args.params_path,
            args.random_action_offset_copies,
            args.paligemma_variant,
            args.action_expert_variant,
            args.max_token_len,
            args.action_horizon,
        )
        status["effective_model"] = {
            "paligemma_variant": cfg.model.paligemma_variant,
            "action_expert_variant": cfg.model.action_expert_variant,
            "pi05": getattr(cfg.model, "pi05", None),
            "ema_decay": cfg.ema_decay,
        }
        status["effective_random_action_offset_copies"] = cfg.data.base_config.random_action_offset_copies
        status["effective_max_token_len"] = cfg.model.max_token_len
        status["effective_action_horizon"] = cfg.model.action_horizon
        observation, actions, dataloader = load_batch(cfg)
        status["dataloader"] = dataloader
        params_shape = expected_param_shape(cfg)
        loaded_params, weight_status = load_and_validate_weights(cfg, params_shape)
        status["weight_preflight"] = weight_status
        compute_params = cast_float_tree(loaded_params, args.compute_param_dtype)
        status["compute_params"] = summarize_tree(compute_params)
        status["passed"] = bool(weight_status.get("passed"))
        if args.mode == "forward":
            status["forward"] = numeric_forward(cfg, compute_params, observation, actions)
            status["passed"] = bool(status["passed"] and status["forward"].get("passed"))
        if args.mode == "grad":
            status["grad"] = numeric_grad(cfg, compute_params, observation, actions)
            status["passed"] = bool(status["passed"] and status["grad"].get("passed"))
        if args.mode == "head_grad":
            status["head_grad"] = numeric_head_grad(cfg, compute_params, observation, actions, args.checkpoint_dir)
            status["passed"] = bool(status["passed"] and status["head_grad"].get("passed"))
    except Exception as exc:  # noqa: BLE001
        status["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
        status["passed"] = False
    finally:
        status["gpu_after"] = run_text(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free", "--format=csv,noheader"]
        )
        args.status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        write_report(status, args.report_path)
        print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
