#!/usr/bin/env python3
"""Audit and shape-smoke the openpi_rtc training entry for Table30v2 ALOHA."""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
from pathlib import Path
import sys
import traceback
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
BASELINE = Path(os.environ.get("BASELINE", "/home/yjl/yjl/RoboChallenge/baseline_pi05_multitask"))
BASELINE_PYTHON = BASELINE / ".venv/bin/python3"
if (
    BASELINE_PYTHON.exists()
    and Path(sys.executable).resolve() != BASELINE_PYTHON.resolve()
    and os.environ.get("OPENPI_RTC_TRAIN_AUDIT_REEXEC") != "1"
):
    os.environ["OPENPI_RTC_TRAIN_AUDIT_REEXEC"] = "1"
    os.execv(str(BASELINE_PYTHON), [str(BASELINE_PYTHON), *sys.argv])


OPENPI_ROOT = BASELINE / "openpi"
OPENPI_SRC = OPENPI_ROOT / "src"
OPENPI_CLIENT_SRC = OPENPI_ROOT / "packages/openpi-client/src"
LEROBOT_SRC = Path(os.environ.get("LEROBOT_SRC", "/home/yjl/yjl/RoboChallenge/third_party/lerobot"))
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
DEFAULT_STATUS_PATH = RUNS_DIR / "openpi_rtc_train_entry_audit.json"
DEFAULT_REPORT_PATH = REPORTS_DIR / "openpi_rtc_train_entry_audit.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="审计 openpi_rtc 训练入口，并用 Table30v2 ALOHA 短分片做 1-step shape smoke。"
    )
    parser.add_argument("--config-name", default="cvpr_multitask_aloha_rtc", help="OpenPI RTC config 名称。")
    parser.add_argument("--repo-id", default="robochallenge_table30v2_aloha_short", help="本地 LeRobot repo_id。")
    parser.add_argument("--batch-size", type=int, default=1, help="shape smoke 使用的 batch size。")
    parser.add_argument("--num-workers", type=int, default=1, help="dataloader worker 数。")
    parser.add_argument(
        "--skip-shape-train-step",
        action="store_true",
        help="只做源码和 dataloader preflight，不做抽象 train_step 前向/反向 shape smoke。",
    )
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS_PATH, help="状态 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT_PATH, help="中文报告输出路径。")
    return parser.parse_args()


def ensure_import_paths() -> None:
    for path in [OPENPI_SRC, OPENPI_CLIENT_SRC, LEROBOT_SRC]:
        text = str(path)
        if text not in sys.path:
            sys.path.insert(0, text)


def summarize_array_like(value: Any) -> Any:
    if value is None:
        return {"type": "NoneType", "value": None}
    if isinstance(value, dict):
        return {key: summarize_array_like(item) for key, item in value.items()}
    if hasattr(value, "to_dict"):
        return summarize_array_like(value.to_dict())
    if isinstance(value, (list, tuple)):
        return [summarize_array_like(item) for item in value]
    if hasattr(value, "shape") and hasattr(value, "dtype"):
        return {"shape": list(value.shape), "dtype": str(value.dtype)}
    arr = np.asarray(value)
    return {"shape": list(arr.shape), "dtype": str(arr.dtype)}


def shape_dtype(value: Any) -> dict[str, Any]:
    if hasattr(value, "shape") and hasattr(value, "dtype"):
        return {"shape": list(value.shape), "dtype": str(value.dtype)}
    return {"type": type(value).__name__}


def flatten_shape_summary(value: Any, limit: int = 16) -> dict[str, Any]:
    import jax

    leaves = jax.tree_util.tree_leaves(value)
    return {
        "leaf_count": len(leaves),
        "sample_leaves": [shape_dtype(leaf) for leaf in leaves[:limit]],
    }


def source_audit() -> dict[str, Any]:
    scripts_dir = OPENPI_ROOT / "scripts"
    standard_train = scripts_dir / "train.py"
    rtc_train = scripts_dir / "train_rtc.py"
    rtc_weight_loader = OPENPI_SRC / "openpi_rtc/training/weight_loaders.py"
    rtc_model = OPENPI_SRC / "openpi_rtc/models/pi0.py"

    standard_train_text = standard_train.read_text(encoding="utf-8")
    weight_loader_text = rtc_weight_loader.read_text(encoding="utf-8")
    rtc_model_text = rtc_model.read_text(encoding="utf-8")
    train_candidates = sorted(path.name for path in scripts_dir.glob("*train*.py"))

    return {
        "baseline": str(BASELINE),
        "openpi_root": str(OPENPI_ROOT),
        "train_candidates": train_candidates,
        "standard_train_path": str(standard_train),
        "rtc_train_path": str(rtc_train),
        "rtc_train_entry_exists": rtc_train.exists(),
        "standard_train_uses_openpi_training": "openpi.training" in standard_train_text,
        "standard_train_uses_openpi_rtc_training": "openpi_rtc.training" in standard_train_text,
        "weight_loader_uses_standard_model_namespace": "import openpi.models.model" in weight_loader_text,
        "weight_loader_uses_rtc_model_namespace": "import openpi_rtc.models.model" in weight_loader_text,
        "compute_loss_has_multi_offset_branch": "multi_offset = actions.ndim == 4" in rtc_model_text,
        "compute_loss_requires_prompt_chunk_mask": "Multi-offset training requires per-chunk tokenized_prompt_mask"
        in rtc_model_text,
    }


def make_local_config(config_name: str, repo_id: str, batch_size: int, num_workers: int):
    from openpi_rtc.training import config as train_config

    cfg = train_config.get_config(config_name)
    cfg = dataclasses.replace(
        cfg,
        exp_name=f"robochallenge_{repo_id}_shape_smoke",
        data=dataclasses.replace(cfg.data, repo_id=repo_id),
        batch_size=batch_size,
        num_workers=num_workers,
        num_train_steps=1,
        log_interval=1,
        save_interval=1,
        keep_period=None,
        overwrite=True,
        resume=False,
        wandb_enabled=False,
        checkpoint_base_dir=str(RUNS_DIR / "openpi_rtc_train_checkpoints"),
        assets_base_dir=str(RUNS_DIR / "openpi_rtc_train_assets"),
    )
    return cfg


def load_one_batch(cfg) -> tuple[Any, Any, dict[str, Any]]:
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
    observation_summary = summarize_array_like(observation)
    actions_summary = summarize_array_like(actions)
    checks = {
        "repo_id": cfg.data.repo_id,
        "config_name": cfg.name,
        "model_type": str(cfg.model.model_type),
        "model_action_dim": int(cfg.model.action_dim),
        "action_horizon": int(cfg.model.action_horizon),
        "max_token_len": int(cfg.model.max_token_len),
        "random_action_offset": bool(cfg.data.base_config.random_action_offset),
        "random_action_offset_copies": int(cfg.data.base_config.random_action_offset_copies),
        "random_action_offset_max": int(cfg.data.base_config.random_action_offset_max),
        "observation_summary": observation_summary,
        "actions_summary": actions_summary,
        "state_shape": observation_summary.get("state", {}).get("shape"),
        "actions_shape": actions_summary.get("shape"),
        "image_keys": sorted(observation_summary.get("image", {}).keys()),
        "tokenized_prompt_shape": observation_summary.get("tokenized_prompt", {}).get("shape"),
        "tokenized_prompt_mask_shape": observation_summary.get("tokenized_prompt_mask", {}).get("shape"),
        "action_is_pad_shape": observation_summary.get("action_is_pad", {}).get("shape"),
    }
    checks["passed"] = all(
        [
            checks["state_shape"] == [cfg.batch_size, 5, cfg.model.action_dim],
            checks["actions_shape"] == [cfg.batch_size, 5, cfg.model.action_horizon, cfg.model.action_dim],
            checks["tokenized_prompt_shape"] == [cfg.batch_size, 5, cfg.model.max_token_len],
            checks["tokenized_prompt_mask_shape"] == [cfg.batch_size, 5, cfg.model.max_token_len],
            checks["image_keys"] == ["base_0_rgb", "left_wrist_0_rgb", "right_wrist_0_rgb"],
        ]
    )
    return observation, actions, checks


def rtc_train_step(config, rng, state, batch):
    import dataclasses as _dataclasses

    from flax import nnx
    import jax
    import jax.numpy as jnp
    import optax

    import openpi_rtc.models.model as _model
    import openpi_rtc.shared.array_typing as at
    import openpi_rtc.shared.nnx_utils as nnx_utils

    model = nnx.merge(state.model_def, state.params)
    model.train()

    @at.typecheck
    def loss_fn(model: _model.BaseModel, rng, observation: _model.Observation, actions: _model.Actions):
        chunked_loss = model.compute_loss(rng, observation, actions, train=True)
        return jnp.mean(chunked_loss)

    train_rng = jax.random.fold_in(rng, state.step)
    observation, actions = batch
    diff_state = nnx.DiffState(0, config.trainable_filter)
    loss, grads = nnx.value_and_grad(loss_fn, argnums=diff_state)(model, train_rng, observation, actions)

    params = state.params.filter(config.trainable_filter)
    updates, new_opt_state = state.tx.update(grads, state.opt_state, params)
    new_params = optax.apply_updates(params, updates)
    nnx.update(model, new_params)
    new_params = nnx.state(model)

    new_state = _dataclasses.replace(state, step=state.step + 1, params=new_params, opt_state=new_opt_state)
    if state.ema_decay is not None:
        new_state = _dataclasses.replace(
            new_state,
            ema_params=jax.tree.map(
                lambda old, new: state.ema_decay * old + (1 - state.ema_decay) * new,
                state.ema_params,
                new_params,
            ),
        )

    kernel_params = nnx.state(
        model,
        nnx.All(
            nnx.Param,
            nnx.Not(nnx_utils.PathRegex(".*/(bias|scale|pos_embedding|input_embedding)")),
            lambda _, x: x.value.ndim > 1,
        ),
    )
    info = {
        "loss": loss,
        "grad_norm": optax.global_norm(grads),
        "param_norm": optax.global_norm(kernel_params),
    }
    return new_state, info


def train_step_shape_smoke(cfg, observation, actions) -> dict[str, Any]:
    import jax
    import jax.numpy as jnp
    from flax import nnx

    from openpi_rtc.shared import nnx_utils
    import openpi_rtc.shared.array_typing as at
    from openpi_rtc.training import optimizer as rtc_optimizer
    from openpi_rtc.training import utils as training_utils

    tx = rtc_optimizer.create_optimizer(cfg.optimizer, cfg.lr_schedule, weight_decay_mask=None)

    def init(rng):
        rng, model_rng = jax.random.split(rng)
        del rng
        model = cfg.model.create(model_rng)
        params = nnx.state(model)
        params = nnx_utils.state_map(params, cfg.freeze_filter, lambda p: p.replace(p.value.astype(jnp.bfloat16)))
        return training_utils.TrainState(
            step=0,
            params=params,
            model_def=nnx.graphdef(model),
            tx=tx,
            opt_state=tx.init(params.filter(cfg.trainable_filter)),
            ema_decay=cfg.ema_decay,
            ema_params=None if cfg.ema_decay is None else params,
        )

    rng = jax.random.key(cfg.seed)
    train_state_shape = jax.eval_shape(init, rng)
    with at.disable_typechecking():
        new_state_shape, info_shape = jax.eval_shape(
            lambda step_rng, state, obs, act: rtc_train_step(cfg, step_rng, state, (obs, act)),
            rng,
            train_state_shape,
            observation,
            actions,
        )

    return {
        "passed": True,
        "mode": "jax.eval_shape",
        "meaning": "验证 openpi_rtc train_step 的前向 loss 与反向梯度图形状，不加载 pi05_base 权重，不执行数值训练。",
        "train_state_shape": flatten_shape_summary(train_state_shape),
        "new_state_shape": flatten_shape_summary(new_state_shape),
        "info_shape": summarize_array_like(info_shape),
    }


def write_report(status: dict[str, Any], report_path: Path) -> None:
    source = status["source_audit"]
    data = status["dataloader_preflight"]
    shape = status["train_step_shape_smoke"]
    lines = [
        "# openpi_rtc 训练入口审计",
        "",
        "## 结论",
        "",
        f"- 本轮状态：`passed={status['passed']}`。",
        "- `openpi/scripts/train.py` 绑定的是标准 `openpi.training.*`，不能直接当作 RoboChallenge 的 `openpi_rtc` 训练入口。",
        f"- baseline 中现成 `train_rtc.py`：`exists={source['rtc_train_entry_exists']}`。",
        "- 已用本地 Table30v2 ALOHA 短分片完成 `openpi_rtc` dataloader preflight。",
    ]
    if shape.get("passed"):
        lines.append("- 已完成抽象 `train_step` 前向 loss 与反向梯度 shape smoke。")
    else:
        lines.append("- 抽象 `train_step` shape smoke 未通过，见状态 JSON 的错误栈。")
    lines.extend(
        [
            "",
            "## 源码审计",
            "",
            f"- 训练候选脚本：`{source['train_candidates']}`。",
            f"- 标准训练脚本使用 `openpi.training`：`{source['standard_train_uses_openpi_training']}`。",
            f"- 标准训练脚本使用 `openpi_rtc.training`：`{source['standard_train_uses_openpi_rtc_training']}`。",
            f"- `openpi_rtc` weight loader 仍引用标准 `openpi.models.model`：`{source['weight_loader_uses_standard_model_namespace']}`。",
            f"- `compute_loss` 支持 4 维 multi-offset actions：`{source['compute_loss_has_multi_offset_branch']}`。",
            "",
            "## 数据入口",
            "",
            f"- config：`{data['config_name']}`。",
            f"- repo_id：`{data['repo_id']}`。",
            f"- model/action_dim/action_horizon：`{data['model_type']}` / `{data['model_action_dim']}` / `{data['action_horizon']}`。",
            f"- random_action_offset：`{data['random_action_offset']}`，copies=`{data['random_action_offset_copies']}`，max=`{data['random_action_offset_max']}`。",
            f"- state shape：`{data['state_shape']}`。",
            f"- actions shape：`{data['actions_shape']}`。",
            f"- tokenized prompt shape：`{data['tokenized_prompt_shape']}`。",
            f"- image keys：`{data['image_keys']}`。",
            "",
            "## 边界",
            "",
            "- 本轮验证的是训练图和维度闭合，不代表已经完成真实数值训练。",
            "- 本轮没有加载 `pi05_base` 的 12GB 级权重，也没有写真实训练 checkpoint。",
            "- 下一步应把这个 shape smoke 固化成最小 `openpi_rtc` 训练脚本，再在 GPU 上做真实 1-step loss/grad/checkpoint dry-run。",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    ensure_import_paths()
    args.status_path.parent.mkdir(exist_ok=True, parents=True)
    args.report_path.parent.mkdir(exist_ok=True, parents=True)

    source = source_audit()
    cfg = make_local_config(args.config_name, args.repo_id, args.batch_size, args.num_workers)
    observation, actions, dataloader_status = load_one_batch(cfg)

    if args.skip_shape_train_step:
        shape_status = {
            "passed": False,
            "skipped": True,
            "reason": "--skip-shape-train-step 已启用。",
        }
    else:
        try:
            shape_status = train_step_shape_smoke(cfg, observation, actions)
        except Exception as exc:  # noqa: BLE001 - status JSON needs the complete blocker.
            shape_status = {
                "passed": False,
                "skipped": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }

    status = {
        "source_audit": source,
        "dataloader_preflight": dataloader_status,
        "train_step_shape_smoke": shape_status,
        "passed": bool(
            dataloader_status.get("passed")
            and source.get("standard_train_uses_openpi_training")
            and source.get("compute_loss_has_multi_offset_branch")
            and shape_status.get("passed")
        ),
        "numeric_train_step_done": False,
        "numeric_train_step_blocker": "尚未加载 pi05_base 权重执行真实 1-step；下一轮在 GPU 上做真实 loss/grad/checkpoint dry-run。",
    }
    args.status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(status, args.report_path)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
