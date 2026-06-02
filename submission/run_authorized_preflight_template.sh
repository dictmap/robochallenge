#!/usr/bin/env bash
set +x
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROBOCHALLENGE_ENV_FILE:-$REPO_ROOT/submission/robochallenge_env.local.sh}"

cd "$REPO_ROOT"

check_local_env_permissions() {
  local path="$1"
  local mode
  mode="$(python3 - "$path" <<'PY'
import os
import stat
import sys

print(oct(stat.S_IMODE(os.stat(sys.argv[1]).st_mode)))
PY
)"
  case "$mode" in
    0o600|0o400)
      ;;
    *)
      echo "[authorized-preflight] local env permissions are too broad: $mode" >&2
      echo "[authorized-preflight] run: chmod 600 $path" >&2
      exit 65
      ;;
  esac
}

validate_variant() {
  local value="$1"
  case "$value" in
    baseline|lora)
      ;;
    *)
      echo "[authorized-preflight] unsupported submission variant; use baseline or lora" >&2
      exit 67
      ;;
  esac
}

validate_bool_flag() {
  local name="$1"
  local value="$2"
  case "$value" in
    0|1)
      ;;
    *)
      echo "[authorized-preflight] $name must be 0 or 1; do not use true/false/yes/no or blank values" >&2
      exit 68
      ;;
  esac
}

echo "[authorized-preflight] repo=$REPO_ROOT"
echo "[authorized-preflight] env_file_present=$([[ -f "$ENV_FILE" ]] && echo true || echo false)"

if [[ -f "$ENV_FILE" ]]; then
  check_local_env_permissions "$ENV_FILE"
  # shellcheck source=/dev/null
  source "$ENV_FILE"
fi

VARIANT="${ROBOCHALLENGE_SUBMISSION_VARIANT:-baseline}"
VERIFY_DOWNLOAD="${ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD:-0}"
REQUIRE_READY="${ROBOCHALLENGE_REQUIRE_READY:-0}"

validate_variant "$VARIANT"
validate_bool_flag ROBOCHALLENGE_VERIFY_CHECKPOINT_DOWNLOAD "$VERIFY_DOWNLOAD"
validate_bool_flag ROBOCHALLENGE_REQUIRE_READY "$REQUIRE_READY"

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
esac

echo "[authorized-preflight] dry-run passed; real runner still requires explicit user authorization"
