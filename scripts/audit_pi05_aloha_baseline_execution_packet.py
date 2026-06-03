#!/usr/bin/env python3
"""Summarize pi0.5 + Table30v2 ALOHA offline baseline execution evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
DEFAULT_STATUS = RUNS_DIR / "pi05_aloha_baseline_execution_packet.json"
DEFAULT_REPORT = REPORTS_DIR / "pi05_aloha_baseline_execution_packet.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="汇总 pi0.5 基模、Table30v2 ALOHA 数据、LeRobot 转换和 mock policy smoke 的离线证据。"
    )
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    parser.add_argument("--report-path", type=Path, default=DEFAULT_REPORT, help="中文报告输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path, limit: int = 200_000) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[-limit:]


def shape(value: dict[str, Any], *keys: str) -> list[Any]:
    current: Any = value
    for key in keys:
        if not isinstance(current, dict):
            return []
        current = current.get(key)
    if isinstance(current, dict):
        current = current.get("shape", [])
    return current if isinstance(current, list) else []


def build_status() -> dict[str, Any]:
    pi05 = read_json(RUNS_DIR / "pi05_base_probe_status.json")
    data_audit = read_json(RUNS_DIR / "data_audit_aloha.json")
    selected_robot = read_json(RUNS_DIR / "selected_robot_config.json")
    mapping = read_json(RUNS_DIR / "table30v2_aloha_mapping_audit.json")
    dry_run = read_json(RUNS_DIR / "table30v2_aloha_dry_run_status.json")
    short_lerobot = read_json(RUNS_DIR / "table30v2_aloha_short_lerobot_status.json")
    short_lerobot_cli = read_json(RUNS_DIR / "table30v2_aloha_short_lerobot_cli_status.json")
    policy_smoke = read_json(RUNS_DIR / "policy_smoke_aloha_status.json")
    secret_scan = read_json(RUNS_DIR / "plaintext_secret_scan.json")
    policy_log = read_text(ROOT / policy_smoke.get("log", ""))
    server_log = read_text(ROOT / policy_smoke.get("server_log", ""))

    load_smoke = pi05.get("load_params_smoke", {})
    transform = dry_run.get("transform_smoke", {})
    short_smoke = short_lerobot.get("dataloader_smoke", {})
    cli_smoke = short_lerobot_cli.get("dataloader_smoke", {})
    state_counts = list(data_audit.get("states", {}).values())
    video_counts = list(data_audit.get("videos", {}).values())
    inference_count = policy_log.count("Inference result")

    evidence = {
        "pi05_local_cache_complete": pi05.get("local_complete") is True,
        "pi05_remote_object_count": pi05.get("remote_object_count") == 29,
        "pi05_bytes_match": pi05.get("local_matched_bytes") == pi05.get("remote_total_bytes"),
        "pi05_params_load_smoke_preserved": pi05.get("load_params_smoke_preserved") is True,
        "pi05_params_loaded": load_smoke.get("loaded") is True,
        "pi05_params_leaf_count_positive": int(load_smoke.get("leaf_count", 0)) > 0,
        "pi05_params_total_elements_positive": int(load_smoke.get("total_elements", 0)) > 0,
        "selected_robot_aloha": selected_robot.get("robot_type") == "aloha"
        and selected_robot.get("robot_tag") == "aloha",
        "selected_task_pack_toothbrush": "pack_the_toothbrush_holder"
        in str(selected_robot.get("record_data_dir", "")),
        "selected_checkpoint_exists": selected_robot.get("checkpoint_exists") is True,
        "data_record_exists": data_audit.get("exists") is True,
        "data_state_frame_counts_match": bool(state_counts) and len(set(state_counts)) == 1 and state_counts[0] == 1100,
        "data_video_frame_counts_match": bool(video_counts) and len(set(video_counts)) == 1 and video_counts[0] == 1100,
        "mapping_task_name": mapping.get("task_info", {}).get("task_desc", {}).get("task_name")
        == "pack_the_toothbrush_holder",
        "mapping_episode_frames": mapping.get("episode_meta", {}).get("frames") == 1100,
        "dry_run_passed": dry_run.get("passed") is True,
        "dry_run_sample_count": dry_run.get("sample_count") == 5,
        "dry_run_state_32": shape(transform, "after_padding", "state") == [5, 32],
        "dry_run_actions_50x32": shape(transform, "after_padding", "actions") == [5, 50, 32],
        "short_lerobot_passed": short_lerobot.get("passed") is True,
        "short_lerobot_frame_count": short_lerobot.get("dataset", {}).get("frame_count") == 64,
        "short_lerobot_state_shape": short_smoke.get("state_shape") == [1, 5, 32],
        "short_lerobot_actions_shape": short_smoke.get("actions_shape") == [1, 5, 50, 32],
        "short_lerobot_cli_passed": short_lerobot_cli.get("passed") is True,
        "short_lerobot_cli_frame_count": short_lerobot_cli.get("dataset", {}).get("frame_count") == 80,
        "short_lerobot_cli_state_shape": cli_smoke.get("state_shape") == [1, 5, 32],
        "short_lerobot_cli_actions_shape": cli_smoke.get("actions_shape") == [1, 5, 50, 32],
        "policy_smoke_passed": policy_smoke.get("smoke") == "passed" and policy_smoke.get("exit_code") == 0,
        "policy_smoke_inference_seen": inference_count >= 2,
        "mock_server_started": "Uvicorn running" in server_log or "starting server" in server_log,
        "secret_scan_clean": secret_scan.get("passed") is True and secret_scan.get("hit_count") == 0,
    }
    leak_flags = {
        "credentials_printed": False,
        "link_values_printed": False,
        "secret_values_printed": False,
    }
    contact_flags = {
        "platform_contacted": False,
        "uploads_performed": False,
        "download_host_contacted": False,
        "real_runner_started": False,
    }
    blocking = []
    for key, ok in evidence.items():
        if not ok:
            blocking.append(f"pi0.5 ALOHA baseline 离线执行证据未通过 `{key}`。")
    if not blocking:
        blocking.append("pi0.5 基模缓存、Table30v2 ALOHA 数据转换和本地 mock policy smoke 均已形成离线执行证据。")

    passed = bool(all(evidence.values()) and not any(leak_flags.values()) and not any(contact_flags.values()))
    return {
        "kind": "pi05_aloha_baseline_execution_packet",
        "passed": passed,
        "recommended_route": "baseline_official_aloha",
        "target_benchmark": "Table30v2",
        "robot_type": "aloha",
        "task_name": "pack_the_toothbrush_holder",
        "pi05_local_base": pi05.get("local_base"),
        "pi05_remote_object_count": pi05.get("remote_object_count"),
        "pi05_remote_total_bytes": pi05.get("remote_total_bytes"),
        "pi05_local_matched_bytes": pi05.get("local_matched_bytes"),
        "pi05_params_leaf_count": load_smoke.get("leaf_count"),
        "pi05_params_total_elements": load_smoke.get("total_elements"),
        "data_record_dir": data_audit.get("record_dir"),
        "data_state_frame_count": state_counts[0] if state_counts else None,
        "data_video_frame_count": video_counts[0] if video_counts else None,
        "checkpoint_path": selected_robot.get("checkpoint"),
        "checkpoint_exists": selected_robot.get("checkpoint_exists"),
        "dry_run_sample_count": dry_run.get("sample_count"),
        "dry_run_padded_state_shape": shape(transform, "after_padding", "state"),
        "dry_run_padded_actions_shape": shape(transform, "after_padding", "actions"),
        "short_lerobot_frame_count": short_lerobot.get("dataset", {}).get("frame_count"),
        "short_lerobot_state_shape": short_smoke.get("state_shape"),
        "short_lerobot_actions_shape": short_smoke.get("actions_shape"),
        "short_lerobot_cli_frame_count": short_lerobot_cli.get("dataset", {}).get("frame_count"),
        "short_lerobot_cli_state_shape": cli_smoke.get("state_shape"),
        "short_lerobot_cli_actions_shape": cli_smoke.get("actions_shape"),
        "policy_smoke_exit_code": policy_smoke.get("exit_code"),
        "policy_smoke_inference_count": inference_count,
        "policy_smoke_log": policy_smoke.get("log"),
        "mock_server_log": policy_smoke.get("server_log"),
        "evidence": evidence,
        "leak_flags": leak_flags,
        "contact_flags": contact_flags,
        "platform_contacted": False,
        "uploads_performed": False,
        "credentials_read": False,
        "credentials_printed": False,
        "link_values_printed": False,
        "secret_values_printed": False,
        "blocking": blocking,
    }


def write_report(status: dict[str, Any], path: Path) -> None:
    lines = [
        "# pi0.5 ALOHA baseline 离线执行证据包",
        "",
        "## 结论",
        "",
        f"- 审计状态：`passed={status['passed']}`。",
        f"- 推荐路线：`{status['recommended_route']}`。",
        f"- 目标：`{status['target_benchmark']} / {status['robot_type']} / {status['task_name']}`。",
        f"- pi0.5 本地缓存：`{status['pi05_local_base']}`。",
        f"- pi0.5 GCS 对象数：`{status['pi05_remote_object_count']}`。",
        f"- pi0.5 本地匹配字节：`{status['pi05_local_matched_bytes']}` / `{status['pi05_remote_total_bytes']}`。",
        f"- 参数叶子数：`{status['pi05_params_leaf_count']}`。",
        f"- 参数元素数：`{status['pi05_params_total_elements']}`。",
        f"- ALOHA 数据目录：`{status['data_record_dir']}`。",
        f"- state/video 帧数：`{status['data_state_frame_count']}` / `{status['data_video_frame_count']}`。",
        f"- ALOHA checkpoint：`{status['checkpoint_path']}`。",
        f"- checkpoint 是否存在：`{status['checkpoint_exists']}`。",
        "",
        "## 转换与 smoke",
        "",
        f"- dry-run 抽样数：`{status['dry_run_sample_count']}`。",
        f"- padding 后 state shape：`{status['dry_run_padded_state_shape']}`。",
        f"- padding 后 actions shape：`{status['dry_run_padded_actions_shape']}`。",
        f"- 短 LeRobot episode 帧数：`{status['short_lerobot_frame_count']}`。",
        f"- CLI 短 LeRobot episode 帧数：`{status['short_lerobot_cli_frame_count']}`。",
        f"- mock policy smoke exit_code：`{status['policy_smoke_exit_code']}`。",
        f"- mock policy inference 命中数：`{status['policy_smoke_inference_count']}`。",
        f"- policy log：`{status['policy_smoke_log']}`。",
        f"- mock server log：`{status['mock_server_log']}`。",
        "",
        "## 边界",
        "",
        "- 本审计只读取已有 JSON 和日志，不启动真实 runner。",
        "- 不读取 RoboChallenge token/submission id/local env。",
        "- 不连接 RoboChallenge 平台、不上传、不下载 checkpoint。",
        "",
        "## 证据",
        "",
    ]
    for key, ok in status["evidence"].items():
        lines.append(f"- `{key}`：`{ok}`。")
    lines.extend(["", "## Blocking", ""])
    for item in status["blocking"]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args()
    status = build_status()
    args.status_path.parent.mkdir(parents=True, exist_ok=True)
    args.status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(status, args.report_path)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
