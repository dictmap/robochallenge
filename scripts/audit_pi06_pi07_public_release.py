#!/usr/bin/env python3
"""Audit public reproducibility status for pi0.6 / pi0.7 artifacts."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
OPENPI_ROOT = Path(os.environ.get("OPENPI_ROOT", "/home/yjl/robochallenge/openpi"))
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
STATUS_PATH = RUNS_DIR / "pi06_pi07_public_audit.json"
REPORT_PATH = REPORTS_DIR / "pi06_pi07_public_release_audit.md"

TARGET_PATTERNS = [
    r"\bpi06\b",
    r"\bpi07\b",
    r"\bpi0[._-]?6\b",
    r"\bpi0[._-]?7\b",
    r"π\*?0\.6",
    r"π\*?0\.7",
]
GCS_PREFIXES = [
    "checkpoints/pi06",
    "checkpoints/pi07",
    "checkpoints/pi0_6",
    "checkpoints/pi0_7",
    "checkpoints/pi06_base",
    "checkpoints/pi07_base",
    "checkpoints/pi0.6",
    "checkpoints/pi0.7",
    "checkpoints/pistar06",
    "checkpoints/pi_star06",
]
OFFICIAL_SOURCES = [
    {
        "name": "Physical-Intelligence/openpi",
        "url": "https://github.com/Physical-Intelligence/openpi",
        "note": "公开 OpenPI 仓库当前列出的模型族为 pi0、pi0-FAST、pi0.5。",
    },
    {
        "name": "pi*0.6 paper",
        "url": "https://www.physicalintelligence.company/download/pistar06.pdf",
        "note": "pi*0.6 / RECAP 论文，描述从经验和奖励反馈改进 VLA 的方法。",
    },
    {
        "name": "pi0.7 blog",
        "url": "https://www.pi.website/blog/pi07",
        "note": "pi0.7 博客，发布于 2026-04-16，描述 steerable generalist 和组合泛化。",
    },
    {
        "name": "openpi issue 789",
        "url": "https://github.com/Physical-Intelligence/openpi/issues/789",
        "note": "社区询问 pi0.6 是否会发布的公开 issue。",
    },
    {
        "name": "openpi issue 860",
        "url": "https://github.com/Physical-Intelligence/openpi/issues/860",
        "note": "社区讨论 pi0.6 star 是否可从 pi0.5 checkpoint 实现的公开 issue。",
    },
]


def list_gcs(prefix: str) -> list[dict]:
    query = urllib.parse.urlencode(
        {
            "prefix": prefix,
            "fields": "items(name,size),nextPageToken",
            "maxResults": "50",
        }
    )
    url = f"https://storage.googleapis.com/storage/v1/b/openpi-assets/o?{query}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = json.load(resp)
    return data.get("items", [])


def scan_openpi() -> dict:
    roots = [OPENPI_ROOT / "README.md", OPENPI_ROOT / "src", OPENPI_ROOT / "packages", OPENPI_ROOT / "examples"]
    pattern = re.compile("|".join(TARGET_PATTERNS), re.IGNORECASE)
    matches: list[dict] = []
    scanned_files = 0
    for root in roots:
        if root.is_file():
            paths = [root]
        elif root.exists():
            paths = [p for p in root.rglob("*") if p.is_file()]
        else:
            continue
        for path in paths:
            if any(part in {".git", ".venv", "__pycache__"} for part in path.parts):
                continue
            if path.suffix in {".pyc", ".png", ".jpg", ".jpeg", ".mp4", ".gif"}:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            scanned_files += 1
            for lineno, line in enumerate(text.splitlines(), start=1):
                if pattern.search(line):
                    matches.append(
                        {
                            "path": str(path.relative_to(OPENPI_ROOT)),
                            "line": lineno,
                            "text": line.strip()[:240],
                        }
                    )
    return {"root": str(OPENPI_ROOT), "scanned_files": scanned_files, "matches": matches}


def write_report(status: dict) -> None:
    lines = [
        "# pi0.6 / pi0.7 公开复现性审计",
        "",
        "## 结论",
        "",
        "- 目前没有找到可直接复现的公开 `pi0.6` 或 `pi0.7` OpenPI checkpoint/config。",
        "- 本地 OpenPI 仓库没有 `pi06/pi07/pi0.6/pi0.7` 训练或推理配置命中。",
        "- `openpi-assets` 公共 bucket 常见 `pi06/pi07` 前缀对象数均为 0。",
        "- `pi*0.6` 和 `pi0.7` 有公开论文/博客，但当前只能作为方法参考，不能按 `pi05_base` 那样下载权重并 smoke。",
        "",
        "## 本地 OpenPI 扫描",
        "",
        f"- OpenPI root：`{status['openpi_scan']['root']}`。",
        f"- 扫描文件数：`{status['openpi_scan']['scanned_files']}`。",
        f"- 命中数：`{len(status['openpi_scan']['matches'])}`。",
        "",
        "## 公共 GCS checkpoint 前缀",
        "",
        "| prefix | object_count |",
        "| --- | ---: |",
    ]
    for item in status["gcs_prefixes"]:
        lines.append(f"| `{item['prefix']}` | {item['object_count']} |")
    lines.extend(["", "## 官方/公开资料", ""])
    for src in OFFICIAL_SOURCES:
        lines.append(f"- [{src['name']}]({src['url']})：{src['note']}")
    lines.extend(
        [
            "",
            "## 对 RoboChallenge 的影响",
            "",
            "- 当前可执行路线仍是：`pi05_base` -> Table30/Table30v2 数据适配 -> 任务 finetune/eval -> 官方提交入口。",
            "- `pi*0.6` 可借鉴 RECAP 思路做后续优化，但需要奖励/成功标签、失败轨迹、干预数据或离线 RL 实现；不是一键换 checkpoint。",
            "- `pi0.7` 可借鉴 steerable prompt、subtask、visual subgoal 和 metadata conditioning 思路；没有公开权重时不能声称复现模型本体。",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    gcs_results = []
    for prefix in GCS_PREFIXES:
        try:
            items = list_gcs(prefix)
            gcs_results.append(
                {
                    "prefix": prefix,
                    "object_count": len(items),
                    "sample": items[:5],
                }
            )
        except Exception as exc:  # noqa: BLE001 - status should preserve external errors.
            gcs_results.append({"prefix": prefix, "error": f"{type(exc).__name__}: {exc}", "object_count": None})
    status = {
        "official_sources": OFFICIAL_SOURCES,
        "openpi_scan": scan_openpi(),
        "gcs_prefixes": gcs_results,
        "public_checkpoint_found": any((item.get("object_count") or 0) > 0 for item in gcs_results),
    }
    STATUS_PATH.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(status)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 1 if status["public_checkpoint_found"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
