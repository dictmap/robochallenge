# RoboChallenge 提交包清单

## 结论

- 审计状态：`passed=True`。
- 当前可运行目标：`Table30v2 / aloha / pack_the_toothbrush_holder`。
- 当前最小提交模板走官方 pi0.5 Table30v2 ALOHA baseline；不会伪造网站 token 或 submission_id。
- LoRA scoped checkpoint 已完成恢复/合并审计，但仍不是完整 policy checkpoint，不能单独给 `demo.py --checkpoint` 使用。

## 已准备材料

- 提交 manifest 模板：`submission/submission_manifest_template.json`。
- 启动脚本模板：`submission/run_table30v2_aloha_demo_template.sh`。
- submission 目录说明：`submission/README.md`。
- 入口脚本：`demo.py`，必需参数覆盖情况：`{'user_token': True, 'submission_id': True, 'checkpoint': True, 'prompt': True, 'action_type': True, 'duration': True, 'valid_action_num': True, 'image_size': True, 'robot_type': True}`。
- mock 验证：`passed=True`。
- Table30v2 ALOHA 映射：`ready=True`。
- LoRA 恢复审计：`passed=True`，合并后占位 leaf `0`。

## 提交时需要用户提供

- `ROBOCHALLENGE_USER_TOKEN`：用户登录后获得，不能写入仓库。
- `ROBOCHALLENGE_SUBMISSION_ID`：在网站提交详情页获得，不能伪造。
- 当前评测 run 的 prompt/robot/benchmark 是否仍为 Table30v2 ALOHA；若目标切回原始 Table30，需要重新补齐对应数据和配置。

## 建议填入网站的链接位

- `Inference Code Link`：`https://github.com/dictmap/robochallenge/tree/main`。
- `Fine-tuning Code Link`：同仓库中的 `scripts/`、`notebooks/`、`reports/`。
- `Checkpoint Link`：baseline 路线可指向官方 ALOHA baseline checkpoint；LoRA scoped 路线必须先打包为完整可恢复 checkpoint 或提供完整恢复说明。

## Blocking

- 需要用户提供真实 ROBOCHALLENGE_USER_TOKEN。
- 需要用户提供真实 ROBOCHALLENGE_SUBMISSION_ID。
- 需要确认本次要提交的是 Table30v2 ALOHA 还是原始 Table30；当前可运行链路是 Table30v2 ALOHA。
- 若要提交 LoRA scoped 路线，还需要把 scoped params 打包成 demo.py 可直接恢复的完整 policy 入口。
