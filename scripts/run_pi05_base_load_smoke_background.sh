#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-/home/yjl/robochallenge/repo}"

cd "$REPO"
mkdir -p runs
rm -f runs/pi05_base_load_smoke.done runs/pi05_base_load_smoke.exit

(
  set +e
  env DOWNLOAD_PI05_BASE=0 LOAD_PI05_PARAMS=1 JAX_PLATFORMS=cpu XLA_PYTHON_CLIENT_PREALLOCATE=false \
    bash scripts/probe_pi05_base_model.sh \
    > runs/pi05_base_load_smoke.log 2>&1
  code=$?
  echo "$code" > runs/pi05_base_load_smoke.exit
  date -Is > runs/pi05_base_load_smoke.done
  exit "$code"
) &
pid=$!

echo "$pid" > runs/pi05_base_load_smoke.pid
echo "$pid"
