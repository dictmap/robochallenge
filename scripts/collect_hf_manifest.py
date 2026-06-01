#!/usr/bin/env python3
"""Collect lightweight Hugging Face API manifests for RoboChallenge repos."""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def summarize(payload: dict) -> dict:
    siblings = payload.get("siblings") or []
    return {
        "id": payload.get("id") or payload.get("modelId"),
        "sha": payload.get("sha"),
        "lastModified": payload.get("lastModified"),
        "private": payload.get("private"),
        "gated": payload.get("gated"),
        "usedStorage": payload.get("usedStorage"),
        "downloads": payload.get("downloads"),
        "likes": payload.get("likes"),
        "file_count": len(siblings),
        "top_level_files": [item.get("rfilename") for item in siblings[:20]],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", help="Example: datasets/RoboChallenge/Table30v2 or models/RoboChallenge/foo")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    kind, owner, name = args.repo.split("/", 2)
    if kind == "datasets":
        url = f"https://huggingface.co/api/datasets/{owner}/{name}"
    elif kind == "models":
        url = f"https://huggingface.co/api/models/{owner}/{name}"
    else:
        raise SystemExit("repo must start with datasets/ or models/")

    payload = fetch_json(url)
    result = {"source_url": url, "summary": summarize(payload), "raw": payload}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
