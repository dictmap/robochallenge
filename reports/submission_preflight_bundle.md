# 真实提交前预检汇总

## 结论

- 审计状态：`passed=True`。
- go/no-go：`blocked`。
- 真实提交就绪：`False`。
- Web 表单就绪：`False`。
- baseline runner 就绪：`False`。
- LoRA runner 就绪：`False`。
- checkpoint link 形态就绪：`False`。
- 推荐提交路线：`baseline_official_aloha`。
- baseline 是否需要 checkpoint link：`False`。
- baseline 是否需要 checkpoint upload：`False`。
- baseline dry-run gate：`True`。
- baseline dry-run 命令：`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_ready_real_submission_template.sh`。
- dry-run 是否停在真实 runner 前：`True`。
- baseline 凭据卫生：`True`。
- local env 是否被 Git 忽略：`True`。
- 是否读取 local env 内容：`False`。
- synthetic local env smoke：`True`。
- synthetic 授权预检是否走 baseline：`True`。
- synthetic ready runner 是否停在真实 runner 前：`True`。
- LoRA/web 是否需要 checkpoint link：`True`。
- LoRA/web 是否需要 checkpoint upload：`True`。
- 下载已验证：`False`。
- secret scan 命中数：`0`。

## 只读边界

- 是否连接 RoboChallenge 平台：`False`。
- 是否上传：`False`。
- 是否接触下载 host：`False`。
- 是否打印凭据：`False`。
- 是否打印链接明文：`False`。
- 是否打印 secret 明文：`False`。

## 子审计

- `checkpoint_link_intake`：returncode=`0`，passed=`True`。
- `checkpoint_link_download_verification`：returncode=`0`，passed=`True`。
- `submission_env_template`：returncode=`0`，passed=`True`。
- `notebook_structure`：returncode=`0`，passed=`True`。
- `jupyter_input_template`：returncode=`0`，passed=`True`。
- `jupyter_authorized_preflight_template`：returncode=`0`，passed=`True`。
- `real_submission_readiness`：returncode=`0`，passed=`True`。
- `authorized_preflight_template`：returncode=`0`，passed=`True`。
- `ready_real_runner_template`：returncode=`0`，passed=`True`。
- `authorized_checkpoint_archive_template`：returncode=`0`，passed=`True`。
- `plaintext_secret_scan`：returncode=`0`，passed=`True`。
- `submission_variant_route_packet`：returncode=`0`，passed=`True`。
- `baseline_submission_quickstart`：returncode=`0`，passed=`True`。
- `authorized_execution_checklist`：returncode=`0`，passed=`True`。
- `next_user_action_packet`：returncode=`0`，passed=`True`。
- `web_form_field_packet`：returncode=`0`，passed=`True`。
- `route_aware_submission_blockers`：returncode=`0`，passed=`True`。
- `baseline_dry_run_gate`：returncode=`0`，passed=`True`。
- `baseline_credential_hygiene`：returncode=`0`，passed=`True`。
- `baseline_local_env_smoke`：returncode=`0`，passed=`True`。
- `submission_handoff_docs`：returncode=`0`，passed=`True`。
- `submission_artifact_manifest`：returncode=`0`，passed=`True`。

## Baseline 最短路线当前只差

- `SUBMISSION_TARGET_CONFIRMATION`
- `ROBOCHALLENGE_USER_TOKEN`
- `ROBOCHALLENGE_SUBMISSION_ID`
- `ROBOCHALLENGE_SUBMISSION_VARIANT=baseline`
- `ROBOCHALLENGE_REAL_RUN_CONFIRM`

## LoRA / 网页 checkpoint 路线当前只差

- `SUBMISSION_TARGET_CONFIRMATION`
- `ROBOCHALLENGE_USER_TOKEN`
- `ROBOCHALLENGE_SUBMISSION_ID`
- `ROBOCHALLENGE_SUBMISSION_VARIANT=lora`
- `CHECKPOINT_ARCHIVE_AUTHORIZATION`
- `ROBOCHALLENGE_CHECKPOINT_LINK`
- `ROBOCHALLENGE_REAL_RUN_CONFIRM`

## Blocking

- SUBMISSION_TARGET_CONFIRMATION
- ROBOCHALLENGE_USER_TOKEN
- ROBOCHALLENGE_SUBMISSION_ID
- ROBOCHALLENGE_SUBMISSION_VARIANT=baseline
- ROBOCHALLENGE_REAL_RUN_CONFIRM

## 旧全局阻塞（兼容 readiness/web/LoRA）

- 缺少 ROBOCHALLENGE_USER_TOKEN。
- 缺少 ROBOCHALLENGE_SUBMISSION_ID。
- 缺少真实可访问 checkpoint link；可使用 ROBOCHALLENGE_CHECKPOINT_LINK 或 ROBOCHALLENGE_LORA_CHECKPOINT_LINK 记录。
- 尚未执行 checkpoint 上传，本地 tar 文件也未生成。
- 缺少 checkpoint link；请设置 ROBOCHALLENGE_CHECKPOINT_LINK 或 ROBOCHALLENGE_LORA_CHECKPOINT_LINK。
- 缺少真实 checkpoint link；当前只能审计下载校验协议，不能联网验证。
- 未请求 --verify-download；本轮不联网、不下载、不接触 checkpoint link host。
