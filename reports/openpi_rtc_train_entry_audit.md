# openpi_rtc 训练入口审计

## 结论

- 本轮状态：`passed=True`。
- `openpi/scripts/train.py` 绑定的是标准 `openpi.training.*`，不能直接当作 RoboChallenge 的 `openpi_rtc` 训练入口。
- baseline 中现成 `train_rtc.py`：`exists=False`。
- 已用本地 Table30v2 ALOHA 短分片完成 `openpi_rtc` dataloader preflight。
- 已完成抽象 `train_step` 前向 loss 与反向梯度 shape smoke。

## 源码审计

- 训练候选脚本：`['train.py', 'train_pytorch.py', 'train_test.py']`。
- 标准训练脚本使用 `openpi.training`：`True`。
- 标准训练脚本使用 `openpi_rtc.training`：`False`。
- `openpi_rtc` weight loader 仍引用标准 `openpi.models.model`：`True`。
- `compute_loss` 支持 4 维 multi-offset actions：`True`。

## 数据入口

- config：`cvpr_multitask_aloha_rtc`。
- repo_id：`robochallenge_table30v2_aloha_short`。
- model/action_dim/action_horizon：`ModelType.PI05` / `32` / `50`。
- random_action_offset：`True`，copies=`5`，max=`15`。
- state shape：`[1, 5, 32]`。
- actions shape：`[1, 5, 50, 32]`。
- tokenized prompt shape：`[1, 5, 200]`。
- image keys：`['base_0_rgb', 'left_wrist_0_rgb', 'right_wrist_0_rgb']`。

## 边界

- 本轮验证的是训练图和维度闭合，不代表已经完成真实数值训练。
- 本轮没有加载 `pi05_base` 的 12GB 级权重，也没有写真实训练 checkpoint。
- 下一步应把这个 shape smoke 固化成最小 `openpi_rtc` 训练脚本，再在 GPU 上做真实 1-step loss/grad/checkpoint dry-run。
