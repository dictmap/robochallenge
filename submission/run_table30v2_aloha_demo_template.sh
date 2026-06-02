#!/usr/bin/env bash
set -euo pipefail

# RoboChallenge Table30v2 ALOHA pi0.5 baseline 提交启动模板。
# 不要把真实 token 写进仓库；运行前在 shell 里 export。
: "${ROBOCHALLENGE_USER_TOKEN:?请先 export ROBOCHALLENGE_USER_TOKEN}"
: "${ROBOCHALLENGE_SUBMISSION_ID:?请先 export ROBOCHALLENGE_SUBMISSION_ID}"

CHECKPOINT="${ROBOCHALLENGE_CHECKPOINT:-/home/yjl/yjl/RoboChallenge/checkpoints/table30v2_multitask_baseline_aloha}"
PROMPT="${ROBOCHALLENGE_PROMPT:-Put the toothbrush and toothpaste into the toiletries case in sequence, close the case, and then place it into the basket.}"

cd "$(dirname "$0")/.."

python3 demo.py \
  --user_token "$ROBOCHALLENGE_USER_TOKEN" \
  --submission_id "$ROBOCHALLENGE_SUBMISSION_ID" \
  --checkpoint "$CHECKPOINT" \
  --prompt "$PROMPT" \
  --action_type joint \
  --duration 0.033 \
  --valid_action_num 30 \
  --image_size "640x480" \
  --robot_type aloha
