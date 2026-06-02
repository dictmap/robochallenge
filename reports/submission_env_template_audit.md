# 真实提交环境变量模板审计

## 结论

- 审计状态：`passed=True`。
- 模板路径：`submission/robochallenge_env_template.sh`。
- 建议本地副本：`submission/robochallenge_env.local.sh`。
- 是否连接 RoboChallenge 平台：`False`。
- 是否执行上传：`False`。
- 是否读取真实凭据：`False`。
- 是否打印真实凭据：`False`。
- 是否发现疑似密钥模式：`False`。

## 必需变量

- `ROBOCHALLENGE_USER_TOKEN`：present=`True`，placeholder=`True`。
- `ROBOCHALLENGE_SUBMISSION_ID`：present=`True`，placeholder=`True`。
- `ROBOCHALLENGE_SUBMISSION_VARIANT`：present=`True`，placeholder=`True`。
- `ROBOCHALLENGE_LORA_CHECKPOINT_LINK`：present=`True`，placeholder=`True`。
- `ROBOCHALLENGE_CHECKPOINT_LINK`：present=`True`，placeholder=`True`。

## Git 忽略检查

- `submission/robochallenge_env.local.sh`：ignored=`True`。
- `.env`：ignored=`True`。
- `.env.local`：ignored=`True`。

## Blocking

- 无模板侧阻塞；baseline 默认路线仍取决于用户提供凭据、submission id 和真实 runner 强确认。
