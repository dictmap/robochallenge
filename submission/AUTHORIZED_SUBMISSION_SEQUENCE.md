# 用户授权后的真实提交顺序

本清单只记录用户授权后应执行的顺序，不保存 `user_token`、`submission_id`、checkpoint link 或任何账号凭据。当前自动化只能审计本清单和 dry-run；没有用户明确授权时，不生成 tar、不上传 checkpoint、不连接 RoboChallenge 平台、不启动真实提交 runner。

## 0. 提交前离线自检

```bash
python3 scripts/validate_repro_workspace.py
python3 scripts/audit_plaintext_secrets.py
python3 scripts/audit_submission_env_template.py
python3 scripts/audit_submission_artifact_manifest.py
python3 scripts/create_checkpoint_archive.py
python3 scripts/audit_jupyter_input_template.py
python3 scripts/audit_jupyter_authorized_preflight_template.py
python3 scripts/render_route_aware_submission_blockers.py
python3 scripts/audit_checkpoint_link_intake.py
python3 scripts/audit_real_submission_readiness.py
python3 scripts/audit_submission_blockers_summary.py
python3 scripts/audit_ready_real_runner_template.py
python3 scripts/audit_authorized_checkpoint_archive_template.py
bash submission/run_authorized_checkpoint_archive_template.sh
bash submission/run_authorized_preflight_template.sh
```

预期状态：在没有真实凭据时，`go_no_go=blocked`，`ready_for_real_submission=false`，并且所有审计都不得打印凭据或链接明文。路线感知摘要必须显示 baseline 当前只差提交对象确认 `ROBOCHALLENGE_SUBMISSION_TARGET_CONFIRMATION=CONFIRM_TABLE30V2_ALOHA_BASELINE`、`ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline` 和真实 runner 强确认；baseline 不需要 checkpoint link。LoRA/web checkpoint 路线仍必须显示需要归档/上传授权和真实 checkpoint link。

## 1. 选择提交路线

默认先走官方 Table30v2 ALOHA baseline：

```bash
python3 scripts/render_route_aware_submission_blockers.py
python3 scripts/render_baseline_submission_quickstart.py
```

baseline 路线只需要用户确认提交对象并设置 `ROBOCHALLENGE_SUBMISSION_TARGET_CONFIRMATION=CONFIRM_TABLE30V2_ALOHA_BASELINE`、`ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID`、`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline` 和真实 runner 强确认；不需要生成 tar、不需要上传 checkpoint、不需要 checkpoint link。

只有明确选择 LoRA/web checkpoint 路线时，才继续执行下面的归档、上传和 link 回填步骤。

## 2. 用户授权后生成本地归档

只有用户明确授权生成约 12GB checkpoint tar 时，才设置确认短语执行受控入口。没有确认短语时，该入口必须输出 `stop before creating tar` 并停在生成 tar 前：

```bash
ROBOCHALLENGE_ARCHIVE_CONFIRM=CREATE_ROBOCHALLENGE_CHECKPOINT_ARCHIVE bash submission/run_authorized_checkpoint_archive_template.sh
```

生成后检查：

```bash
ls -lh runs/openpi_rtc_lora_materialized_policy_checkpoint.tar
cat runs/openpi_rtc_lora_materialized_policy_checkpoint.tar.sha256
```

不要把 `runs/openpi_rtc_lora_materialized_policy_checkpoint.tar`、`.tar.sha256` 或 checkpoint 目录提交进 Git。

## 3. 用户授权后上传 checkpoint

上传通道必须由用户选择并授权。上传完成后，只把可访问 HTTPS 下载链接设置为环境变量，不写入 Git、Notebook、报告或命令历史截图。

```bash
python3 scripts/audit_submission_env_template.py
cp submission/robochallenge_env_template.sh submission/robochallenge_env.local.sh
$EDITOR submission/robochallenge_env.local.sh
source submission/robochallenge_env.local.sh
```

## 4. 用户填入比赛凭据

真实 token、submission id、目标确认和 LoRA/web checkpoint link 只写入 `submission/robochallenge_env.local.sh` 本地副本，不写入 tracked 模板、Git、Notebook、报告或命令历史截图：

baseline 本地副本需要填入 `ROBOCHALLENGE_SUBMISSION_TARGET_CONFIRMATION=CONFIRM_TABLE30V2_ALOHA_BASELINE`、`ROBOCHALLENGE_USER_TOKEN`、`ROBOCHALLENGE_SUBMISSION_ID` 和 `ROBOCHALLENGE_SUBMISSION_VARIANT=baseline`；`ROBOCHALLENGE_CHECKPOINT_LINK` 可以留空。LoRA/web checkpoint 路线额外需要填入 `ROBOCHALLENGE_LORA_CHECKPOINT_LINK` 或 `ROBOCHALLENGE_CHECKPOINT_LINK`。tracked 模板中这些字段必须保持 `<真实 user token>`、`<真实 submission id>` 和 `<真实 checkpoint 下载 URL>` 这类占位符。

Jupyter 路线优先使用 `notebooks/robochallenge_pi05_submit_cn.ipynb`。第 44 节默认 `RUN_SAFE_LOCAL_ENV_INPUT_TEMPLATE=False`，只有用户确认填入真实值和目标确认时才改为 `RUN_SAFE_LOCAL_ENV_INPUT_TEMPLATE=True`；该节使用 `getpass` 写入 `submission/robochallenge_env.local.sh`，本地副本已被 Git 忽略。真实值只能进入这个本地副本；`CONFIRM_TABLE30V2_ALOHA_BASELINE` 目标确认也只写入这个本地副本，不写入 tracked 模板、Git、Notebook、报告或命令历史截图。

```bash
source submission/robochallenge_env.local.sh
```

## 5. 链接与 readiness gate

```bash
python3 scripts/render_route_aware_submission_blockers.py
python3 scripts/audit_checkpoint_link_intake.py
python3 scripts/audit_real_submission_readiness.py
bash submission/run_authorized_preflight_template.sh
```

Jupyter 路线可继续运行第 45 节。该节默认 `RUN_JUPYTER_AUTHORIZED_PREFLIGHT_TEMPLATE_AUDIT=True` 且 `RUN_JUPYTER_AUTHORIZED_PREFLIGHT=False`，默认只执行静态审计；确认第 44 节已经写入 local env 后，才把开关改为 `RUN_JUPYTER_AUTHORIZED_PREFLIGHT=True`，实际预检仍只调用 `bash submission/run_authorized_preflight_template.sh`。

baseline 路线以 `render_route_aware_submission_blockers.py` 和 `run_authorized_preflight_template.sh` 为准，不因为缺少 checkpoint link 而进入 LoRA 上传流程。LoRA/web checkpoint 路线只有当 link intake 接受真实链接形态，且 readiness gate 显示可进入真实提交时，才继续。

## 6. 真实 runner 前 dry-run

```bash
ROBOCHALLENGE_DRY_RUN=1 bash submission/run_table30v2_aloha_lora_demo_template.sh
```

dry-run 只能打印 checkpoint 长度、prompt 长度、token 长度和 submission id 长度，不打印 token、submission id 或 checkpoint link 明文，也不调用 `demo.py`。

baseline dry-run 优先通过强确认入口自动执行：

```bash
ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_ready_real_submission_template.sh
```

没有真实确认短语时，该入口必须停在真实 runner 前。

## 7. 真实 LoRA 或 baseline 提交 runner

推荐只通过强确认入口启动真实 runner。该入口会重新执行 link/download/readiness，并先跑 dry-run；没有确认短语时会停在真实 runner 前：

```bash
ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION bash submission/run_ready_real_submission_template.sh
```

底层 LoRA runner 只作为强确认入口调用的执行模板，不建议手动绕过：

```bash
bash submission/run_table30v2_aloha_lora_demo_template.sh
```

如果只提交官方 Table30v2 ALOHA baseline，则先切换 variant 后使用同一个强确认入口：

```bash
ROBOCHALLENGE_SUBMISSION_VARIANT=baseline ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION bash submission/run_ready_real_submission_template.sh
```

底层 baseline runner 只作为强确认入口调用的执行模板：

```bash
bash submission/run_table30v2_aloha_demo_template.sh
```

## 8. 停止条件

- 如果 baseline 路线的 `python3 scripts/render_route_aware_submission_blockers.py` 仍显示缺少目标确认、token、submission id、variant 或真实 runner 强确认，停止。
- 如果 LoRA/web checkpoint 路线的 `python3 scripts/audit_checkpoint_link_intake.py` 显示 `link_shape_ready=false`，停止。
- 如果 `python3 scripts/audit_real_submission_readiness.py` 显示 `ready_for_real_submission=false`，停止。
- 如果 dry-run 泄露凭据、调用 `demo.py` 或未显示预期长度摘要，停止。
- 如果用户没有明确授权生成 tar、上传 checkpoint 或启动真实 runner，停止。
