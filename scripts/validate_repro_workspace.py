#!/usr/bin/env python3
"""Validate that the RoboChallenge pi0.5 workspace has minimum handoff files."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "README.md",
    "work.md",
    "configs/repro_targets.json",
    "sources/source_manifest.json",
    "sources/hf_table30v2_api.json",
    "sources/hf_icra_wbc_api.json",
    "baseline/official_table30v2_convert_to_lerobot.py",
    "baseline/official_table30v2_readme.md",
    "reports/initial_repro_assessment.md",
    "reports/pi05_base_repro.md",
    "reports/pi06_pi07_public_release_audit.md",
    "reports/table30v2_aloha_mapping.md",
    "runs/pi05_base_probe_status.json",
    "runs/pi06_pi07_public_audit.json",
    "runs/table30v2_aloha_mapping_audit.json",
    "scripts/probe_pi05_base_model.sh",
    "scripts/audit_pi06_pi07_public_release.py",
    "scripts/audit_table30v2_aloha_mapping.py",
]


def main() -> int:
    missing = [path for path in REQUIRED if not (ROOT / path).exists()]
    if missing:
        print("缺失文件:")
        for path in missing:
            print(f"- {path}")
        return 1

    targets = json.loads((ROOT / "configs/repro_targets.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "sources/source_manifest.json").read_text(encoding="utf-8"))
    if not targets.get("primary_target", {}).get("url"):
        print("primary_target.url 为空")
        return 1
    if len(manifest.get("sources", [])) < 5:
        print("source_manifest 来源过少")
        return 1
    pi05_status = json.loads((ROOT / "runs/pi05_base_probe_status.json").read_text(encoding="utf-8"))
    if not pi05_status.get("local_complete"):
        print("pi05_base 本地缓存尚未完整")
        return 1
    if not pi05_status.get("load_params_smoke", {}).get("loaded"):
        print("pi05_base 参数读取 smoke 未通过")
        return 1
    pi06_pi07_status = json.loads((ROOT / "runs/pi06_pi07_public_audit.json").read_text(encoding="utf-8"))
    if pi06_pi07_status.get("public_checkpoint_found"):
        print("pi0.6/pi0.7 发现公开 checkpoint，请更新复现路线")
        return 1
    mapping_status = json.loads((ROOT / "runs/table30v2_aloha_mapping_audit.json").read_text(encoding="utf-8"))
    if not mapping_status.get("ready_for_dry_run_converter"):
        print("Table30v2 ALOHA 映射尚未满足 dry-run converter 条件")
        return 1

    print("工作区最低交接材料检查通过")
    print(f"根目录: {ROOT}")
    print(f"来源数量: {len(manifest['sources'])}")
    print("pi05_base 基模缓存与参数读取 smoke 已通过")
    print("pi0.6/pi0.7 公开 checkpoint 审计已完成")
    print("Table30v2 ALOHA 最小分片字段映射已通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
