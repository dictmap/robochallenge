# 用户授权后的真实提交顺序

本清单只记录用户授权后应执行的顺序，不保存 `user_token`、`submission_id`、checkpoint link 或任何账号凭据。当前自动化只能审计本清单和 dry-run；没有用户明确授权时，不生成 tar、不上传 checkpoint、不连接 RoboChallenge 平台、不启动真实提交 runner。

## 0. 提交前离线自检

```bash
python3 scripts/validate_repro_workspace.py
python3 scripts/audit_plaintext_secrets.py
python3 scripts/audit_submission_env_template.py
python3 scripts/audit_submission_artifact_manifest.py
python3 scripts/create_checkpoint_archive.py
python3 scripts/audit_checkpoint_link_intake.py
python3 scripts/audit_real_submission_readiness.py
python3 scripts/audit_submission_blockers_summary.py
```

预期状态：在没有真实凭据和 checkpoint link 时，`go_no_go=blocked`，`ready_for_real_submission=false`，`link_shape_ready=false`，并且所有审计都不得打印凭据或链接明文。

## 1. 用户授权后生成本地归档

只有用户明确授权生成约 12GB checkpoint tar 时，才执行：

```bash
python3 scripts/create_checkpoint_archive.py --execute --confirm-create-large-archive
```

生成后检查：

```bash
ls -lh runs/openpi_rtc_lora_materialized_policy_checkpoint.tar
cat runs/openpi_rtc_lora_materialized_policy_checkpoint.tar.sha256
```

不要把 `runs/openpi_rtc_lora_materialized_policy_checkpoint.tar`、`.tar.sha256` 或 checkpoint 目录提交进 Git。

## 2. 用户授权后上传 checkpoint

上传通道必须由用户选择并授权。上传完成后，只把可访问 HTTPS 下载链接设置为环境变量，不写入 Git、Notebook、报告或命令历史截图。

```bash
python3 scripts/audit_submission_env_template.py
cp submission/robochallenge_env_template.sh submission/robochallenge_env.local.sh
$EDITOR submission/robochallenge_env.local.sh
source submission/robochallenge_env.local.sh
```

## 3. 用户填入比赛凭据

真实 token、submission id 和 checkpoint link 只写入 `submission/robochallenge_env.local.sh` 本地副本，不写入 tracked 模板、Git、Notebook、报告或命令历史截图：

本地副本需要填入 `ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID` 和 `ROBOCHALLENGE_LORA_CHECKPOINT_LINK`；tracked 模板中这些字段必须保持 `<真实 user token>`、`<真实 submission id>` 和 `<真实 checkpoint 下载 URL>` 这类占位符。

```bash
source submission/robochallenge_env.local.sh
```

## 4. 链接与 readiness gate

```bash
python3 scripts/audit_checkpoint_link_intake.py
python3 scripts/audit_real_submission_readiness.py
```

只有当 link intake 接受真实链接形态，且 readiness gate 显示可进入真实提交时，才继续。

## 5. 真实 runner 前 dry-run

```bash
ROBOCHALLENGE_DRY_RUN=1 bash submission/run_table30v2_aloha_lora_demo_template.sh
```

dry-run 只能打印 checkpoint 长度、prompt 长度、token 长度和 submission id 长度，不打印 token、submission id 或 checkpoint link 明文，也不调用 `demo.py`。

## 6. 真实 LoRA 提交 runner

```bash
bash submission/run_table30v2_aloha_lora_demo_template.sh
```

如果只提交官方 Table30v2 ALOHA baseline，则在 readiness gate 通过后执行：

```bash
bash submission/run_table30v2_aloha_demo_template.sh
```

## 7. 停止条件

- 如果 `python3 scripts/audit_checkpoint_link_intake.py` 显示 `link_shape_ready=false`，停止。
- 如果 `python3 scripts/audit_real_submission_readiness.py` 显示 `ready_for_real_submission=false`，停止。
- 如果 dry-run 泄露凭据、调用 `demo.py` 或未显示预期长度摘要，停止。
- 如果用户没有明确授权生成 tar、上传 checkpoint 或启动真实 runner，停止。
