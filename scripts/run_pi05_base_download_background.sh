#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-/home/yjl/robochallenge/repo}"
DOWNLOAD_JOBS="${DOWNLOAD_JOBS:-4}"

cd "$REPO"
mkdir -p runs
rm -f runs/pi05_base_download.done runs/pi05_base_download.exit

(
  set +e
  env DOWNLOAD_PI05_BASE=1 LOAD_PI05_PARAMS=0 DOWNLOAD_JOBS="$DOWNLOAD_JOBS" \
    bash scripts/probe_pi05_base_model.sh \
    > runs/pi05_base_download.log 2>&1
  code=$?
  echo "$code" > runs/pi05_base_download.exit
  date -Is > runs/pi05_base_download.done
  exit "$code"
) &
pid=$!

echo "$pid" > runs/pi05_base_download.pid
echo "$pid"
