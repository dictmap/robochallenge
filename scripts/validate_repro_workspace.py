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
    "runs/robochallenge_submission_package_audit.json",
    "submission/README.md",
    "submission/submission_manifest_template.json",
    "submission/run_table30v2_aloha_demo_template.sh",
    "scripts/probe_pi05_base_model.sh",
    "scripts/audit_pi06_pi07_public_release.py",
    "scripts/audit_table30v2_aloha_mapping.py",
    "scripts/dry_run_table30v2_aloha_converter.py",
    "scripts/write_table30v2_aloha_short_lerobot.py",
    "scripts/audit_openpi_rtc_train_entry.py",
    "scripts/run_openpi_rtc_numeric_dry_run.py",
    "scripts/audit_openpi_rtc_lora_path.py",
    "scripts/audit_openpi_rtc_lora_checkpoint_restore.py",
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
        print("openpi_rtc LoRA scoped checkpoint restore/merge audit 鏈€氳繃")
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
    submission_manifest = json.loads(
        (ROOT / "submission/submission_manifest_template.json").read_text(encoding="utf-8")
    )
    runner_text = (ROOT / "submission/run_table30v2_aloha_demo_template.sh").read_text(encoding="utf-8")
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
            submission_restore.get("direct_demo_checkpoint_ready") is False,
            submission_outputs.get("manifest") == "submission/submission_manifest_template.json",
            submission_outputs.get("runner") == "submission/run_table30v2_aloha_demo_template.sh",
            submission_manifest.get("status") == "template_pending_credentials",
            "ROBOCHALLENGE_USER_TOKEN" in runner_text,
            "ROBOCHALLENGE_SUBMISSION_ID" in runner_text,
            "4f0c447" not in runner_text,
            "sk-" not in runner_text,
            "hf_" not in runner_text,
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
