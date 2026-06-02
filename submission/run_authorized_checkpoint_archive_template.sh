#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIRM_VALUE="${ROBOCHALLENGE_ARCHIVE_CONFIRM:-}"
CONFIRM_PHRASE="CREATE_ROBOCHALLENGE_CHECKPOINT_ARCHIVE"

cd "$REPO_ROOT"

echo "[authorized-checkpoint-archive] repo=$REPO_ROOT"
echo "[authorized-checkpoint-archive] confirmation_present=$([[ -n "$CONFIRM_VALUE" ]] && echo true || echo false)"
echo "[authorized-checkpoint-archive] dry_run_first=true"
echo "[authorized-checkpoint-archive] upload_performed=false"

python3 scripts/audit_checkpoint_archive_plan.py
python3 scripts/audit_checkpoint_split_plan.py
python3 scripts/create_checkpoint_archive.py

if [[ "$CONFIRM_VALUE" != "$CONFIRM_PHRASE" ]]; then
  echo "[authorized-checkpoint-archive] missing explicit archive confirmation"
  echo "[authorized-checkpoint-archive] set ROBOCHALLENGE_ARCHIVE_CONFIRM=$CONFIRM_PHRASE only after user authorizes local 12GB+ tar creation"
  echo "[authorized-checkpoint-archive] stop before creating tar"
  exit 1
fi

echo "[authorized-checkpoint-archive] confirmation accepted; starting archive creation"
python3 scripts/create_checkpoint_archive.py --execute --confirm-create-large-archive
echo "[authorized-checkpoint-archive] archive creation finished; upload still requires separate user authorization"
