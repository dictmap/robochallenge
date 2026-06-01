#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-/home/yjl/yjl/RoboChallenge/baseline_pi05_multitask}"
PYTHON_BIN="${PYTHON_BIN:-$BASE/.venv/bin/python3}"
LEROBOT_SRC="${LEROBOT_SRC:-/home/yjl/yjl/RoboChallenge/third_party/lerobot}"

export PYTHONPATH="$BASE/openpi/src:$BASE/openpi/packages/openpi-client/src:$LEROBOT_SRC:${PYTHONPATH:-}"

"$PYTHON_BIN" - <<'PY'
import importlib.util
import json
import os
import sys

names = [
    "openpi",
    "openpi_rtc",
    "openpi_client",
    "jax",
    "torch",
    "cv2",
    "lerobot",
    "lerobot.common.datasets.lerobot_dataset",
    "jupyterlab",
    "ipykernel",
    "nbformat",
]
result = {
    "python": sys.executable,
    "pythonpath_head": os.environ.get("PYTHONPATH", "").split(":")[:5],
    "imports": {name: bool(importlib.util.find_spec(name)) for name in names},
}
print(json.dumps(result, ensure_ascii=False, indent=2))
missing = [name for name, ok in result["imports"].items() if not ok]
raise SystemExit(1 if missing else 0)
PY
