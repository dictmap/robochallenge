# Checkpoint Link 下载校验审计

## 结论

- 审计状态：`passed=True`。
- 是否请求联网校验：`False`。
- 是否接触下载 host：`False`。
- 下载是否已验证：`False`。
- 是否连接 RoboChallenge 平台：`False`。
- 是否上传：`False`。
- 是否读取凭据：`False`。
- 是否打印链接明文：`False`。
- curl 可用：`True`。

## 当前链接状态

- `ROBOCHALLENGE_CHECKPOINT_LINK`：present=`False`，length=`0`，https=`False`，archive_hint=`False`，placeholder_like=`False`，accepted_shape=`False`。
- `ROBOCHALLENGE_LORA_CHECKPOINT_LINK`：present=`False`，length=`0`，https=`False`，archive_hint=`False`，placeholder_like=`False`，accepted_shape=`False`。

## 授权后校验命令

- `head`：`curl -L --fail --head --max-time 30 [REDACTED_CHECKPOINT_LINK]`。
- `range_smoke`：`curl -L --fail --range 0-1048575 --output /dev/null --max-time 30 [REDACTED_CHECKPOINT_LINK]`。

## 输入证据

- link intake passed：`True`。
- split plan passed：`True`。
- expected archive GiB：`11.064`。
- expected part count：`3`。

## Blocking

- 缺少真实 checkpoint link；当前只能审计下载校验协议，不能联网验证。
- 未请求 --verify-download；本轮不联网、不下载、不接触 checkpoint link host。
