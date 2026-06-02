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
    "reports/checkpoint_split_plan.md",
    "reports/checkpoint_archive_dry_run.md",
    "reports/checkpoint_link_intake.md",
    "reports/checkpoint_link_download_verification.md",
    "reports/authorized_submission_sequence_audit.md",
    "reports/submission_status_dashboard.html",
    "reports/checkpoint_upload_channels_audit.md",
    "reports/real_submission_readiness.md",
    "reports/real_submission_readiness_scenarios.md",
    "reports/submission_handoff_docs_audit.md",
    "reports/submission_preflight_bundle.md",
    "reports/submission_env_template_audit.md",
    "reports/notebook_structure_audit.md",
    "reports/jupyter_input_template_audit.md",
    "reports/jupyter_authorized_preflight_template_audit.md",
    "reports/jupyter_final_handoff_template_audit.md",
    "reports/authorized_preflight_template_audit.md",
    "reports/ready_real_runner_template_audit.md",
    "reports/authorized_checkpoint_archive_template_audit.md",
    "reports/authorized_execution_checklist.md",
    "reports/next_user_action_packet.md",
    "reports/web_form_field_packet.md",
    "reports/submission_variant_route_packet.md",
    "reports/baseline_submission_quickstart.md",
    "reports/baseline_dry_run_gate.md",
    "reports/baseline_credential_hygiene.md",
    "reports/baseline_local_env_smoke.md",
    "reports/baseline_final_handoff_packet.md",
    "reports/baseline_final_handoff_rehearsal.md",
    "reports/route_aware_submission_blockers.md",
    "reports/submission_artifact_manifest.md",
    "reports/submission_blockers_summary.md",
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
    "runs/checkpoint_split_plan.json",
    "runs/checkpoint_archive_dry_run.json",
    "runs/checkpoint_link_intake.json",
    "runs/checkpoint_link_download_verification.json",
    "runs/authorized_submission_sequence_audit.json",
    "runs/submission_status_dashboard.json",
    "runs/checkpoint_upload_channels_audit.json",
    "runs/real_submission_readiness.json",
    "runs/real_submission_readiness_scenarios.json",
    "runs/submission_handoff_docs_audit.json",
    "runs/submission_preflight_bundle.json",
    "runs/submission_env_template_audit.json",
    "runs/notebook_structure_audit.json",
    "runs/jupyter_input_template_audit.json",
    "runs/jupyter_authorized_preflight_template_audit.json",
    "runs/jupyter_final_handoff_template_audit.json",
    "runs/authorized_preflight_template_audit.json",
    "runs/ready_real_runner_template_audit.json",
    "runs/authorized_checkpoint_archive_template_audit.json",
    "runs/authorized_execution_checklist.json",
    "runs/next_user_action_packet.json",
    "runs/web_form_field_packet.json",
    "runs/submission_variant_route_packet.json",
    "runs/baseline_submission_quickstart.json",
    "runs/baseline_dry_run_gate.json",
    "runs/baseline_credential_hygiene.json",
    "runs/baseline_local_env_smoke.json",
    "runs/baseline_final_handoff_packet.json",
    "runs/baseline_final_handoff_rehearsal.json",
    "runs/route_aware_submission_blockers.json",
    "runs/submission_artifact_manifest.json",
    "runs/submission_blockers_summary.json",
    "runs/plaintext_secret_scan.json",
    "runs/robochallenge_submission_package_audit.json",
    "submission/README.md",
    "submission/REAL_SUBMISSION_HANDOFF.md",
    "submission/AUTHORIZED_SUBMISSION_SEQUENCE.md",
    "submission/robochallenge_env_template.sh",
    "submission/submission_manifest_template.json",
    "submission/run_table30v2_aloha_demo_template.sh",
    "submission/run_table30v2_aloha_lora_demo_template.sh",
    "submission/run_authorized_preflight_template.sh",
    "submission/run_ready_real_submission_template.sh",
    "submission/run_authorized_checkpoint_archive_template.sh",
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
    "scripts/audit_checkpoint_split_plan.py",
    "scripts/create_checkpoint_archive.py",
    "scripts/audit_checkpoint_link_intake.py",
    "scripts/audit_checkpoint_link_download_verification.py",
    "scripts/audit_authorized_submission_sequence.py",
    "scripts/render_submission_status_dashboard.py",
    "scripts/audit_checkpoint_upload_channels.py",
    "scripts/audit_real_submission_readiness.py",
    "scripts/audit_real_submission_readiness_scenarios.py",
    "scripts/audit_submission_handoff_docs.py",
    "scripts/audit_submission_preflight_bundle.py",
    "scripts/audit_submission_env_template.py",
    "scripts/audit_notebook_structure.py",
    "scripts/audit_jupyter_input_template.py",
    "scripts/audit_jupyter_authorized_preflight_template.py",
    "scripts/audit_jupyter_final_handoff_template.py",
    "scripts/audit_authorized_preflight_template.py",
    "scripts/audit_ready_real_runner_template.py",
    "scripts/audit_authorized_checkpoint_archive_template.py",
    "scripts/audit_authorized_execution_checklist.py",
    "scripts/render_next_user_action_packet.py",
    "scripts/render_web_form_field_packet.py",
    "scripts/render_submission_variant_route_packet.py",
    "scripts/render_baseline_submission_quickstart.py",
    "scripts/render_baseline_dry_run_gate.py",
    "scripts/render_baseline_credential_hygiene.py",
    "scripts/render_baseline_local_env_smoke.py",
    "scripts/render_baseline_final_handoff_packet.py",
    "scripts/render_baseline_final_handoff_rehearsal.py",
    "scripts/render_route_aware_submission_blockers.py",
    "scripts/audit_submission_artifact_manifest.py",
    "scripts/audit_submission_blockers_summary.py",
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
    split_plan = json.loads((ROOT / "runs/checkpoint_split_plan.json").read_text(encoding="utf-8"))
    split_commands = split_plan.get("commands", {})
    split_parts = split_plan.get("parts", [])
    if not all(
        [
            split_plan.get("kind") == "checkpoint_split_plan",
            split_plan.get("passed"),
            split_plan.get("archive_created") is False,
            split_plan.get("parts_created") is False,
            split_plan.get("upload_performed") is False,
            split_plan.get("credentials_read") is False,
            split_plan.get("platform_contacted") is False,
            split_plan.get("archive_path") == "runs/openpi_rtc_lora_materialized_policy_checkpoint.tar",
            split_plan.get("sha256_path") == "runs/openpi_rtc_lora_materialized_policy_checkpoint.tar.sha256",
            split_plan.get("part_prefix") == "runs/openpi_rtc_lora_materialized_policy_checkpoint.tar.part-",
            split_plan.get("expected_archive_bytes", 0) > 10 * 1024**3,
            split_plan.get("part_size_gib") == 4,
            split_plan.get("expected_part_count") == 3,
            split_plan.get("archive_absent"),
            split_plan.get("sha256_absent"),
            split_plan.get("existing_part_count") == 0,
            split_plan.get("all_parts_git_ignored"),
            len(split_parts) == 3,
            all(part.get("git_ignored") for part in split_parts),
            all(part.get("exists") is False for part in split_parts),
            split_commands.get("commands_safe"),
            "split -b 4G" in split_commands.get("split_archive", ""),
            split_commands.get("reassemble_archive", "").startswith("cat runs/"),
            split_commands.get("verify_reassembled_archive", "").startswith("sha256sum -c runs/"),
        ]
    ):
        print("Checkpoint 分片上传计划审计未通过")
        return 1
    archive_dry_run = json.loads((ROOT / "runs/checkpoint_archive_dry_run.json").read_text(encoding="utf-8"))
    archive_dry_run_disk = archive_dry_run.get("disk", {})
    archive_dry_run_commands = archive_dry_run.get("commands", {})
    if not all(
        [
            archive_dry_run.get("kind") == "checkpoint_archive_dry_run",
            archive_dry_run.get("passed"),
            archive_dry_run.get("dry_run") is True,
            archive_dry_run.get("execute_requested") is False,
            archive_dry_run.get("explicit_execute_gate") is False,
            archive_dry_run.get("missing_execute_confirmation") is False,
            archive_dry_run.get("archive_created") is False,
            archive_dry_run.get("sha256_created") is False,
            archive_dry_run.get("upload_performed") is False,
            archive_dry_run.get("credentials_read") is False,
            archive_dry_run.get("platform_contacted") is False,
            archive_dry_run.get("checkpoint_dir") == "runs/openpi_rtc_lora_materialized_policy_checkpoint",
            archive_dry_run.get("archive_path") == "runs/openpi_rtc_lora_materialized_policy_checkpoint.tar",
            archive_dry_run.get("sha256_path") == "runs/openpi_rtc_lora_materialized_policy_checkpoint.tar.sha256",
            archive_dry_run.get("checkpoint_dir_exists"),
            archive_dry_run.get("archive_absent_before"),
            archive_dry_run.get("sha256_absent_before"),
            archive_dry_run.get("archive_absent_after"),
            archive_dry_run.get("sha256_absent_after"),
            archive_dry_run.get("archive_git_ignored"),
            archive_dry_run.get("sha256_git_ignored"),
            archive_dry_run.get("tar_available"),
            archive_dry_run_disk.get("expected_archive_bytes", 0) > 10 * 1024**3,
            archive_dry_run_disk.get("free_space_margin_passed"),
            archive_dry_run_commands.get("uses_shell") is False,
            archive_dry_run_commands.get("destructive_commands") is False,
            "python3 scripts/create_checkpoint_archive.py" in archive_dry_run_commands.get("dry_run", ""),
            "--execute --confirm-create-large-archive" in archive_dry_run_commands.get("execute", ""),
        ]
    ):
        print("Checkpoint 归档生成 dry-run 未通过")
        return 1
    link_intake = json.loads((ROOT / "runs/checkpoint_link_intake.json").read_text(encoding="utf-8"))
    link_current = link_intake.get("current_env", {})
    link_current_links = link_current.get("links", {})
    link_scenarios = link_intake.get("scenarios", {})
    link_expectations = link_intake.get("expectations", {})
    link_missing = link_scenarios.get("missing_link_expected_blocked", {})
    link_placeholder = link_scenarios.get("placeholder_link_expected_rejected", {})
    link_synthetic = link_scenarios.get("synthetic_https_shape_expected_accepted", {})
    if not all(
        [
            link_intake.get("kind") == "checkpoint_link_intake",
            link_intake.get("passed"),
            link_intake.get("platform_contacted") is False,
            link_intake.get("uploads_performed") is False,
            link_intake.get("archive_created") is False,
            link_intake.get("credentials_printed") is False,
            link_intake.get("link_values_printed") is False,
            link_intake.get("synthetic_values_recorded") is False,
            link_current.get("link_shape_ready") is False,
            link_current.get("download_verified") is False,
            link_current_links.get("ROBOCHALLENGE_CHECKPOINT_LINK", {}).get("present") is False,
            link_current_links.get("ROBOCHALLENGE_LORA_CHECKPOINT_LINK", {}).get("present") is False,
            all(link_expectations.values()),
            link_missing.get("link_shape_ready") is False,
            link_placeholder.get("link_shape_ready") is False,
            link_synthetic.get("link_shape_ready") is True,
            link_synthetic.get("download_verified") is False,
            link_synthetic.get("platform_contacted") is False,
            link_synthetic.get("link_values_printed") is False,
        ]
    ):
        print("Checkpoint link 回填审计未通过")
        return 1
    link_download = json.loads((ROOT / "runs/checkpoint_link_download_verification.json").read_text(encoding="utf-8"))
    link_download_current = link_download.get("current_env", {})
    link_download_links = link_download_current.get("links", {})
    link_download_tooling = link_download.get("tooling", {})
    link_download_checks = link_download.get("checks", {})
    link_download_commands = link_download.get("planned_commands", {})
    link_download_verification = link_download.get("verification", {})
    if not all(
        [
            link_download.get("kind") == "checkpoint_link_download_verification",
            link_download.get("passed"),
            link_download.get("verify_download_requested") is False,
            link_download.get("platform_contacted") is False,
            link_download.get("upload_performed") is False,
            link_download.get("credentials_read") is False,
            link_download.get("credentials_printed") is False,
            link_download.get("link_value_printed") is False,
            link_download_current.get("link_shape_ready") is False,
            link_download_links.get("ROBOCHALLENGE_CHECKPOINT_LINK", {}).get("present") is False,
            link_download_links.get("ROBOCHALLENGE_LORA_CHECKPOINT_LINK", {}).get("present") is False,
            link_download_tooling.get("curl", {}).get("available"),
            link_download_checks.get("link_intake_passed"),
            link_download_checks.get("split_plan_passed"),
            link_download_checks.get("curl_available"),
            link_download_checks.get("commands_redacted"),
            link_download_checks.get("commands_no_shell_redirection"),
            "[REDACTED_CHECKPOINT_LINK]" in link_download_commands.get("head", ""),
            "[REDACTED_CHECKPOINT_LINK]" in link_download_commands.get("range_smoke", ""),
            link_download_verification.get("attempted") is False,
            link_download_verification.get("download_verified") is False,
            link_download_verification.get("download_host_contacted") is False,
            link_download_verification.get("link_value_printed") is False,
            link_download.get("expected_archive_gib", 0) > 10,
            link_download.get("expected_part_count") == 3,
            len(link_download.get("blocking", [])) >= 2,
        ]
    ):
        print("Checkpoint link 下载校验审计未通过")
        return 1
    authorized_sequence = json.loads((ROOT / "runs/authorized_submission_sequence_audit.json").read_text(encoding="utf-8"))
    sequence_commands = authorized_sequence.get("commands", {})
    sequence_command_present = sequence_commands.get("present", {})
    sequence_inputs = authorized_sequence.get("input_evidence", {})
    sequence_paths = authorized_sequence.get("path_mentions", {})
    if not all(
        [
            authorized_sequence.get("kind") == "authorized_submission_sequence_audit",
            authorized_sequence.get("passed"),
            authorized_sequence.get("doc_path") == "submission/AUTHORIZED_SUBMISSION_SEQUENCE.md",
            authorized_sequence.get("platform_contacted") is False,
            authorized_sequence.get("uploads_performed") is False,
            authorized_sequence.get("archive_created") is False,
            authorized_sequence.get("credentials_printed") is False,
            authorized_sequence.get("link_values_printed") is False,
            sequence_commands.get("critical_order_passed"),
            all(sequence_command_present.values()),
            all(authorized_sequence.get("env_mentions", {}).values()),
            all(sequence_paths.values()),
            all(authorized_sequence.get("guardrails", {}).values()),
            all(sequence_inputs.values()),
            authorized_sequence.get("secret_patterns_found") == [],
            authorized_sequence.get("no_contact_evidence"),
            sequence_inputs.get("readiness_currently_blocked"),
            sequence_inputs.get("current_link_missing_as_expected"),
            sequence_inputs.get("jupyter_input_template_passed"),
            sequence_inputs.get("jupyter_input_default_false"),
            sequence_inputs.get("jupyter_input_local_env_ignored"),
            sequence_inputs.get("jupyter_authorized_preflight_template_passed"),
            sequence_inputs.get("jupyter_authorized_preflight_audit_default_true"),
            sequence_inputs.get("jupyter_authorized_preflight_execution_default_false"),
            sequence_inputs.get("jupyter_authorized_preflight_runner_not_started"),
        ]
    ):
        print("用户授权后提交顺序审计未通过")
        return 1
    dashboard = json.loads((ROOT / "runs/submission_status_dashboard.json").read_text(encoding="utf-8"))
    dashboard_cards = dashboard.get("cards", [])
    dashboard_titles = {item.get("title") for item in dashboard_cards}
    dashboard_html = ROOT / "reports/submission_status_dashboard.html"
    dashboard_html_text = dashboard_html.read_text(encoding="utf-8")
    if not all(
        [
            dashboard.get("kind") == "submission_status_dashboard",
            dashboard.get("passed"),
            dashboard.get("html_path") == "reports/submission_status_dashboard.html",
            dashboard_html.exists(),
            "<html lang=\"zh-CN\">" in dashboard_html_text,
            "RoboChallenge pi0.5 提交状态面板" in dashboard_html_text,
            "当前阻塞" in dashboard_html_text,
            dashboard.get("source_count") >= 20,
            dashboard.get("card_count") >= 20,
            dashboard.get("done_count", 0) >= 15,
            dashboard.get("blocked_count", 0) >= 4,
            dashboard.get("ready_for_real_submission") is False,
            dashboard.get("web_form_ready") is False,
            dashboard.get("preflight_passed") is True,
            dashboard.get("preflight_go_no_go") == "blocked",
            dashboard.get("preflight_no_contact") is True,
            dashboard.get("preflight_no_secret_leak") is True,
            dashboard.get("link_shape_ready") is False,
            dashboard.get("archive_created") is False,
            dashboard.get("archive_confirm_gate_passed") is True,
            dashboard.get("archive_confirm_phrase") == "CREATE_ROBOCHALLENGE_CHECKPOINT_ARCHIVE",
            dashboard.get("archive_no_confirm_blocks") is True,
            dashboard.get("authorized_execution_checklist_passed") is True,
            dashboard.get("authorized_execution_go_no_go") == "blocked_by_user_inputs",
            dashboard.get("next_user_action_packet_passed") is True,
            dashboard.get("next_user_action_packet_decision_count", 0) >= 5,
            dashboard.get("next_user_action_packet_local_env_ignored") is True,
            dashboard.get("next_user_action_packet_recommended_route") == "baseline_official_aloha",
            dashboard.get("next_user_action_packet_baseline_no_upload") is True,
            dashboard.get("next_user_action_packet_baseline_no_link") is True,
            dashboard.get("next_user_action_packet_lora_web_needs_upload") is True,
            dashboard.get("next_user_action_packet_lora_web_needs_link") is True,
            dashboard.get("web_form_field_packet_passed") is True,
            dashboard.get("web_form_field_count", 0) >= 10,
            dashboard.get("web_form_ready_field_count", 0) >= 6,
            dashboard.get("web_form_packet_currently_not_ready") is True,
            dashboard.get("submission_variant_route_packet_passed") is True,
            dashboard.get("submission_variant_recommended_default") == "baseline_official_aloha",
            dashboard.get("submission_variant_route_count") == 2,
            dashboard.get("baseline_submission_quickstart_passed") is True,
            dashboard.get("baseline_submission_quickstart_no_upload") is True,
            dashboard.get("baseline_submission_quickstart_no_link") is True,
            dashboard.get("baseline_dry_run_gate_passed") is True,
            dashboard.get("baseline_dry_run_gate_no_upload") is True,
            dashboard.get("baseline_dry_run_gate_no_link") is True,
            dashboard.get("baseline_dry_run_gate_stops_before_real_runner") is True,
            dashboard.get("baseline_dry_run_gate_command")
            == "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_ready_real_submission_template.sh",
            dashboard.get("baseline_credential_hygiene_passed") is True,
            dashboard.get("baseline_credential_hygiene_local_env_gitignored") is True,
            dashboard.get("baseline_credential_hygiene_local_env_not_tracked") is True,
            dashboard.get("baseline_credential_hygiene_does_not_read_local_env") is True,
            dashboard.get("baseline_local_env_smoke_passed") is True,
            dashboard.get("baseline_local_env_smoke_synthetic_values_not_recorded") is True,
            dashboard.get("baseline_local_env_smoke_temp_env_removed") is True,
            dashboard.get("baseline_local_env_smoke_authorized_preflight_baseline") is True,
            dashboard.get("baseline_local_env_smoke_ready_runner_stops") is True,
            dashboard.get("baseline_final_handoff_passed") is True,
            dashboard.get("baseline_final_handoff_no_upload") is True,
            dashboard.get("baseline_final_handoff_no_link") is True,
            dashboard.get("baseline_final_handoff_no_archive_authorization") is True,
            dashboard.get("baseline_final_handoff_command_count") == 4,
            dashboard.get("baseline_final_handoff_no_contact_command_count") == 3,
            dashboard.get("baseline_final_handoff_real_runner_requires_confirmation") is True,
            dashboard.get("baseline_final_handoff_does_not_read_local_env") is True,
            dashboard.get("baseline_final_handoff_rehearsal_passed") is True,
            dashboard.get("baseline_final_handoff_rehearsal_command_count") == 3,
            dashboard.get("baseline_final_handoff_rehearsal_synthetic_values_not_recorded") is True,
            dashboard.get("baseline_final_handoff_rehearsal_temp_env_removed") is True,
            dashboard.get("baseline_final_handoff_rehearsal_workspace_restored") is True,
            dashboard.get("baseline_final_handoff_rehearsal_no_contact") is True,
            dashboard.get("baseline_final_handoff_rehearsal_no_leak") is True,
            dashboard.get("route_aware_submission_blockers_passed") is True,
            dashboard.get("route_aware_recommended_route") == "baseline_official_aloha",
            dashboard.get("route_aware_baseline_no_upload") is True,
            dashboard.get("route_aware_baseline_no_link") is True,
            dashboard.get("route_aware_lora_web_needs_upload") is True,
            dashboard.get("route_aware_lora_web_needs_link") is True,
            dashboard.get("route_aware_baseline_blocking_count", 0) >= 5,
            dashboard.get("jupyter_input_template_passed") is True,
            dashboard.get("jupyter_input_default_off") is True,
            dashboard.get("jupyter_local_env_ignored") is True,
            dashboard.get("jupyter_input_recommended_route") == "baseline_official_aloha",
            dashboard.get("jupyter_input_baseline_no_upload") is True,
            dashboard.get("jupyter_input_baseline_no_link") is True,
            dashboard.get("jupyter_input_lora_web_needs_upload") is True,
            dashboard.get("jupyter_input_lora_web_needs_link") is True,
            dashboard.get("jupyter_authorized_preflight_template_passed") is True,
            dashboard.get("jupyter_authorized_preflight_default_off") is True,
            dashboard.get("jupyter_authorized_preflight_audit_on") is True,
            dashboard.get("jupyter_authorized_recommended_route") == "baseline_official_aloha",
            dashboard.get("jupyter_authorized_baseline_no_upload") is True,
            dashboard.get("jupyter_authorized_baseline_no_link") is True,
            dashboard.get("jupyter_authorized_lora_web_needs_upload") is True,
            dashboard.get("jupyter_authorized_lora_web_needs_link") is True,
            dashboard.get("jupyter_final_handoff_template_passed") is True,
            dashboard.get("jupyter_final_handoff_audit_on") is True,
            dashboard.get("jupyter_final_handoff_packet_default_on") is True,
            dashboard.get("jupyter_final_handoff_real_runner_default_off") is True,
            dashboard.get("jupyter_final_handoff_command_count") == 4,
            dashboard.get("jupyter_final_handoff_no_contact_command_count") == 3,
            dashboard.get("jupyter_final_handoff_real_runner_requires_confirmation") is True,
            dashboard.get("authorized_execution_recommended_route") == "baseline_official_aloha",
            dashboard.get("authorized_execution_baseline_no_upload") is True,
            dashboard.get("authorized_execution_baseline_no_link") is True,
            dashboard.get("authorized_execution_lora_web_needs_upload") is True,
            dashboard.get("authorized_execution_lora_web_needs_link") is True,
            dashboard.get("uploads_performed") is False,
            dashboard.get("platform_contacted") is False,
            dashboard.get("credentials_printed") is False,
            dashboard.get("link_values_printed") is False,
            dashboard.get("secret_values_printed") is False,
            dashboard.get("critical_order_passed"),
            len(dashboard.get("blocking", [])) >= 3,
            "ROBOCHALLENGE_CHECKPOINT_LINK" not in set(dashboard.get("blocking", [])),
            "pi0.5 基模" in dashboard_titles,
            "Table30v2 ALOHA" in dashboard_titles,
            "归档强确认入口" in dashboard_titles,
            "授权执行清单" in dashboard_titles,
            "下一步动作包" in dashboard_titles,
            "网页表单字段" in dashboard_titles,
            "提交路线拆分" in dashboard_titles,
            "Baseline 最短路径" in dashboard_titles,
            "Baseline dry-run gate" in dashboard_titles,
            "Baseline 凭据卫生" in dashboard_titles,
            "Baseline local env smoke" in dashboard_titles,
            "Baseline final handoff" in dashboard_titles,
            "Baseline handoff rehearsal" in dashboard_titles,
            "路线感知阻塞" in dashboard_titles,
            "Jupyter 安全填空" in dashboard_titles,
            "Jupyter 授权预检" in dashboard_titles,
            "真实提交 gate" in dashboard_titles,
            "提交前预检汇总" in dashboard_titles,
            "CREATE_ROBOCHALLENGE_CHECKPOINT_ARCHIVE" in dashboard_html_text,
        ]
    ):
        print("提交状态 GUI 面板未通过")
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
            handoff_inputs.get("link_download_audit_passed"),
            handoff_inputs.get("link_download_not_requested"),
            handoff_inputs.get("link_download_host_not_contacted"),
            handoff_inputs.get("link_download_no_plaintext"),
            handoff_inputs.get("jupyter_input_template_passed"),
            handoff_inputs.get("jupyter_input_default_false"),
            handoff_inputs.get("jupyter_input_local_env_ignored"),
            handoff_inputs.get("jupyter_authorized_preflight_template_passed"),
            handoff_inputs.get("jupyter_authorized_preflight_audit_default_true"),
            handoff_inputs.get("jupyter_authorized_preflight_execution_default_false"),
            handoff_inputs.get("jupyter_authorized_preflight_runner_not_started"),
        ]
    ):
        print("真实提交交接文档审计未通过")
        return 1
    env_template = json.loads((ROOT / "runs/submission_env_template_audit.json").read_text(encoding="utf-8"))
    env_template_paths = env_template.get("local_secret_paths", {})
    if not all(
        [
            env_template.get("kind") == "submission_env_template_audit",
            env_template.get("passed"),
            env_template.get("template_path") == "submission/robochallenge_env_template.sh",
            env_template.get("platform_contacted") is False,
            env_template.get("uploads_performed") is False,
            env_template.get("credentials_read") is False,
            env_template.get("credentials_printed") is False,
            env_template.get("secret_values_printed") is False,
            all(env_template.get("required_present", {}).values()),
            all(env_template.get("placeholder_values", {}).values()),
            all(item.get("ignored") for item in env_template_paths.values()),
            env_template.get("secret_pattern_hits") == [],
            env_template.get("recommended_local_copy") == "submission/robochallenge_env.local.sh",
        ]
    ):
        print("真实提交环境变量模板审计未通过")
        return 1
    notebook_structure = json.loads((ROOT / "runs/notebook_structure_audit.json").read_text(encoding="utf-8"))
    if not all(
        [
            notebook_structure.get("kind") == "notebook_structure_audit",
            notebook_structure.get("passed"),
            notebook_structure.get("platform_contacted") is False,
            notebook_structure.get("uploads_performed") is False,
            notebook_structure.get("credentials_read") is False,
            notebook_structure.get("credentials_printed") is False,
            notebook_structure.get("link_values_printed") is False,
            notebook_structure.get("secret_values_printed") is False,
            notebook_structure.get("notebook_path") == "notebooks/robochallenge_pi05_submit_cn.ipynb",
            notebook_structure.get("nbformat") == 4,
            notebook_structure.get("cell_count", 0) >= 40,
            notebook_structure.get("missing_id_indexes") == [],
            notebook_structure.get("duplicate_ids") == [],
            notebook_structure.get("code_cells_with_outputs") == [],
            notebook_structure.get("code_cells_with_execution_count") == [],
            notebook_structure.get("crlf_count") == 0,
            notebook_structure.get("bad_marker_hits") == [],
            all(notebook_structure.get("required_markers", {}).values()),
        ]
    ):
        print("Notebook 结构与编码审计未通过")
        return 1
    jupyter_input = json.loads((ROOT / "runs/jupyter_input_template_audit.json").read_text(encoding="utf-8"))
    jupyter_required = jupyter_input.get("required_fragments", {})
    jupyter_forbidden = jupyter_input.get("forbidden_fragments", {})
    jupyter_keys = jupyter_input.get("required_keys", {})
    jupyter_variant_logic = jupyter_input.get("variant_logic", {})
    jupyter_route_guidance = jupyter_input.get("route_guidance", {})
    if not all(
        [
            jupyter_input.get("kind") == "jupyter_input_template_audit",
            jupyter_input.get("passed"),
            jupyter_input.get("platform_contacted") is False,
            jupyter_input.get("uploads_performed") is False,
            jupyter_input.get("credentials_read") is False,
            jupyter_input.get("credentials_printed") is False,
            jupyter_input.get("link_values_printed") is False,
            jupyter_input.get("secret_values_printed") is False,
            jupyter_input.get("notebook_path") == "notebooks/robochallenge_pi05_submit_cn.ipynb",
            jupyter_input.get("section_marker") == "第 44 节：安全填空本地 env 入口",
            jupyter_input.get("run_flag") == "RUN_SAFE_LOCAL_ENV_INPUT_TEMPLATE",
            jupyter_input.get("run_flag_default_false") is True,
            jupyter_input.get("local_env_path") == "submission/robochallenge_env.local.sh",
            jupyter_input.get("local_env_ignored", {}).get("ignored") is True,
            all(jupyter_required.values()),
            not any(jupyter_forbidden.values()),
            all(jupyter_keys.values()),
            all(jupyter_variant_logic.values()),
            all(jupyter_route_guidance.values()),
            jupyter_input.get("recommended_route") == "baseline_official_aloha",
            jupyter_input.get("baseline_requires_checkpoint_link") is False,
            jupyter_input.get("baseline_requires_checkpoint_upload") is False,
            jupyter_input.get("lora_web_requires_checkpoint_link") is True,
            jupyter_input.get("lora_web_requires_checkpoint_upload") is True,
            jupyter_input.get("code_cell_clean") is True,
            jupyter_input.get("code_cell_id") == "safe-local-env-input-code",
            jupyter_input.get("secret_pattern_hits") == [],
            jupyter_input.get("whole_notebook_secret_pattern_hits") == [],
        ]
    ):
        print("Jupyter 安全填空本地 env 入口审计未通过")
        return 1
    jupyter_authorized = json.loads(
        (ROOT / "runs/jupyter_authorized_preflight_template_audit.json").read_text(encoding="utf-8")
    )
    jupyter_authorized_required = jupyter_authorized.get("required_fragments", {})
    jupyter_authorized_forbidden = jupyter_authorized.get("forbidden_fragments", {})
    jupyter_authorized_keys = jupyter_authorized.get("required_keys", {})
    jupyter_authorized_route_guidance = jupyter_authorized.get("route_guidance", {})
    if not all(
        [
            jupyter_authorized.get("kind") == "jupyter_authorized_preflight_template_audit",
            jupyter_authorized.get("passed"),
            jupyter_authorized.get("platform_contacted") is False,
            jupyter_authorized.get("uploads_performed") is False,
            jupyter_authorized.get("credentials_read") is False,
            jupyter_authorized.get("credentials_printed") is False,
            jupyter_authorized.get("link_values_printed") is False,
            jupyter_authorized.get("secret_values_printed") is False,
            jupyter_authorized.get("runner_started") is False,
            jupyter_authorized.get("notebook_path") == "notebooks/robochallenge_pi05_submit_cn.ipynb",
            jupyter_authorized.get("section_marker") == "第 45 节：授权后 Jupyter 预检入口",
            jupyter_authorized.get("audit_flag") == "RUN_JUPYTER_AUTHORIZED_PREFLIGHT_TEMPLATE_AUDIT",
            jupyter_authorized.get("audit_default_true") is True,
            jupyter_authorized.get("execution_flag") == "RUN_JUPYTER_AUTHORIZED_PREFLIGHT",
            jupyter_authorized.get("execution_default_false") is True,
            jupyter_authorized.get("local_env_path") == "submission/robochallenge_env.local.sh",
            jupyter_authorized.get("authorized_preflight_command") == "bash submission/run_authorized_preflight_template.sh",
            all(jupyter_authorized_required.values()),
            not any(jupyter_authorized_forbidden.values()),
            all(jupyter_authorized_keys.values()),
            all(jupyter_authorized_route_guidance.values()),
            jupyter_authorized.get("recommended_route") == "baseline_official_aloha",
            jupyter_authorized.get("baseline_requires_checkpoint_link") is False,
            jupyter_authorized.get("baseline_requires_checkpoint_upload") is False,
            jupyter_authorized.get("lora_web_requires_checkpoint_link") is True,
            jupyter_authorized.get("lora_web_requires_checkpoint_upload") is True,
            jupyter_authorized.get("code_cell_clean") is True,
            jupyter_authorized.get("code_cell_id") == "jupyter-authorized-preflight-code",
            jupyter_authorized.get("secret_pattern_hits") == [],
            jupyter_authorized.get("whole_notebook_secret_pattern_hits") == [],
        ]
    ):
        print("授权后 Jupyter 预检入口审计未通过")
        return 1
    jupyter_final_handoff = json.loads(
        (ROOT / "runs/jupyter_final_handoff_template_audit.json").read_text(encoding="utf-8")
    )
    jupyter_final_required = jupyter_final_handoff.get("required_fragments", {})
    jupyter_final_forbidden = jupyter_final_handoff.get("forbidden_fragments", {})
    jupyter_final_route = jupyter_final_handoff.get("route_guidance", {})
    jupyter_final_commands = jupyter_final_handoff.get("command_evidence", {})
    if not all(
        [
            jupyter_final_handoff.get("kind") == "jupyter_final_handoff_template_audit",
            jupyter_final_handoff.get("passed"),
            jupyter_final_handoff.get("platform_contacted") is False,
            jupyter_final_handoff.get("uploads_performed") is False,
            jupyter_final_handoff.get("credentials_read") is False,
            jupyter_final_handoff.get("credentials_printed") is False,
            jupyter_final_handoff.get("link_values_printed") is False,
            jupyter_final_handoff.get("secret_values_printed") is False,
            jupyter_final_handoff.get("runner_started") is False,
            jupyter_final_handoff.get("notebook_path") == "notebooks/robochallenge_pi05_submit_cn.ipynb",
            jupyter_final_handoff.get("audit_flag") == "RUN_JUPYTER_BASELINE_FINAL_HANDOFF_TEMPLATE_AUDIT",
            jupyter_final_handoff.get("audit_default_true") is True,
            jupyter_final_handoff.get("packet_flag") == "RUN_JUPYTER_BASELINE_FINAL_HANDOFF_PACKET",
            jupyter_final_handoff.get("packet_default_true") is True,
            jupyter_final_handoff.get("real_runner_flag") == "RUN_JUPYTER_BASELINE_REAL_RUNNER",
            jupyter_final_handoff.get("real_runner_default_false") is True,
            jupyter_final_handoff.get("final_handoff_script") == "scripts/render_baseline_final_handoff_packet.py",
            jupyter_final_handoff.get("final_handoff_report") == "reports/baseline_final_handoff_packet.md",
            jupyter_final_handoff.get("recommended_route") == "baseline_official_aloha",
            jupyter_final_handoff.get("baseline_requires_checkpoint_link") is False,
            jupyter_final_handoff.get("baseline_requires_checkpoint_upload") is False,
            jupyter_final_handoff.get("command_count") == 4,
            jupyter_final_handoff.get("no_contact_command_count") == 3,
            jupyter_final_handoff.get("real_runner_requires_confirmation") is True,
            all(jupyter_final_required.values()),
            not any(jupyter_final_forbidden.values()),
            all(jupyter_final_route.values()),
            all(jupyter_final_commands.values()),
            jupyter_final_handoff.get("code_cell_clean") is True,
            jupyter_final_handoff.get("code_cell_id") == "jupyter-final-handoff-code",
            jupyter_final_handoff.get("secret_pattern_hits") == [],
            jupyter_final_handoff.get("whole_notebook_secret_pattern_hits") == [],
        ]
    ):
        print("Jupyter final handoff 交接包入口审计未通过")
        return 1
    authorized_preflight = json.loads((ROOT / "runs/authorized_preflight_template_audit.json").read_text(encoding="utf-8"))
    authorized_preflight_smoke = authorized_preflight.get("no_credentials_smoke", {})
    if not all(
        [
            authorized_preflight.get("kind") == "authorized_preflight_template_audit",
            authorized_preflight.get("passed"),
            authorized_preflight.get("platform_contacted") is False,
            authorized_preflight.get("uploads_performed") is False,
            authorized_preflight.get("credentials_read") is False,
            authorized_preflight.get("credentials_printed") is False,
            authorized_preflight.get("link_values_printed") is False,
            authorized_preflight.get("secret_values_printed") is False,
            authorized_preflight.get("template_path") == "submission/run_authorized_preflight_template.sh",
            authorized_preflight.get("bash_n", {}).get("passed"),
            all(authorized_preflight.get("required_fragments", {}).values()),
            not any(authorized_preflight.get("forbidden_fragments", {}).values()),
            authorized_preflight.get("secret_patterns_found") == [],
            authorized_preflight_smoke.get("passed"),
            authorized_preflight_smoke.get("env_file_present_false"),
            authorized_preflight_smoke.get("verify_download_disabled"),
            authorized_preflight_smoke.get("stops_before_runner"),
            authorized_preflight_smoke.get("ready_false"),
            authorized_preflight_smoke.get("real_runner_not_called"),
            all(authorized_preflight.get("input_evidence", {}).values()),
        ]
    ):
        print("授权后安全预检模板审计未通过")
        return 1
    ready_real_runner = json.loads((ROOT / "runs/ready_real_runner_template_audit.json").read_text(encoding="utf-8"))
    ready_real_no_credentials = ready_real_runner.get("no_credentials_smoke", {})
    ready_real_no_confirm = ready_real_runner.get("synthetic_no_confirm_smoke", {})
    if not all(
        [
            ready_real_runner.get("kind") == "ready_real_runner_template_audit",
            ready_real_runner.get("passed"),
            ready_real_runner.get("platform_contacted") is False,
            ready_real_runner.get("uploads_performed") is False,
            ready_real_runner.get("credentials_read") is False,
            ready_real_runner.get("credentials_printed") is False,
            ready_real_runner.get("link_values_printed") is False,
            ready_real_runner.get("secret_values_printed") is False,
            ready_real_runner.get("template_path") == "submission/run_ready_real_submission_template.sh",
            ready_real_runner.get("confirmation_phrase") == "RUN_REAL_ROBOCHALLENGE_SUBMISSION",
            ready_real_runner.get("default_variant") == "baseline",
            ready_real_runner.get("bash_n", {}).get("passed"),
            all(ready_real_runner.get("required_fragments", {}).values()),
            not any(ready_real_runner.get("forbidden_fragments", {}).values()),
            ready_real_runner.get("secret_patterns_found") == [],
            ready_real_no_credentials.get("passed"),
            ready_real_no_credentials.get("ready_false"),
            not ready_real_no_credentials.get("dry_run_called"),
            not ready_real_no_credentials.get("real_runner_started"),
            ready_real_no_confirm.get("passed"),
            ready_real_no_confirm.get("variant") == "baseline",
            ready_real_no_confirm.get("dry_run_called"),
            ready_real_no_confirm.get("missing_confirmation"),
            ready_real_no_confirm.get("stops_before_real_runner"),
            not ready_real_no_confirm.get("real_runner_started"),
            ready_real_runner.get("clean_state_restore", {}).get("passed"),
        ]
    ):
        print("强确认真实 runner 模板审计未通过")
        return 1
    authorized_archive = json.loads(
        (ROOT / "runs/authorized_checkpoint_archive_template_audit.json").read_text(encoding="utf-8")
    )
    authorized_archive_smoke = authorized_archive.get("no_confirm_smoke", {})
    if not all(
        [
            authorized_archive.get("kind") == "authorized_checkpoint_archive_template_audit",
            authorized_archive.get("passed"),
            authorized_archive.get("platform_contacted") is False,
            authorized_archive.get("uploads_performed") is False,
            authorized_archive.get("credentials_read") is False,
            authorized_archive.get("credentials_printed") is False,
            authorized_archive.get("link_values_printed") is False,
            authorized_archive.get("secret_values_printed") is False,
            authorized_archive.get("template_path") == "submission/run_authorized_checkpoint_archive_template.sh",
            authorized_archive.get("confirmation_phrase") == "CREATE_ROBOCHALLENGE_CHECKPOINT_ARCHIVE",
            authorized_archive.get("bash_n", {}).get("passed"),
            all(authorized_archive.get("required_fragments", {}).values()),
            not any(authorized_archive.get("forbidden_fragments", {}).values()),
            authorized_archive.get("secret_patterns_found") == [],
            authorized_archive_smoke.get("passed"),
            authorized_archive_smoke.get("missing_confirmation"),
            authorized_archive_smoke.get("stops_before_creating_tar"),
            authorized_archive_smoke.get("archive_created") is False,
            authorized_archive_smoke.get("sha256_created") is False,
            authorized_archive_smoke.get("upload_performed") is False,
            authorized_archive_smoke.get("credentials_read") is False,
            authorized_archive_smoke.get("platform_contacted") is False,
            authorized_archive_smoke.get("archive_absent_after"),
            authorized_archive_smoke.get("sha256_absent_after"),
            all(authorized_archive.get("input_evidence", {}).values()),
        ]
    ):
        print("授权后 checkpoint 归档模板审计未通过")
        return 1
    authorized_execution = json.loads((ROOT / "runs/authorized_execution_checklist.json").read_text(encoding="utf-8"))
    authorized_execution_evidence = authorized_execution.get("evidence", {})
    authorized_execution_leaks = authorized_execution.get("leak_flags", {})
    authorized_execution_contacts = authorized_execution.get("contact_flags", {})
    authorized_execution_required_ids = {
        item.get("id") for item in authorized_execution.get("required_user_decisions", [])
    }
    authorized_execution_lora_web_ids = set(authorized_execution.get("lora_web_user_decision_ids", []))
    authorized_execution_commands = {item.get("command") for item in authorized_execution.get("authorized_steps", [])}
    if not all(
        [
            authorized_execution.get("kind") == "authorized_execution_checklist",
            authorized_execution.get("passed"),
            authorized_execution.get("go_no_go") == "blocked_by_user_inputs",
            authorized_execution.get("ready_for_real_submission") is False,
            authorized_execution.get("platform_contacted") is False,
            authorized_execution.get("uploads_performed") is False,
            authorized_execution.get("credentials_read") is False,
            authorized_execution.get("credentials_printed") is False,
            authorized_execution.get("link_values_printed") is False,
            authorized_execution.get("secret_values_printed") is False,
            authorized_execution.get("current_runnable_target") == "Table30v2 ALOHA",
            authorized_execution.get("recommended_route") == "baseline_official_aloha",
            authorized_execution.get("baseline_requires_checkpoint_link") is False,
            authorized_execution.get("baseline_requires_checkpoint_upload") is False,
            authorized_execution.get("lora_web_requires_checkpoint_link") is True,
            authorized_execution.get("lora_web_requires_checkpoint_upload") is True,
            {
                "SUBMISSION_TARGET_CONFIRMATION",
                "ROBOCHALLENGE_USER_TOKEN",
                "ROBOCHALLENGE_SUBMISSION_ID",
                "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline",
                "ROBOCHALLENGE_REAL_RUN_CONFIRM",
            }.issubset(authorized_execution_required_ids),
            "ROBOCHALLENGE_CHECKPOINT_LINK" not in authorized_execution_required_ids,
            "CHECKPOINT_ARCHIVE_AUTHORIZATION" not in authorized_execution_required_ids,
            {
                "SUBMISSION_TARGET_CONFIRMATION",
                "ROBOCHALLENGE_USER_TOKEN",
                "ROBOCHALLENGE_SUBMISSION_ID",
                "ROBOCHALLENGE_SUBMISSION_VARIANT=lora",
                "ROBOCHALLENGE_CHECKPOINT_LINK",
                "CHECKPOINT_ARCHIVE_AUTHORIZATION",
                "ROBOCHALLENGE_REAL_RUN_CONFIRM",
            }.issubset(authorized_execution_lora_web_ids),
            "Notebook 第 45 节：RUN_JUPYTER_AUTHORIZED_PREFLIGHT=True" in authorized_execution_commands,
            "bash submission/run_authorized_preflight_template.sh" in authorized_execution_commands,
            (
                "ROBOCHALLENGE_ARCHIVE_CONFIRM=CREATE_ROBOCHALLENGE_CHECKPOINT_ARCHIVE "
                "bash submission/run_authorized_checkpoint_archive_template.sh"
            )
            in authorized_execution_commands,
            (
                "ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION "
                "bash submission/run_ready_real_submission_template.sh"
            )
            in authorized_execution_commands,
            authorized_execution.get("required_evidence_passed") is True,
            all(
                authorized_execution_evidence.get(key) is True
                for key in authorized_execution.get("required_evidence_keys", [])
            ),
            not any(authorized_execution_leaks.values()),
            not any(authorized_execution_contacts.values()),
            len(authorized_execution.get("must_stop_if", [])) >= 5,
            len(authorized_execution.get("lora_web_must_stop_if", [])) >= 7,
            len(authorized_execution.get("blocking", [])) >= 4,
        ]
    ):
        print("授权执行清单审计未通过")
        return 1
    action_packet = json.loads((ROOT / "runs/next_user_action_packet.json").read_text(encoding="utf-8"))
    action_packet_evidence = action_packet.get("evidence", {})
    action_packet_leaks = action_packet.get("leak_flags", {})
    action_packet_contacts = action_packet.get("contact_flags", {})
    action_packet_required_ids = set(action_packet.get("required_decision_ids", []))
    action_packet_baseline_ids = set(action_packet.get("baseline_current_blocking", []))
    action_packet_lora_web_ids = set(action_packet.get("lora_web_current_blocking", []))
    if not all(
        [
            action_packet.get("kind") == "next_user_action_packet",
            action_packet.get("passed"),
            action_packet.get("go_no_go") == "blocked_by_user_inputs",
            action_packet.get("ready_for_real_submission") is False,
            action_packet.get("web_form_ready") is False,
            action_packet.get("notebook_path") == "notebooks/robochallenge_pi05_submit_cn.ipynb",
            action_packet.get("local_env_path") == "submission/robochallenge_env.local.sh",
            action_packet.get("local_env_ignored") is True,
            action_packet.get("platform_contacted") is False,
            action_packet.get("uploads_performed") is False,
            action_packet.get("credentials_read") is False,
            action_packet.get("credentials_printed") is False,
            action_packet.get("link_values_printed") is False,
            action_packet.get("secret_values_printed") is False,
            action_packet.get("recommended_route") == "baseline_official_aloha",
            action_packet.get("baseline_requires_checkpoint_link") is False,
            action_packet.get("baseline_requires_checkpoint_upload") is False,
            action_packet.get("lora_web_requires_checkpoint_link") is True,
            action_packet.get("lora_web_requires_checkpoint_upload") is True,
            "ROBOCHALLENGE_CHECKPOINT_LINK" not in action_packet_baseline_ids,
            "CHECKPOINT_ARCHIVE_AUTHORIZATION" not in action_packet_baseline_ids,
            {
                "SUBMISSION_TARGET_CONFIRMATION",
                "ROBOCHALLENGE_USER_TOKEN",
                "ROBOCHALLENGE_SUBMISSION_ID",
                "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline",
                "ROBOCHALLENGE_REAL_RUN_CONFIRM",
            }.issubset(action_packet_baseline_ids),
            {
                "SUBMISSION_TARGET_CONFIRMATION",
                "ROBOCHALLENGE_USER_TOKEN",
                "ROBOCHALLENGE_SUBMISSION_ID",
                "ROBOCHALLENGE_SUBMISSION_VARIANT=lora",
                "CHECKPOINT_ARCHIVE_AUTHORIZATION",
                "ROBOCHALLENGE_CHECKPOINT_LINK",
                "ROBOCHALLENGE_REAL_RUN_CONFIRM",
            }.issubset(action_packet_lora_web_ids),
            {
                "SUBMISSION_TARGET_CONFIRMATION",
                "ROBOCHALLENGE_USER_TOKEN",
                "ROBOCHALLENGE_SUBMISSION_ID",
                "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline",
                "ROBOCHALLENGE_REAL_RUN_CONFIRM",
            }.issubset(action_packet_required_ids),
            "ROBOCHALLENGE_CHECKPOINT_LINK" not in action_packet_required_ids,
            "CHECKPOINT_ARCHIVE_AUTHORIZATION" not in action_packet_required_ids,
            len(action_packet.get("first_notebook_steps", [])) >= 2,
            len(action_packet.get("current_blocking", [])) >= 5,
            "ROBOCHALLENGE_CHECKPOINT_LINK" not in set(action_packet.get("current_blocking", [])),
            len(action_packet.get("legacy_global_blocking", [])) >= 4,
            all(action_packet_evidence.values()),
            not any(action_packet_leaks.values()),
            not any(action_packet_contacts.values()),
        ]
    ):
        print("下一步用户动作包审计未通过")
        return 1
    web_form_packet = json.loads((ROOT / "runs/web_form_field_packet.json").read_text(encoding="utf-8"))
    web_form_evidence = web_form_packet.get("evidence", {})
    web_form_leaks = web_form_packet.get("leak_flags", {})
    web_form_contacts = web_form_packet.get("contact_flags", {})
    web_form_fields = web_form_packet.get("fields", [])
    web_form_field_names = {item.get("name") for item in web_form_fields}
    if not all(
        [
            web_form_packet.get("kind") == "web_form_field_packet",
            web_form_packet.get("passed"),
            web_form_packet.get("web_form_ready") is False,
            web_form_packet.get("field_count", 0) >= 10,
            web_form_packet.get("ready_field_count", 0) >= 6,
            web_form_packet.get("missing_field_count", 0) >= 3,
            len(web_form_fields) == web_form_packet.get("field_count"),
            {
                "Benchmark",
                "Robot Type",
                "Task Name",
                "Prompt",
                "Inference Code Link",
                "Fine-tuning / Restore Evidence",
                "Checkpoint Link",
                "RoboChallenge User Token",
                "RoboChallenge Submission ID",
                "Submission Variant",
                "Checkpoint Upload / Archive",
                "Authorized Notebook Entry",
            }.issubset(web_form_field_names),
            all(web_form_evidence.values()),
            not any(web_form_leaks.values()),
            not any(web_form_contacts.values()),
            web_form_packet.get("platform_contacted") is False,
            web_form_packet.get("uploads_performed") is False,
            web_form_packet.get("credentials_read") is False,
            web_form_packet.get("credentials_printed") is False,
            web_form_packet.get("link_values_printed") is False,
            web_form_packet.get("secret_values_printed") is False,
        ]
    ):
        print("网页表单字段包审计未通过")
        return 1
    route_packet = json.loads((ROOT / "runs/submission_variant_route_packet.json").read_text(encoding="utf-8"))
    route_evidence = route_packet.get("evidence", {})
    route_leaks = route_packet.get("leak_flags", {})
    route_contacts = route_packet.get("contact_flags", {})
    routes = route_packet.get("routes", [])
    route_by_id = {item.get("id"): item for item in routes}
    baseline_route = route_by_id.get("baseline_official_aloha", {})
    lora_route = route_by_id.get("lora_materialized", {})
    baseline_blocking = set(baseline_route.get("current_blocking", []))
    lora_blocking = set(lora_route.get("current_blocking", []))
    if not all(
        [
            route_packet.get("kind") == "submission_variant_route_packet",
            route_packet.get("passed"),
            route_packet.get("recommended_default") == "baseline_official_aloha",
            route_packet.get("route_count") == 2,
            len(routes) == 2,
            baseline_route.get("recommended") is True,
            baseline_route.get("local_runner_ready_without_credentials") is True,
            baseline_route.get("local_checkpoint_ready") is True,
            baseline_route.get("requires_checkpoint_upload") is False,
            baseline_route.get("requires_checkpoint_link_for_local_runner") is False,
            baseline_route.get("requires_checkpoint_upload_for_public_link") is False,
            {
                "SUBMISSION_TARGET_CONFIRMATION",
                "ROBOCHALLENGE_USER_TOKEN",
                "ROBOCHALLENGE_SUBMISSION_ID",
                "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline",
                "ROBOCHALLENGE_REAL_RUN_CONFIRM",
            }.issubset(baseline_blocking),
            lora_route.get("recommended") is False,
            lora_route.get("local_runner_ready_without_credentials") is True,
            lora_route.get("local_checkpoint_ready") is True,
            lora_route.get("requires_checkpoint_upload") is False,
            lora_route.get("requires_checkpoint_link_for_local_runner") is False,
            lora_route.get("requires_checkpoint_upload_for_public_link") is True,
            {
                "SUBMISSION_TARGET_CONFIRMATION",
                "ROBOCHALLENGE_USER_TOKEN",
                "ROBOCHALLENGE_SUBMISSION_ID",
                "ROBOCHALLENGE_SUBMISSION_VARIANT=lora",
                "CHECKPOINT_ARCHIVE_AUTHORIZATION",
                "ROBOCHALLENGE_CHECKPOINT_LINK",
                "ROBOCHALLENGE_REAL_RUN_CONFIRM",
            }.issubset(lora_blocking),
            all(route_evidence.values()),
            not any(route_leaks.values()),
            not any(route_contacts.values()),
            route_packet.get("platform_contacted") is False,
            route_packet.get("uploads_performed") is False,
            route_packet.get("credentials_read") is False,
            route_packet.get("credentials_printed") is False,
            route_packet.get("link_values_printed") is False,
            route_packet.get("secret_values_printed") is False,
        ]
    ):
        print("提交路线拆分包审计未通过")
        return 1
    baseline_quickstart = json.loads((ROOT / "runs/baseline_submission_quickstart.json").read_text(encoding="utf-8"))
    quickstart_evidence = baseline_quickstart.get("evidence", {})
    quickstart_leaks = baseline_quickstart.get("leak_flags", {})
    quickstart_contacts = baseline_quickstart.get("contact_flags", {})
    quickstart_input_ids = {item.get("id") for item in baseline_quickstart.get("required_user_inputs", [])}
    quickstart_commands = baseline_quickstart.get("commands", [])
    if not all(
        [
            baseline_quickstart.get("kind") == "baseline_submission_quickstart",
            baseline_quickstart.get("passed"),
            baseline_quickstart.get("recommended_route") == "baseline_official_aloha",
            baseline_quickstart.get("requires_checkpoint_upload") is False,
            baseline_quickstart.get("requires_checkpoint_link") is False,
            {
                "SUBMISSION_TARGET_CONFIRMATION",
                "ROBOCHALLENGE_USER_TOKEN",
                "ROBOCHALLENGE_SUBMISSION_ID",
                "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline",
                "ROBOCHALLENGE_REAL_RUN_CONFIRM",
            }.issubset(quickstart_input_ids),
            len(quickstart_commands) >= 4,
            any("run_authorized_preflight_template.sh" in item.get("command", "") for item in quickstart_commands),
            any("run_ready_real_submission_template.sh" in item.get("command", "") for item in quickstart_commands),
            all(quickstart_evidence.values()),
            not any(quickstart_leaks.values()),
            not any(quickstart_contacts.values()),
            baseline_quickstart.get("platform_contacted") is False,
            baseline_quickstart.get("uploads_performed") is False,
            baseline_quickstart.get("credentials_read") is False,
            baseline_quickstart.get("credentials_printed") is False,
            baseline_quickstart.get("link_values_printed") is False,
            baseline_quickstart.get("secret_values_printed") is False,
        ]
    ):
        print("baseline 最短提交路径包审计未通过")
        return 1
    baseline_dry_run_gate = json.loads((ROOT / "runs/baseline_dry_run_gate.json").read_text(encoding="utf-8"))
    dry_run_evidence = baseline_dry_run_gate.get("evidence", {})
    dry_run_leaks = baseline_dry_run_gate.get("leak_flags", {})
    dry_run_contacts = baseline_dry_run_gate.get("contact_flags", {})
    dry_run_required_ids = set(baseline_dry_run_gate.get("baseline_required_ids", []))
    dry_run_lora_only_ids = set(baseline_dry_run_gate.get("lora_only_ids", []))
    if not all(
        [
            baseline_dry_run_gate.get("kind") == "baseline_dry_run_gate",
            baseline_dry_run_gate.get("passed"),
            baseline_dry_run_gate.get("recommended_route") == "baseline_official_aloha",
            baseline_dry_run_gate.get("requires_checkpoint_upload") is False,
            baseline_dry_run_gate.get("requires_checkpoint_link") is False,
            baseline_dry_run_gate.get("authorized_preflight_command")
            == "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_authorized_preflight_template.sh",
            baseline_dry_run_gate.get("dry_run_gate_command")
            == "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_ready_real_submission_template.sh",
            baseline_dry_run_gate.get("real_runner_command")
            == (
                "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline "
                "ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION "
                "bash submission/run_ready_real_submission_template.sh"
            ),
            baseline_dry_run_gate.get("first_real_runner_wrapper_command")
            == "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_ready_real_submission_template.sh",
            baseline_dry_run_gate.get("stops_before_real_runner_without_confirmation") is True,
            {
                "SUBMISSION_TARGET_CONFIRMATION",
                "ROBOCHALLENGE_USER_TOKEN",
                "ROBOCHALLENGE_SUBMISSION_ID",
                "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline",
                "ROBOCHALLENGE_REAL_RUN_CONFIRM",
            }.issubset(dry_run_required_ids),
            {"CHECKPOINT_ARCHIVE_AUTHORIZATION", "ROBOCHALLENGE_CHECKPOINT_LINK"}.issubset(dry_run_lora_only_ids),
            "CHECKPOINT_ARCHIVE_AUTHORIZATION" not in dry_run_required_ids,
            "ROBOCHALLENGE_CHECKPOINT_LINK" not in dry_run_required_ids,
            all(dry_run_evidence.values()),
            not any(dry_run_leaks.values()),
            not any(dry_run_contacts.values()),
            baseline_dry_run_gate.get("platform_contacted") is False,
            baseline_dry_run_gate.get("uploads_performed") is False,
            baseline_dry_run_gate.get("credentials_read") is False,
            baseline_dry_run_gate.get("credentials_printed") is False,
            baseline_dry_run_gate.get("link_values_printed") is False,
            baseline_dry_run_gate.get("secret_values_printed") is False,
        ]
    ):
        print("baseline dry-run gate 证据包审计未通过")
        return 1
    baseline_credential_hygiene = json.loads(
        (ROOT / "runs/baseline_credential_hygiene.json").read_text(encoding="utf-8")
    )
    credential_hygiene_evidence = baseline_credential_hygiene.get("evidence", {})
    credential_hygiene_leaks = baseline_credential_hygiene.get("leak_flags", {})
    credential_hygiene_contacts = baseline_credential_hygiene.get("contact_flags", {})
    credential_hygiene_required_ids = set(baseline_credential_hygiene.get("baseline_required_ids", []))
    credential_hygiene_lora_only_ids = set(baseline_credential_hygiene.get("lora_only_ids", []))
    if not all(
        [
            baseline_credential_hygiene.get("kind") == "baseline_credential_hygiene",
            baseline_credential_hygiene.get("passed"),
            baseline_credential_hygiene.get("recommended_route") == "baseline_official_aloha",
            baseline_credential_hygiene.get("recommended_local_env") == "submission/robochallenge_env.local.sh",
            baseline_credential_hygiene.get("local_env_content_read") is False,
            baseline_credential_hygiene.get("local_env_gitignored") is True,
            baseline_credential_hygiene.get("local_env_tracked") is False,
            baseline_credential_hygiene.get("authorized_preflight_command")
            == "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_authorized_preflight_template.sh",
            baseline_credential_hygiene.get("dry_run_gate_command")
            == "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_ready_real_submission_template.sh",
            baseline_credential_hygiene.get("requires_checkpoint_upload") is False,
            baseline_credential_hygiene.get("requires_checkpoint_link") is False,
            {
                "SUBMISSION_TARGET_CONFIRMATION",
                "ROBOCHALLENGE_USER_TOKEN",
                "ROBOCHALLENGE_SUBMISSION_ID",
                "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline",
                "ROBOCHALLENGE_REAL_RUN_CONFIRM",
            }.issubset(credential_hygiene_required_ids),
            {"CHECKPOINT_ARCHIVE_AUTHORIZATION", "ROBOCHALLENGE_CHECKPOINT_LINK"}.issubset(
                credential_hygiene_lora_only_ids
            ),
            "CHECKPOINT_ARCHIVE_AUTHORIZATION" not in credential_hygiene_required_ids,
            "ROBOCHALLENGE_CHECKPOINT_LINK" not in credential_hygiene_required_ids,
            all(credential_hygiene_evidence.values()),
            not any(credential_hygiene_leaks.values()),
            not any(credential_hygiene_contacts.values()),
            baseline_credential_hygiene.get("platform_contacted") is False,
            baseline_credential_hygiene.get("uploads_performed") is False,
            baseline_credential_hygiene.get("credentials_read") is False,
            baseline_credential_hygiene.get("credentials_printed") is False,
            baseline_credential_hygiene.get("link_values_printed") is False,
            baseline_credential_hygiene.get("secret_values_printed") is False,
        ]
    ):
        print("baseline 凭据卫生证据包审计未通过")
        return 1
    baseline_local_env_smoke = json.loads((ROOT / "runs/baseline_local_env_smoke.json").read_text(encoding="utf-8"))
    local_env_smoke_evidence = baseline_local_env_smoke.get("evidence", {})
    local_env_smoke_leaks = baseline_local_env_smoke.get("leak_flags", {})
    local_env_smoke_contacts = baseline_local_env_smoke.get("contact_flags", {})
    local_env_authorized = baseline_local_env_smoke.get("authorized_preflight", {})
    local_env_ready = baseline_local_env_smoke.get("ready_runner", {})
    if not all(
        [
            baseline_local_env_smoke.get("kind") == "baseline_local_env_smoke",
            baseline_local_env_smoke.get("passed"),
            baseline_local_env_smoke.get("recommended_route") == "baseline_official_aloha",
            baseline_local_env_smoke.get("synthetic_token_length", 0) > 20,
            baseline_local_env_smoke.get("synthetic_submission_id_length", 0) > 20,
            baseline_local_env_smoke.get("synthetic_values_recorded") is False,
            baseline_local_env_smoke.get("synthetic_env_file_removed_after_run") is True,
            baseline_local_env_smoke.get("authorized_preflight_command")
            == "bash submission/run_authorized_preflight_template.sh",
            baseline_local_env_smoke.get("ready_runner_command")
            == "bash submission/run_ready_real_submission_template.sh",
            local_env_authorized.get("returncode") == 0,
            local_env_authorized.get("env_file_present_true") is True,
            local_env_authorized.get("variant_baseline") is True,
            local_env_authorized.get("dry_run_called") is True,
            local_env_authorized.get("robot_type_aloha") is True,
            local_env_authorized.get("printed_protected_values") is False,
            local_env_ready.get("returncode") == 1,
            local_env_ready.get("env_file_present_true") is True,
            local_env_ready.get("variant_baseline") is True,
            local_env_ready.get("dry_run_called") is True,
            local_env_ready.get("missing_confirmation") is True,
            local_env_ready.get("stops_before_real_runner") is True,
            local_env_ready.get("real_runner_started") is False,
            local_env_ready.get("printed_protected_values") is False,
            all(local_env_smoke_evidence.values()),
            not any(local_env_smoke_leaks.values()),
            not any(local_env_smoke_contacts.values()),
            baseline_local_env_smoke.get("platform_contacted") is False,
            baseline_local_env_smoke.get("uploads_performed") is False,
            baseline_local_env_smoke.get("credentials_read") is False,
            baseline_local_env_smoke.get("credentials_printed") is False,
            baseline_local_env_smoke.get("link_values_printed") is False,
            baseline_local_env_smoke.get("secret_values_printed") is False,
        ]
    ):
        print("baseline synthetic local env smoke 审计未通过")
        return 1
    baseline_final_handoff = json.loads((ROOT / "runs/baseline_final_handoff_packet.json").read_text(encoding="utf-8"))
    final_handoff_evidence = baseline_final_handoff.get("evidence", {})
    final_handoff_leaks = baseline_final_handoff.get("leak_flags", {})
    final_handoff_contacts = baseline_final_handoff.get("contact_flags", {})
    final_handoff_blocking_ids = set(baseline_final_handoff.get("baseline_current_blocking", []))
    final_handoff_commands = baseline_final_handoff.get("commands", [])
    final_handoff_command_strings = [item.get("command") for item in final_handoff_commands]
    final_handoff_real_command = final_handoff_commands[3] if len(final_handoff_commands) > 3 else {}
    if not all(
        [
            baseline_final_handoff.get("kind") == "baseline_final_handoff_packet",
            baseline_final_handoff.get("passed"),
            baseline_final_handoff.get("recommended_route") == "baseline_official_aloha",
            baseline_final_handoff.get("recommended_local_env") == "submission/robochallenge_env.local.sh",
            baseline_final_handoff.get("local_env_content_read") is False,
            baseline_final_handoff.get("requires_checkpoint_upload") is False,
            baseline_final_handoff.get("requires_checkpoint_link") is False,
            baseline_final_handoff.get("requires_checkpoint_archive_authorization") is False,
            baseline_final_handoff.get("command_count") == 4,
            baseline_final_handoff.get("no_contact_command_count") == 3,
            baseline_final_handoff.get("real_runner_requires_confirmation") is True,
            baseline_final_handoff.get("real_runner_command")
            == (
                "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline "
                "ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION "
                "bash submission/run_ready_real_submission_template.sh"
            ),
            final_handoff_command_strings
            == [
                "python3 scripts/render_baseline_credential_hygiene.py",
                "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_authorized_preflight_template.sh",
                "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_ready_real_submission_template.sh",
                (
                    "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline "
                    "ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION "
                    "bash submission/run_ready_real_submission_template.sh"
                ),
            ],
            all(item.get("no_contact") is True for item in final_handoff_commands[:3]),
            final_handoff_real_command.get("requires_real_run_confirmation") is True,
            final_handoff_real_command.get("starts_real_runner") is True,
            {
                "SUBMISSION_TARGET_CONFIRMATION",
                "ROBOCHALLENGE_USER_TOKEN",
                "ROBOCHALLENGE_SUBMISSION_ID",
                "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline",
                "ROBOCHALLENGE_REAL_RUN_CONFIRM",
            }
            == final_handoff_blocking_ids,
            "CHECKPOINT_ARCHIVE_AUTHORIZATION" not in final_handoff_blocking_ids,
            "ROBOCHALLENGE_CHECKPOINT_LINK" not in final_handoff_blocking_ids,
            all(final_handoff_evidence.values()),
            not any(final_handoff_leaks.values()),
            not any(final_handoff_contacts.values()),
            baseline_final_handoff.get("platform_contacted") is False,
            baseline_final_handoff.get("uploads_performed") is False,
            baseline_final_handoff.get("credentials_read") is False,
            baseline_final_handoff.get("credentials_printed") is False,
            baseline_final_handoff.get("link_values_printed") is False,
            baseline_final_handoff.get("secret_values_printed") is False,
        ]
    ):
        print("baseline final handoff 证据包审计未通过")
        return 1
    baseline_final_handoff_rehearsal = json.loads(
        (ROOT / "runs/baseline_final_handoff_rehearsal.json").read_text(encoding="utf-8")
    )
    rehearsal_evidence = baseline_final_handoff_rehearsal.get("evidence", {})
    rehearsal_leaks = baseline_final_handoff_rehearsal.get("leak_flags", {})
    rehearsal_contacts = baseline_final_handoff_rehearsal.get("contact_flags", {})
    rehearsal_commands = baseline_final_handoff_rehearsal.get("commands", [])
    rehearsal_step1 = rehearsal_commands[0] if len(rehearsal_commands) > 0 else {}
    rehearsal_step2 = rehearsal_commands[1] if len(rehearsal_commands) > 1 else {}
    rehearsal_step3 = rehearsal_commands[2] if len(rehearsal_commands) > 2 else {}
    if not all(
        [
            baseline_final_handoff_rehearsal.get("kind") == "baseline_final_handoff_rehearsal",
            baseline_final_handoff_rehearsal.get("passed"),
            baseline_final_handoff_rehearsal.get("recommended_route") == "baseline_official_aloha",
            baseline_final_handoff_rehearsal.get("command_count") == 3,
            baseline_final_handoff_rehearsal.get("synthetic_token_length", 0) > 20,
            baseline_final_handoff_rehearsal.get("synthetic_submission_id_length", 0) > 20,
            baseline_final_handoff_rehearsal.get("synthetic_values_recorded") is False,
            baseline_final_handoff_rehearsal.get("synthetic_env_file_removed_after_run") is True,
            baseline_final_handoff_rehearsal.get("workspace_state_restored_after_rehearsal") is True,
            baseline_final_handoff_rehearsal.get("expected_first_three_commands")
            == [
                "python3 scripts/render_baseline_credential_hygiene.py",
                "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_authorized_preflight_template.sh",
                "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_ready_real_submission_template.sh",
            ],
            baseline_final_handoff_rehearsal.get("handoff_first_three_commands")
            == baseline_final_handoff_rehearsal.get("expected_first_three_commands"),
            rehearsal_step1.get("returncode") == 0,
            rehearsal_step1.get("printed_protected_values") is False,
            rehearsal_step2.get("returncode") == 0,
            rehearsal_step2.get("env_file_present_true") is True,
            rehearsal_step2.get("variant_baseline") is True,
            rehearsal_step2.get("dry_run_called") is True,
            rehearsal_step2.get("robot_type_aloha") is True,
            rehearsal_step2.get("printed_protected_values") is False,
            rehearsal_step3.get("returncode") == 1,
            rehearsal_step3.get("env_file_present_true") is True,
            rehearsal_step3.get("variant_baseline") is True,
            rehearsal_step3.get("dry_run_called") is True,
            rehearsal_step3.get("missing_confirmation") is True,
            rehearsal_step3.get("stops_before_real_runner") is True,
            rehearsal_step3.get("real_runner_started") is False,
            rehearsal_step3.get("printed_protected_values") is False,
            all(rehearsal_evidence.values()),
            not any(rehearsal_leaks.values()),
            not any(rehearsal_contacts.values()),
            baseline_final_handoff_rehearsal.get("platform_contacted") is False,
            baseline_final_handoff_rehearsal.get("uploads_performed") is False,
            baseline_final_handoff_rehearsal.get("credentials_read") is False,
            baseline_final_handoff_rehearsal.get("credentials_printed") is False,
            baseline_final_handoff_rehearsal.get("link_values_printed") is False,
            baseline_final_handoff_rehearsal.get("secret_values_printed") is False,
        ]
    ):
        print("baseline final handoff 前三步演练审计未通过")
        return 1
    route_aware_blockers = json.loads((ROOT / "runs/route_aware_submission_blockers.json").read_text(encoding="utf-8"))
    route_aware_evidence = route_aware_blockers.get("evidence", {})
    route_aware_leaks = route_aware_blockers.get("leak_flags", {})
    route_aware_contacts = route_aware_blockers.get("contact_flags", {})
    route_aware_baseline_ids = set(route_aware_blockers.get("baseline_current_blocking", []))
    route_aware_lora_ids = set(route_aware_blockers.get("lora_web_current_blocking", []))
    if not all(
        [
            route_aware_blockers.get("kind") == "route_aware_submission_blockers",
            route_aware_blockers.get("passed"),
            route_aware_blockers.get("recommended_route") == "baseline_official_aloha",
            route_aware_blockers.get("baseline_requires_checkpoint_upload") is False,
            route_aware_blockers.get("baseline_requires_checkpoint_link") is False,
            route_aware_blockers.get("baseline_requires_archive_authorization") is False,
            route_aware_blockers.get("lora_web_requires_checkpoint_upload") is True,
            route_aware_blockers.get("lora_web_requires_checkpoint_link") is True,
            route_aware_blockers.get("lora_web_requires_archive_authorization") is True,
            "ROBOCHALLENGE_CHECKPOINT_LINK" not in route_aware_baseline_ids,
            "CHECKPOINT_ARCHIVE_AUTHORIZATION" not in route_aware_baseline_ids,
            {
                "SUBMISSION_TARGET_CONFIRMATION",
                "ROBOCHALLENGE_USER_TOKEN",
                "ROBOCHALLENGE_SUBMISSION_ID",
                "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline",
                "ROBOCHALLENGE_REAL_RUN_CONFIRM",
            }.issubset(route_aware_baseline_ids),
            {
                "SUBMISSION_TARGET_CONFIRMATION",
                "ROBOCHALLENGE_USER_TOKEN",
                "ROBOCHALLENGE_SUBMISSION_ID",
                "ROBOCHALLENGE_SUBMISSION_VARIANT=lora",
                "CHECKPOINT_ARCHIVE_AUTHORIZATION",
                "ROBOCHALLENGE_CHECKPOINT_LINK",
                "ROBOCHALLENGE_REAL_RUN_CONFIRM",
            }.issubset(route_aware_lora_ids),
            all(route_aware_evidence.values()),
            not any(route_aware_leaks.values()),
            not any(route_aware_contacts.values()),
            route_aware_blockers.get("platform_contacted") is False,
            route_aware_blockers.get("uploads_performed") is False,
            route_aware_blockers.get("credentials_read") is False,
            route_aware_blockers.get("credentials_printed") is False,
            route_aware_blockers.get("link_values_printed") is False,
            route_aware_blockers.get("secret_values_printed") is False,
        ]
    ):
        print("路线感知阻塞摘要审计未通过")
        return 1
    artifact_manifest = json.loads((ROOT / "runs/submission_artifact_manifest.json").read_text(encoding="utf-8"))
    artifact_inputs = artifact_manifest.get("inputs", {})
    artifact_leaks = artifact_manifest.get("leak_flags", {})
    artifact_contacts = artifact_manifest.get("contact_flags", {})
    artifact_ignored = artifact_manifest.get("ignored_local_secret_or_large_paths", {})
    artifact_items = artifact_manifest.get("artifacts", [])
    if not all(
        [
            artifact_manifest.get("kind") == "submission_artifact_manifest",
            artifact_manifest.get("passed"),
            artifact_manifest.get("artifact_count", 0) >= 30,
            len(artifact_items) == artifact_manifest.get("artifact_count"),
            all(item.get("exists") and len(item.get("sha256", "")) == 64 for item in artifact_items),
            artifact_manifest.get("missing_required_artifacts") == [],
            artifact_manifest.get("unhashed_artifacts") == [],
            artifact_manifest.get("forbidden_tracked_paths") == [],
            all(item.get("ignored") for item in artifact_ignored.values()),
            all(artifact_inputs.values()),
            artifact_manifest.get("platform_contacted") is False,
            artifact_manifest.get("uploads_performed") is False,
            artifact_manifest.get("credentials_read") is False,
            artifact_manifest.get("credentials_printed") is False,
            artifact_manifest.get("link_values_printed") is False,
            artifact_manifest.get("secret_values_printed") is False,
            not any(artifact_leaks.values()),
            not any(artifact_contacts.values()),
        ]
    ):
        print("提交准备材料 manifest 审计未通过")
        return 1
    preflight = json.loads((ROOT / "runs/submission_preflight_bundle.json").read_text(encoding="utf-8"))
    preflight_subcommands = preflight.get("subcommands", {})
    preflight_leaks = preflight.get("leak_flags", {})
    preflight_contacts = preflight.get("contact_flags", {})
    expected_preflight_subcommands = {
        "checkpoint_link_intake",
        "checkpoint_link_download_verification",
        "submission_env_template",
        "notebook_structure",
        "jupyter_input_template",
        "jupyter_authorized_preflight_template",
        "jupyter_final_handoff_template",
        "real_submission_readiness",
        "authorized_preflight_template",
        "ready_real_runner_template",
        "authorized_checkpoint_archive_template",
        "submission_handoff_docs",
        "plaintext_secret_scan",
        "authorized_execution_checklist",
        "next_user_action_packet",
        "web_form_field_packet",
        "submission_variant_route_packet",
        "baseline_submission_quickstart",
        "baseline_dry_run_gate",
        "baseline_credential_hygiene",
        "baseline_local_env_smoke",
        "baseline_final_handoff_packet",
        "baseline_final_handoff_rehearsal",
        "route_aware_submission_blockers",
        "submission_artifact_manifest",
    }
    if not all(
        [
            preflight.get("kind") == "submission_preflight_bundle",
            preflight.get("passed"),
            preflight.get("go_no_go") == "blocked",
            preflight.get("ready_for_real_submission") is False,
            preflight.get("web_form_ready") is False,
            preflight.get("local_baseline_runner_ready") is False,
            preflight.get("local_lora_runner_ready") is False,
            preflight.get("verify_download_requested") is False,
            preflight.get("download_verified") is False,
            preflight.get("link_shape_ready") is False,
            preflight.get("baseline_dry_run_gate_passed") is True,
            preflight.get("baseline_dry_run_gate_command")
            == "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_ready_real_submission_template.sh",
            preflight.get("baseline_dry_run_gate_stops_before_real_runner") is True,
            preflight.get("baseline_credential_hygiene_passed") is True,
            preflight.get("baseline_credential_hygiene_local_env_gitignored") is True,
            preflight.get("baseline_credential_hygiene_local_env_content_read") is False,
            preflight.get("baseline_local_env_smoke_passed") is True,
            preflight.get("baseline_local_env_smoke_authorized_preflight_variant_baseline") is True,
            preflight.get("baseline_local_env_smoke_ready_runner_stops_before_real_runner") is True,
            preflight.get("jupyter_final_handoff_passed") is True,
            preflight.get("jupyter_final_handoff_packet_default_true") is True,
            preflight.get("jupyter_final_handoff_real_runner_default_false") is True,
            preflight.get("jupyter_final_handoff_command_count") == 4,
            preflight.get("jupyter_final_handoff_no_contact_command_count") == 3,
            preflight.get("jupyter_final_handoff_real_runner_requires_confirmation") is True,
            preflight.get("baseline_final_handoff_passed") is True,
            preflight.get("baseline_final_handoff_command_count") == 4,
            preflight.get("baseline_final_handoff_no_contact_command_count") == 3,
            preflight.get("baseline_final_handoff_real_runner_requires_confirmation") is True,
            preflight.get("baseline_final_handoff_no_upload") is True,
            preflight.get("baseline_final_handoff_no_link") is True,
            preflight.get("baseline_final_handoff_does_not_read_local_env") is True,
            preflight.get("baseline_final_handoff_rehearsal_passed") is True,
            preflight.get("baseline_final_handoff_rehearsal_command_count") == 3,
            preflight.get("baseline_final_handoff_rehearsal_ready_runner_stops") is True,
            preflight.get("baseline_final_handoff_rehearsal_no_contact") is True,
            preflight.get("baseline_final_handoff_rehearsal_no_leak") is True,
            preflight.get("secret_scan_hit_count") == 0,
            set(preflight_subcommands) == expected_preflight_subcommands,
            all(item.get("returncode") == 0 and item.get("passed") for item in preflight_subcommands.values()),
            preflight_contacts.get("platform_contacted") is False,
            preflight_contacts.get("uploads_performed") is False,
            preflight_contacts.get("download_host_contacted") is False,
            preflight_leaks.get("credentials_printed") is False,
            preflight_leaks.get("link_values_printed") is False,
            preflight_leaks.get("secret_values_printed") is False,
            len(preflight.get("blocking", [])) >= 4,
        ]
    ):
        print("真实提交前预检汇总未通过")
        return 1
    blockers_summary = json.loads((ROOT / "runs/submission_blockers_summary.json").read_text(encoding="utf-8"))
    blocker_state = blockers_summary.get("current_state", {})
    blocker_local_ready = blockers_summary.get("local_ready", {})
    blocker_leaks = blockers_summary.get("leak_flags", {})
    blocker_contacts = blockers_summary.get("contact_flags", {})
    required_input_ids = {item.get("id") for item in blockers_summary.get("required_user_inputs", [])}
    blocker_baseline_ids = set(blockers_summary.get("baseline_current_blocking", []))
    blocker_lora_web_ids = set(blockers_summary.get("lora_web_current_blocking", []))
    if not all(
        [
            blockers_summary.get("kind") == "submission_blockers_summary",
            blockers_summary.get("passed"),
            blockers_summary.get("platform_contacted") is False,
            blockers_summary.get("uploads_performed") is False,
            blockers_summary.get("credentials_read") is False,
            blockers_summary.get("credentials_printed") is False,
            blockers_summary.get("link_values_printed") is False,
            blockers_summary.get("secret_values_printed") is False,
            blocker_state.get("go_no_go") == "blocked",
            blocker_state.get("ready_for_real_submission") is False,
            blocker_state.get("web_form_ready") is False,
            blocker_state.get("link_shape_ready") is False,
            blocker_state.get("download_verified") is False,
            all(blocker_local_ready.values()),
            blockers_summary.get("recommended_route") == "baseline_official_aloha",
            blockers_summary.get("baseline_requires_checkpoint_link") is False,
            blockers_summary.get("baseline_requires_checkpoint_upload") is False,
            blockers_summary.get("lora_web_requires_checkpoint_link") is True,
            blockers_summary.get("lora_web_requires_checkpoint_upload") is True,
            "ROBOCHALLENGE_CHECKPOINT_LINK" not in blocker_baseline_ids,
            {
                "SUBMISSION_TARGET_CONFIRMATION",
                "ROBOCHALLENGE_USER_TOKEN",
                "ROBOCHALLENGE_SUBMISSION_ID",
                "ROBOCHALLENGE_SUBMISSION_VARIANT=baseline",
                "ROBOCHALLENGE_REAL_RUN_CONFIRM",
            }.issubset(blocker_baseline_ids),
            {
                "SUBMISSION_TARGET_CONFIRMATION",
                "ROBOCHALLENGE_USER_TOKEN",
                "ROBOCHALLENGE_SUBMISSION_ID",
                "ROBOCHALLENGE_SUBMISSION_VARIANT=lora",
                "CHECKPOINT_ARCHIVE_AUTHORIZATION",
                "ROBOCHALLENGE_CHECKPOINT_LINK",
                "ROBOCHALLENGE_REAL_RUN_CONFIRM",
            }.issubset(blocker_lora_web_ids),
            {"ROBOCHALLENGE_USER_TOKEN", "ROBOCHALLENGE_SUBMISSION_ID", "ROBOCHALLENGE_CHECKPOINT_LINK"}.issubset(
                required_input_ids
            ),
            blockers_summary.get("blocking_count", 0) >= 4,
            not any(blocker_leaks.values()),
            not any(blocker_contacts.values()),
            blockers_summary.get("next_command_after_user_inputs") == "python3 scripts/audit_real_submission_readiness.py",
        ]
    ):
        print("真实提交阻塞项摘要未通过")
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
            baseline_runner_audit.get("dry_run_no_contact", {}).get("printed_checkpoint") is False,
            baseline_runner_audit.get("dry_run_no_contact", {}).get("has_checkpoint_length"),
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
            lora_runner_audit.get("dry_run_no_contact", {}).get("printed_checkpoint") is False,
            lora_runner_audit.get("dry_run_no_contact", {}).get("has_checkpoint_length"),
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
    print("Checkpoint 分片上传计划审计已通过")
    print("Checkpoint 归档生成 dry-run 已通过")
    print("Checkpoint link 回填审计已通过")
    print("Checkpoint link 下载校验审计已通过")
    print("用户授权后提交顺序审计已通过")
    print("提交状态 GUI 面板已通过")
    print("Checkpoint 上传通道审计已通过")
    print("真实提交 readiness gate 已通过")
    print("真实提交 readiness 场景 smoke 已通过")
    print("真实提交交接文档审计已通过")
    print("真实提交环境变量模板审计已通过")
    print("Notebook 结构与编码审计已通过")
    print("Jupyter 安全填空本地 env 入口审计已通过")
    print("授权后 Jupyter 预检入口审计已通过")
    print("授权后安全预检模板审计已通过")
    print("强确认真实 runner 模板审计已通过")
    print("授权后 checkpoint 归档模板审计已通过")
    print("授权执行清单审计已通过")
    print("下一步用户动作包审计已通过")
    print("网页表单字段包审计已通过")
    print("提交路线拆分包审计已通过")
    print("baseline 最短提交路径包审计已通过")
    print("路线感知阻塞摘要审计已通过")
    print("提交准备材料 manifest 审计已通过")
    print("真实提交前预检汇总已通过")
    print("真实提交阻塞项摘要已通过")
    print("明文凭据扫描已通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
