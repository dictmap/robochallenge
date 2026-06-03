# 官方 ALOHA baseline 最短提交路径

## 结论

- 审计状态：`passed=True`。
- 推荐路线：`baseline_official_aloha`。
- 目标确认值：`CONFIRM_TABLE30V2_ALOHA_BASELINE`。
- 是否要求手动输入目标确认：`True`。
- 是否要求精确匹配目标确认：`True`。
- 是否需要 checkpoint upload：`False`。
- 是否需要 checkpoint link：`False`。

## 用户需要补齐

- `SUBMISSION_TARGET_CONFIRMATION`：确认提交对象是 Table30v2 ALOHA baseline，不是原始 Table30，也不是 LoRA 网页 checkpoint 路线。
- `ROBOCHALLENGE_USER_TOKEN`：从 RoboChallenge 页面获得，只写入本地 shell 或被 Git 忽略的 local env。
- `ROBOCHALLENGE_SUBMISSION_ID`：从 RoboChallenge 提交页面获得，不能伪造。
- `ROBOCHALLENGE_SUBMISSION_VARIANT=baseline`：当前 wrapper 已默认 baseline；显式设置可避免误走 LoRA。
- `ROBOCHALLENGE_REAL_RUN_CONFIRM`：只有用户确认启动真实 runner 后，才设置 RUN_REAL_ROBOCHALLENGE_SUBMISSION。

## 最短命令顺序

1. 写入本地 env：`Notebook 第 44 节：RUN_SAFE_LOCAL_ENV_INPUT_TEMPLATE=True；确认值填 CONFIRM_TABLE30V2_ALOHA_BASELINE；variant 填 baseline。`
   - 边界：只写 submission/robochallenge_env.local.sh；不把真实值写入 Notebook 源码或 tracked 文件。
2. 授权前只读预检：`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_authorized_preflight_template.sh`
   - 边界：只读检查；ready=false 时停止。
3. baseline wrapper dry-run gate：`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_ready_real_submission_template.sh`
   - 边界：未设置真实确认短语时，最多跑 baseline dry-run，然后停在真实 runner 前。
4. 真实 runner 强确认：`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION bash submission/run_ready_real_submission_template.sh`
   - 边界：只有用户明确授权真实提交时运行；该命令会启动 demo.py 并连接 RoboChallenge。

## 只读边界

- `platform_contacted`：`False`。
- `uploads_performed`：`False`。
- `download_host_contacted`：`False`。
- `credentials_printed`：`False`。
- `link_values_printed`：`False`。
- `secret_values_printed`：`False`。

## 输入证据

- `route_packet_passed`：`True`。
- `baseline_is_recommended_default`：`True`。
- `baseline_route_ready_without_credentials`：`True`。
- `baseline_checkpoint_ready`：`True`。
- `baseline_does_not_need_upload`：`True`。
- `baseline_does_not_need_checkpoint_link`：`True`。
- `ready_runner_template_passed`：`True`。
- `ready_runner_default_baseline`：`True`。
- `target_confirmation_packet_passed`：`True`。
- `target_confirmation_value_exact`：`True`。
- `jupyter_input_requires_manual_target_confirmation`：`True`。
- `jupyter_input_requires_exact_target_confirmation`：`True`。
- `synthetic_baseline_no_confirm_dry_run`：`True`。
- `package_audit_passed`：`True`。
- `readiness_gate_passed`：`True`。
- `secret_scan_clean`：`True`。

## Blocking

- baseline 最短路径已固化；真实提交仍等待用户目标确认、token、submission id、variant=baseline 和真实 runner 强确认。
