#!/usr/bin/env python3
"""Validate that the RoboChallenge pi0.5 workspace has minimum handoff files."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "README.md",
    "work.md",
    "configs/repro_targets.json",
    "sources/source_manifest.json",
    "sources/hf_table30v2_api.json",
    "sources/hf_icra_wbc_api.json",
    "baseline/official_table30v2_convert_to_lerobot.py",
    "baseline/official_table30v2_readme.md",
    "reports/initial_repro_assessment.md",
    "reports/pi05_base_repro.md",
    "reports/pi06_pi07_public_release_audit.md",
    "reports/table30v2_aloha_mapping.md",
    "reports/table30v2_aloha_dry_run_converter.md",
    "reports/table30v2_aloha_short_lerobot.md",
    "reports/table30v2_aloha_short_lerobot_cli.md",
    "reports/openpi_rtc_train_entry_audit.md",
    "reports/openpi_rtc_numeric_weight_preflight.md",
    "reports/openpi_rtc_numeric_grad_attempt.md",
    "reports/openpi_rtc_numeric_head_grad.md",
    "reports/openpi_rtc_numeric_head_grad_reduced.md",
    "runs/pi05_base_probe_status.json",
    "runs/pi06_pi07_public_audit.json",
    "runs/table30v2_aloha_mapping_audit.json",
    "runs/table30v2_aloha_dry_run_status.json",
    "runs/table30v2_aloha_dry_run_samples.jsonl",
    "runs/table30v2_aloha_short_lerobot_status.json",
    "runs/table30v2_aloha_short_lerobot_cli_status.json",
    "runs/openpi_rtc_train_entry_audit.json",
    "runs/openpi_rtc_numeric_weight_preflight_status.json",
    "runs/openpi_rtc_numeric_grad_attempt_status.json",
    "runs/openpi_rtc_numeric_head_grad_status.json",
    "runs/openpi_rtc_numeric_head_grad_reduced_status.json",
    "scripts/probe_pi05_base_model.sh",
    "scripts/audit_pi06_pi07_public_release.py",
    "scripts/audit_table30v2_aloha_mapping.py",
    "scripts/dry_run_table30v2_aloha_converter.py",
    "scripts/write_table30v2_aloha_short_lerobot.py",
    "scripts/audit_openpi_rtc_train_entry.py",
    "scripts/run_openpi_rtc_numeric_dry_run.py",
]


def main() -> int:
    missing = [path for path in REQUIRED if not (ROOT / path).exists()]
    if missing:
        print("缺失文件:")
        for path in missing:
            print(f"- {path}")
        return 1

    targets = json.loads((ROOT / "configs/repro_targets.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "sources/source_manifest.json").read_text(encoding="utf-8"))
    if not targets.get("primary_target", {}).get("url"):
        print("primary_target.url 为空")
        return 1
    if len(manifest.get("sources", [])) < 5:
        print("source_manifest 来源过少")
        return 1
    pi05_status = json.loads((ROOT / "runs/pi05_base_probe_status.json").read_text(encoding="utf-8"))
    if not pi05_status.get("local_complete"):
        print("pi05_base 本地缓存尚未完整")
        return 1
    if not pi05_status.get("load_params_smoke", {}).get("loaded"):
        print("pi05_base 参数读取 smoke 未通过")
        return 1
    pi06_pi07_status = json.loads((ROOT / "runs/pi06_pi07_public_audit.json").read_text(encoding="utf-8"))
    if pi06_pi07_status.get("public_checkpoint_found"):
        print("pi0.6/pi0.7 发现公开 checkpoint，请更新复现路线")
        return 1
    mapping_status = json.loads((ROOT / "runs/table30v2_aloha_mapping_audit.json").read_text(encoding="utf-8"))
    if not mapping_status.get("ready_for_dry_run_converter"):
        print("Table30v2 ALOHA 映射尚未满足 dry-run converter 条件")
        return 1
    dry_run_status = json.loads((ROOT / "runs/table30v2_aloha_dry_run_status.json").read_text(encoding="utf-8"))
    if not dry_run_status.get("passed"):
        print("Table30v2 ALOHA dry-run converter 未通过")
        return 1
    smoke = dry_run_status.get("transform_smoke", {})
    if not all(
        [
            smoke.get("state_14d_after_data_transforms"),
            smoke.get("actions_50x14_after_data_transforms"),
            smoke.get("state_32d_after_padding"),
            smoke.get("actions_50x32_after_padding"),
        ]
    ):
        print("Table30v2 ALOHA dry-run transform 形状校验未全部通过")
        return 1
    short_status = json.loads((ROOT / "runs/table30v2_aloha_short_lerobot_status.json").read_text(encoding="utf-8"))
    if not short_status.get("passed"):
        print("Table30v2 ALOHA 短 episode LeRobot writer 或 dataloader smoke 未通过")
        return 1
    short_smoke = short_status.get("dataloader_smoke", {})
    if not all(
        [
            short_smoke.get("state_shape") == [1, 5, 32],
            short_smoke.get("actions_shape") == [1, 5, 50, 32],
            short_smoke.get("image_keys") == ["base_0_rgb", "left_wrist_0_rgb", "right_wrist_0_rgb"],
            short_smoke.get("tokenized_prompt_shape") == [1, 5, 200],
        ]
    ):
        print("Table30v2 ALOHA 短 episode dataloader smoke 形状校验未全部通过")
        return 1
    short_dataset = short_status.get("dataset", {})
    if short_dataset.get("frame_count") != 64 or short_dataset.get("start_index") != 0:
        print("Table30v2 ALOHA 默认短 episode writer 参数不符合预期")
        return 1
    cli_status = json.loads((ROOT / "runs/table30v2_aloha_short_lerobot_cli_status.json").read_text(encoding="utf-8"))
    cli_dataset = cli_status.get("dataset", {})
    cli_smoke = cli_status.get("dataloader_smoke", {})
    if not all(
        [
            cli_status.get("passed"),
            cli_dataset.get("repo_id") == "robochallenge_table30v2_aloha_short_offset10",
            cli_dataset.get("frame_count") == 80,
            cli_dataset.get("start_index") == 10,
            cli_smoke.get("state_shape") == [1, 5, 32],
            cli_smoke.get("actions_shape") == [1, 5, 50, 32],
        ]
    ):
        print("Table30v2 ALOHA 可控分片 writer CLI smoke 未通过")
        return 1
    train_entry = json.loads((ROOT / "runs/openpi_rtc_train_entry_audit.json").read_text(encoding="utf-8"))
    source_audit = train_entry.get("source_audit", {})
    train_data = train_entry.get("dataloader_preflight", {})
    shape_smoke = train_entry.get("train_step_shape_smoke", {})
    if not train_entry.get("passed"):
        print("openpi_rtc 训练入口 shape smoke 未通过")
        return 1
    if not all(
        [
            source_audit.get("standard_train_uses_openpi_training"),
            not source_audit.get("standard_train_uses_openpi_rtc_training"),
            not source_audit.get("rtc_train_entry_exists"),
            source_audit.get("compute_loss_has_multi_offset_branch"),
        ]
    ):
        print("openpi_rtc 训练入口源码审计结果不符合预期")
        return 1
    if not all(
        [
            train_data.get("passed"),
            train_data.get("state_shape") == [1, 5, 32],
            train_data.get("actions_shape") == [1, 5, 50, 32],
            train_data.get("tokenized_prompt_shape") == [1, 5, 200],
            train_data.get("image_keys") == ["base_0_rgb", "left_wrist_0_rgb", "right_wrist_0_rgb"],
        ]
    ):
        print("openpi_rtc 训练入口 dataloader preflight 未通过")
        return 1
    if not all(
        [
            shape_smoke.get("passed"),
            shape_smoke.get("mode") == "jax.eval_shape",
            shape_smoke.get("info_shape", {}).get("loss", {}).get("shape") == [],
            shape_smoke.get("info_shape", {}).get("grad_norm", {}).get("shape") == [],
        ]
    ):
        print("openpi_rtc train_step 前向/反向 shape smoke 未通过")
        return 1
    weight_preflight = json.loads(
        (ROOT / "runs/openpi_rtc_numeric_weight_preflight_status.json").read_text(encoding="utf-8")
    )
    weight_data = weight_preflight.get("dataloader", {})
    weight_status = weight_preflight.get("weight_preflight", {})
    if not all(
        [
            weight_preflight.get("mode") == "weight_preflight",
            weight_preflight.get("passed"),
            weight_preflight.get("effective_random_action_offset_copies") == 5,
            weight_data.get("state_shape") == [1, 5, 32],
            weight_data.get("actions_shape") == [1, 5, 50, 32],
            weight_data.get("tokenized_prompt_shape") == [1, 5, 200],
            weight_status.get("passed"),
            weight_status.get("partial_params", {}).get("leaf_count") == 51,
            weight_status.get("removed_shape_dtype_struct_count") == 2,
        ]
    ):
        print("openpi_rtc pi05_base 数值权重预检未通过")
        return 1
    grad_attempt = json.loads(
        (ROOT / "runs/openpi_rtc_numeric_grad_attempt_status.json").read_text(encoding="utf-8")
    )
    grad_error = grad_attempt.get("error", {})
    if not all(
        [
            grad_attempt.get("mode") == "grad",
            not grad_attempt.get("passed"),
            grad_attempt.get("weight_preflight", {}).get("passed"),
            grad_error.get("type") == "XlaRuntimeError",
            "CUDA_ERROR_OUT_OF_MEMORY" in grad_error.get("message", ""),
        ]
    ):
        print("openpi_rtc 全量 grad 尝试未记录为预期 CUDA OOM blocker")
        return 1
    head_grad = json.loads(
        (ROOT / "runs/openpi_rtc_numeric_head_grad_status.json").read_text(encoding="utf-8")
    )
    head_data = head_grad.get("dataloader", {})
    head_error = head_grad.get("error", {})
    if not all(
        [
            head_grad.get("mode") == "head_grad",
            not head_grad.get("passed"),
            head_grad.get("weight_preflight", {}).get("passed"),
            head_grad.get("effective_random_action_offset_copies") == 1,
            head_data.get("state_shape") == [1, 32],
            head_data.get("actions_shape") == [1, 50, 32],
            head_data.get("tokenized_prompt_shape") == [1, 200],
            head_error.get("type") == "XlaRuntimeError",
            "CUDA_ERROR_OUT_OF_MEMORY" in head_error.get("message", ""),
        ]
    ):
        print("openpi_rtc 小头部 head_grad 尝试未记录为预期 CUDA OOM blocker")
        return 1
    head_grad_reduced = json.loads(
        (ROOT / "runs/openpi_rtc_numeric_head_grad_reduced_status.json").read_text(encoding="utf-8")
    )
    reduced_data = head_grad_reduced.get("dataloader", {})
    reduced_error = head_grad_reduced.get("error", {})
    reduced_error_message = reduced_error.get("message", "")
    if not all(
        [
            head_grad_reduced.get("mode") == "head_grad",
            not head_grad_reduced.get("passed"),
            head_grad_reduced.get("weight_preflight", {}).get("passed"),
            head_grad_reduced.get("effective_random_action_offset_copies") == 1,
            head_grad_reduced.get("effective_max_token_len") == 64,
            head_grad_reduced.get("effective_action_horizon") == 10,
            reduced_data.get("state_shape") == [1, 32],
            reduced_data.get("actions_shape") == [1, 10, 32],
            reduced_data.get("tokenized_prompt_shape") == [1, 64],
            reduced_error.get("type") == "XlaRuntimeError",
            (
                "INTERNAL: an internal operation failed" in reduced_error_message
                or "CUDA_ERROR_OUT_OF_MEMORY" in reduced_error_message
            ),
        ]
    ):
        print("openpi_rtc 缩短序列 head_grad 尝试未记录为预期 XLA blocker")
        return 1
    if (ROOT / "runs/openpi_rtc_head_grad_checkpoint/metadata.json").exists():
        print("检测到 head_grad checkpoint metadata，但当前已验证状态并未成功写出 checkpoint")
        return 1

    print("工作区最低交接材料检查通过")
    print(f"根目录: {ROOT}")
    print(f"来源数量: {len(manifest['sources'])}")
    print("pi05_base 基模缓存与参数读取 smoke 已通过")
    print("pi0.6/pi0.7 公开 checkpoint 审计已完成")
    print("Table30v2 ALOHA 最小分片字段映射已通过")
    print("Table30v2 ALOHA dry-run converter 已通过")
    print("Table30v2 ALOHA 短 episode LeRobot writer 与 dataloader smoke 已通过")
    print("Table30v2 ALOHA 可控分片 writer CLI smoke 已通过")
    print("openpi_rtc 训练入口 shape smoke 已通过")
    print("openpi_rtc pi05_base 权重预检已通过，全量 grad 与小头部 grad blocker 已记录")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
