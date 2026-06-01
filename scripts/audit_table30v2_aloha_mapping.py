#!/usr/bin/env python3
"""Audit the minimal Table30v2 ALOHA shard mapping for OpenPI/LeRobot."""

from __future__ import annotations

import json
import os
from pathlib import Path
import statistics
import sys


ROOT = Path(__file__).resolve().parents[1]
BASELINE = Path(os.environ.get("BASELINE", "/home/yjl/yjl/RoboChallenge/baseline_pi05_multitask"))
BASELINE_PYTHON = BASELINE / ".venv/bin/python3"
if (
    BASELINE_PYTHON.exists()
    and Path(sys.executable).resolve() != BASELINE_PYTHON.resolve()
    and os.environ.get("TABLE30V2_ALOHA_MAPPING_REEXEC") != "1"
):
    os.environ["TABLE30V2_ALOHA_MAPPING_REEXEC"] = "1"
    os.execv(str(BASELINE_PYTHON), [str(BASELINE_PYTHON), *sys.argv])

import cv2
OPENPI_SRC = BASELINE / "openpi/src"
OPENPI_CLIENT_SRC = BASELINE / "openpi/packages/openpi-client/src"
LEROBOT_SRC = Path(os.environ.get("LEROBOT_SRC", "/home/yjl/yjl/RoboChallenge/third_party/lerobot"))
TASK = os.environ.get("TASK", "pack_the_toothbrush_holder")
ROBOT = os.environ.get("ROBOT", "aloha")
EPISODE_DIR = Path(os.environ.get("EPISODE_DIR", str(BASELINE / f"20260413/{ROBOT}/{TASK}")))
TASK_INFO = Path(
    os.environ.get(
        "TASK_INFO",
        f"/home/yjl/yjl/RoboChallenge/datasets/Table30v2_extracted/{TASK}/meta/task_info.json",
    )
)
CHECKPOINT = Path(
    os.environ.get(
        "CHECKPOINT",
        "/home/yjl/yjl/RoboChallenge/checkpoints/table30v2_multitask_baseline_aloha",
    )
)
CONFIG_NAME = os.environ.get("CONFIG_NAME", "cvpr_multitask_aloha_rtc")
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
STATUS_PATH = RUNS_DIR / "table30v2_aloha_mapping_audit.json"
REPORT_PATH = REPORTS_DIR / "table30v2_aloha_mapping.md"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl_sample(path: Path, limit: int = 20) -> tuple[list[dict], int]:
    rows = []
    count = 0
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            count += 1
            if len(rows) < limit:
                rows.append(json.loads(line))
    return rows, count


def dim_summary(rows: list[dict]) -> dict:
    keys = sorted({key for row in rows for key in row.keys()})
    summary = {}
    for key in keys:
        values = [row.get(key) for row in rows if key in row]
        first = values[0]
        if isinstance(first, list):
            lengths = [len(v) for v in values if isinstance(v, list)]
            summary[key] = {
                "kind": "list",
                "lengths": sorted(set(lengths)),
                "first_values": first[:5],
            }
        else:
            numeric = [v for v in values if isinstance(v, (int, float))]
            summary[key] = {
                "kind": type(first).__name__,
                "first_value": first,
                "mean_first_sample": statistics.mean(numeric) if numeric else None,
            }
    return summary


def video_summary(videos_dir: Path) -> dict:
    result = {}
    for path in sorted(videos_dir.glob("*.mp4")):
        cap = cv2.VideoCapture(str(path))
        ok, frame = cap.read()
        result[path.name] = {
            "opened": bool(cap.isOpened()),
            "frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "fps": float(cap.get(cv2.CAP_PROP_FPS)),
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "first_frame_shape": list(frame.shape) if ok and frame is not None else None,
        }
        cap.release()
    return result


def config_summary() -> dict:
    sys.path[:0] = [str(OPENPI_SRC), str(OPENPI_CLIENT_SRC), str(LEROBOT_SRC)]
    from openpi_rtc.training import config as train_config

    cfg = train_config.get_config(CONFIG_NAME)
    return {
        "name": cfg.name,
        "model_type": type(cfg.model).__name__,
        "pi05": getattr(cfg.model, "pi05", None),
        "model_action_dim": getattr(cfg.model, "action_dim", None),
        "action_horizon": getattr(cfg.model, "action_horizon", None),
        "data_type": type(cfg.data).__name__,
        "repo_id": getattr(cfg.data, "repo_id", None),
        "action_sequence_keys": getattr(cfg.data.base_config, "action_sequence_keys", None),
        "prompt_from_task": getattr(cfg.data.base_config, "prompt_from_task", None),
        "random_action_offset": getattr(cfg.data.base_config, "random_action_offset", None),
        "weight_loader": repr(cfg.weight_loader),
    }


def norm_stats_summary() -> dict:
    path = CHECKPOINT / "assets/cvpr_multitask_aloha/norm_stats.json"
    data = load_json(path)
    stats = data["norm_stats"]
    return {
        "path": str(path),
        "keys": sorted(stats.keys()),
        "dims": {
            key: {
                "mean": len(value.get("mean", [])),
                "std": len(value.get("std", [])),
                "q01": len(value.get("q01", [])),
                "q99": len(value.get("q99", [])),
            }
            for key, value in stats.items()
        },
    }


def build_mapping(status: dict) -> dict:
    return {
        "raw_to_lerobot": {
            "observation/cam_high": "videos/cam_high_rgb.mp4 frame",
            "observation/cam_wrist_left": "videos/cam_left_wrist_rgb.mp4 frame",
            "observation/cam_wrist_right": "videos/cam_right_wrist_rgb.mp4 frame",
            "state": "concat(left.master_qpos[0:7], right.master_qpos[0:7]) -> 14",
            "action": "concat(left.master_qpos[t+1][0:7], right.master_qpos[t+1][0:7]) -> 14",
            "prompt/task": "Table30v2 task_info.task_desc.prompt",
        },
        "lerobot_to_openpi": {
            "repack": "LeRobotW1DualDataConfig + AlohaDualInputs expects observation/cam_high, observation/cam_wrist_left, observation/cam_wrist_right, state, actions/prompt",
            "model_padding": f"14-dim state/action padded to pi0.5 model action_dim={status['config']['model_action_dim']}",
            "policy_output": "AlohaDualOutputs returns actions[:, :14]",
        },
    }


def write_report(status: dict) -> None:
    lines = [
        "# Table30v2 ALOHA 最小分片字段映射",
        "",
        "## 结论",
        "",
        "- 官方 `convert_to_lerobot.py` 是单臂模板，不能直接用于当前 ALOHA 双臂分片。",
        "- 当前可用最小分片是 `pack_the_toothbrush_holder`，包含 `left_states.jsonl`、`right_states.jsonl` 和三路视频。",
        "- 数据本体是 14 维双臂状态/动作：左臂 7 维 + 右臂 7 维。",
        f"- OpenPI 配置 `{CONFIG_NAME}` 使用 pi0.5，模型动作维度 `{status['config']['model_action_dim']}`，训练/推理通过 padding 和输出截断桥接 14 维数据。",
        "- checkpoint 的 `cvpr_multitask_aloha` norm stats 也是 14 维 `state/actions`，与该分片一致。",
        "",
        "## 样例分片",
        "",
        f"- episode：`{EPISODE_DIR}`",
        f"- task_info：`{TASK_INFO}`",
        f"- prompt：{status['task_info']['task_desc']['prompt']}",
        f"- task_tag：`{status['task_info']['task_desc']['task_tag']}`",
        "",
        "## 视频/状态长度",
        "",
        f"- left states：`{status['states']['left']['count']}`",
        f"- right states：`{status['states']['right']['count']}`",
    ]
    for name, item in status["videos"].items():
        lines.append(f"- {name}: `{item['frames']}` frames, `{item['fps']}` fps, `{item['width']}x{item['height']}`")
    lines.extend(["", "## 字段维度", ""])
    for side in ["left", "right"]:
        lines.append(f"### {side}")
        for key, value in status["states"][side]["dims"].items():
            if value["kind"] == "list":
                lines.append(f"- `{key}`: list dims `{value['lengths']}`")
            else:
                lines.append(f"- `{key}`: `{value['kind']}`")
        lines.append("")
    lines.extend(
        [
            "## 推荐映射",
            "",
            "```json",
            json.dumps(status["mapping"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## 下一步",
            "",
            "- 写一个只处理该分片的 dry-run converter，不先写全量 LeRobot 数据，先验证 14 维 state/action 和三路图像键。",
            "- converter 通过后再接 `LeRobotW1DualDataConfig(repo_id='cvpr_multitask_aloha')` 的训练/评测入口。",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    left_rows, left_count = load_jsonl_sample(EPISODE_DIR / "states/left_states.jsonl")
    right_rows, right_count = load_jsonl_sample(EPISODE_DIR / "states/right_states.jsonl")
    status = {
        "episode_dir": str(EPISODE_DIR),
        "task_info_path": str(TASK_INFO),
        "checkpoint": str(CHECKPOINT),
        "task_info": load_json(TASK_INFO),
        "episode_meta": load_json(EPISODE_DIR / "meta/episode_meta.json"),
        "states": {
            "left": {"count": left_count, "dims": dim_summary(left_rows)},
            "right": {"count": right_count, "dims": dim_summary(right_rows)},
        },
        "videos": video_summary(EPISODE_DIR / "videos"),
        "config": config_summary(),
        "norm_stats": norm_stats_summary(),
    }
    status["mapping"] = build_mapping(status)

    counts = [left_count, right_count, *[v["frames"] for v in status["videos"].values()]]
    status["lengths_match"] = len(set(counts)) == 1
    status["aloha_norm_stats_14d"] = status["norm_stats"]["dims"].get("state", {}).get("mean") == 14 and status["norm_stats"][
        "dims"
    ].get("actions", {}).get("mean") == 14
    status["ready_for_dry_run_converter"] = bool(status["lengths_match"] and status["aloha_norm_stats_14d"])

    STATUS_PATH.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(status)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["ready_for_dry_run_converter"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
