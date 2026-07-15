"""Create browser-rendered preview images from the real dashboard data and figures.

This is a packaging/QC helper. The live app itself is still started with
run_demo_mac.command or python start_demo.py.
"""
from __future__ import annotations

import html as html_escape_module
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("START_SIMULATOR", "0")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright  # noqa: E402
from plotly.offline import get_plotlyjs  # noqa: E402

import app  # noqa: E402

OUT = ROOT / "screenshots_v2"
OUT.mkdir(exist_ok=True)
CSS = (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
PLOTLY_JS = get_plotlyjs()


def esc(value: object) -> str:
    return html_escape_module.escape(str(value))


def plot_scripts(figures: dict[str, object]) -> str:
    scripts: list[str] = []
    for element_id, figure in figures.items():
        payload = json.loads(figure.to_json())
        scripts.append(
            f"Plotly.newPlot('{element_id}', {json.dumps(payload['data'])}, "
            f"{json.dumps(payload['layout'])}, {{displayModeBar:false,responsive:true}});"
        )
    return "".join(scripts)


def sidebar(active: str) -> str:
    nav = [
        ("overview", "⌁", "Overview"),
        ("explorer", "⌕", "Metric Explorer"),
        ("operations", "⚙", "Pipeline Operations"),
    ]
    buttons = "".join(
        f"<button class='nav-item {'active' if key == active else ''}'><span>{icon}</span>{label}</button>"
        for key, icon, label in nav
    )
    return f"""
    <aside class='sidebar'>
      <div class='brand'><div class='brand-mark'>◉</div><div><div class='brand-title'>GALAXY RING</div><div class='brand-subtitle'>LIVE ANALYTICS</div></div></div>
      <div class='live-pill'><span class='live-dot'></span>SIMULATED LIVE FEED</div>
      <nav>{buttons}</nav>
      <div class='path-panel'><div class='side-label'>MEDALLION FLOW</div>
        <div class='stage-node bronze'><span>01</span><b>Bronze</b><small>Raw events</small></div><div class='stage-line'></div>
        <div class='stage-node silver'><span>02</span><b>Silver</b><small>Trusted current state</small></div><div class='stage-line'></div>
        <div class='stage-node gold'><span>03</span><b>Gold</b><small>Daily aggregates</small></div><div class='stage-line'></div>
        <div class='stage-node direct'><span>04</span><b>Direct Lake</b><small>BI-ready model</small></div>
      </div>
    </aside>"""


def topbar(title: str, subtitle: str, status: str = "Pipeline healthy") -> str:
    return f"""
    <header class='topbar'>
      <div><div class='eyebrow'>LIVE PORTFOLIO PROJECT</div><h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div>
      <div class='header-actions'>
        <div class='status-stack'><div class='health-status healthy'><span class='status-dot'></span>{esc(status)}</div><div class='last-refresh'>Live capture</div></div>
        <div class='view-controls'><div class='tiny-label'>VIEW</div><div class='viewport-label'>1440×900</div><div class='mode-switch'><label class='mode-label'>Fit 1440×900</label><label class='mode-label'>Auto</label></div></div>
        <button class='live-control running'>Pause live</button>
      </div>
    </header>"""


def document(body: str, scripts: str) -> str:
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>{CSS}
    body{{width:1440px;height:900px;overflow:hidden}}.sidebar{{left:0}}.main{{height:900px;overflow:hidden}}
    table{{width:100%;border-collapse:collapse;font-size:10px}}th{{text-align:left;background:#112b4b;color:#c9ecff;padding:9px}}td{{padding:8px 9px;color:#dceaff;border-bottom:1px solid rgba(80,130,180,.08)}}tr:nth-child(even) td{{background:#0d223b}}
    </style><script>{PLOTLY_JS}</script></head><body>
    <div class='app-shell fit-viewport' style='--sidebar-width:228px;--header-height:76px;--kpi-height:104px;--chart-height:224px;--ops-height:78px'>{body}</div>
    <script>{scripts}</script></body></html>"""


def overview_html() -> str:
    result = app.refresh_overview(0, "14d")
    values, deltas = result[:6], result[6:12]
    kpis = [
        ("Steps", values[0], deltas[0], "↟", "steps"),
        ("Sleep Hours", values[1], deltas[1], "☾", "sleep"),
        ("Avg Heart Rate", values[2], deltas[2], "♥", "hr"),
        ("SpO₂", values[3], deltas[3], "◉", "spo2"),
        ("Skin Temp", values[4], deltas[4], "♨", "temp"),
        ("Energy Score", values[5], deltas[5], "ϟ", "energy"),
    ]
    kpi_cards = "".join(
        f"<div class='kpi-card metric-{accent}'><div class='kpi-title'><span class='kpi-icon'>{icon}</span>{esc(title)}</div><div class='kpi-value'>{esc(value)}</div><div class='kpi-delta good'>{esc(delta)}</div><div class='kpi-meter-track'><div class='kpi-meter-fill'></div></div><div class='kpi-glow'></div></div>"
        for title, value, delta, icon, accent in kpis
    )
    content = f"""
    {sidebar('overview')}<main class='main'>{topbar('Health Overview','Near-real-time Galaxy Ring telemetry and daily trends',result[29])}
    <section><div class='overview-toolbar'><div class='trend-control'><span class='control-label'>TREND WINDOW</span><div class='segment-control'><label class='segment-label'>7D</label><label class='segment-label' style='color:white;background:linear-gradient(135deg,rgba(49,168,255,.35),rgba(45,226,255,.13))'>14D</label></div></div><div class='event-ticker'><span class='control-label'>LATEST EVENT</span><span class='ticker-value'>{esc(result[27])}</span></div><div class='rate-chip'><span class='control-label'>EVENT RATE</span><span class='event-rate-value'>{esc(result[28])}</span></div></div>
    <div class='kpi-grid'>{kpi_cards}</div>
    <div class='dashboard-grid'>
      <div class='panel span-7'><div class='panel-header'><div class='panel-title'>Daily Steps Trend</div><div class='panel-badge'>10K target</div></div><div id='steps' class='graph'></div></div>
      <div class='panel span-5'><div class='panel-header'><div class='panel-title'>Sleep Duration</div><div class='panel-badge'>color-coded</div></div><div id='sleep' class='graph'></div></div>
      <div class='panel span-7'><div class='panel-header'><div class='panel-title'>Heart Rate — Last 24 Hours</div><div class='panel-badge'>live samples</div></div><div id='heart' class='graph'></div></div>
      <div class='panel span-5'><div class='panel-header'><div class='panel-title'>Sleep Stages</div><div class='panel-badge'>latest session</div></div><div id='donut' class='graph'></div></div>
    </div>
    <div class='ops-strip'><div class='ops-mini freshness'><div class='ops-mini-title'>Data Freshness</div><div class='ops-mini-value green'>{esc(result[22])}</div><div class='muted'>Latest Silver event</div></div><div class='ops-mini runs'><div class='ops-mini-title'>Pipeline Runs</div><div class='ops-mini-value blue'>{esc(result[23])}</div><div class='muted'>Successful today</div></div><div class='ops-mini quality'><div class='ops-mini-title'>Failed Quality Checks</div><div class='ops-mini-value green'>{esc(result[24])}</div><div class='muted'>Latest validation cycle</div></div><div class='ops-mini watermark'><div class='ops-mini-title'>Current Watermark</div><div class='watermark-text'>{esc(result[25])}</div><div class='muted'>30-minute safety overlap</div></div></div></section></main>"""
    return document(content, plot_scripts(dict(zip(["steps", "sleep", "heart", "donut"], result[18:22]))))


def explorer_html() -> str:
    figure, rows, columns, latest, minimum, maximum, records = app.refresh_explorer(0, "heart_rate", "24h", "smooth")
    headers = "".join(f"<th>{esc(column['name'])}</th>" for column in columns)
    table_rows = "".join(
        "<tr>" + "".join(f"<td>{esc(row.get(column['id'], ''))}</td>" for column in columns) + "</tr>"
        for row in rows[:8]
    )
    content = f"""
    {sidebar('explorer')}<main class='main'>{topbar('Metric Explorer','Filter, smooth, zoom, and inspect event-level measurements')}
      <div class='filter-row'><div class='filter-control'><label>Metric</label><div>Heart Rate ▾</div></div><div class='filter-control'><label>Window</label><div>Last 24 hours ▾</div></div><div class='filter-control wider'><label>Display</label><div class='segment-control explorer-segment'><span class='segment-label'>Raw</span><span class='segment-label' style='color:white;background:linear-gradient(135deg,rgba(49,168,255,.35),rgba(45,226,255,.13))'>5-point average</span></div></div></div>
      <div class='explorer-stats'><div class='explorer-stat latest'><div class='explorer-stat-label'>Latest</div><div class='explorer-stat-value'>{esc(latest)}</div></div><div class='explorer-stat minimum'><div class='explorer-stat-label'>Minimum</div><div class='explorer-stat-value'>{esc(minimum)}</div></div><div class='explorer-stat maximum'><div class='explorer-stat-label'>Maximum</div><div class='explorer-stat-value'>{esc(maximum)}</div></div><div class='explorer-stat records'><div class='explorer-stat-label'>Records</div><div class='explorer-stat-value'>{esc(records)}</div></div></div>
      <div class='panel explorer-panel'><div class='panel-header'><div class='panel-title'>Metric Timeline</div><div class='panel-badge'>zoom + hover enabled</div></div><div id='explorer' class='graph explorer-graph'></div></div>
      <div class='panel table-panel'><div class='panel-header'><div class='panel-title'>Latest Event Records</div><div class='panel-badge'>sortable table</div></div><table><thead><tr>{headers}</tr></thead><tbody>{table_rows}</tbody></table></div>
    </main>"""
    return document(content, plot_scripts({"explorer": figure}))


def operations_html() -> str:
    result = app.refresh_operations(0)
    cards = [
        ("BRONZE", result[0], "Raw immutable events", "bronze-card", "bronze-tag"),
        ("SILVER", result[1], "Current trusted state", "silver-card", "silver-tag"),
        ("LATEST UPSERTS", result[2], "Last pipeline run", "upsert-card", "upsert-tag"),
        ("LATEST DELETES", result[3], "Source corrections", "delete-card", "delete-tag"),
    ]
    card_html = "".join(f"<div class='ops-card {card_class}'><div class='stage-tag {tag_class}'>{label}</div><div class='ops-card-value'>{value}</div><div class='muted'>{desc}</div></div>" for label, value, desc, card_class, tag_class in cards)
    content = f"""
    {sidebar('operations')}<main class='main'>{topbar('Pipeline Operations','Watermarks, upserts, deletes, quality checks, and throughput')}
      <div class='ops-card-grid'>{card_html}</div>
      <div class='pipeline-flow'><div class='flow-step eventstream'><span>01</span><b>Eventstream</b><small>JSON ingress</small></div><div class='flow-arrow'>→</div><div class='flow-step bronze'><span>02</span><b>Bronze</b><small>append only</small></div><div class='flow-arrow'>→</div><div class='flow-step spark'><span>03</span><b>Spark MERGE</b><small>dedupe + CDC</small></div><div class='flow-arrow'>→</div><div class='flow-step silver'><span>04</span><b>Silver</b><small>trusted state</small></div><div class='flow-arrow'>→</div><div class='flow-step gold'><span>05</span><b>Gold</b><small>BI model</small></div></div>
      <div class='dashboard-grid operations-grid'><div class='panel span-7'><div class='panel-header'><div class='panel-title'>Pipeline Throughput</div><div class='panel-badge'>input vs dedupe</div></div><div id='throughput' class='graph'></div></div><div class='panel span-5'><div class='panel-header'><div class='panel-title'>Run Duration</div><div class='panel-badge'>milliseconds</div></div><div id='duration' class='graph'></div></div><div class='panel span-7'><div class='panel-header'><div class='panel-title'>Upserts vs Deletes</div><div class='panel-badge'>CDC activity</div></div><div id='cdc' class='graph'></div></div><div class='panel span-5'><div class='panel-header'><div class='panel-title'>Data Quality</div><div class='panel-badge'>latest cycle</div></div><div id='quality' class='graph'></div></div></div>
      <div class='panel code-summary'><div class='panel-title'>Incremental Processing Logic</div><pre><code>watermark − 30 min overlap  →  deduplicate(record_id, metric_type)\n→ MERGE latest modification  →  UPSERT current state | propagate DELETE\n→ aggregate Gold  →  quality checks  →  advance watermark</code></pre></div>
    </main>"""
    return document(content, plot_scripts(dict(zip(["throughput", "duration", "cdc", "quality"], result[4:8]))))


def capture(name: str, content: str, page) -> None:
    page.set_content(content, wait_until="load", timeout=60_000)
    page.wait_for_timeout(1_000)
    page.screenshot(path=str(OUT / name), full_page=False)


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        capture("overview_1440x900.png", overview_html(), page)
        capture("metric_explorer_1440x900.png", explorer_html(), page)
        capture("pipeline_operations_1440x900.png", operations_html(), page)
        browser.close()
    print(f"Saved previews to {OUT}")


if __name__ == "__main__":
    main()
