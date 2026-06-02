#!/usr/bin/env bash
# RoboChallenge 真实提交环境变量模板。
# 使用方式：
#   cp submission/robochallenge_env_template.sh submission/robochallenge_env.local.sh
#   chmod 600 submission/robochallenge_env.local.sh
#   $EDITOR submission/robochallenge_env.local.sh
#   source submission/robochallenge_env.local.sh
#
# 只能编辑 .local.sh 本地副本；不要把真实 token、submission id 或 checkpoint link 写入本模板。

export ROBOCHALLENGE_USER_TOKEN="<真实 user token>"
export ROBOCHALLENGE_SUBMISSION_ID="<真实 submission id>"

# 默认推荐先走官方 Table30v2 ALOHA baseline；只有明确选择 LoRA 物化路线时再改成 lora。
export ROBOCHALLENGE_SUBMISSION_VARIANT="baseline"

# LoRA / fine-tuned checkpoint 下载链接。走 LoRA 路线时设置这一项。
export ROBOCHALLENGE_LORA_CHECKPOINT_LINK="<真实 checkpoint 下载 URL>"

# 可选：如果平台表单或 baseline 路线要求通用 checkpoint link，再设置这一项。
export ROBOCHALLENGE_CHECKPOINT_LINK="<真实 checkpoint 下载 URL>"
