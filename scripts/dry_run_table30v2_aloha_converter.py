#!/usr/bin/env python3
"""Dry-run converter for one Table30v2 ALOHA episode.

This script intentionally does not create a full LeRobot dataset. It samples a
few frames, builds LeRobot-like records, and validates that one 50-step window
passes the OpenPI ALOHA data transforms plus pi0.5 padding.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
BASELINE = Path(os.environ.get("BASELINE", "/home/yjl/yjl/RoboChallenge/baseline_pi05_multitask"))
BASELINE_PYTHON = BASELINE / ".venv/bin/python3"
if (
    BASELINE_PYTHON.exists()
    and Path(sys.executable).resolve() != BASELINE_PYTHON.resolve()
    and os.environ.get("TABLE30V2_ALOHA_DRY_RUN_REEXEC") != "1"
):
    os.environ["TABLE30V2_ALOHA_DRY_RUN_REEXEC"] = "1"
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
CONFIG_NAME = os.environ.get("CONFIG_NAME", "cvpr_multitask_aloha_rtc")
SAMPLE_COUNT = int(os.environ.get("SAMPLE_COUNT", "5"))
START_INDEX = int(os.environ.get("START_INDEX", "0"))
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
STATUS_PATH = RUNS_DIR / "table30v2_aloha_dry_run_status.json"
SAMPLES_PATH = RUNS_DIR / "table30v2_aloha_dry_run_samples.jsonl"
REPORT_PATH = REPORTS_DIR / "table30v2_aloha_dry_run_converter.md"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path, limit: int | None = None) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))
            if limit is not None and len(rows) >= limit:
                break
    return rows


def qpos14(left: dict, right: dict) -> np.ndarray:
    return np.asarray(left["master_qpos"][:7] + right["master_qpos"][:7], dtype=np.float32)


def read_frame(video_path: Path, frame_index: int) -> np.ndarray:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"视频无法打开: {video_path}")
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        raise RuntimeError(f"读取视频帧失败: {video_path} frame={frame_index}")
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


def image_summary(image: np.ndarray) -> dict:
    return {
        "shape": list(image.shape),
        "dtype": str(image.dtype),
        "min": int(image.min()),
        "max": int(image.max()),
        "mean": float(np.mean(image)),
    }


def serial_vector(values: np.ndarray) -> list[float]:
    return [float(x) for x in np.asarray(values).reshape(-1)]


def summarize_tree(data: dict) -> dict:
    out = {}
    for key, value in data.items():
        if isinstance(value, dict):
            out[key] = summarize_tree(value)
        elif isinstance(value, np.ndarray):
            out[key] = {"shape": list(value.shape), "dtype": str(value.dtype)}
        else:
            out[key] = {"type": type(value).__name__, "value": str(value)[:200]}
    return out


def build_sample_records(left_rows: list[dict], right_rows: list[dict], prompt: str) -> tuple[list[dict], dict]:
    videos_dir = EPISODE_DIR / "videos"
    records = []
    first_images = None
    for offset in range(SAMPLE_COUNT):
        idx = START_INDEX + offset
        action_idx = idx + 1
        base = read_frame(videos_dir / "cam_high_rgb.mp4", idx)
        left_img = read_frame(videos_dir / "cam_left_wrist_rgb.mp4", idx)
        right_img = read_frame(videos_dir / "cam_right_wrist_rgb.mp4", idx)
        if first_images is None:
            first_images = {
                "front_image": base,
                "left_image": left_img,
                "right_image": right_img,
            }
        records.append(
            {
                "frame_index": idx,
                "state": serial_vector(qpos14(left_rows[idx], right_rows[idx])),
                "action": serial_vector(qpos14(left_rows[action_idx], right_rows[action_idx])),
                "prompt": prompt,
                "images": {
                    "observation.images.front_image": image_summary(base),
                    "observation.images.left_image": image_summary(left_img),
                    "observation.images.right_image": image_summary(right_img),
                },
            }
        )
    assert first_images is not None
    return records, first_images


def build_transform_window(
    left_rows: list[dict],
    right_rows: list[dict],
    first_images: dict,
    prompt: str,
    action_horizon: int,
) -> dict:
    states = np.stack([qpos14(left_rows[i], right_rows[i]) for i in range(action_horizon)], axis=0)
    actions = np.stack([qpos14(left_rows[i + 1], right_rows[i + 1]) for i in range(action_horizon)], axis=0)
    # LeRobotW1DualDataConfig's RepackTransform expects flat dotted
    # dataset keys, then maps them to the slash-separated inference keys.
    return {
        "observation.images.front_image": first_images["front_image"],
        "observation.images.left_image": first_images["left_image"],
        "observation.images.right_image": first_images["right_image"],
        "observation.state": states,
        "action": actions,
        "action_is_pad": np.zeros((action_horizon,), dtype=bool),
        "prompt": prompt,
        # LeRobotW1DualDataConfig inserts metadata=None when it is absent.
        # Keep it as a leaf value; a nested dict breaks RepackTransform's flat key lookup.
        "metadata": None,
    }


def run_openpi_transform_smoke(raw_window: dict) -> dict:
    sys.path[:0] = [str(OPENPI_SRC), str(OPENPI_CLIENT_SRC), str(LEROBOT_SRC)]
    np.random.seed(0)
    from openpi_rtc import transforms as pi_transforms
    from openpi_rtc.training import config as train_config

    cfg = train_config.get_config(CONFIG_NAME)
    data_config = cfg.data.create(cfg.assets_dirs, cfg.model)

    data = raw_window
    for transform in data_config.repack_transforms.inputs:
        data = transform(data)
    after_repack = summarize_tree(data)

    for transform in data_config.data_transforms.inputs:
        data = transform(data)
    after_data_transforms = summarize_tree(data)

    padded = pi_transforms.PadStatesAndActions(cfg.model.action_dim)(dict(data))
    after_padding = summarize_tree(padded)

    state_shape = list(np.asarray(data["state"]).shape)
    actions_shape = list(np.asarray(data["actions"]).shape)
    padded_state_shape = list(np.asarray(padded["state"]).shape)
    padded_actions_shape = list(np.asarray(padded["actions"]).shape)
    prefill_len = np.asarray(padded.get("action_prefill_len", 0))

    checks = {
        "config_name": cfg.name,
        "model_action_dim": int(cfg.model.action_dim),
        "action_horizon": int(cfg.model.action_horizon),
        "raw_state_sequence_shape": list(raw_window["observation.state"].shape),
        "raw_action_sequence_shape": list(raw_window["action"].shape),
        "after_repack": after_repack,
        "after_data_transforms": after_data_transforms,
        "after_padding": after_padding,
        "state_shape_after_data_transforms": state_shape,
        "actions_shape_after_data_transforms": actions_shape,
        "state_shape_after_padding": padded_state_shape,
        "actions_shape_after_padding": padded_actions_shape,
        "state_14d_after_data_transforms": state_shape[-1:] == [14],
        "actions_50x14_after_data_transforms": actions_shape[-2:] == [cfg.model.action_horizon, 14],
        "state_32d_after_padding": padded_state_shape[-1:] == [cfg.model.action_dim],
        "actions_50x32_after_padding": padded_actions_shape[-2:] == [cfg.model.action_horizon, cfg.model.action_dim],
        "image_keys": sorted(padded["image"].keys()),
        "image_masks": {key: bool(value) for key, value in padded["image_mask"].items()},
        "action_prefill_len_shape": list(prefill_len.shape),
        "action_prefill_len_values": [int(x) for x in prefill_len.reshape(-1).tolist()],
    }
    checks["passed"] = all(
        [
            checks["state_14d_after_data_transforms"],
            checks["actions_50x14_after_data_transforms"],
            checks["state_32d_after_padding"],
            checks["actions_50x32_after_padding"],
            checks["image_keys"] == ["base_0_rgb", "left_wrist_0_rgb", "right_wrist_0_rgb"],
            all(checks["image_masks"].values()),
        ]
    )
    return checks


def write_report(status: dict) -> None:
    lines = [
        "# Table30v2 ALOHA Dry-Run Converter",
        "",
        "## 结论",
        "",
        f"- dry-run 状态：`passed={status['passed']}`。",
        f"- 抽样帧数：`{status['sample_count']}`，输出 JSONL：`{SAMPLES_PATH}`。",
        "- 未写入全量 LeRobot 数据，未复制视频帧，只保存 schema 与数值摘要。",
        "- raw ALOHA 双臂 14 维 state/action 已能通过 OpenPI ALOHA repack、50 步窗口、delta action 和 pi0.5 32 维 padding smoke。",
        "",
        "## 关键形状",
        "",
        f"- raw state sequence：`{status['transform_smoke']['raw_state_sequence_shape']}`。",
        f"- raw action sequence：`{status['transform_smoke']['raw_action_sequence_shape']}`。",
        f"- after data transforms state shape：`{status['transform_smoke']['state_shape_after_data_transforms']}`，14D 校验：`{status['transform_smoke']['state_14d_after_data_transforms']}`。",
        f"- after data transforms actions shape：`{status['transform_smoke']['actions_shape_after_data_transforms']}`，50x14 校验：`{status['transform_smoke']['actions_50x14_after_data_transforms']}`。",
        f"- after padding state shape：`{status['transform_smoke']['state_shape_after_padding']}`，32D 校验：`{status['transform_smoke']['state_32d_after_padding']}`。",
        f"- after padding actions shape：`{status['transform_smoke']['actions_shape_after_padding']}`，50x32 校验：`{status['transform_smoke']['actions_50x32_after_padding']}`。",
        f"- random action offset prefill：shape=`{status['transform_smoke']['action_prefill_len_shape']}`，values=`{status['transform_smoke']['action_prefill_len_values']}`。",
        f"- image keys：`{status['transform_smoke']['image_keys']}`。",
        "",
        "## 下一步",
        "",
        "- 将 dry-run 逻辑扩展为可选小 episode LeRobot writer，先只写一个短 episode。",
        "- 小 episode 通过后，再用 `LeRobotW1DualDataConfig(repo_id='cvpr_multitask_aloha')` 做 dataloader smoke。",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    task_info = load_json(TASK_INFO)
    prompt = task_info["task_desc"]["prompt"]
    action_horizon = 50
    required_rows = max(START_INDEX + SAMPLE_COUNT + 1, action_horizon + 1)
    left_rows = load_jsonl(EPISODE_DIR / "states/left_states.jsonl", limit=required_rows)
    right_rows = load_jsonl(EPISODE_DIR / "states/right_states.jsonl", limit=required_rows)
    if len(left_rows) < required_rows or len(right_rows) < required_rows:
        raise RuntimeError(f"样本不足: required={required_rows}, left={len(left_rows)}, right={len(right_rows)}")

    records, first_images = build_sample_records(left_rows, right_rows, prompt)
    with SAMPLES_PATH.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    raw_window = build_transform_window(left_rows, right_rows, first_images, prompt, action_horizon)
    smoke = run_openpi_transform_smoke(raw_window)
    status = {
        "episode_dir": str(EPISODE_DIR),
        "task_info": str(TASK_INFO),
        "config_name": CONFIG_NAME,
        "sample_count": SAMPLE_COUNT,
        "samples_path": str(SAMPLES_PATH),
        "transform_smoke": smoke,
        "passed": bool(smoke["passed"]),
    }
    STATUS_PATH.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(status)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
