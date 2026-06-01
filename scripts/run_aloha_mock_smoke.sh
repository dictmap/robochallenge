#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-/home/yjl/yjl/RoboChallenge/baseline_pi05_multitask}"
REPO="${REPO:-/home/yjl/robochallenge/repo}"
PYTHON_BIN="${PYTHON_BIN:-$BASE/.venv/bin/python3}"
CHECKPOINT="${CHECKPOINT:-/home/yjl/yjl/RoboChallenge/checkpoints/table30v2_multitask_baseline_aloha}"
PROMPT="${PROMPT:-Put the toothbrush and toothpaste into the toiletries case in sequence, close the case, and then place it into the basket.}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-300}"

mkdir -p "$REPO/runs"
cd "$BASE"

cat > mock_server/mock_settings.py <<'EOF'
# -*- coding: utf-8 -*-
REALSENSE_DEVICE_IDS = None
ROBOT_TAG = 'aloha'
RECORD_DATA_DIR = '../20260413/aloha/pack_the_toothbrush_holder'
EOF

pkill -f 'mock_robot_server.py' 2>/dev/null || true
(
  cd "$BASE/mock_server"
  nohup "$PYTHON_BIN" mock_robot_server.py > "$REPO/runs/mock_server_aloha.log" 2>&1 &
  echo $! > "$REPO/runs/mock_server_aloha.pid"
)
sleep 5

set +e
cd "$REPO"
PYTHONPATH="$BASE/openpi/src:$BASE/openpi/packages/openpi-client/src:/home/yjl/yjl/RoboChallenge/third_party/lerobot:${PYTHONPATH:-}" timeout "$TIMEOUT_SECONDS"s "$PYTHON_BIN" "$REPO/test.py" \
  --checkpoint "$CHECKPOINT" \
  --prompt "$PROMPT" \
  --robot_type aloha \
  --action_type joint \
  --image_size 640x480 \
  --valid_action_num 2 \
  --duration 0.033 \
  --max_wait 20 \
  > "$REPO/runs/policy_smoke_aloha.log" 2>&1
code=$?
set -e

kill "$(cat "$REPO/runs/mock_server_aloha.pid")" 2>/dev/null || true
sleep 2

if grep -q 'Inference result' "$REPO/runs/policy_smoke_aloha.log"; then
  smoke="passed"
else
  smoke="failed"
fi

cat > "$REPO/runs/policy_smoke_aloha_status.json" <<EOF
{"exit_code": $code, "smoke": "$smoke", "log": "runs/policy_smoke_aloha.log", "server_log": "runs/mock_server_aloha.log"}
EOF

cat "$REPO/runs/policy_smoke_aloha_status.json"
if [ "$smoke" != "passed" ]; then
  tail -120 "$REPO/runs/policy_smoke_aloha.log"
  exit 1
fi
