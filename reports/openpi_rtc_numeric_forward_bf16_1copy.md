# openpi_rtc 数值训练 dry-run

## 结论

- 本轮模式：`forward`。
- 本轮状态：`passed=False`。
- 使用权重：`/home/yjl/.cache/openpi/openpi-assets/checkpoints/pi05_base/params`。
- GPU 状态：`NVIDIA GeForce RTX 4090, 24564 MiB, 5595 MiB, 18487 MiB`。

## 已验证

- dataloader state shape：`[1, 32]`。
- dataloader actions shape：`[1, 50, 32]`。
- tokenized prompt shape：`[1, 200]`。
- 权重结构校验：`passed=True`。
- 权重加载耗时：`4.221` 秒。
- 权重 leaf 数：`53`。
- 可实际注入的 partial params leaf 数：`51`。
- 已过滤 `ShapeDtypeStruct` leaf 数：`2`。
- 权重元素数：`3353434897`。
- 权重 dtype 分布：`{'float32': 53}`。

## 错误

- 类型：`XlaRuntimeError`。
- 信息：`RESOURCE_EXHAUSTED: Failed to get module function: CUDA_ERROR_OUT_OF_MEMORY: out of memory`。

## 边界

- `weight_preflight` 只证明 `openpi_rtc` 参数结构能接上 `pi05_base` 权重，不代表已经完成训练。
- `forward` 才代表真实数值 loss 前向；`grad` 才代表真实反向梯度。
- 全量 `grad` 可能超过 24GB 显存；失败时应优先改成 LoRA/冻结层 dry-run，而不是假装完成。
