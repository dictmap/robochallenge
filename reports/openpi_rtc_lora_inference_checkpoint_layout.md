# openpi_rtc LoRA 推理 checkpoint 物化审计

## 结论

- 审计状态：`passed=True`。
- 当前是否已有 `demo.py --checkpoint` 可直接消费的 LoRA 完整 checkpoint：`False`。
- 当前默认只完成目录形态、源材料和 tiny Orbax 写入/读取 smoke；没有自动写出 12GB+ 完整权重目录。
- 如需物化完整 checkpoint，需要显式运行 `python3 scripts/audit_openpi_rtc_lora_inference_checkpoint_layout.py --materialize --force`。

## 已确认的推理 checkpoint 目录形态

- `create_trained_policy` 对 JAX/NNX checkpoint 的读取路径是 `<checkpoint>/params`。
- `<checkpoint>/params` 需要是 Orbax PyTree checkpoint，顶层 item 形态为 `{"params": full_params}`。
- norm stats 需要放在 `<checkpoint>/assets/cvpr_multitask_aloha/norm_stats.json`。
- tiny 保存/读取 smoke：`passed=True`，目录 `runs/openpi_rtc_lora_checkpoint_layout_smoke`。

## 源材料

- `pi05_base` params：`/home/yjl/.cache/openpi/openpi-assets/checkpoints/pi05_base`，`_METADATA=True`。
- 官方 ALOHA checkpoint：`/home/yjl/yjl/RoboChallenge/checkpoints/table30v2_multitask_baseline_aloha`，norm stats 存在：`True`。
- LoRA scoped checkpoint：`runs/openpi_rtc_lora_grad_checkpoint/trainable_params_step1.npz`，leaf 数：`53`。
- restore/merge 审计：`passed=True`，合并后占位 leaf：`0`。

## 目标目录

- 目标目录：`runs/openpi_rtc_lora_materialized_policy_checkpoint`。
- Git ignore：`ignored=True`，规则：`.gitignore:20:runs/*checkpoint*/	runs/openpi_rtc_lora_materialized_policy_checkpoint/params/_METADATA`。
- 物化执行：`attempted=False`，`passed=None`。

## 边界

- 本轮没有声明 LoRA 策略质量提升；已有 loss/grad smoke 只说明链路能跑通。
- 未提供 RoboChallenge `user_token` 和 `submission_id` 前，不会运行真实提交。
- 如果后续选择 `--materialize`，生成的大 checkpoint 必须留在 ignored 目录，不能提交到 Git。
