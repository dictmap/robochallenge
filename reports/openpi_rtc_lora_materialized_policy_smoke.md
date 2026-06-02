# openpi_rtc LoRA 完整物化 policy 加载 smoke

## 结论

- smoke 状态：`passed=True`。
- checkpoint：`runs/openpi_rtc_lora_materialized_policy_checkpoint`。
- `create_trained_policy` 加载：`passed=True`。
- policy 类型：`Policy`；模型类型：`Pi0`。
- 加载耗时：`4.641` 秒。

## checkpoint 结构

- `params/_METADATA`：`True`。
- `params/manifest.ocdbt`：`True`。
- `assets/cvpr_multitask_aloha/norm_stats.json`：`True`。

## 边界

- 本 smoke 只验证 `create_trained_policy` 能构建 policy，不执行真实 RoboChallenge 提交。
- 本 smoke 不评价策略质量；此前 LoRA reduced 训练只证明链路可跑通。
- 真实提交仍需要用户提供 `ROBOCHALLENGE_USER_TOKEN` 和 `ROBOCHALLENGE_SUBMISSION_ID`。
