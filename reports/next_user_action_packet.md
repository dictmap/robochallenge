# 下一步用户动作包

## 结论

- 审计状态：`passed=True`。
- go/no-go：`blocked_by_user_inputs`。
- 真实提交就绪：`False`。
- Web 表单就绪：`False`。
- Notebook：`notebooks/robochallenge_pi05_submit_cn.ipynb`。
- 本地 env：`submission/robochallenge_env.local.sh`，Git 忽略：`True`。
- 推荐路线：`baseline_official_aloha`。
- baseline 是否需要 checkpoint link：`False`。
- baseline 是否需要 checkpoint upload：`False`。
- LoRA/web 是否需要 checkpoint link：`True`。
- LoRA/web 是否需要 checkpoint upload：`True`。

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

## Baseline 主决策清单

- `SUBMISSION_TARGET_CONFIRMATION`：提交对象确认。需要用户确认提交 Table30v2 ALOHA；原始 Table30 还不能直接沿用当前链路。
- `ROBOCHALLENGE_USER_TOKEN`：RoboChallenge user token。只能放入本地 shell 或被 Git 忽略的 local env 文件，不能写入 tracked 文件。
- `ROBOCHALLENGE_SUBMISSION_ID`：RoboChallenge submission id。必须来自 RoboChallenge 页面，不能伪造。
- `ROBOCHALLENGE_SUBMISSION_VARIANT=baseline`：提交路线确认。默认先走 baseline_official_aloha；baseline 不需要 checkpoint link 或 checkpoint upload。
- `ROBOCHALLENGE_REAL_RUN_CONFIRM`：真实 runner 强确认。启动真实 runner 前必须显式设置真实提交确认短语。

## LoRA/web checkpoint 分支决策清单

- `SUBMISSION_TARGET_CONFIRMATION`：提交对象确认。需要用户确认提交 Table30v2 ALOHA；原始 Table30 还不能直接沿用当前链路。
- `ROBOCHALLENGE_USER_TOKEN`：RoboChallenge user token。只能放入本地 shell 或被 Git 忽略的 local env 文件，不能写入 tracked 文件。
- `ROBOCHALLENGE_SUBMISSION_ID`：RoboChallenge submission id。必须来自 RoboChallenge 页面，不能伪造。
- `ROBOCHALLENGE_SUBMISSION_VARIANT=lora`：LoRA/web checkpoint 路线确认。只有用户明确选择 LoRA/web checkpoint 路线时才需要。
- `CHECKPOINT_ARCHIVE_AUTHORIZATION`：checkpoint 归档授权。生成 11GB+ tar 前必须显式设置归档确认短语。
- `ROBOCHALLENGE_CHECKPOINT_LINK`：真实 checkpoint link。LoRA/web checkpoint 提交需要可访问 checkpoint link；默认只做脱敏形态检查。
- `ROBOCHALLENGE_REAL_RUN_CONFIRM`：真实 runner 强确认。启动真实 runner 前必须显式设置真实提交确认短语。

## 推荐入口

1. 打开 `notebooks/robochallenge_pi05_submit_cn.ipynb`。
2. 在第 44 节手动设置 `RUN_SAFE_LOCAL_ENV_INPUT_TEMPLATE=True`，把真实 token、submission id 和 `baseline` variant 写入被 Git 忽略的 local env。
3. 在第 45 节手动设置 `RUN_JUPYTER_AUTHORIZED_PREFLIGHT=True`，优先运行 baseline 授权预检。
4. 先按 `reports/baseline_submission_quickstart.md` 跑 baseline dry-run gate；只有明确选择 LoRA/web checkpoint 路线时，才进入 checkpoint 归档、上传和 link 回填。

## 当前阻塞（baseline 默认路线）

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
- SUBMISSION_TARGET_CONFIRMATION
- ROBOCHALLENGE_USER_TOKEN
- ROBOCHALLENGE_SUBMISSION_ID
- ROBOCHALLENGE_SUBMISSION_VARIANT=baseline
- ROBOCHALLENGE_REAL_RUN_CONFIRM
- 缺少 checkpoint link；请设置 ROBOCHALLENGE_CHECKPOINT_LINK 或 ROBOCHALLENGE_LORA_CHECKPOINT_LINK。
- 缺少真实 checkpoint link；当前只能审计下载校验协议，不能联网验证。
- 未请求 --verify-download；本轮不联网、不下载、不接触 checkpoint link host。
- 需要用户提供真实 ROBOCHALLENGE_USER_TOKEN。
- 需要用户提供真实 ROBOCHALLENGE_SUBMISSION_ID。
- 需要确认本次要提交的是 Table30v2 ALOHA 还是原始 Table30；当前可运行链路是 Table30v2 ALOHA。
- 若要提交 LoRA 版本，还需要把本地 12GB+ checkpoint 放到网站可访问的 checkpoint link。

## 只读边界

- `platform_contacted`：`False`。
- `uploads_performed`：`False`。
- `download_host_contacted`：`False`。
- `credentials_printed`：`False`。
- `link_values_printed`：`False`。
- `secret_values_printed`：`False`。

## 输入证据

- `readiness_gate_passed`：`True`。
- `ready_for_real_submission_false`：`True`。
- `web_form_ready_false`：`True`。
- `authorized_execution_checklist_passed`：`True`。
- `authorized_execution_go_no_go_blocked`：`True`。
- `authorized_execution_recommends_baseline`：`True`。
- `all_expected_decisions_listed`：`True`。
- `baseline_decisions_have_no_checkpoint_link`：`True`。
- `baseline_decisions_have_no_archive_authorization`：`True`。
- `lora_web_expected_decisions_listed`：`True`。
- `jupyter_input_template_passed`：`True`。
- `jupyter_input_default_false`：`True`。
- `jupyter_authorized_preflight_template_passed`：`True`。
- `jupyter_authorized_preflight_execution_default_false`：`True`。
- `local_env_ignored`：`True`。
- `handoff_docs_available`：`True`。
- `authorized_sequence_available`：`True`。
- `route_packet_passed`：`True`。
- `route_packet_recommends_baseline`：`True`。
- `baseline_quickstart_passed`：`True`。
- `baseline_quickstart_no_link`：`True`。
- `baseline_quickstart_no_upload`：`True`。
- `baseline_blocking_has_no_checkpoint_link`：`True`。
- `baseline_blocking_has_no_archive_authorization`：`True`。
- `baseline_required_ids_complete`：`True`。
- `lora_web_requires_checkpoint_link`：`True`。
- `lora_web_requires_archive_authorization`：`True`。
- `lora_web_required_ids_complete`：`True`。
- `secret_scan_clean`：`True`。

## Blocking

- 动作包已生成；baseline 仍等待用户 token、submission id 和真实 runner 强确认，LoRA/web checkpoint 路线额外等待授权上传和真实 checkpoint link。
