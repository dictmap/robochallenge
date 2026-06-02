# RoboChallenge 真实提交交接清单

本文件只记录真实提交前的可执行步骤，不保存明文 `user_token`、`submission_id`、私有下载链接或任何账号凭据。

## 当前已具备的本地材料

- pi0.5 基模缓存和参数读取 smoke 已通过。
- Table30v2 ALOHA baseline runner 已生成：`submission/run_table30v2_aloha_demo_template.sh`。
- LoRA 完整物化 checkpoint 已生成并通过 policy 加载 smoke：`runs/openpi_rtc_lora_materialized_policy_checkpoint`。
- LoRA checkpoint 导出结构已通过 tar stream smoke，但还没有生成真实 tar 文件。
- 上传通道审计只确认本机工具和凭据迹象，不会执行上传。
- 真实提交 readiness gate 已能准确报告缺失的凭据和 checkpoint link。

## 用户拿到凭据后的最短流程

完整顺序清单见 `submission/AUTHORIZED_SUBMISSION_SEQUENCE.md`。修改清单后先运行：

```bash
python3 scripts/audit_authorized_submission_sequence.py
```

先在 Linux 仓库根目录执行：

```bash
python3 scripts/audit_real_submission_readiness.py
```

如果走 LoRA checkpoint 提交路线，必须先由用户确认上传通道和存储位置，然后再打包本地物化 checkpoint：

```bash
tar -C runs -cf runs/openpi_rtc_lora_materialized_policy_checkpoint.tar openpi_rtc_lora_materialized_policy_checkpoint
sha256sum runs/openpi_rtc_lora_materialized_policy_checkpoint.tar > runs/openpi_rtc_lora_materialized_policy_checkpoint.tar.sha256
```

上传完成后，在当前 shell 中设置真实环境变量。下面的尖括号是占位说明，不能原样提交，也不要写入仓库：

```bash
export ROBOCHALLENGE_USER_TOKEN="<真实 user token>"
export ROBOCHALLENGE_SUBMISSION_ID="<真实 submission id>"
export ROBOCHALLENGE_LORA_CHECKPOINT_LINK="<真实 checkpoint 下载 URL>"
```

再次运行 readiness gate：

```bash
python3 scripts/audit_real_submission_readiness.py
```

如果 gate 显示 LoRA runner 已就绪，先做不连接平台的 dry-run。该命令只打印 checkpoint、prompt 长度和凭据长度，不会打印 token 或 submission id 明文，也不会调用 `demo.py`：

```bash
ROBOCHALLENGE_DRY_RUN=1 bash submission/run_table30v2_aloha_lora_demo_template.sh
```

确认 dry-run 输出正常后，再执行：

```bash
bash submission/run_table30v2_aloha_lora_demo_template.sh
```

如果只提交官方 Table30v2 ALOHA baseline，则设置 `ROBOCHALLENGE_USER_TOKEN` 和 `ROBOCHALLENGE_SUBMISSION_ID` 后执行：

```bash
bash submission/run_table30v2_aloha_demo_template.sh
```

## 不允许自动完成的事项

- 不要伪造 RoboChallenge token、submission id 或 checkpoint link。
- 不要把真实 token、submission id、checkpoint link 写入 Git、Notebook、报告或命令历史截图。
- 不要在未获得用户授权时上传 checkpoint 或生成公开下载链接。
- 不要把 `runs/openpi_rtc_lora_materialized_policy_checkpoint.tar` 或 checkpoint 目录提交进 Git。
- 如果 `scripts/audit_real_submission_readiness.py` 仍显示 `ready_for_real_submission=false`，就不要启动真实提交 runner。

## Web 表单填写边界

- benchmark：当前可复现链路是 `Table30v2`。
- robot type：当前 runner 使用 `aloha`。
- task：当前已验证任务是 `pack_the_toothbrush_holder`。
- inference code：建议填写当前 GitHub 仓库主分支链接。
- checkpoint link：必须由用户授权上传后填写真实可访问链接。
- fine-tuning / restore evidence：使用仓库内 Notebook、reports 和 scripts 作为证据，不上传明文凭据。

## Checkpoint Link 回填前检查

拿到真实 checkpoint 下载链接后，先在当前 shell 中设置链接环境变量，再运行离线形态审计：

```bash
python3 scripts/audit_checkpoint_link_intake.py
```

该审计只检查 `ROBOCHALLENGE_CHECKPOINT_LINK` 和 `ROBOCHALLENGE_LORA_CHECKPOINT_LINK` 是否为非占位符 HTTPS 下载链接形态，不联网下载，不连接 RoboChallenge 平台，不打印链接明文。审计通过后再运行：

```bash
python3 scripts/audit_real_submission_readiness.py
```
