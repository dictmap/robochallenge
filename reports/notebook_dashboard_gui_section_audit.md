# Notebook GUI 首屏截图章节审计

## 结论

- 审计状态：`passed=True`。
- Notebook：`notebooks/robochallenge_pi05_submit_cn.ipynb`。
- 章节：`第 47 节：GUI 首屏截图证据`。
- 章节索引：`95`。
- 代码 cell id：`dashboard-gui-screenshot-code`。
- 代码 cell 干净：`True`。
- 默认运行 flag：`RUN_DASHBOARD_GUI_SCREENSHOT_PACKET` / `True`。
- GUI packet：`runs/dashboard_gui_access_packet.json`。
- 截图路径：`reports/submission_status_dashboard_browser.png`。
- 是否连接平台：`False`。
- 是否上传：`False`。
- 是否读取真实凭据：`False`。

## 语义检查

- `run_flag_default_true`：`True`。
- `uses_gui_packet_script`：`True`。
- `reads_gui_packet_json`：`True`。
- `checks_packet_passed`：`True`。
- `checks_browser_not_blocked`：`True`。
- `checks_screenshot_created`：`True`。
- `checks_screenshot_path`：`True`。
- `checks_screenshot_size`：`True`。
- `checks_no_platform_contact`：`True`。
- `checks_no_upload`：`True`。
- `checks_no_credential_read`：`True`。
- `displays_screenshot_inline`：`True`。
- `does_not_read_local_env`：`True`。
- `does_not_call_real_runner`：`True`。

## GUI Packet 检查

- `gui_packet_passed`：`True`。
- `gui_packet_screenshot_created`：`True`。
- `gui_packet_browser_not_blocked`：`True`。
- `gui_packet_screenshot_path`：`True`。
- `gui_packet_screenshot_size`：`True`。
- `screenshot_file_exists`：`True`。
- `html_file_exists`：`True`。
- `packet_no_platform_contact`：`True`。
- `packet_no_upload`：`True`。
- `packet_no_credential_read`：`True`。

## 禁止片段

- `submission/robochallenge_env.local.sh`：`False`。
- `ROBOCHALLENGE_USER_TOKEN`：`False`。
- `ROBOCHALLENGE_SUBMISSION_ID`：`False`。
- `ROBOCHALLENGE_REAL_RUN_CONFIRM`：`False`。
- `RUN_REAL_ROBOCHALLENGE_SUBMISSION`：`False`。
- `run_authorized_preflight_template.sh`：`False`。
- `run_ready_real_submission_template.sh`：`False`。
- `run_table30v2_aloha_demo_template.sh`：`False`。
- `demo.py`：`False`。
- `getpass.`：`False`。
- `input(`：`False`。
- `requests.`：`False`。
- `urllib.request`：`False`。
- `subprocess.run(`：`False`。
- `os.system(`：`False`。
- `curl `：`False`。
- `wget `：`False`。

## Blocking

- Jupyter GUI 首屏截图章节已通过语义审计，默认只读且可内联显示 PNG。
