# RoboChallenge 提交包清单

## 结论

- 审计状态：`passed=True`。
- 当前可运行目标：`Table30v2 / aloha / pack_the_toothbrush_holder`。
- 官方 Table30v2 ALOHA baseline 仍是最稳的提交模板。
- LoRA 完整物化 checkpoint 本地可读：`True`。
- 真实提交仍不能伪造 token、submission_id 或 checkpoint link。

## 已准备材料

- 提交 manifest 模板：`submission/submission_manifest_template.json`。
- 启动脚本模板：`submission/run_table30v2_aloha_demo_template.sh`。
- LoRA 启动脚本模板：`submission/run_table30v2_aloha_lora_demo_template.sh`。
- submission 目录说明：`submission/README.md`。
- `demo.py` 必需参数覆盖：`{'user_token': True, 'submission_id': True, 'checkpoint': True, 'prompt': True, 'action_type': True, 'duration': True, 'valid_action_num': True, 'image_size': True, 'robot_type': True}`。
- baseline runner 语法检查：`True`，无凭据 fail-fast：`True`。
- LoRA runner 语法检查：`True`，无凭据 fail-fast：`True`。
- mock 验证：`passed=True`。
- Table30v2 ALOHA 映射：`ready=True`。
- LoRA restore 审计：`passed=True`，合并后占位 leaf `0`。
- LoRA 完整 checkpoint：`runs/openpi_rtc_lora_materialized_policy_checkpoint`，本地存在 `True`，Git 忽略 `True`。
- LoRA policy 加载 smoke：`passed=True`，模型类型 `Pi0`。

## 提交时需要用户提供

- `ROBOCHALLENGE_USER_TOKEN`：用户登录后获得，不能写入仓库。
- `ROBOCHALLENGE_SUBMISSION_ID`：在网站提交详情页获得，不能伪造。
- 如果提交 LoRA 版本，还需要把本地 12GB+ checkpoint 放到网站可访问的 checkpoint link。
- 如果目标切回原始 Table30，需要重新补齐对应数据和配置；当前可运行链路是 Table30v2 ALOHA。

## 建议填入网站的链接位

- `Inference Code Link`：`https://github.com/dictmap/robochallenge/tree/main`。
- `Fine-tuning Code Link`：同仓库中的 `scripts/`、`notebooks/`、`reports/`。
- `Checkpoint Link`：baseline 可指向官方 ALOHA checkpoint；LoRA 版本需要上传本地物化 checkpoint 后填可访问链接。

## Blocking

- 需要用户提供真实 ROBOCHALLENGE_USER_TOKEN。
- 需要用户提供真实 ROBOCHALLENGE_SUBMISSION_ID。
- 需要确认本次要提交的是 Table30v2 ALOHA 还是原始 Table30；当前可运行链路是 Table30v2 ALOHA。
- 若要提交 LoRA 版本，还需要把本地 12GB+ checkpoint 放到网站可访问的 checkpoint link。
