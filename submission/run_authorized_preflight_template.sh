#!/usr/bin/env bash
set +x
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROBOCHALLENGE_ENV_FILE:-$REPO_ROOT/submission/robochallenge_env.local.sh}"

cd "$REPO_ROOT"

echo "[authorized-preflight] repo=$REPO_ROOT"
echo "[authorized-preflight] env_file_present=$([[ -f "$ENV_FILE" ]] && echo true || echo false)"

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck source=/dev/null
  source "$ENV_FILE"
fi

VARIANT="${ROBOCHALLENGE_SUBMISSION_VARIANT:-baseline}"
VERIFY_DOWNLOAD="${ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD:-0}"
REQUIRE_READY="${ROBOCHALLENGE_REQUIRE_READY:-0}"

echo "[authorized-preflight] variant=$VARIANT"
echo "[authorized-preflight] verify_download=$VERIFY_DOWNLOAD"

python3 scripts/audit_checkpoint_link_intake.py

if [[ "$VERIFY_DOWNLOAD" == "1" ]]; then
  echo "[authorized-preflight] checkpoint link download verification is explicitly enabled"
  python3 scripts/audit_checkpoint_link_download_verification.py --verify-download
else
  python3 scripts/audit_checkpoint_link_download_verification.py
fi

python3 scripts/audit_real_submission_readiness.py
BLOCKERS_RETURN=0
python3 scripts/audit_submission_blockers_summary.py || BLOCKERS_RETURN=$?

READY="$(python3 - <<'PY'
import json
from pathlib import Path
status = json.loads(Path("runs/real_submission_readiness.json").read_text(encoding="utf-8"))
print("true" if status.get("ready_for_real_submission") is True else "false")
PY
)"

if [[ "$READY" != "true" ]]; then
  echo "[authorized-preflight] ready_for_real_submission=false"
  echo "[authorized-preflight] stop before runner dry-run; see reports/submission_blockers_summary.md"
  if [[ "$REQUIRE_READY" == "1" ]]; then
    exit 1
  fi
  exit 0
fi

if [[ "$BLOCKERS_RETURN" != "0" ]]; then
  echo "[authorized-preflight] blockers summary still reports route-aware user decisions; continuing dry-run only" >&2
fi

case "$VARIANT" in
  lora)
    ROBOCHALLENGE_DRY_RUN=1 bash submission/run_table30v2_aloha_lora_demo_template.sh
    ;;
  baseline)
    ROBOCHALLENGE_DRY_RUN=1 bash submission/run_table30v2_aloha_demo_template.sh
    ;;
  *)
    echo "[authorized-preflight] unsupported variant; use lora or baseline" >&2
    exit 2
    ;;
esac

echo "[authorized-preflight] dry-run passed; real runner still requires explicit user authorization"
