# Jupyter 与 shell 只读预检一致性审计

## 结论

- 审计状态：`passed=True`。
- 推荐路线：`baseline_official_aloha`。
- 目标确认值：`CONFIRM_TABLE30V2_ALOHA_BASELINE`。
- shell 入口：`ROBOCHALLENGE_SUBMISSION_VARIANT=baseline bash submission/run_authorized_preflight_template.sh`。
- Jupyter 入口：`source submission/robochallenge_env.local.sh; bash submission/run_authorized_preflight_template.sh`。
- 共同 wrapper：`submission/run_authorized_preflight_template.sh`。
- 两条入口是否收敛到同一 wrapper：`True`。
- shell variant 来源：`inline env prefix`。
- Jupyter variant 来源：`第 44 节：安全填空本地 env 入口 写入 submission/robochallenge_env.local.sh`。
- Jupyter 目标确认来源：`第 44 节：安全填空本地 env 入口 手动精确填写 CONFIRM_TABLE30V2_ALOHA_BASELINE`。
- 是否需要 checkpoint link：`False`。
- 是否需要 checkpoint upload：`False`。
- 只读预检是否需要真实 runner 强确认：`False`。
- 真实提交是否仍需要真实 runner 强确认：`True`。
- 是否读取真实凭据：`False`。
- 是否打印 token/link/submission id：`False`。
- 是否连接平台：`False`。
- 是否上传：`False`。
- 是否启动 runner：`False`。

## 机器证据

- `readonly_entry_passed`：`True`。
- `shell_command_exact`：`True`。
- `shell_variant_prefix_present`：`True`。
- `shell_uses_same_wrapper`：`True`。
- `shell_no_real_runner_confirm`：`True`。
- `shell_no_checkpoint_link`：`True`。
- `jupyter_input_passed`：`True`。
- `jupyter_input_writes_local_env`：`True`。
- `jupyter_input_has_variant_key`：`True`。
- `jupyter_input_has_target_confirmation_key`：`True`。
- `jupyter_input_target_confirmation_exact`：`True`。
- `jupyter_input_target_confirmation_manual`：`True`。
- `jupyter_input_target_confirmation_exact_match`：`True`。
- `jupyter_authorized_passed`：`True`。
- `jupyter_authorized_default_off`：`True`。
- `jupyter_authorized_command_same_wrapper`：`True`。
- `jupyter_code_sources_local_env`：`True`。
- `jupyter_code_uses_same_wrapper`：`True`。
- `jupyter_code_has_safe_shell`：`True`。
- `jupyter_code_redacts_sensitive_output`：`True`。
- `jupyter_code_no_real_runner`：`True`。
- `jupyter_code_no_checkpoint_archive`：`True`。
- `routes_converge_to_same_wrapper`：`True`。
- `variant_delivery_split_is_explicit`：`True`。
- `target_confirmation_delivery_split_is_explicit`：`True`。

## 泄漏与联网边界

- `credentials_printed`：`False`。
- `link_values_printed`：`False`。
- `secret_values_printed`：`False`。
- `section_secret_hits`：`False`。
- `whole_notebook_secret_hits`：`False`。
- `platform_contacted`：`False`。
- `uploads_performed`：`False`。
- `download_host_contacted`：`False`。

## Blocking

- Jupyter 与 shell 只读预检入口已闭环：两者进入同一 wrapper，variant 来源明确，不触发真实 runner。
