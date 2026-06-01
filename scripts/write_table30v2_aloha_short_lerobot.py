#!/usr/bin/env python3
"""Write a short Table30v2 ALOHA LeRobot dataset and smoke-test OpenPI loading."""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
from pathlib import Path
import shutil
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
BASELINE = Path(os.environ.get("BASELINE", "/home/yjl/yjl/RoboChallenge/baseline_pi05_multitask"))
BASELINE_PYTHON = BASELINE / ".venv/bin/python3"
if (
    BASELINE_PYTHON.exists()
    and Path(sys.executable).resolve() != BASELINE_PYTHON.resolve()
    and os.environ.get("TABLE30V2_ALOHA_SHORT_REEXEC") != "1"
):
    os.environ["TABLE30V2_ALOHA_SHORT_REEXEC"] = "1"
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
REPO_ID = os.environ.get("SHORT_REPO_ID", "robochallenge_table30v2_aloha_short")
FRAME_COUNT = int(os.environ.get("FRAME_COUNT", "64"))
START_INDEX = int(os.environ.get("START_INDEX", "0"))
OVERWRITE = os.environ.get("OVERWRITE_SHORT_REPO", "1") == "1"
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
STATUS_PATH = RUNS_DIR / "table30v2_aloha_short_lerobot_status.json"
REPORT_PATH = REPORTS_DIR / "table30v2_aloha_short_lerobot.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="写出 Table30v2 ALOHA 短 LeRobot 分片，并用 OpenPI dataloader 做 smoke。"
    )
    parser.add_argument("--task", default=TASK, help="Table30v2 task 名称。")
    parser.add_argument("--robot", default=ROBOT, help="机器人类型，当前已验证 aloha。")
    parser.add_argument("--episode-dir", type=Path, default=EPISODE_DIR, help="原始 episode 目录。")
    parser.add_argument("--task-info", type=Path, default=TASK_INFO, help="task_info.json 路径。")
    parser.add_argument("--config-name", default=CONFIG_NAME, help="OpenPI RTC config 名称。")
    parser.add_argument("--repo-id", default=REPO_ID, help="写入的本地 LeRobot repo_id。")
    parser.add_argument("--frame-count", type=int, default=FRAME_COUNT, help="写入帧数。")
    parser.add_argument("--start-index", type=int, default=START_INDEX, help="从原始 episode 的第几帧开始。")
    parser.add_argument("--overwrite", dest="overwrite", action="store_true", default=OVERWRITE, help="覆盖已有 repo。")
    parser.add_argument("--no-overwrite", dest="overwrite", action="store_false", help="已有 repo 时直接失败。")
    parser.add_argument("--status-path", type=Path, default=STATUS_PATH, help="状态 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=REPORT_PATH, help="中文报告输出路径。")
    return parser.parse_args()


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


def open_video(path: Path) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"视频无法打开: {path}")
    return cap


def read_next_rgb(cap: cv2.VideoCapture, name: str, frame_index: int) -> np.ndarray:
    ok, frame = cap.read()
    if not ok or frame is None:
        raise RuntimeError(f"读取视频帧失败: {name} frame={frame_index}")
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


def write_short_dataset() -> dict:
    sys.path[:0] = [str(OPENPI_SRC), str(OPENPI_CLIENT_SRC), str(LEROBOT_SRC)]
    from lerobot.common.constants import HF_LEROBOT_HOME
    from lerobot.common.datasets.lerobot_dataset import LeRobotDataset

    task_info = load_json(TASK_INFO)
    prompt = task_info["task_desc"]["prompt"]
    fps = int(round(float(task_info.get("video_info", {}).get("fps", 30))))
    required_rows = START_INDEX + FRAME_COUNT + 1
    left_rows = load_jsonl(EPISODE_DIR / "states/left_states.jsonl", limit=required_rows)
    right_rows = load_jsonl(EPISODE_DIR / "states/right_states.jsonl", limit=required_rows)
    if len(left_rows) < required_rows or len(right_rows) < required_rows:
        raise RuntimeError(f"状态帧不足: left={len(left_rows)} right={len(right_rows)} required={required_rows}")

    repo_root = HF_LEROBOT_HOME / REPO_ID
    repo_root = repo_root.resolve()
    cache_root = HF_LEROBOT_HOME.resolve()
    if not str(repo_root).startswith(str(cache_root)) or not REPO_ID.startswith("robochallenge_"):
        raise RuntimeError(f"拒绝删除非本项目 LeRobot 路径: {repo_root}")
    if OVERWRITE and repo_root.exists():
        shutil.rmtree(repo_root)
    if not OVERWRITE and repo_root.exists():
        raise RuntimeError(f"LeRobot repo 已存在且 --no-overwrite 生效: {repo_root}")

    features = {
        "observation.images.front_image": {
            "dtype": "image",
            "shape": (480, 640, 3),
            "names": ["height", "width", "channel"],
        },
        "observation.images.left_image": {
            "dtype": "image",
            "shape": (480, 640, 3),
            "names": ["height", "width", "channel"],
        },
        "observation.images.right_image": {
            "dtype": "image",
            "shape": (480, 640, 3),
            "names": ["height", "width", "channel"],
        },
        "observation.state": {
            "dtype": "float32",
            "shape": (14,),
            "names": ["state"],
        },
        "action": {
            "dtype": "float32",
            "shape": (14,),
            "names": ["action"],
        },
    }
    dataset = LeRobotDataset.create(
        repo_id=REPO_ID,
        robot_type="aloha",
        fps=fps,
        features=features,
        use_videos=False,
    )

    videos_dir = EPISODE_DIR / "videos"
    caps = {
        "front": open_video(videos_dir / "cam_high_rgb.mp4"),
        "left": open_video(videos_dir / "cam_left_wrist_rgb.mp4"),
        "right": open_video(videos_dir / "cam_right_wrist_rgb.mp4"),
    }
    for cap in caps.values():
        cap.set(cv2.CAP_PROP_POS_FRAMES, START_INDEX)
    try:
        for offset in range(FRAME_COUNT):
            idx = START_INDEX + offset
            dataset.add_frame(
                {
                    "observation.images.front_image": read_next_rgb(caps["front"], "cam_high_rgb.mp4", idx),
                    "observation.images.left_image": read_next_rgb(
                        caps["left"], "cam_left_wrist_rgb.mp4", idx
                    ),
                    "observation.images.right_image": read_next_rgb(
                        caps["right"], "cam_right_wrist_rgb.mp4", idx
                    ),
                    "observation.state": qpos14(left_rows[idx], right_rows[idx]),
                    "action": qpos14(left_rows[idx + 1], right_rows[idx + 1]),
                    "task": prompt,
                }
            )
        dataset.save_episode()
    finally:
        for cap in caps.values():
            cap.release()

    return {
        "repo_id": REPO_ID,
        "repo_root": str(repo_root),
        "task": TASK,
        "robot": ROBOT,
        "episode_dir": str(EPISODE_DIR),
        "task_info": str(TASK_INFO),
        "fps": fps,
        "frame_count": FRAME_COUNT,
        "start_index": START_INDEX,
        "overwrite": OVERWRITE,
        "prompt": prompt,
    }


def summarize_tree(data: object) -> object:
    if data is None:
        return {"type": "NoneType", "value": None}
    if isinstance(data, dict):
        return {key: summarize_tree(value) for key, value in data.items()}
    if hasattr(data, "to_dict"):
        return summarize_tree(data.to_dict())
    if isinstance(data, (list, tuple)):
        return [summarize_tree(value) for value in data]
    arr = np.asarray(data)
    return {"shape": list(arr.shape), "dtype": str(arr.dtype)}


def smoke_openpi_dataloader(repo_id: str) -> dict:
    sys.path[:0] = [str(OPENPI_SRC), str(OPENPI_CLIENT_SRC), str(LEROBOT_SRC)]
    from openpi_rtc.training import config as train_config
    from openpi_rtc.training import data_loader

    cfg = train_config.get_config(CONFIG_NAME)
    cfg = dataclasses.replace(
        cfg,
        data=dataclasses.replace(cfg.data, repo_id=repo_id),
        batch_size=1,
        num_workers=1,
    )
    data_config = cfg.data.create(cfg.assets_dirs, cfg.model)
    loader = data_loader.create_torch_data_loader(
        data_config,
        model_config=cfg.model,
        action_horizon=cfg.model.action_horizon,
        batch_size=1,
        shuffle=False,
        num_batches=1,
        num_workers=1,
        skip_norm_stats=True,
        framework="numpy",
    )
    observation, actions = next(iter(loader))
    observation_summary = summarize_tree(observation)
    actions_summary = summarize_tree(actions)
    checks = {
        "config_name": cfg.name,
        "repo_id": repo_id,
        "model_action_dim": int(cfg.model.action_dim),
        "action_horizon": int(cfg.model.action_horizon),
        "observation_summary": observation_summary,
        "actions_summary": actions_summary,
        "state_shape": observation_summary.get("state", {}).get("shape"),
        "actions_shape": actions_summary.get("shape"),
        "observation_actions_shape": observation_summary.get("actions", {}).get("shape"),
        "image_keys": sorted(observation_summary.get("image", {}).keys()),
        "tokenized_prompt_shape": observation_summary.get("tokenized_prompt", {}).get("shape"),
    }
    checks["passed"] = all(
        [
            checks["state_shape"] == [1, 5, cfg.model.action_dim],
            checks["actions_shape"] == [1, 5, cfg.model.action_horizon, cfg.model.action_dim],
            checks["image_keys"] == ["base_0_rgb", "left_wrist_0_rgb", "right_wrist_0_rgb"],
            checks["tokenized_prompt_shape"] is not None,
        ]
    )
    return checks


def write_report(status: dict) -> None:
    smoke = status["dataloader_smoke"]
    lines = [
        "# Table30v2 ALOHA 短 episode LeRobot writer",
        "",
        "## 结论",
        "",
        f"- 写出状态：`passed={status['passed']}`。",
        f"- LeRobot repo_id：`{status['dataset']['repo_id']}`。",
        f"- 本地路径：`{status['dataset']['repo_root']}`。",
        f"- task/robot：`{status['dataset']['task']}` / `{status['dataset']['robot']}`。",
        f"- 写入帧段：start_index=`{status['dataset']['start_index']}`，frame_count=`{status['dataset']['frame_count']}`，fps=`{status['dataset']['fps']}`。",
        "- 写入字段：三路图像、14D `observation.state`、14D `action`、任务 prompt。",
        "",
        "## dataloader smoke",
        "",
        f"- OpenPI config：`{smoke['config_name']}`。",
        f"- state shape：`{smoke['state_shape']}`。",
        f"- actions shape：`{smoke['actions_shape']}`。",
        f"- image keys：`{smoke['image_keys']}`。",
        f"- tokenized prompt shape：`{smoke['tokenized_prompt_shape']}`。",
        "",
        "## 下一步",
        "",
        "- 将短 episode writer 扩展为可控分片 writer，再接小步数微调 dry-run。",
        "- 真实提交仍需要 RoboChallenge `user_token` 和 `submission_id`。",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    global TASK, ROBOT, EPISODE_DIR, TASK_INFO, CONFIG_NAME, REPO_ID, FRAME_COUNT, START_INDEX, OVERWRITE
    global STATUS_PATH, REPORT_PATH
    args = parse_args()
    TASK = args.task
    ROBOT = args.robot
    EPISODE_DIR = args.episode_dir
    TASK_INFO = args.task_info
    CONFIG_NAME = args.config_name
    REPO_ID = args.repo_id
    FRAME_COUNT = args.frame_count
    START_INDEX = args.start_index
    OVERWRITE = args.overwrite
    STATUS_PATH = args.status_path
    REPORT_PATH = args.report_path

    STATUS_PATH.parent.mkdir(exist_ok=True, parents=True)
    REPORT_PATH.parent.mkdir(exist_ok=True, parents=True)
    dataset_status = write_short_dataset()
    smoke = smoke_openpi_dataloader(dataset_status["repo_id"])
    status = {
        "dataset": dataset_status,
        "dataloader_smoke": smoke,
        "passed": bool(smoke["passed"]),
    }
    STATUS_PATH.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(status)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
