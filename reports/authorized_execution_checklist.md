# 授权执行清单审计

## 结论

- 审计状态：`passed=True`。
- go/no-go：`blocked_by_user_inputs`。
- 当前可运行目标：`Table30v2 ALOHA`。
- 真实提交就绪：`False`。
- 推荐路线：`baseline_official_aloha`。
- baseline 是否需要 checkpoint link：`False`。
- baseline 是否需要 checkpoint upload：`False`。
- LoRA/web 是否需要 checkpoint link：`True`。
- LoRA/web 是否需要 checkpoint upload：`True`。
- 是否连接平台：`False`。
- 是否上传：`False`。
- 是否读取真实凭据：`False`。

## Baseline 最短路线需要用户确认或提供

- `SUBMISSION_TARGET_CONFIRMATION`：需要用户确认提交 Table30v2 ALOHA；原始 Table30 还不能直接沿用当前链路。
- `ROBOCHALLENGE_USER_TOKEN`：只能放入本地 shell 或被 Git 忽略的 local env 文件，不能写入 tracked 文件。
- `ROBOCHALLENGE_SUBMISSION_ID`：必须来自 RoboChallenge 页面，不能伪造。
- `ROBOCHALLENGE_SUBMISSION_VARIANT=baseline`：默认先走 baseline_official_aloha；baseline 不需要 checkpoint link 或 checkpoint upload。
- `ROBOCHALLENGE_REAL_RUN_CONFIRM`：启动真实 runner 前必须显式设置真实提交确认短语。

## LoRA/web checkpoint 分支额外需要

- `SUBMISSION_TARGET_CONFIRMATION`：需要用户确认提交 Table30v2 ALOHA；原始 Table30 还不能直接沿用当前链路。
- `ROBOCHALLENGE_USER_TOKEN`：只能放入本地 shell 或被 Git 忽略的 local env 文件，不能写入 tracked 文件。
- `ROBOCHALLENGE_SUBMISSION_ID`：必须来自 RoboChallenge 页面，不能伪造。
- `ROBOCHALLENGE_SUBMISSION_VARIANT=lora`：只有用户明确选择 LoRA/web checkpoint 路线时才需要。
- `CHECKPOINT_ARCHIVE_AUTHORIZATION`：生成 11GB+ tar 前必须显式设置归档确认短语。
- `ROBOCHALLENGE_CHECKPOINT_LINK`：LoRA/web checkpoint 提交需要可访问 checkpoint link；默认只做脱敏形态检查。
- `ROBOCHALLENGE_REAL_RUN_CONFIRM`：启动真实 runner 前必须显式设置真实提交确认短语。

## 授权后执行顺序

1. Jupyter 安全填空本地 env：`Notebook 第 44 节：RUN_SAFE_LOCAL_ENV_INPUT_TEMPLATE=True`
   - 边界：只写入被 Git 忽略的 submission/robochallenge_env.local.sh；不把真实 token/link 写入 Notebook 源码或 tracked 文件。
2. 填写本地 env：`cp submission/robochallenge_env_template.sh submission/robochallenge_env.local.sh`
   - 边界：只编辑被 Git 忽略的 local env 文件；不把真实 token 写入 tracked 文件。
3. 加载本地 env：`source submission/robochallenge_env.local.sh`
   - 边界：shell 中加载，不打印变量值。
4. Jupyter 授权预检：`Notebook 第 45 节：RUN_JUPYTER_AUTHORIZED_PREFLIGHT=True`
   - 边界：只运行授权预检模板；不生成 tar、不上传、不启动真实 runner。
5. 只读预检：`bash submission/run_authorized_preflight_template.sh`
   - 边界：如果 ready_for_real_submission=false，必须停止。
6. 可选下载校验：`python3 scripts/audit_checkpoint_link_download_verification.py --verify-download`
   - 边界：只有用户明确允许联网验证 checkpoint link 时才运行。
7. 可选 checkpoint 归档：`ROBOCHALLENGE_ARCHIVE_CONFIRM=CREATE_ROBOCHALLENGE_CHECKPOINT_ARCHIVE bash submission/run_authorized_checkpoint_archive_template.sh`
   - 边界：只有用户明确授权生成 11GB+ tar 时才运行。
8. 真实 runner 强确认：`ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION bash submission/run_ready_real_submission_template.sh`
   - 边界：只有 readiness、dry-run 和确认短语全部通过后才会进入真实 runner。

## Baseline 必须停止的情况

- 未确认提交对象是 Table30v2 ALOHA。
- 缺少 ROBOCHALLENGE_USER_TOKEN。
- 缺少 ROBOCHALLENGE_SUBMISSION_ID。
- ready_for_real_submission=false。
- 未设置 ROBOCHALLENGE_REAL_RUN_CONFIRM 但试图启动真实 runner。

## LoRA/web checkpoint 分支必须停止的情况

- 未确认提交对象是 Table30v2 ALOHA。
- 缺少 ROBOCHALLENGE_USER_TOKEN。
- 缺少 ROBOCHALLENGE_SUBMISSION_ID。
- 缺少真实 checkpoint link。
- link_shape_ready=false。
- 未设置 ROBOCHALLENGE_ARCHIVE_CONFIRM 但试图生成 checkpoint tar。
- 未设置 ROBOCHALLENGE_REAL_RUN_CONFIRM 但试图启动真实 runner。

## 本地证据

- `preflight_bundle_passed`：`False`。
- `preflight_go_no_go_blocked`：`True`。
- `blockers_summary_passed`：`False`。
- `blockers_summary_go_no_go_blocked`：`True`。
- `readiness_gate_passed`：`True`。
- `readiness_currently_false`：`True`。
- `web_form_currently_false`：`True`。
- `token_missing_as_expected`：`True`。
- `submission_id_missing_as_expected`：`True`。
- `checkpoint_link_missing_as_expected`：`True`。
- `env_template_passed`：`True`。
- `local_env_ignored`：`True`。
- `jupyter_input_template_passed`：`True`。
- `jupyter_local_env_ignored`：`True`。
- `jupyter_authorized_preflight_template_passed`：`True`。
- `jupyter_authorized_preflight_default_off`：`True`。
- `authorized_preflight_template_passed`：`True`。
- `ready_real_runner_template_passed`：`True`。
- `real_runner_confirmation_phrase`：`True`。
- `real_runner_no_confirm_blocks`：`True`。
- `authorized_archive_template_passed`：`True`。
- `archive_confirmation_phrase`：`True`。
- `archive_no_confirm_blocks`：`True`。
- `archive_not_created_without_confirm`：`True`。
- `authorized_sequence_passed`：`True`。
- `route_packet_passed`：`True`。
- `route_packet_recommends_baseline`：`True`。
- `baseline_quickstart_passed`：`True`。
- `baseline_quickstart_no_link`：`True`。
- `baseline_quickstart_no_upload`：`True`。
- `notebook_structure_passed`：`True`。
- `secret_scan_clean`：`True`。

## 当前阻塞项

- SUBMISSION_TARGET_CONFIRMATION
- ROBOCHALLENGE_USER_TOKEN
- ROBOCHALLENGE_SUBMISSION_ID
- ROBOCHALLENGE_SUBMISSION_VARIANT=baseline
- ROBOCHALLENGE_REAL_RUN_CONFIRM
