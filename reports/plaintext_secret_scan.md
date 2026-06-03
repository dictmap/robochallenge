# 明文凭据扫描

## 结论

- 审计状态：`passed=True`。
- 扫描范围：`git tracked files plus unignored untracked files`。
- 扫描文本文件数：`247`。
- 跳过二进制文件数：`0`。
- 规则数量：`7`。
- 命中数量：`0`。
- 是否连接平台：`False`。
- 是否执行上传：`False`。
- 是否打印匹配值：`False`。

## 命中项

- 未发现明文凭据模式。

## Blocking

- 如发现命中项，先移除明文凭据并轮换对应 token，再重新运行本审计。
- 本审计不替代真实平台权限检查；baseline 真实提交仍需要用户目标确认、token、submission id、variant=baseline 和真实 runner 强确认。
