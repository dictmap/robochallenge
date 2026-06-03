# GUI dashboard 截图覆盖审计

## 结论

- 审计状态：`passed=True`。
- 截图路径：`reports/submission_status_dashboard_browser.png`。
- 截图大小：`618325` bytes。
- 截图尺寸：`1440 x 5200`。
- dashboard 卡片数：`42`。
- dashboard 来源数：`42`。
- HTML 必需短语数量：`5`。

## HTML 覆盖

- `RoboChallenge pi0.5 提交状态面板`：`True`。
- `pi0.5 ALOHA 离线执行`：`True`。
- `inference=162`：`True`。
- `交接报告一致性`：`True`。
- `mismatch=0`：`True`。

## 证据

- `dashboard_status_passed`：`True`。
- `dashboard_card_count_current`：`True`。
- `dashboard_source_count_current`：`True`。
- `dashboard_ready_for_real_submission_false`：`True`。
- `dashboard_key_handoff_consistency_passed`：`True`。
- `dashboard_key_handoff_mismatch_zero`：`True`。
- `gui_packet_passed`：`True`。
- `gui_packet_screenshot_created`：`True`。
- `gui_packet_screenshot_path_exact`：`True`。
- `gui_packet_screenshot_size_matches_file`：`True`。
- `html_exists`：`True`。
- `html_required_phrases_present`：`True`。
- `html_key_handoff_card_present`：`True`。
- `png_exists`：`True`。
- `png_signature_ok`：`True`。
- `png_ihdr_ok`：`True`。
- `png_width_expected`：`True`。
- `png_height_expected_full_page`：`True`。
- `png_size_expected_full_page`：`True`。

## 边界

- 本审计只读取本地 dashboard JSON、HTML 和 PNG 文件。
- 本审计不连接 RoboChallenge 平台、不上传 checkpoint、不启动真实 runner、不读取真实 token 或 local env 内容。

## Blocking

- GUI 截图为当前 42 卡 dashboard 的整页 PNG，且 HTML 覆盖关键交接一致性卡片。
