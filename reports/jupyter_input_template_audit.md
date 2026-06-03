# Jupyter 安全填空本地 env 入口审计

## 结论

- 审计状态：`passed=True`。
- Notebook：`notebooks/robochallenge_pi05_submit_cn.ipynb`。
- 章节：`第 44 节：安全填空本地 env 入口`。
- 入口默认执行：`False`。
- 本地 env 路径：`submission/robochallenge_env.local.sh`。
- 本地 env 已被 Git 忽略：`True`。
- 是否读取真实凭据：`False`。
- 是否打印 token/link/submission id：`False`。
- 是否连接 RoboChallenge 平台：`False`。
- 是否执行上传：`False`。
- 推荐路线：`baseline_official_aloha`。
- baseline 是否要求 checkpoint link：`False`。
- baseline 是否要求 checkpoint upload：`False`。
- LoRA/web 是否要求 checkpoint link：`True`。
- LoRA/web 是否要求 checkpoint upload：`True`。
- 目标确认变量：`ROBOCHALLENGE_SUBMISSION_TARGET_CONFIRMATION`。
- 目标确认值：`CONFIRM_TABLE30V2_ALOHA_BASELINE`。
- 是否要求手动输入目标确认：`True`。
- 是否要求精确匹配目标确认：`True`。

## 必要变量

- `ROBOCHALLENGE_USER_TOKEN`：`True`。
- `ROBOCHALLENGE_SUBMISSION_ID`：`True`。
- `ROBOCHALLENGE_SUBMISSION_VARIANT`：`True`。
- `ROBOCHALLENGE_SUBMISSION_TARGET_CONFIRMATION`：`True`。
- `ROBOCHALLENGE_LORA_CHECKPOINT_LINK`：`True`。
- `ROBOCHALLENGE_CHECKPOINT_LINK`：`True`。

## Variant 逻辑

- `submission_variant_supported`：`True`。
- `baseline_checkpoint_link_optional`：`True`。
- `recommended_route_baseline`：`True`。
- `lora_checkpoint_link_required`：`True`。

## 路线引导

- `baseline_guides_to_route_aware`：`True`。
- `baseline_quickstart_referenced`：`True`。
- `baseline_no_checkpoint_link`：`True`。
- `baseline_no_lora_upload_when_link_blank`：`True`。
- `lora_web_upload_flow_separate`：`True`。

## 提交对象确认

- `target_confirmation_key_written`：`True`。
- `target_confirmation_value_exact`：`True`。
- `target_confirmation_manual_input`：`True`。
- `target_confirmation_exact_match`：`True`。
- `target_confirmation_route_named`：`True`。

## 关键片段

- `第 44 节：安全填空本地 env 入口`：`True`。
- `RUN_SAFE_LOCAL_ENV_INPUT_TEMPLATE`：`True`。
- `RUN_SAFE_LOCAL_ENV_INPUT_TEMPLATE = False`：`True`。
- `import getpass`：`True`。
- `import shlex`：`True`。
- `getpass.getpass`：`True`。
- `shlex.quote`：`True`。
- `is_placeholder_like`：`True`。
- `PLACEHOLDER_MARKERS`：`True`。
- `missing_or_placeholder`：`True`。
- `normalize_submission_variant`：`True`。
- `required_for_variant`：`True`。
- `TARGET_CONFIRMATION_VALUE`：`True`。
- `CONFIRM_TABLE30V2_ALOHA_BASELINE`：`True`。
- `ROBOCHALLENGE_SUBMISSION_TARGET_CONFIRMATION`：`True`。
- `target_confirmation != TARGET_CONFIRMATION_VALUE`：`True`。
- `确认 Table30v2 / aloha / pack_the_toothbrush_holder 后`：`True`。
- `submission_variant == "lora"`：`True`。
- `ROBOCHALLENGE_CHECKPOINT_LINK [baseline 可留空]`：`True`。
- `baseline 官方 ALOHA 路线只要求 token、submission id 和目标确认，不要求 checkpoint link`：`True`。
- `scripts/render_route_aware_submission_blockers.py`：`True`。
- `reports/baseline_submission_quickstart.md`：`True`。
- `baseline 不因 checkpoint link 留空进入 LoRA 上传流程`：`True`。
- `os.chmod`：`True`。
- `submission/robochallenge_env.local.sh`：`True`。
- `ROBOCHALLENGE_USER_TOKEN`：`True`。
- `ROBOCHALLENGE_SUBMISSION_ID`：`True`。
- `ROBOCHALLENGE_SUBMISSION_VARIANT`：`True`。
- `ROBOCHALLENGE_LORA_CHECKPOINT_LINK`：`True`。
- `ROBOCHALLENGE_CHECKPOINT_LINK`：`True`。

## 禁止片段

- `print(token`：`False`。
- `print(env_values`：`False`。
- `print(value`：`False`。
- `display(env_values`：`False`。
- `ROBOCHALLENGE_USER_TOKEN =`：`False`。
- `ROBOCHALLENGE_SUBMISSION_ID =`：`False`。
- `ROBOCHALLENGE_SUBMISSION_TARGET_CONFIRMATION =`：`False`。
- `ROBOCHALLENGE_LORA_CHECKPOINT_LINK =`：`False`。
- `ROBOCHALLENGE_CHECKPOINT_LINK =`：`False`。

## Blocking

- Jupyter 安全填空本地 env 入口已就绪；当前未读取、未写入、未打印真实凭据。
