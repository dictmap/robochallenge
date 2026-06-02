# RoboChallenge 提交包模板

本目录只保存提交准备材料，不保存明文 `user_token`、`submission_id` 或大模型权重。

- `submission/submission_manifest_template.json`：机器可读提交 manifest 模板。
- `submission/run_table30v2_aloha_demo_template.sh`：Table30v2 ALOHA baseline 的 `demo.py` 启动模板。

当前默认可运行提交路线是官方 pi0.5 Table30v2 ALOHA baseline。LoRA scoped checkpoint 已通过恢复/合并审计，但它不是 `demo.py` 可直接消费的完整 checkpoint，不能单独作为 checkpoint 提交。

运行前需要用户在 shell 中提供 `ROBOCHALLENGE_USER_TOKEN` 和 `ROBOCHALLENGE_SUBMISSION_ID` 两个环境变量；不要把具体值写入仓库、Notebook 或报告。设置好之后运行：

```bash
bash submission/run_table30v2_aloha_demo_template.sh
```
