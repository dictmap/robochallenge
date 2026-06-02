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
    "reports/openpi_rtc_lora_path_audit.md",
    "reports/openpi_rtc_lora_numeric_weight_preflight.md",
    "reports/openpi_rtc_lora_numeric_forward_reduced.md",
    "reports/openpi_rtc_lora_numeric_grad_reduced.md",
    "reports/openpi_rtc_lora_checkpoint_restore_audit.md",
    "reports/openpi_rtc_lora_inference_checkpoint_layout.md",
    "reports/openpi_rtc_lora_inference_checkpoint_materialize.md",
    "reports/openpi_rtc_lora_materialized_policy_smoke.md",
    "reports/lora_checkpoint_export_readiness.md",
    "reports/checkpoint_archive_plan.md",
    "reports/checkpoint_upload_channels_audit.md",
    "reports/real_submission_readiness.md",
    "reports/real_submission_readiness_scenarios.md",
    "reports/submission_handoff_docs_audit.md",
    "reports/plaintext_secret_scan.md",
    "reports/robochallenge_submission_package_checklist.md",
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
    "runs/openpi_rtc_lora_path_audit.json",
    "runs/openpi_rtc_lora_numeric_weight_preflight_status.json",
    "runs/openpi_rtc_lora_numeric_forward_reduced_status.json",
    "runs/openpi_rtc_lora_numeric_grad_reduced_status.json",
    "runs/openpi_rtc_lora_checkpoint_restore_audit.json",
    "runs/openpi_rtc_lora_inference_checkpoint_layout_audit.json",
    "runs/openpi_rtc_lora_inference_checkpoint_materialize_status.json",
    "runs/openpi_rtc_lora_materialized_policy_smoke_status.json",
    "runs/lora_checkpoint_export_readiness.json",
    "runs/checkpoint_archive_plan.json",
    "runs/checkpoint_upload_channels_audit.json",
    "runs/real_submission_readiness.json",
    "runs/real_submission_readiness_scenarios.json",
    "runs/submission_handoff_docs_audit.json",
    "runs/plaintext_secret_scan.json",
    "runs/robochallenge_submission_package_audit.json",
    "submission/README.md",
    "submission/REAL_SUBMISSION_HANDOFF.md",
    "submission/submission_manifest_template.json",
    "submission/run_table30v2_aloha_demo_template.sh",
    "submission/run_table30v2_aloha_lora_demo_template.sh",
    "scripts/probe_pi05_base_model.sh",
    "scripts/audit_pi06_pi07_public_release.py",
    "scripts/audit_table30v2_aloha_mapping.py",
    "scripts/dry_run_table30v2_aloha_converter.py",
    "scripts/write_table30v2_aloha_short_lerobot.py",
    "scripts/audit_openpi_rtc_train_entry.py",
    "scripts/run_openpi_rtc_numeric_dry_run.py",
    "scripts/audit_openpi_rtc_lora_path.py",
    "scripts/audit_openpi_rtc_lora_checkpoint_restore.py",
    "scripts/audit_openpi_rtc_lora_inference_checkpoint_layout.py",
    "scripts/smoke_openpi_rtc_materialized_policy.py",
    "scripts/audit_lora_checkpoint_export_readiness.py",
    "scripts/audit_checkpoint_archive_plan.py",
    "scripts/audit_checkpoint_upload_channels.py",
    "scripts/audit_real_submission_readiness.py",
    "scripts/audit_real_submission_readiness_scenarios.py",
    "scripts/audit_submission_handoff_docs.py",
    "scripts/audit_plaintext_secrets.py",
    "scripts/audit_robochallenge_submission_package.py",
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
    lora_audit = json.loads((ROOT / "runs/openpi_rtc_lora_path_audit.json").read_text(encoding="utf-8"))
    lora_model = lora_audit.get("model", {})
    lora_counts = lora_audit.get("param_counts", {})
    lora_weight = lora_audit.get("weight_preflight", {})
    if not all(
        [
            lora_audit.get("passed"),
            lora_model.get("paligemma_variant") == "gemma_2b_lora",
            lora_model.get("action_expert_variant") == "gemma_300m_lora",
            lora_model.get("pi05") is True,
            lora_audit.get("ema_decay") is None,
            lora_counts.get("all", {}).get("leaf_count") == 73,
            lora_counts.get("lora", {}).get("leaf_count") == 20,
            lora_counts.get("lora", {}).get("total_elements") == 49987584,
            lora_counts.get("trainable", {}).get("leaf_count") == 53,
            lora_weight.get("passed"),
            lora_weight.get("loaded_leaf_count") == 73,
            lora_weight.get("loaded_lora_leaf_count") == 20,
            lora_weight.get("loaded_knob_leaf_count") == 2,
        ]
    ):
        print("openpi_rtc LoRA 低显存路线审计未通过")
        return 1
    lora_weight = json.loads(
        (ROOT / "runs/openpi_rtc_lora_numeric_weight_preflight_status.json").read_text(encoding="utf-8")
    )
    lora_weight_model = lora_weight.get("effective_model", {})
    lora_weight_data = lora_weight.get("dataloader", {})
    lora_weight_status = lora_weight.get("weight_preflight", {})
    if not all(
        [
            lora_weight.get("mode") == "weight_preflight",
            lora_weight.get("passed"),
            lora_weight_model.get("paligemma_variant") == "gemma_2b_lora",
            lora_weight_model.get("action_expert_variant") == "gemma_300m_lora",
            lora_weight_model.get("pi05") is True,
            lora_weight_model.get("ema_decay") is None,
            lora_weight.get("effective_random_action_offset_copies") == 1,
            lora_weight.get("effective_max_token_len") == 64,
            lora_weight.get("effective_action_horizon") == 10,
            lora_weight_data.get("state_shape") == [1, 32],
            lora_weight_data.get("actions_shape") == [1, 10, 32],
            lora_weight_data.get("tokenized_prompt_shape") == [1, 64],
            lora_weight_status.get("passed"),
            lora_weight_status.get("loaded", {}).get("leaf_count") == 73,
            lora_weight_status.get("partial_params", {}).get("leaf_count") == 51,
            lora_weight_status.get("removed_shape_dtype_struct_count") == 22,
        ]
    ):
        print("openpi_rtc LoRA 数值权重预检未通过")
        return 1
    lora_forward = json.loads(
        (ROOT / "runs/openpi_rtc_lora_numeric_forward_reduced_status.json").read_text(encoding="utf-8")
    )
    lora_forward_model = lora_forward.get("effective_model", {})
    lora_forward_data = lora_forward.get("dataloader", {})
    lora_forward_result = lora_forward.get("forward", {})
    if not all(
        [
            lora_forward.get("mode") == "forward",
            lora_forward.get("passed"),
            lora_forward_model.get("paligemma_variant") == "gemma_2b_lora",
            lora_forward_model.get("action_expert_variant") == "gemma_300m_lora",
            lora_forward_model.get("pi05") is True,
            lora_forward.get("compute_param_dtype") == "bfloat16",
            lora_forward.get("effective_random_action_offset_copies") == 1,
            lora_forward.get("effective_max_token_len") == 64,
            lora_forward.get("effective_action_horizon") == 10,
            lora_forward_data.get("state_shape") == [1, 32],
            lora_forward_data.get("actions_shape") == [1, 10, 32],
            lora_forward_data.get("tokenized_prompt_shape") == [1, 64],
            lora_forward.get("weight_preflight", {}).get("passed"),
            lora_forward.get("weight_preflight", {}).get("loaded", {}).get("leaf_count") == 73,
            lora_forward.get("weight_preflight", {}).get("removed_shape_dtype_struct_count") == 22,
            lora_forward_result.get("passed"),
            isinstance(lora_forward_result.get("loss"), (int, float)),
        ]
    ):
        print("openpi_rtc LoRA reduced forward smoke 未通过")
        return 1
    lora_grad = json.loads(
        (ROOT / "runs/openpi_rtc_lora_numeric_grad_reduced_status.json").read_text(encoding="utf-8")
    )
    lora_grad_model = lora_grad.get("effective_model", {})
    lora_grad_data = lora_grad.get("dataloader", {})
    lora_grad_result = lora_grad.get("lora_grad", {})
    lora_grad_summary = lora_grad_result.get("trainable_param_summary", {})
    lora_restore = json.loads(
        (ROOT / "runs/openpi_rtc_lora_checkpoint_restore_audit.json").read_text(encoding="utf-8")
    )
    lora_restore_model = lora_restore.get("model", {})
    lora_restore_checkpoint = lora_restore.get("checkpoint", {})
    lora_restore_metadata = lora_restore_checkpoint.get("metadata", {})
    lora_restore_merge = lora_restore.get("merge_audit", {})
    if not all(
        [
            lora_restore.get("passed"),
            lora_restore_model.get("paligemma_variant") == "gemma_2b_lora",
            lora_restore_model.get("action_expert_variant") == "gemma_300m_lora",
            lora_restore_model.get("pi05") is True,
            lora_restore.get("ema_decay") is None,
            lora_restore_checkpoint.get("checkpoint_npz")
            == "runs/openpi_rtc_lora_grad_checkpoint/trainable_params_step1.npz",
            lora_restore_checkpoint.get("metadata_path") == "runs/openpi_rtc_lora_grad_checkpoint/metadata.json",
            lora_restore_metadata.get("kind") == "scoped_trainable_checkpoint",
            lora_restore_metadata.get("scope") == "cfg.trainable_filter",
            lora_restore_merge.get("expected_leaf_count") == 73,
            lora_restore_merge.get("base_loaded_leaf_count") == 73,
            lora_restore_merge.get("trainable_filter_key_count") == 53,
            lora_restore_merge.get("checkpoint_key_count") == 53,
            lora_restore_merge.get("checkpoint_lora_key_count") == 20,
            lora_restore_merge.get("checkpoint_knob_key_count") == 2,
            lora_restore_merge.get("placeholder_before_count") == 22,
            lora_restore_merge.get("overwritten_leaf_count") == 53,
            lora_restore_merge.get("placeholder_after_count") == 0,
            lora_restore_merge.get("missing_checkpoint_keys") == [],
            lora_restore_merge.get("unexpected_checkpoint_keys") == [],
            lora_restore_merge.get("checkpoint_not_trainable_keys") == [],
            lora_restore_merge.get("shape_mismatches") == [],
            lora_restore_merge.get("tree_check_passed"),
            lora_restore_merge.get("state_replace_passed"),
        ]
    ):
        print("openpi_rtc LoRA scoped checkpoint restore/merge audit 未通过")
        return 1
    lora_layout = json.loads(
        (ROOT / "runs/openpi_rtc_lora_inference_checkpoint_layout_audit.json").read_text(encoding="utf-8")
    )
    lora_layout_model = lora_layout.get("model", {})
    lora_layout_info = lora_layout.get("layout", {})
    lora_layout_base = lora_layout_info.get("pi05_base_params", {})
    lora_layout_official = lora_layout_info.get("official_aloha_checkpoint", {})
    lora_layout_target = lora_layout_info.get("target_checkpoint", {})
    lora_layout_scoped = lora_layout.get("scoped_checkpoint", {})
    lora_layout_restore = lora_layout.get("restore_audit", {})
    lora_layout_smoke = lora_layout.get("tiny_save_smoke", {})
    lora_layout_materialize = lora_layout.get("materialize", {})
    if not all(
        [
            lora_layout.get("passed"),
            lora_layout.get("direct_demo_checkpoint_ready") is False,
            lora_layout_model.get("paligemma_variant") == "gemma_2b_lora",
            lora_layout_model.get("action_expert_variant") == "gemma_300m_lora",
            lora_layout_model.get("pi05") is True,
            lora_layout_model.get("ema_decay") is None,
            lora_layout_model.get("expected_leaf_count") == 73,
            lora_layout_model.get("trainable_filter_key_count") == 53,
            lora_layout_info.get("asset_id") == "cvpr_multitask_aloha",
            lora_layout_base.get("params_dir_exists"),
            lora_layout_base.get("params_metadata_exists"),
            lora_layout_base.get("params_manifest_exists"),
            lora_layout_official.get("params_dir_exists"),
            lora_layout_official.get("params_metadata_exists"),
            lora_layout_official.get("asset_norm_stats_exists"),
            lora_layout_target.get("safe_target_under_runs"),
            lora_layout_target.get("git_ignore", {}).get("ignored"),
            lora_layout_scoped.get("leaf_count") == 53,
            lora_layout_scoped.get("metadata_kind") == "scoped_trainable_checkpoint",
            lora_layout_scoped.get("metadata_scope") == "cfg.trainable_filter",
            lora_layout_restore.get("passed"),
            lora_layout_restore.get("placeholder_after_count") == 0,
            lora_layout_smoke.get("attempted"),
            lora_layout_smoke.get("passed"),
            lora_layout_smoke.get("metadata_exists"),
            lora_layout_smoke.get("manifest_exists"),
            lora_layout_materialize.get("attempted") is False,
        ]
    ):
        print("openpi_rtc LoRA 推理 checkpoint 物化布局审计未通过")
        return 1
    lora_materialize = json.loads(
        (ROOT / "runs/openpi_rtc_lora_inference_checkpoint_materialize_status.json").read_text(encoding="utf-8")
    )
    lora_materialize_result = lora_materialize.get("materialize", {})
    lora_materialize_target = lora_materialize.get("layout", {}).get("target_checkpoint", {})
    if not all(
        [
            lora_materialize.get("passed"),
            lora_materialize.get("direct_demo_checkpoint_ready") is True,
            lora_materialize.get("model", {}).get("paligemma_variant") == "gemma_2b_lora",
            lora_materialize.get("model", {}).get("action_expert_variant") == "gemma_300m_lora",
            lora_materialize.get("model", {}).get("pi05") is True,
            lora_materialize_target.get("git_ignore", {}).get("ignored"),
            lora_materialize_result.get("attempted"),
            lora_materialize_result.get("passed"),
            lora_materialize_result.get("safe_target_under_runs"),
            lora_materialize_result.get("asset_norm_stats_exists"),
            lora_materialize_result.get("restored_leaf_count") == 73,
            lora_materialize_result.get("restored_tree_check_passed"),
            lora_materialize_result.get("state_replace_passed"),
        ]
    ):
        print("openpi_rtc LoRA 完整推理 checkpoint 物化未通过")
        return 1
    lora_policy_smoke = json.loads(
        (ROOT / "runs/openpi_rtc_lora_materialized_policy_smoke_status.json").read_text(encoding="utf-8")
    )
    lora_policy_layout = lora_policy_smoke.get("checkpoint_layout", {})
    lora_policy_load = lora_policy_smoke.get("policy_load_smoke", {})
    if not all(
        [
            lora_policy_smoke.get("passed"),
            lora_policy_smoke.get("checkpoint_dir") == "runs/openpi_rtc_lora_materialized_policy_checkpoint",
            lora_policy_smoke.get("asset_id") == "cvpr_multitask_aloha",
            lora_policy_smoke.get("model", {}).get("paligemma_variant") == "gemma_2b_lora",
            lora_policy_smoke.get("model", {}).get("action_expert_variant") == "gemma_300m_lora",
            lora_policy_smoke.get("model", {}).get("pi05") is True,
            lora_policy_layout.get("params_metadata_exists"),
            lora_policy_layout.get("params_manifest_exists"),
            lora_policy_layout.get("asset_norm_stats_exists"),
            lora_policy_load.get("passed"),
            lora_policy_load.get("policy_type") == "Policy",
            lora_policy_load.get("model_type") == "Pi0",
            lora_policy_load.get("is_pytorch_model") is False,
        ]
    ):
        print("openpi_rtc LoRA 完整物化 policy 加载 smoke 未通过")
        return 1
    lora_export = json.loads(
        (ROOT / "runs/lora_checkpoint_export_readiness.json").read_text(encoding="utf-8")
    )
    lora_export_inventory = lora_export.get("inventory", {})
    lora_export_required = {item.get("path"): item for item in lora_export.get("required_files", [])}
    lora_export_tar_smoke = lora_export.get("tar_stream_smoke", {})
    expected_export_files = [
        "runs/openpi_rtc_lora_materialized_policy_checkpoint/params/_METADATA",
        "runs/openpi_rtc_lora_materialized_policy_checkpoint/params/_CHECKPOINT_METADATA",
        "runs/openpi_rtc_lora_materialized_policy_checkpoint/params/manifest.ocdbt",
        "runs/openpi_rtc_lora_materialized_policy_checkpoint/params/ocdbt.process_0/manifest.ocdbt",
        "runs/openpi_rtc_lora_materialized_policy_checkpoint/assets/cvpr_multitask_aloha/norm_stats.json",
    ]
    if not all(
        [
            lora_export.get("passed"),
            lora_export.get("local_export_ready"),
            lora_export.get("web_submission_ready") is False,
            lora_export.get("checkpoint_dir") == "runs/openpi_rtc_lora_materialized_policy_checkpoint",
            lora_export.get("git_ignore", {}).get("ignored"),
            lora_export_inventory.get("total_size_bytes", 0) > 10 * 1024**3,
            lora_export_inventory.get("params_data_file_count", 0) > 0,
            all(lora_export_required.get(path, {}).get("exists") for path in expected_export_files),
            "tar -C runs -cf" in lora_export.get("recommended_local_archive", {}).get("create_command", ""),
            lora_export_tar_smoke.get("attempted"),
            lora_export_tar_smoke.get("passed"),
            lora_export_tar_smoke.get("returncode") == 0,
            "| wc -c" in lora_export_tar_smoke.get("command", ""),
            lora_export_tar_smoke.get("archive_stream_bytes", 0) > lora_export_inventory.get("total_size_bytes", 0),
        ]
    ):
        print("LoRA checkpoint 导出就绪审计未通过")
        return 1
    archive_plan = json.loads((ROOT / "runs/checkpoint_archive_plan.json").read_text(encoding="utf-8"))
    archive_inputs = archive_plan.get("required_inputs", {})
    archive_git = archive_plan.get("git_ignore", {})
    archive_disk = archive_plan.get("disk", {})
    archive_commands = archive_plan.get("commands", {})
    if not all(
        [
            archive_plan.get("passed"),
            archive_plan.get("archive_created") is False,
            archive_plan.get("upload_performed") is False,
            archive_plan.get("credentials_read") is False,
            archive_plan.get("checkpoint_dir") == "runs/openpi_rtc_lora_materialized_policy_checkpoint",
            archive_plan.get("archive_path") == "runs/openpi_rtc_lora_materialized_policy_checkpoint.tar",
            archive_plan.get("sha256_path") == "runs/openpi_rtc_lora_materialized_policy_checkpoint.tar.sha256",
            archive_plan.get("expected_archive_bytes", 0) > 10 * 1024**3,
            all(archive_inputs.values()),
            archive_git.get("archive_ignored"),
            archive_git.get("sha256_ignored"),
            archive_git.get("split_part_ignored"),
            archive_disk.get("free_space_margin_passed"),
            archive_commands.get("commands_safe"),
            "tar -C runs -cf" in archive_commands.get("create_archive", ""),
            "sha256sum runs/" in archive_commands.get("write_sha256", ""),
        ]
    ):
        print("Checkpoint 归档计划审计未通过")
        return 1
    upload_audit = json.loads((ROOT / "runs/checkpoint_upload_channels_audit.json").read_text(encoding="utf-8"))
    upload_channels = upload_audit.get("channels", {})
    if not all(
        [
            upload_audit.get("passed"),
            upload_audit.get("uploads_performed") is False,
            upload_audit.get("plaintext_credentials_read") is False,
            upload_audit.get("local_tar_ready"),
            upload_audit.get("archive_exists") is False,
            upload_audit.get("archive_git_ignored"),
            upload_audit.get("disk", {}).get("free_bytes", 0) > 0,
            upload_channels.get("huggingface_hub", {}).get("selected") is False,
            upload_channels.get("object_storage", {}).get("selected") is False,
            upload_channels.get("manual_download", {}).get("selected") is False,
        ]
    ):
        print("Checkpoint 上传通道审计未通过")
        return 1
    real_submission = json.loads((ROOT / "runs/real_submission_readiness.json").read_text(encoding="utf-8"))
    real_env = real_submission.get("env", {})
    real_inputs = real_submission.get("inputs", {})
    if not all(
        [
            real_submission.get("passed"),
            real_submission.get("ready_for_real_submission") is False,
            real_submission.get("web_form_ready") is False,
            real_submission.get("local_baseline_runner_ready") is False,
            real_submission.get("local_lora_runner_ready") is False,
            real_submission.get("platform_contacted") is False,
            real_submission.get("credentials_printed") is False,
            real_submission.get("runner_checks", {}).get("baseline", {}).get("passed"),
            real_submission.get("runner_checks", {}).get("lora", {}).get("passed"),
            real_inputs.get("submission_audit_passed"),
            real_inputs.get("export_audit_local_ready"),
            real_inputs.get("upload_audit_passed"),
            real_inputs.get("uploads_performed") is False,
            real_env.get("ROBOCHALLENGE_USER_TOKEN", {}).get("present") is False,
            real_env.get("ROBOCHALLENGE_SUBMISSION_ID", {}).get("present") is False,
        ]
    ):
        print("真实提交 readiness gate 未通过或当前阻塞状态未准确记录")
        return 1
    readiness_scenarios = json.loads(
        (ROOT / "runs/real_submission_readiness_scenarios.json").read_text(encoding="utf-8")
    )
    missing_scenario = readiness_scenarios.get("scenarios", {}).get("missing_env_expected_blocked", {})
    synthetic_scenario = readiness_scenarios.get("scenarios", {}).get("synthetic_env_expected_ready_shape", {})
    if not all(
        [
            readiness_scenarios.get("passed"),
            readiness_scenarios.get("platform_contacted") is False,
            readiness_scenarios.get("credentials_printed") is False,
            readiness_scenarios.get("synthetic_values_recorded") is False,
            readiness_scenarios.get("expectations", {}).get("missing_env_expected_blocked"),
            readiness_scenarios.get("expectations", {}).get("synthetic_env_expected_ready_shape"),
            missing_scenario.get("ready_for_real_submission") is False,
            missing_scenario.get("web_form_ready") is False,
            missing_scenario.get("value_leak_detected") is False,
            synthetic_scenario.get("ready_for_real_submission") is True,
            synthetic_scenario.get("web_form_ready") is True,
            synthetic_scenario.get("local_baseline_runner_ready") is True,
            synthetic_scenario.get("local_lora_runner_ready") is True,
            synthetic_scenario.get("platform_contacted") is False,
            synthetic_scenario.get("credentials_printed") is False,
            synthetic_scenario.get("value_leak_detected") is False,
        ]
    ):
        print("真实提交 readiness 场景 smoke 未通过")
        return 1
    handoff = json.loads((ROOT / "runs/submission_handoff_docs_audit.json").read_text(encoding="utf-8"))
    handoff_inputs = handoff.get("input_evidence", {})
    handoff_guardrails = handoff.get("guardrails", {})
    handoff_commands = handoff.get("command_mentions", {})
    handoff_paths = handoff.get("path_mentions", {})
    handoff_env = handoff.get("env_mentions", {})
    if not all(
        [
            handoff.get("passed"),
            handoff.get("doc_path") == "submission/REAL_SUBMISSION_HANDOFF.md",
            handoff.get("platform_contacted") is False,
            handoff.get("uploads_performed") is False,
            handoff.get("credentials_printed") is False,
            handoff.get("secret_patterns_found") == [],
            all(handoff_env.values()),
            all(handoff_paths.values()),
            all(handoff_commands.values()),
            all(handoff_guardrails.values()),
            handoff_inputs.get("real_submission_gate_passed"),
            handoff_inputs.get("real_submission_currently_blocked"),
            handoff_inputs.get("export_audit_local_ready"),
            handoff_inputs.get("upload_audit_passed"),
            handoff_inputs.get("upload_not_performed"),
        ]
    ):
        print("真实提交交接文档审计未通过")
        return 1
    secret_scan = json.loads((ROOT / "runs/plaintext_secret_scan.json").read_text(encoding="utf-8"))
    if not all(
        [
            secret_scan.get("passed"),
            secret_scan.get("platform_contacted") is False,
            secret_scan.get("uploads_performed") is False,
            secret_scan.get("secret_values_printed") is False,
            secret_scan.get("hit_count") == 0,
            secret_scan.get("scanned_files", 0) > 0,
            secret_scan.get("pattern_count", 0) >= 6,
            secret_scan.get("hits") == [],
        ]
    ):
        print("明文凭据扫描未通过")
        return 1
    if not all(
        [
            lora_grad.get("mode") == "lora_grad",
            lora_grad.get("passed"),
            lora_grad_model.get("paligemma_variant") == "gemma_2b_lora",
            lora_grad_model.get("action_expert_variant") == "gemma_300m_lora",
            lora_grad_model.get("pi05") is True,
            lora_grad_model.get("ema_decay") is None,
            lora_grad.get("compute_param_dtype") == "bfloat16",
            lora_grad.get("effective_random_action_offset_copies") == 1,
            lora_grad.get("effective_max_token_len") == 64,
            lora_grad.get("effective_action_horizon") == 10,
            lora_grad_data.get("state_shape") == [1, 32],
            lora_grad_data.get("actions_shape") == [1, 10, 32],
            lora_grad_data.get("tokenized_prompt_shape") == [1, 64],
            lora_grad.get("weight_preflight", {}).get("passed"),
            lora_grad.get("weight_preflight", {}).get("loaded", {}).get("leaf_count") == 73,
            lora_grad.get("weight_preflight", {}).get("removed_shape_dtype_struct_count") == 22,
            lora_grad_result.get("passed"),
            isinstance(lora_grad_result.get("loss"), (int, float)),
            isinstance(lora_grad_result.get("grad_norm"), (int, float)),
            lora_grad_summary.get("leaf_count") == 53,
            lora_grad_summary.get("total_elements") == 466958097,
            lora_grad_result.get("checkpoint_npz") == "runs/openpi_rtc_lora_grad_checkpoint/trainable_params_step1.npz",
            lora_grad_result.get("checkpoint_metadata") == "runs/openpi_rtc_lora_grad_checkpoint/metadata.json",
        ]
    ):
        print("openpi_rtc LoRA reduced trainable-filter grad/checkpoint smoke 未通过")
        return 1
    submission_audit = json.loads(
        (ROOT / "runs/robochallenge_submission_package_audit.json").read_text(encoding="utf-8")
    )
    submission_target = submission_audit.get("selected_target", {})
    submission_entry = submission_audit.get("entrypoint_audit", {})
    submission_evidence = submission_audit.get("evidence", {})
    submission_restore = submission_audit.get("model_restore_materials", {})
    submission_outputs = submission_audit.get("outputs", {})
    submission_runner_audit = submission_audit.get("runner_audit", {})
    baseline_runner_audit = submission_runner_audit.get("baseline", {})
    lora_runner_audit = submission_runner_audit.get("lora", {})
    submission_manifest = json.loads(
        (ROOT / "submission/submission_manifest_template.json").read_text(encoding="utf-8")
    )
    runner_text = (ROOT / "submission/run_table30v2_aloha_demo_template.sh").read_text(encoding="utf-8")
    lora_runner_text = (ROOT / "submission/run_table30v2_aloha_lora_demo_template.sh").read_text(encoding="utf-8")
    if not all(
        [
            submission_audit.get("passed"),
            submission_target.get("benchmark") == "Table30v2",
            submission_target.get("robot_type") == "aloha",
            submission_target.get("task_name") == "pack_the_toothbrush_holder",
            submission_target.get("checkpoint_exists"),
            all(submission_entry.get("required_args_present", {}).values()),
            submission_entry.get("api_base_url_present"),
            submission_entry.get("job_loop_uses_submission_id"),
            submission_evidence.get("mock_smoke_passed"),
            submission_evidence.get("table30v2_mapping_ready"),
            submission_restore.get("official_aloha_checkpoint_exists"),
            submission_restore.get("scoped_checkpoint_exists"),
            submission_restore.get("scoped_checkpoint_git_ignored"),
            submission_restore.get("restore_audit_passed"),
            submission_restore.get("placeholder_after_count") == 0,
            submission_restore.get("materialized_checkpoint_exists"),
            submission_restore.get("materialized_checkpoint_git_ignored"),
            submission_restore.get("materialize_passed"),
            submission_restore.get("materialized_restored_leaf_count") == 73,
            submission_restore.get("policy_smoke_passed"),
            submission_restore.get("policy_smoke_model_type") == "Pi0",
            submission_restore.get("direct_demo_checkpoint_ready") is True,
            submission_outputs.get("manifest") == "submission/submission_manifest_template.json",
            submission_outputs.get("runner") == "submission/run_table30v2_aloha_demo_template.sh",
            submission_outputs.get("lora_runner") == "submission/run_table30v2_aloha_lora_demo_template.sh",
            baseline_runner_audit.get("exists"),
            baseline_runner_audit.get("mentions_user_token"),
            baseline_runner_audit.get("mentions_submission_id"),
            baseline_runner_audit.get("mentions_expected_checkpoint"),
            baseline_runner_audit.get("mentions_placeholder_guard"),
            baseline_runner_audit.get("mentions_dry_run_guard"),
            baseline_runner_audit.get("contains_plaintext_secret_pattern") is False,
            baseline_runner_audit.get("bash_n", {}).get("passed"),
            baseline_runner_audit.get("no_credentials_failfast", {}).get("passed"),
            baseline_runner_audit.get("placeholder_credentials_failfast", {}).get("passed"),
            baseline_runner_audit.get("dry_run_no_contact", {}).get("passed"),
            baseline_runner_audit.get("dry_run_no_contact", {}).get("printed_secret") is False,
            lora_runner_audit.get("exists"),
            lora_runner_audit.get("mentions_user_token"),
            lora_runner_audit.get("mentions_submission_id"),
            lora_runner_audit.get("mentions_expected_checkpoint"),
            lora_runner_audit.get("mentions_placeholder_guard"),
            lora_runner_audit.get("mentions_dry_run_guard"),
            lora_runner_audit.get("contains_plaintext_secret_pattern") is False,
            lora_runner_audit.get("bash_n", {}).get("passed"),
            lora_runner_audit.get("no_credentials_failfast", {}).get("passed"),
            lora_runner_audit.get("placeholder_credentials_failfast", {}).get("passed"),
            lora_runner_audit.get("dry_run_no_contact", {}).get("passed"),
            lora_runner_audit.get("dry_run_no_contact", {}).get("printed_secret") is False,
            submission_manifest.get("status") == "template_pending_credentials",
            submission_manifest.get("runner_templates", {}).get("baseline")
            == "submission/run_table30v2_aloha_demo_template.sh",
            submission_manifest.get("runner_templates", {}).get("lora_materialized")
            == "submission/run_table30v2_aloha_lora_demo_template.sh",
            "ROBOCHALLENGE_USER_TOKEN" in runner_text,
            "ROBOCHALLENGE_SUBMISSION_ID" in runner_text,
            "ROBOCHALLENGE_USER_TOKEN" in lora_runner_text,
            "ROBOCHALLENGE_SUBMISSION_ID" in lora_runner_text,
            "runs/openpi_rtc_lora_materialized_policy_checkpoint" in lora_runner_text,
            "reject_placeholder" in runner_text,
            "reject_placeholder" in lora_runner_text,
            "ROBOCHALLENGE_DRY_RUN" in runner_text,
            "ROBOCHALLENGE_DRY_RUN" in lora_runner_text,
            "sk-" not in runner_text,
            "hf_" not in runner_text,
            "sk-" not in lora_runner_text,
            "hf_" not in lora_runner_text,
        ]
    ):
        print("RoboChallenge submission package checklist/template audit 未通过")
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
    print("openpi_rtc LoRA 低显存路线权重合并预检已通过")
    print("openpi_rtc LoRA reduced 数值 forward smoke 已通过")
    print("openpi_rtc LoRA reduced trainable-filter grad/checkpoint smoke 已通过")
    print("openpi_rtc LoRA scoped checkpoint restore/merge audit 已通过")
    print("RoboChallenge submission package checklist/template audit 已通过")
    print("openpi_rtc LoRA 推理 checkpoint 物化布局审计已通过")
    print("openpi_rtc LoRA 完整推理 checkpoint 物化已通过")
    print("openpi_rtc LoRA 完整物化 policy 加载 smoke 已通过")
    print("LoRA checkpoint 导出就绪审计已通过")
    print("Checkpoint 归档计划审计已通过")
    print("Checkpoint 上传通道审计已通过")
    print("真实提交 readiness gate 已通过")
    print("真实提交 readiness 场景 smoke 已通过")
    print("真实提交交接文档审计已通过")
    print("明文凭据扫描已通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
