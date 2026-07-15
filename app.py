from __future__ import annotations

import os
from datetime import datetime, timezone

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, callback_context, dash_table, dcc, html

from db import fetch_df, initialize_db, seed_history
from simulator import LiveRingSimulator
from ui_config import (
    CHART_HEIGHT,
    COMPACT_BREAKPOINT_HEIGHT,
    COMPACT_BREAKPOINT_WIDTH,
    DEFAULT_VIEWPORT_HEIGHT,
    DEFAULT_VIEWPORT_WIDTH,
    HEADER_HEIGHT,
    KPI_HEIGHT,
    OPS_STRIP_HEIGHT,
    REFRESH_MS,
    SIDEBAR_WIDTH,
    VIEWPORT_POLL_MS,
)

initialize_db()
seed_history()
SIMULATOR = LiveRingSimulator(interval_seconds=float(os.getenv("SIM_INTERVAL", "2")))
if os.getenv("START_SIMULATOR", "1") == "1":
    SIMULATOR.start()

app = Dash(__name__, title="Galaxy Ring Live Analytics", suppress_callback_exceptions=True)
server = app.server


@server.get("/healthz")
def healthz():
    """Lightweight health endpoint for cloud hosting platforms."""
    return {"status": "ok", "service": "galaxy-ring-live-dashboard"}, 200


PLOT_BG = "rgba(0,0,0,0)"
GRID = "rgba(128, 167, 219, .12)"
TEXT = "#edf7ff"
MUTED = "#88a2bf"
BLUE = "#31a8ff"
CYAN = "#2de2ff"
PURPLE = "#8b7bff"
GREEN = "#44e59a"
YELLOW = "#ffc857"
ORANGE = "#ff9357"
RED = "#ff647c"

METRIC_META = {
    "heart_rate": {"label": "Heart Rate", "color": RED, "unit": "bpm", "icon": "♥"},
    "blood_oxygen": {"label": "Blood Oxygen", "color": CYAN, "unit": "%", "icon": "◉"},
    "skin_temperature": {"label": "Skin Temperature", "color": ORANGE, "unit": "°C", "icon": "♨"},
    "steps": {"label": "Steps", "color": BLUE, "unit": "steps", "icon": "↟"},
    "energy_score": {"label": "Energy Score", "color": YELLOW, "unit": "score", "icon": "ϟ"},
}

GRAPH_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
    "scrollZoom": False,
    "showTips": False,
}


def empty_figure(message: str = "Waiting for data") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, x=.5, y=.5, showarrow=False, font={"color": MUTED, "size": 16})
    fig.update_layout(
        template=None,
        paper_bgcolor=PLOT_BG,
        plot_bgcolor=PLOT_BG,
        xaxis={"visible": False},
        yaxis={"visible": False},
        margin=dict(l=10, r=10, t=10, b=10),
    )
    return fig


def style_figure(
    fig: go.Figure,
    *,
    legend: bool = True,
    margin: dict | None = None,
    uirevision: str = "stable",
    hovermode: str | bool = "x unified",
) -> go.Figure:
    fig.update_layout(
        paper_bgcolor=PLOT_BG,
        plot_bgcolor=PLOT_BG,
        autosize=True,
        font={"family": "Inter, Segoe UI, Arial", "color": TEXT, "size": 11},
        margin=margin or dict(l=42, r=18, t=32, b=34),
        hoverlabel={"bgcolor": "#102847", "font_color": "white", "bordercolor": "#2a5c8f"},
        hovermode=hovermode,
        legend={
            "orientation": "h",
            "y": 1.10,
            "x": 0,
            "font": {"size": 10, "color": "#bcd4eb"},
            "bgcolor": "rgba(0,0,0,0)",
        } if legend else {},
        transition={"duration": 280, "easing": "cubic-in-out"},
        uirevision=uirevision,
    )
    fig.update_xaxes(showgrid=False, zeroline=False, color=MUTED, automargin=True)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, color=MUTED, automargin=True)
    return fig


def safe_float(value: object, default: float = 0.0) -> float:
    try:
        return default if value is None or pd.isna(value) else float(value)
    except (TypeError, ValueError):
        return default


def kpi_card(title: str, value_id: str, delta_id: str, icon: str, accent: str) -> html.Div:
    return html.Div(
        [
            html.Div(
                [html.Span(icon, className="kpi-icon"), html.Span(title)],
                className="kpi-title",
            ),
            html.Div(id=value_id, className="kpi-value"),
            html.Div(id=delta_id, className="kpi-delta"),
            html.Div(className="kpi-meter-track", children=html.Div(className="kpi-meter-fill")),
            html.Div(className="kpi-glow"),
        ],
        className=f"kpi-card metric-{accent}",
    )


def panel(title: str, graph_id: str, span: str, badge: str | None = None) -> html.Div:
    header = [html.Div(title, className="panel-title")]
    if badge:
        header.append(html.Div(badge, className="panel-badge"))
    return html.Div(
        [
            html.Div(header, className="panel-header"),
            dcc.Loading(
                dcc.Graph(
                    id=graph_id,
                    config=GRAPH_CONFIG,
                    responsive=True,
                    className="graph",
                ),
                type="dot",
                color=CYAN,
                parent_className="graph-loading",
            ),
        ],
        className=f"panel {span}",
    )


app.layout = html.Div(
    id="app-shell",
    className="app-shell fit-viewport",
    style={
        "--sidebar-width": f"{SIDEBAR_WIDTH}px",
        "--header-height": f"{HEADER_HEIGHT}px",
        "--kpi-height": f"{KPI_HEIGHT}px",
        "--chart-height": f"{CHART_HEIGHT}px",
        "--ops-height": f"{OPS_STRIP_HEIGHT}px",
        "--design-width": f"{DEFAULT_VIEWPORT_WIDTH}px",
        "--design-height": f"{DEFAULT_VIEWPORT_HEIGHT}px",
    },
    children=[
        dcc.Interval(id="refresh", interval=REFRESH_MS, n_intervals=0, disabled=False),
        dcc.Interval(id="viewport-poll", interval=VIEWPORT_POLL_MS, n_intervals=0),
        dcc.Store(id="active-page", data="overview"),
        dcc.Store(id="viewport-store", data={"width": DEFAULT_VIEWPORT_WIDTH, "height": DEFAULT_VIEWPORT_HEIGHT}),
        html.Aside(
            [
                html.Div(
                    [
                        html.Div("◉", className="brand-mark"),
                        html.Div(
                            [
                                html.Div("GALAXY RING", className="brand-title"),
                                html.Div("LIVE ANALYTICS", className="brand-subtitle"),
                            ]
                        ),
                    ],
                    className="brand",
                ),
                html.Div(
                    [html.Span(className="live-dot"), html.Span("SIMULATED LIVE FEED")],
                    className="live-pill",
                ),
                html.Nav(
                    [
                        html.Button([html.Span("⌁"), "Overview"], id="nav-overview", n_clicks=0, className="nav-item active"),
                        html.Button([html.Span("⌕"), "Metric Explorer"], id="nav-explorer", n_clicks=0, className="nav-item"),
                        html.Button([html.Span("⚙"), "Pipeline Operations"], id="nav-operations", n_clicks=0, className="nav-item"),
                    ]
                ),
                html.Div(
                    [
                        html.Div("MEDALLION FLOW", className="side-label"),
                        html.Div([html.Span("01"), html.B("Bronze"), html.Small("Raw events")], className="stage-node bronze"),
                        html.Div(className="stage-line"),
                        html.Div([html.Span("02"), html.B("Silver"), html.Small("Trusted current state")], className="stage-node silver"),
                        html.Div(className="stage-line"),
                        html.Div([html.Span("03"), html.B("Gold"), html.Small("Daily aggregates")], className="stage-node gold"),
                        html.Div(className="stage-line"),
                        html.Div([html.Span("04"), html.B("Direct Lake"), html.Small("BI-ready model")], className="stage-node direct"),
                    ],
                    className="path-panel",
                ),
                html.Div(
                    [
                        html.Div("Synthetic wellness analytics demo"),
                        html.Div("Not medical advice", className="muted"),
                    ],
                    className="disclaimer",
                ),
            ],
            className="sidebar",
        ),
        html.Main(
            [
                html.Header(
                    [
                        html.Div(
                            [
                                html.Div("LIVE PORTFOLIO PROJECT", className="eyebrow"),
                                html.H1(id="page-title", children="Health Overview"),
                                html.P(id="page-subtitle", children="Near-real-time Galaxy Ring telemetry and daily trends"),
                            ],
                            className="title-block",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div([html.Span(className="status-dot"), html.Span(id="pipeline-status-text", children="Pipeline healthy")], id="pipeline-status", className="health-status healthy"),
                                        html.Div(id="last-refresh", className="last-refresh"),
                                    ],
                                    className="status-stack",
                                ),
                                html.Div(
                                    [
                                        html.Div("VIEW", className="tiny-label"),
                                        dcc.RadioItems(
                                            id="layout-mode",
                                            value="fit",
                                            options=[
                                                {"label": "Fit 1440×900", "value": "fit"},
                                                {"label": "Auto", "value": "auto"},
                                            ],
                                            className="mode-switch",
                                            inputClassName="mode-input",
                                            labelClassName="mode-label",
                                        ),
                                        html.Div(id="viewport-label", className="viewport-label"),
                                    ],
                                    className="view-controls",
                                ),
                                html.Button("Pause live", id="live-toggle", n_clicks=0, className="live-control running"),
                            ],
                            className="header-actions",
                        ),
                    ],
                    className="topbar",
                ),
                html.Section(
                    id="overview-page",
                    children=[
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Span("TREND WINDOW", className="control-label"),
                                        dcc.RadioItems(
                                            id="trend-window",
                                            value="14d",
                                            options=[
                                                {"label": "7D", "value": "7d"},
                                                {"label": "14D", "value": "14d"},
                                            ],
                                            className="segment-control",
                                            inputClassName="segment-input",
                                            labelClassName="segment-label",
                                        ),
                                    ],
                                    className="trend-control",
                                ),
                                html.Div(
                                    [
                                        html.Span("LATEST EVENT", className="control-label"),
                                        html.Span(id="latest-event", className="ticker-value"),
                                    ],
                                    className="event-ticker",
                                ),
                                html.Div(
                                    [
                                        html.Span("EVENT RATE", className="control-label"),
                                        html.Span(id="event-rate", className="event-rate-value"),
                                    ],
                                    className="rate-chip",
                                ),
                            ],
                            className="overview-toolbar",
                        ),
                        html.Div(
                            [
                                kpi_card("Steps", "kpi-steps", "delta-steps", "↟", "steps"),
                                kpi_card("Sleep Hours", "kpi-sleep", "delta-sleep", "☾", "sleep"),
                                kpi_card("Avg Heart Rate", "kpi-hr", "delta-hr", "♥", "hr"),
                                kpi_card("SpO₂", "kpi-spo2", "delta-spo2", "◉", "spo2"),
                                kpi_card("Skin Temp", "kpi-temp", "delta-temp", "♨", "temp"),
                                kpi_card("Energy Score", "kpi-energy", "delta-energy", "ϟ", "energy"),
                            ],
                            className="kpi-grid",
                        ),
                        html.Div(
                            [
                                panel("Daily Steps Trend", "steps-chart", "span-7", "10K target"),
                                panel("Sleep Duration", "sleep-chart", "span-5", "color-coded"),
                                panel("Heart Rate — Last 24 Hours", "hr-chart", "span-7", "live samples"),
                                panel("Sleep Stages", "sleep-donut", "span-5", "latest session"),
                            ],
                            className="dashboard-grid",
                        ),
                        html.Div(
                            [
                                html.Div([html.Div("Data Freshness", className="ops-mini-title"), html.Div(id="freshness-value", className="ops-mini-value green"), html.Div("Latest Silver event", className="muted")], className="ops-mini freshness"),
                                html.Div([html.Div("Pipeline Runs", className="ops-mini-title"), html.Div(id="run-count", className="ops-mini-value blue"), html.Div("Successful today", className="muted")], className="ops-mini runs"),
                                html.Div([html.Div("Failed Quality Checks", className="ops-mini-title"), html.Div(id="dq-fail", className="ops-mini-value green"), html.Div("Latest validation cycle", className="muted")], className="ops-mini quality"),
                                html.Div([html.Div("Current Watermark", className="ops-mini-title"), html.Div(id="watermark-mini", className="watermark-text"), html.Div("30-minute safety overlap", className="muted")], className="ops-mini wide watermark"),
                            ],
                            className="ops-strip",
                        ),
                    ],
                ),
                html.Section(
                    id="explorer-page",
                    style={"display": "none"},
                    children=[
                        html.Div(
                            [
                                html.Div([html.Label("Metric"), dcc.Dropdown(id="metric-select", value="heart_rate", clearable=False, searchable=False, options=[{"label": meta["label"], "value": key} for key, meta in METRIC_META.items()])], className="filter-control"),
                                html.Div([html.Label("Window"), dcc.Dropdown(id="window-select", value="24h", clearable=False, searchable=False, options=[{"label": "Last 1 hour", "value": "1h"}, {"label": "Last 6 hours", "value": "6h"}, {"label": "Last 24 hours", "value": "24h"}, {"label": "All history", "value": "all"}])], className="filter-control"),
                                html.Div([html.Label("Display"), dcc.RadioItems(id="smoothing-select", value="raw", options=[{"label": "Raw", "value": "raw"}, {"label": "5-point average", "value": "smooth"}], className="segment-control explorer-segment", inputClassName="segment-input", labelClassName="segment-label")], className="filter-control wider"),
                            ],
                            className="filter-row",
                        ),
                        html.Div(
                            [
                                html.Div([html.Div("Latest", className="explorer-stat-label"), html.Div(id="explorer-latest", className="explorer-stat-value")], className="explorer-stat latest"),
                                html.Div([html.Div("Minimum", className="explorer-stat-label"), html.Div(id="explorer-min", className="explorer-stat-value")], className="explorer-stat minimum"),
                                html.Div([html.Div("Maximum", className="explorer-stat-label"), html.Div(id="explorer-max", className="explorer-stat-value")], className="explorer-stat maximum"),
                                html.Div([html.Div("Records", className="explorer-stat-label"), html.Div(id="explorer-records", className="explorer-stat-value")], className="explorer-stat records"),
                            ],
                            className="explorer-stats",
                        ),
                        html.Div(
                            [
                                html.Div([html.Div("Metric Timeline", className="panel-title"), html.Div("zoom + hover enabled", className="panel-badge")], className="panel-header"),
                                dcc.Loading(dcc.Graph(id="explorer-chart", config={**GRAPH_CONFIG, "displayModeBar": True}, responsive=True, className="graph explorer-graph"), type="dot", color=CYAN),
                            ],
                            className="panel explorer-panel",
                        ),
                        html.Div(
                            [
                                html.Div([html.Div("Latest Event Records", className="panel-title"), html.Div("sortable table", className="panel-badge")], className="panel-header"),
                                dash_table.DataTable(
                                    id="event-table",
                                    page_size=10,
                                    sort_action="native",
                                    style_as_list_view=True,
                                    fixed_rows={"headers": True},
                                    style_table={"overflowX": "auto", "maxHeight": "300px", "overflowY": "auto"},
                                    style_header={"backgroundColor": "#112b4b", "color": "#c9ecff", "fontWeight": "700", "border": "none", "position": "sticky", "top": 0},
                                    style_cell={"backgroundColor": "#08192d", "color": "#e4f2ff", "border": "none", "padding": "10px", "fontFamily": "Inter, Segoe UI", "fontSize": "11px", "minWidth": "110px", "maxWidth": "240px", "whiteSpace": "normal"},
                                    style_data_conditional=[{"if": {"row_index": "odd"}, "backgroundColor": "#0d223b"}],
                                ),
                            ],
                            className="panel table-panel",
                        ),
                    ],
                ),
                html.Section(
                    id="operations-page",
                    style={"display": "none"},
                    children=[
                        html.Div(
                            [
                                html.Div([html.Div("BRONZE", className="stage-tag bronze-tag"), html.Div(id="bronze-count", className="ops-card-value"), html.Div("Raw immutable events", className="muted")], className="ops-card bronze-card"),
                                html.Div([html.Div("SILVER", className="stage-tag silver-tag"), html.Div(id="silver-count", className="ops-card-value"), html.Div("Current trusted state", className="muted")], className="ops-card silver-card"),
                                html.Div([html.Div("LATEST UPSERTS", className="stage-tag upsert-tag"), html.Div(id="latest-upserts", className="ops-card-value"), html.Div("Last pipeline run", className="muted")], className="ops-card upsert-card"),
                                html.Div([html.Div("LATEST DELETES", className="stage-tag delete-tag"), html.Div(id="latest-deletes", className="ops-card-value"), html.Div("Source corrections", className="muted")], className="ops-card delete-card"),
                            ],
                            className="ops-card-grid",
                        ),
                        html.Div(
                            [
                                html.Div([html.Span("01"), html.B("Eventstream"), html.Small("JSON ingress")], className="flow-step eventstream"),
                                html.Div("→", className="flow-arrow"),
                                html.Div([html.Span("02"), html.B("Bronze"), html.Small("append only")], className="flow-step bronze"),
                                html.Div("→", className="flow-arrow"),
                                html.Div([html.Span("03"), html.B("Spark MERGE"), html.Small("dedupe + CDC")], className="flow-step spark"),
                                html.Div("→", className="flow-arrow"),
                                html.Div([html.Span("04"), html.B("Silver"), html.Small("trusted state")], className="flow-step silver"),
                                html.Div("→", className="flow-arrow"),
                                html.Div([html.Span("05"), html.B("Gold"), html.Small("BI model")], className="flow-step gold"),
                            ],
                            className="pipeline-flow",
                        ),
                        html.Div(
                            [
                                panel("Pipeline Throughput", "pipeline-chart", "span-7", "input vs dedupe"),
                                panel("Run Duration", "duration-chart", "span-5", "milliseconds"),
                                panel("Upserts vs Deletes", "upsert-delete-chart", "span-7", "CDC activity"),
                                panel("Data Quality", "dq-chart", "span-5", "latest cycle"),
                            ],
                            className="dashboard-grid operations-grid",
                        ),
                        html.Div(
                            [
                                html.Div("Incremental Processing Logic", className="panel-title"),
                                html.Pre(
                                    html.Code(
                                        "watermark − 30 min overlap  →  deduplicate(record_id, metric_type)\n"
                                        "→ MERGE latest source modification  →  UPSERT current state | propagate DELETE\n"
                                        "→ aggregate Gold  →  quality checks  →  advance watermark"
                                    )
                                ),
                            ],
                            className="panel code-summary",
                        ),
                    ],
                ),
            ],
            className="main",
        ),
    ],
)


@app.callback(
    Output("active-page", "data"),
    Input("nav-overview", "n_clicks"),
    Input("nav-explorer", "n_clicks"),
    Input("nav-operations", "n_clicks"),
    prevent_initial_call=True,
)
def switch_page(_o: int, _e: int, _p: int) -> str:
    trigger = callback_context.triggered_id
    return {"nav-overview": "overview", "nav-explorer": "explorer", "nav-operations": "operations"}.get(trigger, "overview")


@app.callback(
    Output("overview-page", "style"),
    Output("explorer-page", "style"),
    Output("operations-page", "style"),
    Output("nav-overview", "className"),
    Output("nav-explorer", "className"),
    Output("nav-operations", "className"),
    Output("page-title", "children"),
    Output("page-subtitle", "children"),
    Input("active-page", "data"),
)
def render_page(page: str):
    visible = {"display": "block"}
    hidden = {"display": "none"}
    mapping = {
        "overview": ("Health Overview", "Near-real-time Galaxy Ring telemetry and daily trends"),
        "explorer": ("Metric Explorer", "Filter, smooth, zoom, and inspect event-level measurements"),
        "operations": ("Pipeline Operations", "Watermarks, upserts, deletes, quality checks, and throughput"),
    }
    return (
        visible if page == "overview" else hidden,
        visible if page == "explorer" else hidden,
        visible if page == "operations" else hidden,
        "nav-item active" if page == "overview" else "nav-item",
        "nav-item active" if page == "explorer" else "nav-item",
        "nav-item active" if page == "operations" else "nav-item",
        *mapping[page],
    )


app.clientside_callback(
    f"""
    function(n, mode) {{
        const width = window.innerWidth || {DEFAULT_VIEWPORT_WIDTH};
        const height = window.innerHeight || {DEFAULT_VIEWPORT_HEIGHT};
        const compact = width < {COMPACT_BREAKPOINT_WIDTH} || height < {COMPACT_BREAKPOINT_HEIGHT};
        let cssClass = 'app-shell ';
        if (mode === 'fit') {{
            cssClass += 'fit-viewport';
        }} else {{
            cssClass += compact ? 'compact-viewport' : 'auto-viewport';
        }}
        return [{{width: width, height: height}}, cssClass, width + '×' + height];
    }}
    """,
    Output("viewport-store", "data"),
    Output("app-shell", "className"),
    Output("viewport-label", "children"),
    Input("viewport-poll", "n_intervals"),
    Input("layout-mode", "value"),
)


@app.callback(
    Output("refresh", "disabled"),
    Output("live-toggle", "children"),
    Output("live-toggle", "className"),
    Input("live-toggle", "n_clicks"),
)
def toggle_live(n_clicks: int):
    paused = bool(n_clicks and n_clicks % 2 == 1)
    return paused, ("Resume live" if paused else "Pause live"), ("live-control paused" if paused else "live-control running")


def pct_delta(current: float, previous: float, inverse: bool = False):
    if previous in (None, 0) or pd.isna(previous) or pd.isna(current):
        return "—", "neutral"
    p = (current - previous) / abs(previous) * 100
    arrow = "↓" if p < 0 else "↑"
    good = (p <= 0) if inverse else (p >= 0)
    return f"{arrow} {abs(p):.1f}% vs prior day", ("good" if good else "bad")


@app.callback(
    [Output(x, "children") for x in ["kpi-steps", "kpi-sleep", "kpi-hr", "kpi-spo2", "kpi-temp", "kpi-energy"]]
    + [Output(x, "children") for x in ["delta-steps", "delta-sleep", "delta-hr", "delta-spo2", "delta-temp", "delta-energy"]]
    + [Output(x, "className") for x in ["delta-steps", "delta-sleep", "delta-hr", "delta-spo2", "delta-temp", "delta-energy"]]
    + [
        Output("steps-chart", "figure"),
        Output("sleep-chart", "figure"),
        Output("hr-chart", "figure"),
        Output("sleep-donut", "figure"),
        Output("freshness-value", "children"),
        Output("run-count", "children"),
        Output("dq-fail", "children"),
        Output("watermark-mini", "children"),
        Output("last-refresh", "children"),
        Output("latest-event", "children"),
        Output("event-rate", "children"),
        Output("pipeline-status-text", "children"),
        Output("pipeline-status", "className"),
    ],
    Input("refresh", "n_intervals"),
    Input("trend-window", "value"),
)
def refresh_overview(_n: int, trend_window: str):
    daily_all = fetch_df("SELECT * FROM gold_daily_health ORDER BY health_date")
    day_count = 7 if trend_window == "7d" else 14
    daily = daily_all.tail(day_count).copy()

    def latest_pair(column: str):
        valid = daily_all.dropna(subset=[column]) if not daily_all.empty else daily_all
        if valid.empty:
            return 0.0, 0.0
        current = safe_float(valid.iloc[-1][column])
        previous = safe_float(valid.iloc[-2][column], current) if len(valid) > 1 else current
        return current, previous

    steps, prev_steps = latest_pair("steps")
    sleep_minutes, prev_sleep_minutes = latest_pair("sleep_minutes")
    hr, prev_hr = latest_pair("avg_heart_rate")
    spo2, prev_spo2 = latest_pair("avg_blood_oxygen")
    temp, prev_temp = latest_pair("avg_skin_temperature")
    energy, prev_energy = latest_pair("energy_score")
    steps = int(steps)
    sleep_h = sleep_minutes / 60
    values = [f"{steps:,}", f"{sleep_h:.2f}", f"{hr:.0f} bpm", f"{spo2:.1f}%", f"{temp:.1f} °C", f"{energy:.0f}"]
    deltas = [
        pct_delta(steps, prev_steps),
        pct_delta(sleep_h, prev_sleep_minutes / 60),
        pct_delta(hr, prev_hr, inverse=True),
        pct_delta(spo2, prev_spo2),
        pct_delta(temp, prev_temp, inverse=True),
        pct_delta(energy, prev_energy),
    ]
    delta_text = [item[0] for item in deltas]
    delta_classes = [f"kpi-delta {item[1]}" for item in deltas]

    steps_fig = go.Figure()
    if not daily.empty:
        x = pd.to_datetime(daily.health_date)
        y = daily.steps.fillna(0)
        steps_fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", name="Steps", line={"color": BLUE, "width": 3, "shape": "spline"}, marker={"size": 7, "color": BLUE, "line": {"color": "#d8f4ff", "width": 1}}, fill="tozeroy", fillcolor="rgba(49,168,255,.10)"))
        avg = y.rolling(7, min_periods=1).mean()
        steps_fig.add_trace(go.Scatter(x=x, y=avg, mode="lines", name="7-day average", line={"color": CYAN, "dash": "dot", "width": 2, "shape": "spline"}))
        steps_fig.add_hline(y=10000, line_dash="dash", line_color="rgba(68,229,154,.55)")
    style_figure(steps_fig, uirevision=f"steps-{trend_window}")

    sleep_fig = go.Figure()
    sleep_daily = daily.dropna(subset=["sleep_minutes"]) if not daily.empty else daily
    if not sleep_daily.empty:
        sleep_hours = sleep_daily.sleep_minutes / 60
        colors = [GREEN if value >= 7 else (YELLOW if value >= 6 else ORANGE) for value in sleep_hours]
        sleep_fig.add_trace(go.Bar(x=pd.to_datetime(sleep_daily.health_date), y=sleep_hours, name="Sleep hours", marker={"color": colors, "line": {"color": "rgba(255,255,255,.22)", "width": .5}}, text=sleep_hours.round(1), textposition="outside", cliponaxis=False))
        sleep_fig.add_hline(y=7, line_dash="dot", line_color=CYAN, annotation_text="7h guide", annotation_font_color=CYAN, annotation_font_size=10)
    style_figure(sleep_fig, legend=False, uirevision=f"sleep-{trend_window}")

    hr_df = fetch_df("""
        SELECT event_time_utc, numeric_value FROM silver_metrics
        WHERE metric_type='heart_rate' AND datetime(replace(event_time_utc,'Z','')) >= datetime('now','-24 hours')
        ORDER BY event_time_utc
    """)
    hr_fig = go.Figure()
    if not hr_df.empty:
        hr_series = hr_df.numeric_value.astype(float)
        rolling = hr_series.rolling(5, min_periods=1).mean()
        marker_colors = [GREEN if value < 85 else (YELLOW if value < 105 else RED) for value in hr_series]
        hr_fig.add_trace(go.Scatter(x=pd.to_datetime(hr_df.event_time_utc), y=hr_series, mode="lines+markers", line={"color": "rgba(45,226,255,.55)", "width": 1.5, "shape": "spline"}, marker={"size": 5, "color": marker_colors}, name="Live samples"))
        hr_fig.add_trace(go.Scatter(x=pd.to_datetime(hr_df.event_time_utc), y=rolling, mode="lines", line={"color": RED, "width": 2.5, "shape": "spline"}, name="5-point average"))
    style_figure(hr_fig, uirevision="heart-rate-live")

    sleep_source = daily_all.dropna(subset=["sleep_minutes"]) if not daily_all.empty else daily_all
    sleep_row = sleep_source.iloc[-1] if not sleep_source.empty else pd.Series(dtype=float)
    stage_values = [safe_float(sleep_row.get(column)) for column in ["deep_sleep_minutes", "light_sleep_minutes", "rem_sleep_minutes", "awake_sleep_minutes"]]
    donut = go.Figure(go.Pie(labels=["Deep", "Light", "REM", "Awake"], values=stage_values, hole=.70, marker={"colors": ["#1f76ff", CYAN, PURPLE, "#94a5bd"], "line": {"color": "#081527", "width": 3}}, textinfo="label+percent", textfont={"size": 10}, sort=False))
    total = sum(stage_values) / 60
    donut.add_annotation(text=f"<b>{total:.1f}h</b><br><span style='font-size:10px;color:#88a2bf'>Total sleep</span>", x=.5, y=.5, showarrow=False, font={"color": "white", "size": 20})
    style_figure(donut, legend=False, margin=dict(l=8, r=8, t=4, b=4), uirevision="sleep-donut", hovermode=False)

    latest_event_ts = fetch_df("SELECT MAX(ingestion_time_utc) AS t FROM silver_metrics").iloc[0, 0]
    age_seconds = None
    if latest_event_ts:
        age_seconds = max(0, (datetime.now(timezone.utc) - pd.to_datetime(latest_event_ts, utc=True).to_pydatetime()).total_seconds())
        freshness = f"{int(age_seconds)} sec ago" if age_seconds < 60 else f"{int(age_seconds // 60)} min ago"
    else:
        freshness = "—"
    runs = int(fetch_df("SELECT COUNT(*) AS c FROM pipeline_runs WHERE substr(completed_utc,1,10)=date('now')").iloc[0, 0])
    dq_failures = int(fetch_df("SELECT COUNT(*) AS c FROM data_quality WHERE status='FAIL' AND check_time_utc=(SELECT MAX(check_time_utc) FROM data_quality)").iloc[0, 0])
    watermark_df = fetch_df("SELECT watermark_utc FROM pipeline_state WHERE pipeline_name='bronze_to_silver'")
    watermark = watermark_df.iloc[0, 0] if not watermark_df.empty else "—"
    refreshed = datetime.now().strftime("Updated %I:%M:%S %p")

    latest_row = fetch_df("""
        SELECT metric_type, numeric_value, unit, ingestion_time_utc
        FROM silver_metrics ORDER BY ingestion_time_utc DESC LIMIT 1
    """)
    if latest_row.empty:
        latest_event_text = "Waiting for first event"
    else:
        row = latest_row.iloc[0]
        meta = METRIC_META.get(row.metric_type, {"label": row.metric_type.replace("_", " ").title(), "icon": "•"})
        value_text = "—" if pd.isna(row.numeric_value) else f"{safe_float(row.numeric_value):.1f} {row.unit or ''}".strip()
        latest_event_text = f"{meta['icon']} {meta['label']} · {value_text}"

    event_rate = int(fetch_df("SELECT COUNT(*) AS c FROM bronze_events WHERE datetime(replace(ingestion_time_utc,'Z','')) >= datetime('now','-1 minute')").iloc[0, 0])
    healthy = age_seconds is not None and age_seconds < 20 and dq_failures == 0
    status_text = "Pipeline healthy" if healthy else "Pipeline catching up"
    status_class = "health-status healthy" if healthy else "health-status warning"

    return values + delta_text + delta_classes + [
        steps_fig,
        sleep_fig,
        hr_fig,
        donut,
        freshness,
        f"{runs}",
        f"{dq_failures}",
        str(watermark).replace("T", " ")[:19] + " UTC" if watermark != "—" else "—",
        refreshed,
        latest_event_text,
        f"{event_rate}/min",
        status_text,
        status_class,
    ]


@app.callback(
    Output("explorer-chart", "figure"),
    Output("event-table", "data"),
    Output("event-table", "columns"),
    Output("explorer-latest", "children"),
    Output("explorer-min", "children"),
    Output("explorer-max", "children"),
    Output("explorer-records", "children"),
    Input("refresh", "n_intervals"),
    Input("metric-select", "value"),
    Input("window-select", "value"),
    Input("smoothing-select", "value"),
)
def refresh_explorer(_n: int, metric: str, window: str, smoothing: str):
    intervals = {"1h": "-1 hours", "6h": "-6 hours", "24h": "-24 hours"}
    where = "metric_type=?"
    params: list[object] = [metric]
    if window != "all":
        where += " AND datetime(replace(event_time_utc,'Z','')) >= datetime('now', ?)"
        params.append(intervals[window])
    df = fetch_df(f"SELECT record_id, metric_type, event_time_utc, numeric_value, unit, source_last_modified_utc, ingestion_time_utc FROM silver_metrics WHERE {where} ORDER BY event_time_utc", params)
    meta = METRIC_META.get(metric, {"label": metric.replace("_", " ").title(), "color": CYAN, "unit": ""})
    if df.empty:
        return empty_figure("No records in selected window"), [], [], "—", "—", "—", "0"

    values = df.numeric_value.astype(float)
    display_values = values.rolling(5, min_periods=1).mean() if smoothing == "smooth" else values
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=pd.to_datetime(df.event_time_utc), y=display_values, mode="lines+markers", line={"color": meta["color"], "width": 2.8, "shape": "spline"}, marker={"color": meta["color"], "size": 6, "line": {"color": "white", "width": .6}}, fill="tozeroy", fillcolor="rgba(49,168,255,.07)", name=meta["label"]))
    fig.update_layout(xaxis={"rangeslider": {"visible": window == "all", "thickness": .08}})
    style_figure(fig, legend=False, margin=dict(l=54, r=18, t=24, b=46), uirevision=f"explorer-{metric}-{window}-{smoothing}")

    table = df.sort_values("event_time_utc", ascending=False).head(100).copy()
    table["numeric_value"] = table["numeric_value"].round(2)
    unit = str(table.iloc[0].unit or meta.get("unit", ""))
    value_format = lambda value: f"{value:,.1f} {unit}".strip()
    return (
        fig,
        table.to_dict("records"),
        [{"name": column.replace("_", " ").title(), "id": column} for column in table.columns],
        value_format(values.iloc[-1]),
        value_format(values.min()),
        value_format(values.max()),
        f"{len(df):,}",
    )


@app.callback(
    Output("bronze-count", "children"),
    Output("silver-count", "children"),
    Output("latest-upserts", "children"),
    Output("latest-deletes", "children"),
    Output("pipeline-chart", "figure"),
    Output("duration-chart", "figure"),
    Output("upsert-delete-chart", "figure"),
    Output("dq-chart", "figure"),
    Input("refresh", "n_intervals"),
)
def refresh_operations(_n: int):
    bronze = int(fetch_df("SELECT COUNT(*) AS c FROM bronze_events").iloc[0, 0])
    silver = int(fetch_df("SELECT COUNT(*) AS c FROM silver_metrics").iloc[0, 0])
    runs = fetch_df("SELECT * FROM pipeline_runs ORDER BY completed_utc DESC LIMIT 40").sort_values("completed_utc")
    recent_runs = runs[runs.input_rows < 500] if not runs.empty else runs
    if len(recent_runs) >= 8:
        runs = recent_runs.tail(30)
    last = runs.iloc[-1] if not runs.empty else None
    upserts = int(last.upsert_rows) if last is not None else 0
    deletes = int(last.delete_rows) if last is not None else 0

    throughput = go.Figure()
    if not runs.empty:
        timestamps = pd.to_datetime(runs.completed_utc)
        throughput.add_trace(go.Scatter(x=timestamps, y=runs.input_rows, mode="lines+markers", name="Input", line={"color": BLUE, "width": 2.5, "shape": "spline"}, marker={"size": 5}, fill="tozeroy", fillcolor="rgba(49,168,255,.06)"))
        throughput.add_trace(go.Scatter(x=timestamps, y=runs.deduplicated_rows, mode="lines+markers", name="After dedupe", line={"color": CYAN, "width": 2.3, "shape": "spline"}, marker={"size": 5}))
    style_figure(throughput, uirevision="pipeline-throughput")

    duration = go.Figure()
    if not runs.empty:
        duration_colors = [GREEN if value < 50 else (YELLOW if value < 100 else ORANGE) for value in runs.duration_ms]
        duration.add_trace(go.Bar(x=pd.to_datetime(runs.completed_utc), y=runs.duration_ms, name="Duration ms", marker={"color": duration_colors, "line": {"color": "rgba(255,255,255,.18)", "width": .5}}))
    style_figure(duration, legend=False, uirevision="pipeline-duration")

    upsert_delete = go.Figure()
    if not runs.empty:
        timestamps = pd.to_datetime(runs.completed_utc)
        upsert_delete.add_trace(go.Bar(x=timestamps, y=runs.upsert_rows, name="Upserts", marker={"color": GREEN}))
        upsert_delete.add_trace(go.Bar(x=timestamps, y=runs.delete_rows, name="Deletes", marker={"color": RED}))
    upsert_delete.update_layout(barmode="stack")
    style_figure(upsert_delete, uirevision="upsert-delete")

    dq_df = fetch_df("""
        SELECT check_name, status, failed_rows FROM data_quality
        WHERE check_time_utc=(SELECT MAX(check_time_utc) FROM data_quality)
    """)
    if dq_df.empty:
        dq_fig = empty_figure("Quality checks have not run yet")
    else:
        display_values = [max(0.12, safe_float(value)) for value in dq_df.failed_rows]
        dq_fig = go.Figure(go.Bar(x=display_values, y=dq_df.check_name, orientation="h", marker={"color": [GREEN if status == "PASS" else RED for status in dq_df.status]}, text=dq_df.status, textposition="inside", insidetextanchor="middle", hovertemplate="%{y}<br>Failed rows: %{customdata}<extra></extra>", customdata=dq_df.failed_rows))
        style_figure(dq_fig, legend=False, margin=dict(l=138, r=18, t=18, b=28), uirevision="data-quality", hovermode=False)
        dq_fig.update_xaxes(visible=False)
    return f"{bronze:,}", f"{silver:,}", f"{upserts:,}", f"{deletes:,}", throughput, duration, upsert_delete, dq_fig


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8050")), debug=False)
