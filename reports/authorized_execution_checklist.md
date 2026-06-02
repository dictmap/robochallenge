# 授权执行清单审计

## 结论

- 审计状态：`passed=True`。
- go/no-go：`blocked_by_user_inputs`。
- 当前可运行目标：`Table30v2 ALOHA`。
- 真实提交就绪：`False`。
- 是否连接平台：`False`。
- 是否上传：`False`。
- 是否读取真实凭据：`False`。

## 需要用户确认或提供

- `SUBMISSION_TARGET_CONFIRMATION`：需要用户确认提交 Table30v2 ALOHA；原始 Table30 还不能直接沿用当前链路。
- `ROBOCHALLENGE_USER_TOKEN`：只能放入本地 shell 或被 Git 忽略的 local env 文件，不能写入 tracked 文件。
- `ROBOCHALLENGE_SUBMISSION_ID`：必须来自 RoboChallenge 页面，不能伪造。
- `ROBOCHALLENGE_CHECKPOINT_LINK`：LoRA 提交需要可访问 checkpoint link；默认只做脱敏形态检查。
- `CHECKPOINT_ARCHIVE_AUTHORIZATION`：生成 11GB+ tar 前必须显式设置归档确认短语。
- `ROBOCHALLENGE_REAL_RUN_CONFIRM`：启动真实 runner 前必须显式设置真实提交确认短语。

## 授权后执行顺序

1. 填写本地 env：`cp submission/robochallenge_env_template.sh submission/robochallenge_env.local.sh`
   - 边界：只编辑被 Git 忽略的 local env 文件；不把真实 token 写入 tracked 文件。
2. 加载本地 env：`source submission/robochallenge_env.local.sh`
   - 边界：shell 中加载，不打印变量值。
3. 只读预检：`bash submission/run_authorized_preflight_template.sh`
   - 边界：如果 ready_for_real_submission=false，必须停止。
4. 可选下载校验：`python3 scripts/audit_checkpoint_link_download_verification.py --verify-download`
   - 边界：只有用户明确允许联网验证 checkpoint link 时才运行。
5. 可选 checkpoint 归档：`ROBOCHALLENGE_ARCHIVE_CONFIRM=CREATE_ROBOCHALLENGE_CHECKPOINT_ARCHIVE bash submission/run_authorized_checkpoint_archive_template.sh`
   - 边界：只有用户明确授权生成 11GB+ tar 时才运行。
6. 真实 runner 强确认：`ROBOCHALLENGE_REAL_RUN_CONFIRM=RUN_REAL_ROBOCHALLENGE_SUBMISSION bash submission/run_ready_real_submission_template.sh`
   - 边界：只有 readiness、dry-run 和确认短语全部通过后才会进入真实 runner。

## 必须停止的情况

- 未确认提交对象是 Table30v2 ALOHA。
- 缺少 ROBOCHALLENGE_USER_TOKEN。
- 缺少 ROBOCHALLENGE_SUBMISSION_ID。
- 缺少真实 checkpoint link。
- ready_for_real_submission=false。
- link_shape_ready=false。
- 未设置 ROBOCHALLENGE_ARCHIVE_CONFIRM 但试图生成 checkpoint tar。
- 未设置 ROBOCHALLENGE_REAL_RUN_CONFIRM 但试图启动真实 runner。

## 本地证据

- `preflight_bundle_passed`：`True`。
- `preflight_go_no_go_blocked`：`True`。
- `blockers_summary_passed`：`True`。
- `blockers_summary_go_no_go_blocked`：`True`。
- `readiness_gate_passed`：`True`。
- `readiness_currently_false`：`True`。
- `web_form_currently_false`：`True`。
- `token_missing_as_expected`：`True`。
- `submission_id_missing_as_expected`：`True`。
- `checkpoint_link_missing_as_expected`：`True`。
- `env_template_passed`：`True`。
- `local_env_ignored`：`True`。
- `authorized_preflight_template_passed`：`True`。
- `ready_real_runner_template_passed`：`True`。
- `real_runner_confirmation_phrase`：`True`。
- `real_runner_no_confirm_blocks`：`True`。
- `authorized_archive_template_passed`：`True`。
- `archive_confirmation_phrase`：`True`。
- `archive_no_confirm_blocks`：`True`。
- `archive_not_created_without_confirm`：`True`。
- `authorized_sequence_passed`：`True`。
- `notebook_structure_passed`：`True`。
- `secret_scan_clean`：`True`。

## 当前阻塞项

- 缺少 ROBOCHALLENGE_USER_TOKEN。
- 缺少 ROBOCHALLENGE_SUBMISSION_ID。
- 缺少真实可访问 checkpoint link；可使用 ROBOCHALLENGE_CHECKPOINT_LINK 或 ROBOCHALLENGE_LORA_CHECKPOINT_LINK 记录。
- 尚未执行 checkpoint 上传，本地 tar 文件也未生成。
- 缺少 checkpoint link；请设置 ROBOCHALLENGE_CHECKPOINT_LINK 或 ROBOCHALLENGE_LORA_CHECKPOINT_LINK。
- 缺少真实 checkpoint link；当前只能审计下载校验协议，不能联网验证。
- 未请求 --verify-download；本轮不联网、不下载、不接触 checkpoint link host。
- 需要用户提供真实 ROBOCHALLENGE_USER_TOKEN。
- 需要用户提供真实 ROBOCHALLENGE_SUBMISSION_ID。
- 需要确认本次要提交的是 Table30v2 ALOHA 还是原始 Table30；当前可运行链路是 Table30v2 ALOHA。
- 若要提交 LoRA 版本，还需要把本地 12GB+ checkpoint 放到网站可访问的 checkpoint link。
