# openpi_rtc LoRA 低显存路线审计

## 结论

- 审计状态：`passed=True`。
- 基础配置：`cvpr_multitask_aloha_rtc`。
- LoRA 变体：`gemma_2b_lora` + `gemma_300m_lora`。
- `pi05` 标志保持：`True`。
- 本轮只做配置、参数树和权重合并预检，没有跑真实 forward/grad，也没有写训练 checkpoint。

## 参数规模

- 总参数 leaf：`73`，元素数：`3403422481`。
- LoRA leaf：`20`，元素数：`49987584`。
- 冻结 leaf：`20`，元素数：`2936464384`。
- 可训练 leaf：`53`，元素数：`466958097`。

## 权重合并

- `pi05_base` 路径：`/home/yjl/.cache/openpi/openpi-assets/checkpoints/pi05_base/params`。
- 合并校验：`passed=True`。
- 加载并合并耗时：`3.848` 秒。
- 合并后 leaf：`73`。
- 从模型初始化补入的 LoRA leaf：`20`。
- 从模型初始化补入的 knob leaf：`2`。

## 边界

- LoRA 路线能接上 `pi05_base` 权重，不等于已经完成数值训练。
- 当前真实 `forward/head_grad/full grad` 仍受 GPU 显存与 XLA 执行阻塞影响。
- 下一步若不释放 GPU，需要把 LoRA 路线接入数值 dry-run，并优先尝试更短序列、CPU/offload 或分布式训练。
