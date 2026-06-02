# bash xtrace 防泄漏审计

## 结论

- 审计状态：`passed=True`。
- 推荐路线：`baseline_official_aloha`。
- 覆盖入口数量：`4`。
- 是否记录 synthetic 明文：`False`。
- 是否连接平台：`False`。
- 是否上传：`False`。

## xtrace 入口防护

- `baseline_demo`：首条有效命令为 `set +x` -> `True`。
- `lora_demo`：首条有效命令为 `set +x` -> `True`。
- `authorized_preflight`：首条有效命令为 `set +x` -> `True`。
- `ready_real_runner`：首条有效命令为 `set +x` -> `True`。

## bash -x smoke

- `baseline_demo` / `submission/run_table30v2_aloha_demo_template.sh`：returncode=`0`，set_plus_x_trace_seen=`True`，unexpected_trace_after_guard=`False`，printed_protected_values=`False`，real_runner_started=`False`。
- `lora_demo` / `submission/run_table30v2_aloha_lora_demo_template.sh`：returncode=`0`，set_plus_x_trace_seen=`True`，unexpected_trace_after_guard=`False`，printed_protected_values=`False`，real_runner_started=`False`。
- `authorized_preflight` / `submission/run_authorized_preflight_template.sh`：returncode=`0`，set_plus_x_trace_seen=`True`，unexpected_trace_after_guard=`False`，printed_protected_values=`False`，real_runner_started=`False`。
- `ready_real_runner` / `submission/run_ready_real_submission_template.sh`：returncode=`1`，set_plus_x_trace_seen=`True`，unexpected_trace_after_guard=`False`，printed_protected_values=`False`，real_runner_started=`False`。

## 只读边界

- `platform_contacted`：`False`。
- `uploads_performed`：`False`。
- `download_host_contacted`：`False`。
- `credentials_printed`：`False`。
- `link_values_printed`：`False`。
- `secret_values_printed`：`False`。

## 输入证据

- `all_templates_disable_xtrace_first`：`True`。
- `all_cases_saw_set_plus_x_trace`：`True`。
- `all_cases_stop_trace_after_guard`：`True`。
- `all_cases_no_protected_values`：`True`。
- `demo_dry_runs_passed`：`True`。
- `demo_outputs_lengths_only`：`True`。
- `authorized_preflight_passed`：`True`。
- `ready_runner_stops_before_real_runner`：`True`。
- `restore_clean_state_passed`：`True`。

## Blocking

- bash -x 防泄漏审计已通过；四个提交入口都会先关闭 xtrace，合成凭据未出现在日志中。
