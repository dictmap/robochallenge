# openpi_rtc 数值训练 dry-run

## 结论

- 本轮模式：`lora_grad`。
- 本轮状态：`passed=True`。
- 使用权重：`/home/yjl/.cache/openpi/openpi-assets/checkpoints/pi05_base/params`。
- 模型变体：`gemma_2b_lora` + `gemma_300m_lora`。
- GPU 状态：`NVIDIA GeForce RTX 4090, 24564 MiB, 2514 MiB, 21568 MiB`。

## 已验证

- dataloader state shape：`[1, 32]`。
- dataloader actions shape：`[1, 10, 32]`。
- tokenized prompt shape：`[1, 64]`。
- 权重结构校验：`passed=True`。
- 权重加载耗时：`6.061` 秒。
- 权重 leaf 数：`73`。
- 可实际注入的 partial params leaf 数：`51`。
- 已过滤 `ShapeDtypeStruct` leaf 数：`22`。
- 权重元素数：`3403422481`。
- 权重 dtype 分布：`{'float32': 53, 'bfloat16': 20}`。

## LoRA 反向

- 结果：`{'passed': True, 'loss': 0.0, 'grad_norm': 0.0, 'seconds': 59.893, 'checkpoint_dir': 'runs/openpi_rtc_lora_grad_checkpoint', 'checkpoint_npz': 'runs/openpi_rtc_lora_grad_checkpoint/trainable_params_step1.npz', 'checkpoint_metadata': 'runs/openpi_rtc_lora_grad_checkpoint/metadata.json', 'trainable_param_summary': {'leaf_count': 53, 'total_elements': 466958097, 'dtype_counts': {'bfloat16': 31, 'float32': 22}, 'sample_leaves': [{'shape': [1152], 'dtype': 'bfloat16'}, {'shape': [1152], 'dtype': 'bfloat16'}, {'shape': [27, 1152], 'dtype': 'bfloat16'}, {'shape': [27, 1152], 'dtype': 'bfloat16'}, {'shape': [27, 1152], 'dtype': 'bfloat16'}, {'shape': [27, 1152], 'dtype': 'bfloat16'}, {'shape': [27, 4304], 'dtype': 'bfloat16'}, {'shape': [27, 1152, 4304], 'dtype': 'bfloat16'}, {'shape': [27, 1152], 'dtype': 'bfloat16'}, {'shape': [27, 4304, 1152], 'dtype': 'bfloat16'}, {'shape': [27, 16, 72], 'dtype': 'bfloat16'}, {'shape': [27, 1152, 16, 72], 'dtype': 'bfloat16'}, {'shape': [27, 1152], 'dtype': 'bfloat16'}, {'shape': [27, 16, 72, 1152], 'dtype': 'bfloat16'}, {'shape': [27, 16, 72], 'dtype': 'bfloat16'}, {'shape': [27, 1152, 16, 72], 'dtype': 'bfloat16'}]}}`。
- 该 checkpoint 只包含 `config.trainable_filter` 选中的 scoped trainable params，不是完整 OpenPI 发布 checkpoint。

## 边界

- `weight_preflight` 只证明 `openpi_rtc` 参数结构能接上 `pi05_base` 权重，不代表已经完成训练。
- `forward` 才代表真实数值 loss 前向；`grad` 才代表真实反向梯度。
- `head_grad` 是冻结大模型、只更新小头部参数的低显存 dry-run，用于验证反向和 checkpoint 写出链路。
- `lora_grad` 使用 `config.trainable_filter`，用于验证 LoRA/非冻结参数的反向和 scoped checkpoint 写出链路。
- 全量 `grad` 可能超过 24GB 显存；失败时应优先改成 LoRA/冻结层 dry-run，而不是假装完成。
