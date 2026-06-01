#!/usr/bin/env bash
set -euo pipefail

REPO="${REPO:-/home/yjl/robochallenge/repo}"
BASE="${BASE:-/home/yjl/yjl/RoboChallenge/baseline_pi05_multitask}"
OPENPI_ROOT="${OPENPI_ROOT:-/home/yjl/robochallenge/openpi}"
LEROBOT_SRC="${LEROBOT_SRC:-/home/yjl/yjl/RoboChallenge/third_party/lerobot}"
PYTHON_BIN="${PYTHON_BIN:-$BASE/.venv/bin/python3}"

mkdir -p "$REPO/runs" "$REPO/reports"
export PYTHONPATH="$OPENPI_ROOT/src:$OPENPI_ROOT/packages/openpi-client/src:$LEROBOT_SRC:${PYTHONPATH:-}"

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed


REPO = Path(os.environ.get("REPO", "/home/yjl/robochallenge/repo"))
OPENPI_ROOT = Path(os.environ.get("OPENPI_ROOT", "/home/yjl/robochallenge/openpi"))
CACHE_DIR = Path(os.environ.get("OPENPI_DATA_HOME", "~/.cache/openpi")).expanduser().resolve()
DOWNLOAD = os.environ.get("DOWNLOAD_PI05_BASE", "0") == "1"
LOAD_PARAMS = os.environ.get("LOAD_PI05_PARAMS", "0") == "1"
DOWNLOAD_JOBS = int(os.environ.get("DOWNLOAD_JOBS", "1"))
PREFIX = "checkpoints/pi05_base/"
BUCKET = "openpi-assets"
LOCAL_BASE = CACHE_DIR / BUCKET / "checkpoints/pi05_base"
MANIFEST_PATH = REPO / "runs/pi05_base_manifest.json"
STATUS_PATH = REPO / "runs/pi05_base_probe_status.json"
REPORT_PATH = REPO / "reports/pi05_base_repro.md"


def list_gcs_objects() -> list[dict]:
    items: list[dict] = []
    page_token = ""
    while True:
        query = {
            "prefix": PREFIX,
            "fields": "items(name,size),nextPageToken",
            "maxResults": "1000",
        }
        if page_token:
            query["pageToken"] = page_token
        url = f"https://storage.googleapis.com/storage/v1/b/{BUCKET}/o?{urllib.parse.urlencode(query)}"
        with urllib.request.urlopen(url, timeout=60) as resp:
            data = json.load(resp)
        items.extend(data.get("items", []))
        page_token = data.get("nextPageToken", "")
        if not page_token:
            break
    return items


def summarize_config(name: str) -> dict:
    from openpi.training import config as train_config

    cfg = train_config.get_config(name)
    model = cfg.model
    data = cfg.data
    weight_loader = getattr(cfg, "weight_loader", None)
    return {
        "name": cfg.name,
        "model_type": type(model).__name__,
        "model_pi05": getattr(model, "pi05", None),
        "action_dim": getattr(model, "action_dim", None),
        "action_horizon": getattr(model, "action_horizon", None),
        "max_token_len": getattr(model, "max_token_len", None),
        "discrete_state_input": getattr(model, "discrete_state_input", None),
        "data_type": type(data).__name__,
        "repo_id": getattr(data, "repo_id", None),
        "default_prompt": getattr(data, "default_prompt", None),
        "weight_loader": repr(weight_loader),
        "batch_size": getattr(cfg, "batch_size", None),
        "num_train_steps": getattr(cfg, "num_train_steps", None),
    }


def object_local_status(obj: dict) -> dict:
    name = obj["name"]
    size = int(obj.get("size", "0") or 0)
    dest = CACHE_DIR / BUCKET / name
    local_size = dest.stat().st_size if dest.exists() else 0
    return {
        "name": name,
        "size": size,
        "local_path": str(dest),
        "exists": dest.exists(),
        "local_size": local_size,
        "size_match": dest.exists() and local_size == size,
    }


def download_object(obj: dict) -> None:
    name = obj["name"]
    size = int(obj.get("size", "0") or 0)
    dest = CACHE_DIR / BUCKET / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    if size == 0:
        dest.touch()
        return
    if dest.exists() and dest.stat().st_size == size:
        return
    if dest.exists() and dest.stat().st_size > size:
        dest.unlink()

    quoted = urllib.parse.quote(name, safe="/")
    url = f"https://storage.googleapis.com/{BUCKET}/{quoted}"
    curl = shutil.which("curl")
    if curl:
        cmd = [
            curl,
            "-L",
            "--fail",
            "--silent",
            "--show-error",
            "--retry",
            "5",
            "--retry-all-errors",
            "--connect-timeout",
            "30",
            "--speed-time",
            "120",
            "--speed-limit",
            "1024",
            "-C",
            "-",
            "-o",
            str(dest),
            url,
        ]
        print(f"[download] {name} -> {dest}", flush=True)
        subprocess.run(cmd, check=True)
    else:
        print(f"[download] curl not found, using urllib: {name}", flush=True)
        with urllib.request.urlopen(url, timeout=120) as resp, dest.open("ab") as fh:
            shutil.copyfileobj(resp, fh)
    if dest.stat().st_size != size:
        raise RuntimeError(f"下载大小不匹配: {dest} local={dest.stat().st_size} expected={size}")


def load_params_smoke() -> dict:
    from openpi.models import model as openpi_model
    import jax
    import jax.numpy as jnp

    params_path = LOCAL_BASE / "params"
    if not params_path.exists():
        raise FileNotFoundError(f"缺少参数目录: {params_path}")
    t0 = time.time()
    params = openpi_model.restore_params(params_path, dtype=jnp.bfloat16)
    leaves = jax.tree_util.tree_leaves(params)
    leaf_count = len(leaves)
    total_elements = 0
    first_shapes = []
    for leaf in leaves[:20]:
        shape = getattr(leaf, "shape", None)
        dtype = getattr(leaf, "dtype", None)
        size = getattr(leaf, "size", 0)
        first_shapes.append({"shape": list(shape) if shape is not None else None, "dtype": str(dtype)})
        total_elements += int(size or 0)
    for leaf in leaves[20:]:
        total_elements += int(getattr(leaf, "size", 0) or 0)
    return {
        "loaded": True,
        "seconds": round(time.time() - t0, 2),
        "leaf_count": leaf_count,
        "total_elements": total_elements,
        "first_shapes": first_shapes,
    }


def write_report(status: dict) -> None:
    total_gib = status["remote_total_bytes"] / 1024**3
    local_gib = status["local_matched_bytes"] / 1024**3
    configs = status.get("configs", [])
    lines = [
        "# pi0.5 基模复现记录",
        "",
        "## 结论",
        "",
        f"- 官方基模路径：`gs://openpi-assets/checkpoints/pi05_base`。",
        f"- 公共 GCS 对象数：`{status['remote_object_count']}`，总大小约 `{total_gib:.3f} GiB`。",
        f"- 本地缓存路径：`{LOCAL_BASE}`。",
        f"- 当前已匹配大小：`{local_gib:.3f} GiB`。",
        f"- 下载开关 `DOWNLOAD_PI05_BASE={int(DOWNLOAD)}`，并行数 `DOWNLOAD_JOBS={DOWNLOAD_JOBS}`，参数加载开关 `LOAD_PI05_PARAMS={int(LOAD_PARAMS)}`。",
        "",
        "## 配置核对",
        "",
    ]
    for cfg in configs:
        lines.extend(
            [
                f"### {cfg['name']}",
                "",
                f"- model：`{cfg['model_type']}`，`pi05={cfg['model_pi05']}`。",
                f"- action_dim：`{cfg['action_dim']}`，action_horizon：`{cfg['action_horizon']}`。",
                f"- data：`{cfg['data_type']}`，repo_id：`{cfg['repo_id']}`。",
                f"- weight_loader：`{cfg['weight_loader']}`。",
                "",
            ]
        )
    lines.extend(
        [
            "## 说明",
            "",
            "- `pi05_base` 是 Fine-Tuning 基模，不是 RoboChallenge 可直接提交的任务 policy。",
            "- 对 RoboChallenge 提交仍需要在该基模或官方 Table30v2 baseline 上接数据、任务配置和评测入口。",
            "- 真实提交需要用户提供 RoboChallenge 网站的 `user_token` 和 `submission_id`。",
            "",
        ]
    )
    if "load_params_smoke" in status:
        if status.get("load_params_smoke_preserved"):
            lines.extend(["- 本次为轻量探测，下面的参数加载 smoke 来自此前已通过的同一缓存状态。", ""])
        lines.extend(["## 参数加载 smoke", "", f"```json\n{json.dumps(status['load_params_smoke'], ensure_ascii=False, indent=2)}\n```", ""])
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    status: dict = {
        "python": sys.executable,
        "openpi_root": str(OPENPI_ROOT),
        "cache_dir": str(CACHE_DIR),
        "local_base": str(LOCAL_BASE),
        "download_requested": DOWNLOAD,
        "download_jobs": DOWNLOAD_JOBS,
        "load_params_requested": LOAD_PARAMS,
    }
    config_names = [
        "pi05_libero",
        "pi05_aloha_pen_uncap",
        "pi05_full_droid_finetune",
        "pi05_droid_finetune",
    ]
    configs = []
    for name in config_names:
        try:
            configs.append(summarize_config(name))
        except Exception as exc:  # noqa: BLE001 - status file should preserve failures.
            configs.append({"name": name, "error": f"{type(exc).__name__}: {exc}"})
    status["configs"] = configs

    objects = list_gcs_objects()
    statuses = [object_local_status(obj) for obj in objects]
    status["remote_object_count"] = len(objects)
    status["remote_total_bytes"] = sum(x["size"] for x in statuses)
    status["local_matched_bytes"] = sum(x["size"] for x in statuses if x["size_match"])
    status["local_complete"] = bool(statuses) and all(x["size_match"] for x in statuses)
    MANIFEST_PATH.write_text(json.dumps({"objects": statuses}, ensure_ascii=False, indent=2), encoding="utf-8")

    if DOWNLOAD:
        pending = [obj for obj in objects if not object_local_status(obj)["size_match"]]
        if pending and DOWNLOAD_JOBS > 1:
            with ThreadPoolExecutor(max_workers=DOWNLOAD_JOBS) as executor:
                future_to_name = {executor.submit(download_object, obj): obj["name"] for obj in pending}
                for future in as_completed(future_to_name):
                    name = future_to_name[future]
                    try:
                        future.result()
                        print(f"[done] {name}", flush=True)
                    except Exception as exc:
                        raise RuntimeError(f"下载失败: {name}: {exc}") from exc
        else:
            for obj in pending:
                download_object(obj)
        statuses = [object_local_status(obj) for obj in objects]
        status["local_matched_bytes"] = sum(x["size"] for x in statuses if x["size_match"])
        status["local_complete"] = bool(statuses) and all(x["size_match"] for x in statuses)
        MANIFEST_PATH.write_text(json.dumps({"objects": statuses}, ensure_ascii=False, indent=2), encoding="utf-8")

    if LOAD_PARAMS:
        status["load_params_smoke"] = load_params_smoke()
    elif STATUS_PATH.exists():
        try:
            previous = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
            previous_smoke = previous.get("load_params_smoke")
            if previous_smoke and previous_smoke.get("loaded") and status.get("local_complete"):
                status["load_params_smoke"] = previous_smoke
                status["load_params_smoke_preserved"] = True
        except Exception:
            pass

    STATUS_PATH.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(status)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["local_complete"] or not DOWNLOAD else 1


if __name__ == "__main__":
    raise SystemExit(main())
PY
