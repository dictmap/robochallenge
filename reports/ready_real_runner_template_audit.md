# 强确认真实 runner 模板审计

## 结论

- 审计状态：`passed=True`。
- 模板路径：`submission/run_ready_real_submission_template.sh`。
- 默认提交路线：`baseline`。
- 确认短语：`RUN_REAL_ROBOCHALLENGE_SUBMISSION`。
- bash 语法检查：`True`。
- 无凭据 smoke：`True`。
- synthetic 无确认 smoke：`True`。
- 是否连接平台：`False`。
- 是否上传：`False`。
- 是否读取或打印凭据：`False`。

## 必要片段

- `sources_local_env_file`：`True`。
- `runs_link_intake`：`True`。
- `runs_download_default`：`True`。
- `download_verify_guarded`：`True`。
- `runs_readiness`：`True`。
- `reads_readiness_json`：`True`。
- `default_variant_baseline`：`True`。
- `checks_lora_ready`：`True`。
- `checks_baseline_ready`：`True`。
- `lora_dry_run_first`：`True`。
- `baseline_dry_run_first`：`True`。
- `requires_confirmation`：`True`。
- `confirmation_phrase`：`True`。
- `lora_real_runner_available`：`True`。
- `baseline_real_runner_available`：`True`。

## 禁止片段

- `creates_large_archive`：`False`。
- `uploads_with_rclone`：`False`。
- `uploads_with_aws`：`False`。
- `uploads_with_curl`：`False`。

## Smoke 结果

- 无凭据返回码：`1`。
- 无凭据是否停在真实 runner 前：`True`。
- synthetic 是否先 dry-run：`True`。
- synthetic 默认路线：`baseline`。
- synthetic 是否因缺少确认停止：`True`。
- synthetic 是否启动真实 runner：`False`。
- clean state restore：`True`。

## Blocking

- 强确认真实 runner 模板已通过；没有确认短语时不会启动真实 runner。
