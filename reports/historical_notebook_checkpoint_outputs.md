# Notebook 历史 checkpoint 输出审计

## 结论

- 审计状态：`passed=True`。
- 当前材料旧口径命中数：`0`。
- 当前 Notebook 旧口径命中数：`0`。
- executed Notebook 历史旧口径命中数：`13`。
- work.md 旧短语仅作为审计记录：`True`。
- 结论：当前提交材料以 reports/submission/当前 Notebook 为准；executed Notebook 中的旧 checkpoint-link 输出只保留为历史运行证据。

## 当前 baseline 阻塞

- `SUBMISSION_TARGET_CONFIRMATION`
- `ROBOCHALLENGE_USER_TOKEN`
- `ROBOCHALLENGE_SUBMISSION_ID`
- `ROBOCHALLENGE_SUBMISSION_VARIANT=baseline`
- `ROBOCHALLENGE_REAL_RUN_CONFIRM`

## 当前可信入口

- `reports/next_user_action_packet.md`
- `reports/route_aware_submission_blockers.md`
- `reports/submission_status_dashboard.html`
- `submission/README.md`
- `submission/REAL_SUBMISSION_HANDOFF.md`
- `submission/AUTHORIZED_SUBMISSION_SEQUENCE.md`

## 历史输出样例

- `notebooks/robochallenge_pi05_submit_cn.executed.ipynb:7667`：真实网站提交仍需要用户提供 token/submission_id 和可访问 checkpoint link
- `notebooks/robochallenge_pi05_submit_cn.executed.ipynb:7755`：需要确认本次要提交的是 Table30v2 ALOHA 还是原始 Table30
- `notebooks/robochallenge_pi05_submit_cn.executed.ipynb:7775`：真实网站提交仍需要用户提供 token/submission_id 和可访问 checkpoint link
- `notebooks/robochallenge_pi05_submit_cn.executed.ipynb:7863`：需要确认本次要提交的是 Table30v2 ALOHA 还是原始 Table30
- `notebooks/robochallenge_pi05_submit_cn.executed.ipynb:7871`：需要确认本次要提交的是 Table30v2 ALOHA 还是原始 Table30
- `notebooks/robochallenge_pi05_submit_cn.executed.ipynb:8599`：真实提交仍需要 ROBOCHALLENGE_USER_TOKEN 和 ROBOCHALLENGE_SUBMISSION_ID
- `notebooks/robochallenge_pi05_submit_cn.executed.ipynb:8757`：真实提交仍需要 ROBOCHALLENGE_USER_TOKEN 和 ROBOCHALLENGE_SUBMISSION_ID
- `notebooks/robochallenge_pi05_submit_cn.executed.ipynb:9673`：真实提交仍需要用户提供 token、submission id 和可访问 checkpoint link
- `notebooks/robochallenge_pi05_submit_cn.executed.ipynb:9719`：真实提交仍需要用户提供 token、submission id 和可访问 checkpoint link
- `notebooks/robochallenge_pi05_submit_cn.executed.ipynb:9820`：真实提交仍需要用户提供 token、submission id 和真实可访问 checkpoint link

## Blocking

- executed notebook 中仍有旧口径历史输出；不要把它当作当前 baseline 提交前置条件。
- 当前 baseline 真实提交仍等待用户目标确认、token、submission id、variant=baseline 和真实 runner 强确认。
