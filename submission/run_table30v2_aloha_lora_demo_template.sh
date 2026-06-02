#!/usr/bin/env bash
set -euo pipefail

# RoboChallenge Table30v2 ALOHA pi0.5 LoRA 完整物化 checkpoint 提交启动模板。
# 不要把真实 token 写进仓库；运行前在 shell 里 export。
: "${ROBOCHALLENGE_USER_TOKEN:?请先 export ROBOCHALLENGE_USER_TOKEN}"
: "${ROBOCHALLENGE_SUBMISSION_ID:?请先 export ROBOCHALLENGE_SUBMISSION_ID}"

reject_placeholder() {
  local name="$1"
  local value="$2"
  case "$value" in
    *"<"*|*">"*|*"真实"*|*"占位"*|*"placeholder"*|*"PLACEHOLDER"*|*"replace_me"*|*"REPLACE_ME"*|*"example"*|*"EXAMPLE"*)
      echo "$name 看起来仍是占位符，请设置真实值。" >&2
      exit 64
      ;;
  esac
}

reject_placeholder ROBOCHALLENGE_USER_TOKEN "$ROBOCHALLENGE_USER_TOKEN"
reject_placeholder ROBOCHALLENGE_SUBMISSION_ID "$ROBOCHALLENGE_SUBMISSION_ID"

cd "$(dirname "$0")/.."

DEFAULT_CHECKPOINT='runs/openpi_rtc_lora_materialized_policy_checkpoint'
DEFAULT_PROMPT='Put the toothbrush and toothpaste into the toiletries case in sequence, close the case, and then place it into the basket.'
CHECKPOINT="${ROBOCHALLENGE_CHECKPOINT:-$DEFAULT_CHECKPOINT}"
PROMPT="${ROBOCHALLENGE_PROMPT:-$DEFAULT_PROMPT}"

if [[ "${ROBOCHALLENGE_DRY_RUN:-0}" == "1" ]]; then
  echo "dry_run=true"
  echo "checkpoint_length=${#CHECKPOINT}"
  echo "prompt_length=${#PROMPT}"
  echo "user_token_length=${#ROBOCHALLENGE_USER_TOKEN}"
  echo "submission_id_length=${#ROBOCHALLENGE_SUBMISSION_ID}"
  echo "robot_type=aloha"
  exit 0
fi

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
