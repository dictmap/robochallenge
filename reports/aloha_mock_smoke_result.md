# ALOHA mock smoke 结果

## 结论

ALOHA Table30v2 pi0.5 baseline 的本地 mock 推理链路已经跑通。

## 验证命令

```bash
cd /home/yjl/robochallenge/repo
TIMEOUT_SECONDS=180 scripts/run_aloha_mock_smoke.sh
```

## 结果

`runs/policy_smoke_aloha_status.json`：

```json
{"exit_code": 0, "smoke": "passed", "log": "runs/policy_smoke_aloha.log", "server_log": "runs/mock_server_aloha.log"}
```

## 关键证据

- `runs/policy_smoke_aloha.log` 出现多条 `Inference result`。
- 输入链路使用 ALOHA 样例：`20260413/aloha/pack_the_toothbrush_holder`。
- checkpoint 使用：`/home/yjl/yjl/RoboChallenge/checkpoints/table30v2_multitask_baseline_aloha`。
- LeRobot 使用本地源码：`/home/yjl/yjl/RoboChallenge/third_party/lerobot`。

## 本轮修复

- mock server 从 `baseline_pi05_multitask/mock_server` 启动，确保 `../20260413/...` 样例路径能解析。
- mock client 去掉尾部 `/`，避免 `//clock-sync` 404。
- `test.py` 增加 `--max_wait`，smoke 可以自然退出，不再靠超时杀进程。

## 剩余事项

- 当前只证明 Table30v2 ALOHA baseline 链路可运行。
- 真实提交还需要 RoboChallenge `user_token` 和 `submission_id`。
- 如果目标是 Table30 原榜，需要补 Table30 原版数据和对应配置，不能直接把 Table30v2 baseline 当成 Table30 结果。
