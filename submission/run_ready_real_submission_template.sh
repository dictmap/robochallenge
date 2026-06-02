#!/usr/bin/env bash
set +x
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROBOCHALLENGE_ENV_FILE:-$REPO_ROOT/submission/robochallenge_env.local.sh}"
CONFIRM_PHRASE="RUN_REAL_ROBOCHALLENGE_SUBMISSION"

cd "$REPO_ROOT"

echo "[ready-real-runner] repo=$REPO_ROOT"
echo "[ready-real-runner] env_file_present=$([[ -f "$ENV_FILE" ]] && echo true || echo false)"

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck source=/dev/null
  source "$ENV_FILE"
fi

VARIANT="${ROBOCHALLENGE_SUBMISSION_VARIANT:-baseline}"
VERIFY_DOWNLOAD="${ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD:-0}"
CONFIRM_VALUE="${ROBOCHALLENGE_REAL_RUN_CONFIRM:-}"

echo "[ready-real-runner] variant=$VARIANT"
echo "[ready-real-runner] verify_download=$VERIFY_DOWNLOAD"
echo "[ready-real-runner] confirmation_present=$([[ -n "$CONFIRM_VALUE" ]] && echo true || echo false)"

python3 scripts/audit_checkpoint_link_intake.py --scenario-only
if [[ "$VERIFY_DOWNLOAD" == "1" ]]; then
  python3 scripts/audit_checkpoint_link_download_verification.py --verify-download
else
  python3 scripts/audit_checkpoint_link_download_verification.py
fi
python3 scripts/audit_real_submission_readiness.py

readiness_field() {
  local key="$1"
  python3 - "$key" <<'PY'
import json
import sys
from pathlib import Path

key = sys.argv[1]
status = json.loads(Path("runs/real_submission_readiness.json").read_text(encoding="utf-8"))
print("true" if status.get(key) is True else "false")
PY
}

READY="$(readiness_field ready_for_real_submission)"
LORA_READY="$(readiness_field local_lora_runner_ready)"
BASELINE_READY="$(readiness_field local_baseline_runner_ready)"

if [[ "$READY" != "true" ]]; then
  echo "[ready-real-runner] ready_for_real_submission=false"
  echo "[ready-real-runner] stop before dry-run and real runner"
  exit 1
fi

case "$VARIANT" in
  lora)
    if [[ "$LORA_READY" != "true" ]]; then
      echo "[ready-real-runner] local_lora_runner_ready=false" >&2
      exit 1
    fi
    ROBOCHALLENGE_DRY_RUN=1 bash submission/run_table30v2_aloha_lora_demo_template.sh
    RUNNER=(bash submission/run_table30v2_aloha_lora_demo_template.sh)
    ;;
  baseline)
    if [[ "$BASELINE_READY" != "true" ]]; then
      echo "[ready-real-runner] local_baseline_runner_ready=false" >&2
      exit 1
    fi
    ROBOCHALLENGE_DRY_RUN=1 bash submission/run_table30v2_aloha_demo_template.sh
    RUNNER=(bash submission/run_table30v2_aloha_demo_template.sh)
    ;;
  *)
    echo "[ready-real-runner] unsupported variant; use lora or baseline" >&2
    exit 2
    ;;
esac

if [[ "$CONFIRM_VALUE" != "$CONFIRM_PHRASE" ]]; then
  echo "[ready-real-runner] missing explicit real-run confirmation"
  echo "[ready-real-runner] set ROBOCHALLENGE_REAL_RUN_CONFIRM=$CONFIRM_PHRASE only after user authorizes platform submission"
  echo "[ready-real-runner] stop before real runner"
  exit 1
fi

echo "[ready-real-runner] confirmation accepted; starting real runner"
"${RUNNER[@]}"
