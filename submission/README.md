# RoboChallenge 提交包模板

本目录只保存提交准备材料，不保存明文 `user_token`、`submission_id` 或大模型权重。

- `submission/submission_manifest_template.json`：机器可读提交 manifest 模板。
- `submission/run_table30v2_aloha_demo_template.sh`：Table30v2 ALOHA baseline 的 `demo.py` 启动模板。
- `submission/run_table30v2_aloha_lora_demo_template.sh`：Table30v2 ALOHA LoRA 完整物化 checkpoint 的 `demo.py` 启动模板。
- `submission/REAL_SUBMISSION_HANDOFF.md`：用户拿到 token 和 submission id 后的真实提交交接清单；baseline 路线不需要 checkpoint link，LoRA/web checkpoint 路线才需要 link。

当前默认稳妥提交路线仍是官方 pi0.5 Table30v2 ALOHA baseline。该路线使用 Linux 上已有的官方 ALOHA checkpoint，本地 runner 不需要生成 LoRA tar，也不需要 checkpoint link。LoRA scoped checkpoint 已被物化为本地完整 checkpoint，并通过 `create_trained_policy` 加载 smoke；只有选择 LoRA/web checkpoint 路线时，才需要用户提供凭据并把本地 checkpoint 上传成网站可访问链接。

运行前需要用户在 shell 中提供 `ROBOCHALLENGE_USER_TOKEN` 和 `ROBOCHALLENGE_SUBMISSION_ID` 两个环境变量；不要把具体值写入仓库、Notebook 或报告。runner 会拒绝 `<真实 ...>`、`example`、`replace_me` 这类占位符。可以先设置 `ROBOCHALLENGE_DRY_RUN=1` 做不连接平台的本地命令摘要检查，输出不会包含 token、submission id 或 checkpoint/link 明文。设置好之后运行：

```bash
bash submission/run_table30v2_aloha_demo_template.sh
# 或本地 LoRA 物化 checkpoint 路线：
bash submission/run_table30v2_aloha_lora_demo_template.sh
```
