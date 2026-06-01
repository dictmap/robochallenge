# openpi_rtc LoRA checkpoint 恢复/合并审计

## 结论

- 审计状态：`passed=True`。
- 基础权重：`/home/yjl/.cache/openpi/openpi-assets/checkpoints/pi05_base/params`。
- scoped checkpoint：`runs/openpi_rtc_lora_grad_checkpoint/trainable_params_step1.npz`。
- checkpoint 范围：`cfg.trainable_filter`，不是完整 policy checkpoint。
- 恢复方式：先加载 `pi05_base` 到 LoRA 参数树，再用 scoped trainable params 覆盖对应 leaf。

## 关键证据

- LoRA 模型 leaf 数：`73`。
- `pi05_base` 合并后 leaf 数：`73`。
- scoped checkpoint key 数：`53`。
- `cfg.trainable_filter` key 数：`53`。
- checkpoint 中 LoRA key 数：`20`。
- checkpoint 中 `knob_*` key 数：`2`。
- 合并前 `ShapeDtypeStruct` 占位 leaf：`22`。
- scoped 覆盖 leaf：`53`。
- 合并后剩余 `ShapeDtypeStruct` 占位 leaf：`0`。
- 参数树 shape/dtype 校验：`True`。
- NNX state 恢复 smoke：`True`。

## 边界

- 这个 scoped checkpoint 只能和相同 config、相同 LoRA variant、相同 `pi05_base` 一起恢复。
- 本轮只验证恢复/合并链路，没有声明策略质量，也没有完成 RoboChallenge 真实提交。
- 真实提交仍需要网站 `user_token` 和 `submission_id`，不能伪造。
