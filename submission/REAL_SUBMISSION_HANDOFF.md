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
python3 scripts/audit_submission_blockers_summary.py
python3 scripts/audit_authorized_preflight_template.py
python3 scripts/audit_ready_real_runner_template.py
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

上传完成后，先复制 tracked 模板到被 Git 忽略的本地副本，再只编辑本地副本。下面命令不会保存真实值到仓库：

tracked 模板只允许保留 `<真实 user token>`、`<真实 submission id>` 和 `<真实 checkpoint 下载 URL>` 占位符；真实值只能进入 `submission/robochallenge_env.local.sh`。

```bash
python3 scripts/audit_submission_env_template.py
cp submission/robochallenge_env_template.sh submission/robochallenge_env.local.sh
$EDITOR submission/robochallenge_env.local.sh
source submission/robochallenge_env.local.sh
```

再次运行 readiness gate：

```bash
python3 scripts/audit_real_submission_readiness.py
```

也可以直接运行授权后安全预检模板。该脚本会 source 本地 env 副本，默认只做离线 link/readiness/blockers 检查；只有 readiness 通过时才执行对应 runner 的 `ROBOCHALLENGE_DRY_RUN=1`，不会启动真实 runner：

```bash
bash submission/run_authorized_preflight_template.sh
```

如果 gate 显示 LoRA runner 已就绪，先做不连接平台的 dry-run。该命令只打印 checkpoint 长度、prompt 长度和凭据长度，不会打印 token、submission id、checkpoint/link 明文，也不会调用 `demo.py`：

```bash
ROBOCHALLENGE_DRY_RUN=1 bash submission/run_table30v2_aloha_lora_demo_template.sh
```

确认 dry-run 输出正常后，推荐只通过强确认入口执行真实 runner。该入口会重新执行 link/download/readiness，并先跑 dry-run；没有确认短语时会停在真实 runner 前：

```bash
ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION bash submission/run_ready_real_submission_template.sh
```

底层 LoRA runner 只作为强确认入口调用的执行模板，不建议手动绕过：

```bash
bash submission/run_table30v2_aloha_lora_demo_template.sh
```

如果只提交官方 Table30v2 ALOHA baseline，则设置 `ROBOCHALLENGE_USER_TOKEN` 和 `ROBOCHALLENGE_SUBMISSION_ID` 后，通过同一个强确认入口并切换 variant：

```bash
ROBOCHALLENGE_SUBMISSION_VARIANT=baseline ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION bash submission/run_ready_real_submission_template.sh
```

底层 baseline runner 只作为强确认入口调用的执行模板：

```bash
bash submission/run_table30v2_aloha_demo_template.sh
```

## 不允许自动完成的事项

- 不要伪造 RoboChallenge token、submission id 或 checkpoint link。
- 不要把真实 token、submission id、checkpoint link 写入 Git、Notebook、报告或命令历史截图。
- 不要在未获得用户授权时上传 checkpoint 或生成公开下载链接。
- 不要把 `runs/openpi_rtc_lora_materialized_policy_checkpoint.tar` 或 checkpoint 目录提交进 Git。
- 如果 `scripts/audit_real_submission_readiness.py` 仍显示 `ready_for_real_submission=false`，就不要启动真实提交 runner。
- 如果没有设置 `ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION`，强确认入口必须停在真实 runner 前。

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

该审计只检查 `ROBOCHALLENGE_CHECKPOINT_LINK` 和 `ROBOCHALLENGE_LORA_CHECKPOINT_LINK` 是否为非占位符 HTTPS 下载链接形态，不联网下载，不连接 RoboChallenge 平台，不打印链接明文。

随后运行默认离线下载校验协议审计：

```bash
python3 scripts/audit_checkpoint_link_download_verification.py
```

真实提交前也可以先生成提交准备材料 manifest，再运行一键预检汇总；manifest 会列出小型交接文件 sha256，并确认本地凭据副本、checkpoint 目录、tar 和分片不会进入 Git：

```bash
python3 scripts/audit_submission_artifact_manifest.py
```

一键预检汇总会串联 link intake、默认下载校验协议、环境变量模板、提交材料 manifest、readiness gate、handoff 文档和明文凭据扫描，不上传、不连接 RoboChallenge 平台、不接触下载 host：

```bash
python3 scripts/audit_submission_preflight_bundle.py
```

该命令默认不联网、不下载、不接触 checkpoint link host，只检查 `curl` 是否可用、HEAD/Range 校验命令是否使用脱敏占位符，以及前置 link intake / split plan 是否通过。

如果用户明确授权联网验证真实 checkpoint link，再运行：

```bash
python3 scripts/audit_checkpoint_link_download_verification.py --verify-download
```

该命令只对 checkpoint link host 做 HEAD 和 1MiB Range smoke，不连接 RoboChallenge 平台，不上传文件，不打印链接明文。下载校验通过后再运行：

```bash
python3 scripts/audit_real_submission_readiness.py
```
