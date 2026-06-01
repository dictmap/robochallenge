#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_DIR:-/home/yjl/robochallenge/repo}"
BASELINE_DIR="${BASELINE_DIR:-/home/yjl/yjl/RoboChallenge/baseline_pi05_multitask}"
PYTHON_BIN="${PYTHON_BIN:-$BASELINE_DIR/.venv/bin/python3}"
NOTEBOOK="${NOTEBOOK:-notebooks/robochallenge_pi05_submit_cn.ipynb}"
OUTPUT="${OUTPUT:-robochallenge_pi05_submit_cn.executed.ipynb}"

cd "$REPO_DIR"
"$PYTHON_BIN" -m nbconvert \
  --to notebook \
  --execute "$NOTEBOOK" \
  --output "$OUTPUT" \
  --output-dir notebooks \
  --ExecutePreprocessor.timeout=180
