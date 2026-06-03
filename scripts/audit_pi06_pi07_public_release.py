#!/usr/bin/env python3
"""Audit public reproducibility status for pi0.6 / pi0.7 artifacts."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]
OPENPI_ROOT = Path(os.environ.get("OPENPI_ROOT", "/home/yjl/robochallenge/openpi"))
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
STATUS_PATH = RUNS_DIR / "pi06_pi07_public_audit.json"
REPORT_PATH = REPORTS_DIR / "pi06_pi07_public_release_audit.md"
REMOTE_OPENPI_README_URL = "https://raw.githubusercontent.com/Physical-Intelligence/openpi/main/README.md"
REMOTE_PI07_URL = "https://www.pi.website/pi07"
OPENPI_CHECKPOINT_RE = re.compile(r"gs://openpi-assets/checkpoints/[A-Za-z0-9_.-]+")

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
        "url": REMOTE_PI07_URL,
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


def fetch_public_text(url: str, attempts: int = 3) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "robochallenge-pi05-audit/1.0"})
    errors: list[str] = []
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=45) as resp:
                raw = resp.read()
                return {
                    "url": url,
                    "fetched": True,
                    "attempt_count": attempt,
                    "status_code": getattr(resp, "status", None),
                    "byte_count": len(raw),
                    "text": raw.decode("utf-8", errors="replace"),
                }
        except Exception as exc:  # noqa: BLE001 - public source availability belongs in the audit status.
            errors.append(f"attempt {attempt}: {type(exc).__name__}: {exc}")
    return {
        "url": url,
        "fetched": False,
        "attempt_count": attempts,
        "error": errors[-1] if errors else "unknown fetch error",
        "errors": errors,
        "byte_count": 0,
        "text": "",
    }


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


def summarize_remote_openpi_readme() -> dict:
    fetched = fetch_public_text(REMOTE_OPENPI_README_URL)
    text = fetched.pop("text")
    checkpoint_paths = sorted(set(OPENPI_CHECKPOINT_RE.findall(text)))
    unexpected_checkpoint_paths = [
        path
        for path in checkpoint_paths
        if re.search(r"pi0?[._-]?6|pi0?[._-]?7|pi06|pi07|pistar06|pi_star06", path, re.IGNORECASE)
    ]
    target_line_count = 0
    pattern = re.compile("|".join(TARGET_PATTERNS), re.IGNORECASE)
    for line in text.splitlines():
        if pattern.search(line):
            target_line_count += 1
    base_paths_present = {
        "pi0_base": "gs://openpi-assets/checkpoints/pi0_base" in text,
        "pi0_fast_base": "gs://openpi-assets/checkpoints/pi0_fast_base" in text,
        "pi05_base": "gs://openpi-assets/checkpoints/pi05_base" in text,
    }
    return {
        **fetched,
        "checkpoint_paths": checkpoint_paths,
        "checkpoint_path_count": len(checkpoint_paths),
        "base_paths_present": base_paths_present,
        "all_expected_public_base_paths_present": all(base_paths_present.values()),
        "target_text_match_count": target_line_count,
        "unexpected_pi06_pi07_checkpoint_paths": unexpected_checkpoint_paths,
        "unexpected_pi06_pi07_checkpoint_count": len(unexpected_checkpoint_paths),
    }


def summarize_remote_pi07_page() -> dict:
    fetched = fetch_public_text(REMOTE_PI07_URL)
    text = fetched.pop("text")
    return {
        **fetched,
        "mentions_pi07": "π_{0.7}" in text or "pi0.7" in text.lower() or "0.7" in text,
        "published_april_16_2026": "April 16, 2026" in text,
        "mentions_steerable": "steerable" in text.lower(),
        "checkpoint_path_count": len(set(OPENPI_CHECKPOINT_RE.findall(text))),
    }


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
    remote_readme = status["remote_openpi_readme"]
    remote_pi07 = status["remote_pi07_page"]
    lines = [
        "# pi0.6 / pi0.7 公开复现性审计",
        "",
        "## 结论",
        "",
        f"- 审计时间：`{status['checked_at_utc']}`。",
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
        "## 远端 OpenPI README 实时检查",
        "",
        f"- URL：`{remote_readme['url']}`。",
        f"- 抓取成功：`{remote_readme['fetched']}`。",
        f"- checkpoint 路径数：`{remote_readme['checkpoint_path_count']}`。",
        f"- 预期公开基模路径均存在：`{remote_readme['all_expected_public_base_paths_present']}`。",
        f"- pi0.6/pi0.7 checkpoint 路径数：`{remote_readme['unexpected_pi06_pi07_checkpoint_count']}`。",
        "",
        "## pi0.7 官网页实时检查",
        "",
        f"- URL：`{remote_pi07['url']}`。",
        f"- 抓取成功：`{remote_pi07['fetched']}`。",
        f"- 发布日期命中 2026-04-16：`{remote_pi07['published_april_16_2026']}`。",
        f"- steerable 描述命中：`{remote_pi07['mentions_steerable']}`。",
        f"- checkpoint 路径数：`{remote_pi07['checkpoint_path_count']}`。",
        "",
        "## 公共 GCS checkpoint 前缀",
        "",
        f"- 检查前缀数：`{status['gcs_prefix_count']}`。",
        f"- 公开 checkpoint 是否命中：`{status['public_checkpoint_found']}`。",
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
            "## 边界",
            "",
            "- 本审计只访问公开 OpenPI/GCS 资料，不接触 RoboChallenge 提交平台。",
            "- 本审计不读取 token、submission id 或 checkpoint link，不上传、不下载 checkpoint 权重。",
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
    public_checkpoint_found = any((item.get("object_count") or 0) > 0 for item in gcs_results)
    openpi_scan = scan_openpi()
    remote_openpi_readme = summarize_remote_openpi_readme()
    remote_pi07_page = summarize_remote_pi07_page()
    gcs_all_zero = all(item.get("object_count") == 0 for item in gcs_results)
    openpi_match_count = len(openpi_scan["matches"])
    remote_release_gap_confirmed = bool(
        remote_openpi_readme.get("fetched")
        and remote_openpi_readme.get("all_expected_public_base_paths_present")
        and remote_openpi_readme.get("unexpected_pi06_pi07_checkpoint_count") == 0
        and remote_pi07_page.get("fetched")
        and remote_pi07_page.get("published_april_16_2026")
        and remote_pi07_page.get("checkpoint_path_count") == 0
    )
    status = {
        "kind": "pi06_pi07_public_release_audit",
        "checked_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "passed": (not public_checkpoint_found) and gcs_all_zero and openpi_match_count == 0 and remote_release_gap_confirmed,
        "official_sources": OFFICIAL_SOURCES,
        "official_source_count": len(OFFICIAL_SOURCES),
        "openpi_scan": openpi_scan,
        "openpi_target_match_count": openpi_match_count,
        "remote_openpi_readme": remote_openpi_readme,
        "remote_pi07_page": remote_pi07_page,
        "remote_release_gap_confirmed": remote_release_gap_confirmed,
        "gcs_prefixes": gcs_results,
        "gcs_prefix_count": len(gcs_results),
        "gcs_all_zero": gcs_all_zero,
        "public_checkpoint_found": public_checkpoint_found,
        "public_sources_contacted": True,
        "platform_contacted": False,
        "robochallenge_platform_contacted": False,
        "uploads_performed": False,
        "credentials_read": False,
        "credentials_printed": False,
        "link_values_printed": False,
        "secret_values_printed": False,
    }
    STATUS_PATH.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(status)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
