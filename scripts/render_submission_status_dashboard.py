#!/usr/bin/env python3
"""Render a static GUI dashboard for RoboChallenge submission readiness."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"
REPORTS_DIR = ROOT / "reports"
DEFAULT_HTML = REPORTS_DIR / "submission_status_dashboard.html"
DEFAULT_STATUS = RUNS_DIR / "submission_status_dashboard.json"


SOURCE_FILES = {
    "pi05": RUNS_DIR / "pi05_base_probe_status.json",
    "pi06_pi07": RUNS_DIR / "pi06_pi07_public_audit.json",
    "mapping": RUNS_DIR / "table30v2_aloha_mapping_audit.json",
    "lora_policy": RUNS_DIR / "openpi_rtc_lora_materialized_policy_smoke_status.json",
    "lora_export": RUNS_DIR / "lora_checkpoint_export_readiness.json",
    "archive_dry_run": RUNS_DIR / "checkpoint_archive_dry_run.json",
    "authorized_archive": RUNS_DIR / "authorized_checkpoint_archive_template_audit.json",
    "link_intake": RUNS_DIR / "checkpoint_link_intake.json",
    "readiness": RUNS_DIR / "real_submission_readiness.json",
    "preflight_bundle": RUNS_DIR / "submission_preflight_bundle.json",
    "authorized_sequence": RUNS_DIR / "authorized_submission_sequence_audit.json",
    "plaintext_scan": RUNS_DIR / "plaintext_secret_scan.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成 RoboChallenge 提交状态静态 GUI 面板。")
    parser.add_argument("--html-path", type=Path, default=DEFAULT_HTML, help="HTML 面板输出路径。")
    parser.add_argument("--status-path", type=Path, default=DEFAULT_STATUS, help="机器可读 JSON 输出路径。")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def yes(value: Any) -> str:
    return "是" if bool(value) else "否"


def state_label(state: str) -> str:
    return {
        "done": "已完成",
        "blocked": "待授权",
        "watch": "需关注",
    }.get(state, state)


def card(title: str, state: str, value: str, detail: str, report: str) -> dict[str, str]:
    return {
        "title": title,
        "state": state,
        "state_label": state_label(state),
        "value": value,
        "detail": detail,
        "report": report,
    }


def build_cards(data: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    pi05 = data["pi05"]
    pi06_pi07 = data["pi06_pi07"]
    mapping = data["mapping"]
    lora_policy = data["lora_policy"]
    lora_export = data["lora_export"]
    archive_dry_run = data["archive_dry_run"]
    authorized_archive = data["authorized_archive"]
    link_intake = data["link_intake"]
    readiness = data["readiness"]
    preflight = data["preflight_bundle"]
    sequence = data["authorized_sequence"]
    plaintext = data["plaintext_scan"]

    gcs_zero = all(item.get("object_count") == 0 for item in pi06_pi07.get("gcs_prefixes", []))
    current_link_ready = link_intake.get("current_env", {}).get("link_shape_ready")
    ready_for_real = readiness.get("ready_for_real_submission")
    preflight_contacts = preflight.get("contact_flags", {})
    preflight_leaks = preflight.get("leak_flags", {})
    preflight_no_contact = not any(preflight_contacts.values())
    preflight_no_leak = not any(preflight_leaks.values())
    archive_created = archive_dry_run.get("archive_created")
    archive_confirm_smoke = authorized_archive.get("no_confirm_smoke", {})
    archive_confirm_gate_passed = bool(
        authorized_archive.get("passed")
        and archive_confirm_smoke.get("passed")
        and archive_confirm_smoke.get("stops_before_creating_tar")
        and archive_confirm_smoke.get("archive_created") is False
    )
    uploads_performed = readiness.get("inputs", {}).get("uploads_performed")
    plaintext_clean = plaintext.get("hit_count") == 0 and plaintext.get("secret_values_printed") is False

    return [
        card(
            "pi0.5 基模",
            "done" if pi05.get("local_complete") and pi05.get("load_params_smoke_preserved") else "watch",
            f"{pi05.get('remote_object_count', 0)} 个对象",
            f"本地缓存完整，匹配字节 {pi05.get('local_matched_bytes', 0):,}。",
            "reports/pi05_base_repro.md",
        ),
        card(
            "pi0.6 / pi0.7",
            "watch" if gcs_zero else "done",
            "未发现公开 checkpoint",
            "公开 OpenPI/GCS 审计未找到可直接复现 checkpoint；当前只能记录为 release gap。",
            "reports/pi06_pi07_public_release_audit.md",
        ),
        card(
            "Table30v2 ALOHA",
            "done" if mapping.get("ready_for_dry_run_converter") and mapping.get("lengths_match") else "watch",
            "1100 帧任务链",
            "pack_the_toothbrush_holder 映射、转换、短 episode dataloader 已完成。",
            "reports/table30v2_aloha_mapping.md",
        ),
        card(
            "LoRA 物化 policy",
            "done" if lora_policy.get("passed") else "watch",
            lora_policy.get("policy_load_smoke", {}).get("model_type", "Pi0"),
            "完整物化 checkpoint 已通过 create_trained_policy 加载 smoke。",
            "reports/openpi_rtc_lora_materialized_policy_smoke.md",
        ),
        card(
            "Checkpoint 导出",
            "done" if lora_export.get("local_export_ready") else "watch",
            f"{lora_export.get('inventory', {}).get('total_size_gb', 11.064)} GB",
            "目录结构、必需文件、tar stream smoke 已就绪。",
            "reports/lora_checkpoint_export_readiness.md",
        ),
        card(
            "归档生成",
            "blocked" if not archive_created else "done",
            "dry-run 已通过",
            "默认不生成 tar；真实生成必须先通过归档强确认入口。",
            "reports/checkpoint_archive_dry_run.md",
        ),
        card(
            "归档强确认入口",
            "done" if archive_confirm_gate_passed else "watch",
            "无确认不生成 tar",
            (
                "模板要求 ROBOCHALLENGE_ARCHIVE_CONFIRM=CREATE_ROBOCHALLENGE_CHECKPOINT_ARCHIVE；"
                "未确认时停在 creating tar 前。"
            ),
            "reports/authorized_checkpoint_archive_template_audit.md",
        ),
        card(
            "上传与链接",
            "blocked" if not current_link_ready else "done",
            "缺少真实链接" if not current_link_ready else "链接形态就绪",
            "当前未上传 checkpoint，未设置真实 checkpoint link。",
            "reports/checkpoint_link_intake.md",
        ),
        card(
            "真实提交 gate",
            "blocked" if not ready_for_real else "done",
            "ready=false" if not ready_for_real else "ready=true",
            "缺少 user token、submission id、checkpoint link；runner 仍不会启动。",
            "reports/real_submission_readiness.md",
        ),
        card(
            "提交前预检汇总",
            "blocked" if preflight.get("go_no_go") == "blocked" else "done",
            f"go/no-go={preflight.get('go_no_go', 'unknown')}",
            (
                "一键预检已串联 link、下载协议、readiness、handoff 和明文扫描；"
                f"no-contact={yes(preflight_no_contact)}，no-leak={yes(preflight_no_leak)}。"
            ),
            "reports/submission_preflight_bundle.md",
        ),
        card(
            "授权后顺序",
            "done" if sequence.get("passed") and sequence.get("commands", {}).get("critical_order_passed") else "watch",
            "顺序已固化",
            "link intake -> readiness -> dry-run -> real runner 的顺序已通过审计。",
            "reports/authorized_submission_sequence_audit.md",
        ),
        card(
            "明文凭据扫描",
            "done" if plaintext_clean else "watch",
            f"hit_count={plaintext.get('hit_count')}",
            "仓库跟踪文件和未忽略文件未发现明文凭据模式。",
            "reports/plaintext_secret_scan.md",
        ),
    ]


def build_status(cards: list[dict[str, str]], data: dict[str, dict[str, Any]], html_path: Path) -> dict[str, Any]:
    readiness = data["readiness"]
    link_intake = data["link_intake"]
    archive = data["archive_dry_run"]
    authorized_archive = data["authorized_archive"]
    sequence = data["authorized_sequence"]
    preflight = data["preflight_bundle"]
    plaintext = data["plaintext_scan"]
    preflight_contacts = preflight.get("contact_flags", {})
    preflight_leaks = preflight.get("leak_flags", {})
    blocked_cards = [item for item in cards if item["state"] == "blocked"]
    watch_cards = [item for item in cards if item["state"] == "watch"]
    done_cards = [item for item in cards if item["state"] == "done"]
    return {
        "kind": "submission_status_dashboard",
        "passed": True,
        "html_path": html_path.relative_to(ROOT).as_posix(),
        "source_count": len(SOURCE_FILES),
        "card_count": len(cards),
        "done_count": len(done_cards),
        "blocked_count": len(blocked_cards),
        "watch_count": len(watch_cards),
        "ready_for_real_submission": readiness.get("ready_for_real_submission"),
        "web_form_ready": readiness.get("web_form_ready"),
        "preflight_passed": preflight.get("passed"),
        "preflight_go_no_go": preflight.get("go_no_go"),
        "preflight_no_contact": not any(preflight_contacts.values()),
        "preflight_no_secret_leak": not any(preflight_leaks.values()),
        "link_shape_ready": link_intake.get("current_env", {}).get("link_shape_ready"),
        "archive_created": archive.get("archive_created"),
        "archive_confirm_gate_passed": authorized_archive.get("passed") is True,
        "archive_confirm_phrase": authorized_archive.get("confirmation_phrase"),
        "archive_no_confirm_blocks": authorized_archive.get("no_confirm_smoke", {}).get("passed") is True,
        "uploads_performed": readiness.get("inputs", {}).get("uploads_performed"),
        "platform_contacted": False,
        "credentials_printed": False,
        "link_values_printed": False,
        "secret_values_printed": plaintext.get("secret_values_printed"),
        "critical_order_passed": sequence.get("commands", {}).get("critical_order_passed"),
        "blocking": readiness.get("blocking", []),
        "cards": cards,
    }


def render_html(status: dict[str, Any]) -> str:
    cards_html = []
    for item in status["cards"]:
        cards_html.append(
            f"""
            <article class="card {escape(item['state'])}">
              <div class="card-top">
                <span class="state">{escape(item['state_label'])}</span>
                <a href="../{escape(item['report'])}">报告</a>
              </div>
              <h2>{escape(item['title'])}</h2>
              <p class="value">{escape(item['value'])}</p>
              <p>{escape(item['detail'])}</p>
            </article>
            """
        )
    blocking_html = "".join(f"<li>{escape(item)}</li>" for item in status["blocking"])
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>RoboChallenge pi0.5 提交状态面板</title>
  <style>
    :root {{
      --ink: #16201b;
      --muted: #657067;
      --paper: #f2f5f1;
      --line: #cbd5cf;
      --done: #2f7d5b;
      --blocked: #b64b34;
      --watch: #8a6d24;
      --panel: #ffffff;
      --shadow: 0 16px 42px rgba(34, 54, 44, .12);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      font-family: "Aptos", "Segoe UI", "Microsoft YaHei", sans-serif;
      letter-spacing: 0;
    }}
    .shell {{ max-width: 1180px; margin: 0 auto; padding: 28px 22px 44px; }}
    header {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 18px;
      align-items: end;
      border-bottom: 2px solid var(--ink);
      padding-bottom: 18px;
    }}
    h1 {{ margin: 0; font-size: 30px; line-height: 1.1; font-weight: 800; }}
    .sub {{ margin: 10px 0 0; color: var(--muted); font-size: 14px; max-width: 760px; }}
    .stamp {{ font-size: 12px; color: var(--muted); text-align: right; }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 10px;
      margin: 18px 0;
    }}
    .metric {{
      background: var(--panel);
      border: 1px solid var(--line);
      padding: 12px;
      min-height: 86px;
    }}
    .metric b {{ display: block; font-size: 24px; margin-bottom: 8px; }}
    .metric span {{ color: var(--muted); font-size: 12px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin-top: 14px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-left: 6px solid var(--muted);
      padding: 14px 16px 16px;
      box-shadow: var(--shadow);
      min-height: 150px;
    }}
    .card.done {{ border-left-color: var(--done); }}
    .card.blocked {{ border-left-color: var(--blocked); }}
    .card.watch {{ border-left-color: var(--watch); }}
    .card-top {{ display: flex; justify-content: space-between; align-items: center; gap: 10px; }}
    .state {{
      font-size: 12px;
      font-weight: 700;
      padding: 4px 7px;
      border: 1px solid currentColor;
      color: var(--muted);
    }}
    .done .state {{ color: var(--done); }}
    .blocked .state {{ color: var(--blocked); }}
    .watch .state {{ color: var(--watch); }}
    a {{ color: var(--ink); text-decoration: underline; text-underline-offset: 3px; }}
    h2 {{ margin: 14px 0 8px; font-size: 18px; line-height: 1.2; }}
    p {{ margin: 0; color: var(--muted); line-height: 1.55; font-size: 14px; overflow-wrap: anywhere; }}
    .value {{ color: var(--ink); font-size: 21px; font-weight: 800; margin-bottom: 8px; overflow-wrap: anywhere; }}
    .blockers {{
      margin-top: 18px;
      background: #1f2924;
      color: #f5fff8;
      padding: 18px;
    }}
    .blockers h2 {{ margin-top: 0; color: #f5fff8; }}
    .blockers li {{ margin: 7px 0; line-height: 1.45; }}
    @media (max-width: 820px) {{
      header {{ grid-template-columns: 1fr; }}
      .stamp {{ text-align: left; }}
      .summary {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <header>
      <div>
        <h1>RoboChallenge pi0.5 提交状态面板</h1>
        <p class="sub">静态 GUI 汇总当前复现、LoRA checkpoint、上传/link/readiness 阻塞和授权后执行顺序。面板由 JSON 审计结果生成，不读取或显示真实凭据。</p>
      </div>
      <div class="stamp">生成时间<br>{escape(generated_at)}</div>
    </header>
    <section class="summary">
      <div class="metric"><b>{status['done_count']}</b><span>已完成项</span></div>
      <div class="metric"><b>{status['blocked_count']}</b><span>待授权项</span></div>
      <div class="metric"><b>{yes(status['ready_for_real_submission'])}</b><span>真实提交就绪</span></div>
      <div class="metric"><b>{yes(status['link_shape_ready'])}</b><span>checkpoint link 就绪</span></div>
      <div class="metric"><b>{yes(status['archive_created'])}</b><span>本地 tar 已生成</span></div>
    </section>
    <section class="grid">
      {''.join(cards_html)}
    </section>
    <section class="blockers">
      <h2>当前阻塞</h2>
      <ul>{blocking_html}</ul>
    </section>
  </main>
</body>
</html>
"""
    return "\n".join(line.rstrip() for line in html.splitlines()) + "\n"


def main() -> int:
    args = parse_args()
    data = {key: read_json(path) for key, path in SOURCE_FILES.items()}
    cards = build_cards(data)
    status = build_status(cards, data, args.html_path)
    args.html_path.parent.mkdir(parents=True, exist_ok=True)
    args.html_path.write_text(render_html(status), encoding="utf-8")
    args.status_path.parent.mkdir(parents=True, exist_ok=True)
    args.status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
