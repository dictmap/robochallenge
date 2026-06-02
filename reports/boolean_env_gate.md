# 布尔环境变量 gate 审计

## 结论

- 审计状态：`passed=True`。
- 推荐路线：`baseline_official_aloha`。
- 覆盖 case 数量：`8`。
- 错误布尔值 case 数量：`4`。
- 合法布尔值 case 数量：`4`。
- 错误布尔值是否被拒绝：`True`。
- 错误布尔值是否停在预检前：`True`。
- 合法布尔值是否被接受：`True`。
- 是否启动真实 runner：`False`。
- 是否记录 synthetic 明文：`False`。

## 边界

- 本审计只设置 synthetic 环境变量，并显式使用不存在的 local env 路径；不读取真实 token、submission id 或 checkpoint link。
- `ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD` 和 `ROBOCHALLENGE_REQUIRE_READY` 只允许 `0` 或 `1`。
- 错误布尔值会在 checkpoint link、readiness 和 dry-run 前退出，避免 `true/yes/空白` 被静默当成关闭。

## 只读边界

- `platform_contacted`：`False`。
- `uploads_performed`：`False`。
- `download_host_contacted`：`False`。
- `credentials_printed`：`False`。
- `link_values_printed`：`False`。
- `secret_values_printed`：`False`。

## 输入证据

- `bad_flags_rejected`：`True`。
- `bad_flags_stop_before_preflight`：`True`。
- `valid_flags_accepted`：`True`。
- `all_cases_expected_returncodes`：`True`。
- `all_cases_no_protected_values`：`True`。
- `real_runner_not_started`：`True`。
- `restore_clean_state_passed`：`True`。

## Case 摘要

- `authorized_verify_true`：script=`authorized_preflight`，override_keys=`ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD`，returncode=`68`，bool_rejected=`True`，preflight_started=`False`，accepted=`False`，passed=`True`。
- `ready_verify_yes`：script=`ready_runner`，override_keys=`ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD`，returncode=`68`，bool_rejected=`True`，preflight_started=`False`，accepted=`False`，passed=`True`。
- `authorized_require_ready_true`：script=`authorized_preflight`，override_keys=`ROBOCHALLENGE_REQUIRE_READY`，returncode=`68`，bool_rejected=`True`，preflight_started=`False`，accepted=`False`，passed=`True`。
- `authorized_verify_space`：script=`authorized_preflight`，override_keys=`ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD`，returncode=`68`，bool_rejected=`True`，preflight_started=`False`，accepted=`False`，passed=`True`。
- `authorized_flags_zero`：script=`authorized_preflight`，override_keys=`none`，returncode=`0`，bool_rejected=`False`，preflight_started=`True`，accepted=`True`，passed=`True`。
- `authorized_require_ready_one`：script=`authorized_preflight`，override_keys=`ROBOCHALLENGE_REQUIRE_READY`，returncode=`1`，bool_rejected=`False`，preflight_started=`True`，accepted=`True`，passed=`True`。
- `ready_baseline_verify_zero`：script=`ready_runner`，override_keys=`none`，returncode=`1`，bool_rejected=`False`，preflight_started=`True`，accepted=`True`，passed=`True`。
- `ready_lora_verify_zero`：script=`ready_runner`，override_keys=`ROBOCHALLENGE_SUBMISSION_VARIANT`，returncode=`1`，bool_rejected=`False`，preflight_started=`True`，accepted=`True`，passed=`True`。

## Blocking

- 布尔环境变量 gate 已通过；提交入口只接受 0/1，true/false/yes/no 或空白会在预检前被拒绝。
