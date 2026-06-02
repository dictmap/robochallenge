# 授权后 checkpoint 归档模板审计

## 结论

- 审计状态：`passed=True`。
- 模板路径：`submission/run_authorized_checkpoint_archive_template.sh`。
- 确认短语：`CREATE_ROBOCHALLENGE_CHECKPOINT_ARCHIVE`。
- bash 语法检查：`True`。
- 无确认 smoke：`True`。
- 是否生成 tar：`False`。
- 是否上传：`False`。
- 是否读取或打印凭据：`False`。

## 必要片段

- `runs_archive_plan`：`True`。
- `runs_split_plan`：`True`。
- `runs_archive_dry_run`：`True`。
- `requires_archive_confirm_env`：`True`。
- `confirmation_phrase`：`True`。
- `execute_gate`：`True`。
- `stops_before_tar`：`True`。
- `upload_separate_authorization`：`True`。

## 禁止片段

- `uploads_with_rclone`：`False`。
- `uploads_with_aws`：`False`。
- `uploads_with_curl`：`False`。
- `uploads_with_gh_release`：`False`。
- `uploads_with_hf`：`False`。
- `calls_lora_runner`：`False`。
- `calls_baseline_runner`：`False`。
- `mentions_demo_py`：`False`。
- `reads_user_token`：`False`。
- `reads_submission_id`：`False`。

## 无确认 smoke

- `returncode`：`1`。
- `archive_absent_before`：`True`。
- `sha256_absent_before`：`True`。
- `archive_absent_after`：`True`。
- `sha256_absent_after`：`True`。
- `missing_confirmation`：`True`。
- `stops_before_creating_tar`：`True`。
- `archive_created`：`False`。
- `sha256_created`：`False`。
- `upload_performed`：`False`。
- `credentials_read`：`False`。
- `platform_contacted`：`False`。
- `dry_run_passed`：`True`。
- `confirm_phrase_accepted`：`False`。
- `passed`：`True`。

## 输入证据

- `archive_plan_passed`：`True`。
- `split_plan_passed`：`True`。
- `archive_dry_run_passed`：`True`。
- `archive_not_created`：`True`。
- `sha256_not_created`：`True`。
- `upload_not_performed`：`True`。
- `credentials_not_read`：`True`。
- `platform_not_contacted`：`True`。

## Blocking

- 授权后 checkpoint 归档模板已通过；没有确认短语时不会生成 tar。
