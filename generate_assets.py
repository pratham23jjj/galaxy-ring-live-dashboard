from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import html as html_lib
import json
import textwrap

import pandas as pd
import plotly.graph_objects as go
from plotly.offline import get_plotlyjs
from playwright.sync_api import sync_playwright
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer, TextLexer

from db import fetch_df

ROOT = Path(__file__).resolve().parent
SCREEN = ROOT / 'screenshots'
CODE = ROOT / 'code_images'
PBI_DATA = ROOT / 'powerbi' / 'data'
for p in (SCREEN, CODE, PBI_DATA):
    p.mkdir(parents=True, exist_ok=True)

BG='#06101f'; PANEL='#0a1a30'; PANEL2='#0e213c'; TEXT='#eaf4ff'; MUTED='#86a1c3'
BLUE='#28a8ff'; CYAN='#20e3ff'; GREEN='#3ce18c'; RED='#ff627d'; PURPLE='#7c6cff'; GRID='rgba(116,157,214,.14)'


def style(fig, height=265, legend=True, margin=None):
    fig.update_layout(
        height=height, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font={'family':'Inter, Segoe UI, Arial','color':TEXT,'size':11},
        margin=margin or dict(l=45,r=20,t=30,b=38),
        legend={'orientation':'h','y':1.14,'x':0,'font':{'size':10}} if legend else {},
        hovermode='x unified',
    )
    fig.update_xaxes(showgrid=False, zeroline=False, color='#86a1c3')
    fig.update_yaxes(gridcolor=GRID, zeroline=False, color='#86a1c3')
    return fig


def fig_html(fig):
    return fig.to_html(full_html=False, include_plotlyjs=False, config={'displayModeBar':False,'responsive':True})


BASE_CSS = r'''
*{box-sizing:border-box}html,body{margin:0;width:100%;min-height:100%;background:radial-gradient(circle at 76% 0,#0b315e 0,#071427 38%,#040b15 100%);color:#eaf4ff;font-family:Inter,"Segoe UI",Arial,sans-serif}body{overflow:hidden}.shell{display:flex;width:1920px;height:1080px}.sidebar{width:248px;height:100%;padding:27px 18px;background:linear-gradient(180deg,rgba(8,23,43,.99),rgba(3,11,21,.99));border-right:1px solid rgba(67,125,187,.28);position:relative}.brand{display:flex;gap:12px;align-items:center}.mark{font-size:38px;color:#20e3ff;text-shadow:0 0 24px rgba(32,227,255,.8)}.brand-title{font-weight:800;letter-spacing:1.4px}.brand-sub{font-size:10px;color:#28a8ff;letter-spacing:2px}.live{margin:24px 0 25px;padding:9px 11px;border-radius:999px;border:1px solid rgba(60,225,140,.3);background:rgba(20,103,73,.18);font-size:10px;letter-spacing:1.1px;color:#b6f2d5}.dot{display:inline-block;width:8px;height:8px;margin-right:8px;border-radius:50%;background:#3ce18c;box-shadow:0 0 12px #3ce18c}.nav{display:flex;flex-direction:column;gap:7px}.nav div{padding:13px 14px;color:#91aac8;border-radius:10px;font-size:14px}.nav .active{color:white;background:linear-gradient(90deg,rgba(40,168,255,.22),rgba(40,168,255,.04));border-left:3px solid #20e3ff}.path{margin-top:30px;padding:14px;background:rgba(13,36,64,.57);border:1px solid rgba(63,128,191,.2);border-radius:14px}.path-title{font-size:9px;letter-spacing:1.5px;color:#6f8baa;margin-bottom:9px}.node{padding:7px 6px;text-align:center;font-size:11px;color:#bcd1e8;background:rgba(255,255,255,.025);border-radius:7px}.arrow{text-align:center;color:#4c79a4;font-size:10px}.foot{position:absolute;bottom:24px;font-size:10px;color:#7290b0;line-height:1.55}.main{width:1672px;padding:0 27px 24px}.top{height:98px;display:flex;align-items:center;justify-content:space-between}.top h1{font-size:25px;margin:0}.top p{margin:7px 0 0;color:#86a1c3;font-size:12px}.status{font-size:11px;color:#bfead5}.updated{margin-left:18px;color:#7893b2}.kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:12px}.kpi{height:119px;padding:15px 16px;background:linear-gradient(145deg,rgba(16,42,75,.97),rgba(8,24,44,.96));border:1px solid rgba(77,142,204,.24);border-radius:15px;position:relative;overflow:hidden}.kpi:after{content:"";position:absolute;right:-27px;top:-34px;width:82px;height:82px;border-radius:50%;background:rgba(40,168,255,.12);filter:blur(8px)}.kpi-title{font-size:11px;color:#9fb8d4}.kpi-value{font-size:24px;font-weight:760;margin-top:14px}.kpi-delta{font-size:9px;color:#3ce18c;margin-top:8px}.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:13px;margin-top:13px}.panel{background:linear-gradient(150deg,rgba(11,30,54,.98),rgba(5,18,34,.97));border:1px solid rgba(75,136,194,.24);border-radius:15px;padding:12px 13px;overflow:hidden}.p7{grid-column:span 7}.p5{grid-column:span 5}.panel-title{font-size:12px;font-weight:650;color:#d9ebff;padding:2px 4px 4px}.plot{height:260px}.ops-strip{display:grid;grid-template-columns:1fr 1fr 1fr 1.7fr;gap:12px;margin-top:13px}.mini{height:90px;padding:14px 16px;background:linear-gradient(145deg,rgba(10,31,56,.95),rgba(7,22,39,.96));border:1px solid rgba(75,136,194,.22);border-radius:13px}.mini-label{font-size:10px;color:#9cb5d0}.mini-value{font-size:20px;font-weight:760;margin:8px 0 3px}.muted{font-size:9px;color:#86a1c3}.green{color:#3ce18c}.cyan{color:#20e3ff}.cards4{display:grid;grid-template-columns:repeat(4,1fr);gap:13px}.opcard{height:105px;padding:17px;background:linear-gradient(145deg,rgba(15,40,72,.97),rgba(7,21,40,.97));border:1px solid rgba(65,133,199,.25);border-radius:15px}.oplabel{font-size:10px;color:#9db6d1}.opvalue{font-size:29px;font-weight:800;margin:8px 0}.filter{display:flex;gap:12px;margin-bottom:13px}.filterbox{padding:12px 15px;width:230px;border-radius:12px;background:#0a1a30;border:1px solid #1d3a60}.filterlabel{font-size:9px;color:#86a1c3}.filtervalue{margin-top:6px;font-size:13px;color:#eaf4ff}.table{width:100%;border-collapse:collapse;font-size:10px}.table th{padding:10px;text-align:left;background:#112746;color:#bfe6ff}.table td{padding:10px;border-bottom:1px solid rgba(59,104,151,.14);color:#dceaff}.table tr:nth-child(even){background:#0d1e35}.codebox{font-family:Consolas,monospace;font-size:12px;line-height:1.65;color:#79d7ff;background:#05101d;border:1px solid rgba(46,137,209,.25);border-radius:10px;padding:14px 18px}.badge{display:inline-block;padding:3px 7px;border-radius:999px;background:rgba(40,168,255,.12);color:#70d5ff;border:1px solid rgba(40,168,255,.25)}
'''


def sidebar(active):
    items=['Overview','Metric Explorer','Pipeline Operations']
    return f'''<aside class="sidebar"><div class="brand"><div class="mark">◉</div><div><div class="brand-title">GALAXY RING</div><div class="brand-sub">LIVE ANALYTICS</div></div></div><div class="live"><span class="dot"></span>SIMULATED LIVE FEED</div><div class="nav">{''.join(f'<div class="{"active" if i==active else ""}">{i}</div>' for i in items)}</div><div class="path"><div class="path-title">DATA PATH</div><div class="node">Samsung Health</div><div class="arrow">↓</div><div class="node">Fabric Eventstream</div><div class="arrow">↓</div><div class="node">Bronze → Silver → Gold</div><div class="arrow">↓</div><div class="node cyan">Power BI / Direct Lake</div></div><div class="foot">Synthetic wellness analytics demo<br>Not medical advice</div></aside>'''


def document(body, active, title, subtitle):
    stamp=datetime.now().strftime('%I:%M:%S %p')
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>{BASE_CSS}</style><script>{get_plotlyjs()}</script></head><body><div class="shell">{sidebar(active)}<main class="main"><header class="top"><div><h1>{title}</h1><p>{subtitle}</p></div><div class="status"><span class="dot"></span>Pipeline healthy <span class="updated">Updated {stamp}</span></div></header>{body}</main></div></body></html>'''


def build_overview():
    daily=fetch_df('SELECT * FROM gold_daily_health ORDER BY health_date')
    latest=daily.iloc[-1]
    def last_value(column):
        valid=daily.dropna(subset=[column])
        return float(valid.iloc[-1][column]) if not valid.empty else 0.0
    sleep_daily=daily.dropna(subset=['sleep_minutes'])
    sleep_row=sleep_daily.iloc[-1] if not sleep_daily.empty else latest
    vals=[('Steps',f"{int(last_value('steps')):,}",'↟'),('Sleep Hours',f"{last_value('sleep_minutes')/60:.2f}",'☾'),('Avg Heart Rate',f"{last_value('avg_heart_rate'):.0f} bpm",'♡'),('SpO₂',f"{last_value('avg_blood_oxygen'):.1f}%",'◉'),('Skin Temp',f"{last_value('avg_skin_temperature'):.1f} °C",'♨'),('Energy Score',f"{last_value('energy_score'):.0f}",'ϟ')]
    kpis=''.join(f'<div class="kpi"><div class="kpi-title">{icon} &nbsp; {t}</div><div class="kpi-value">{v}</div><div class="kpi-delta">Live Silver/Gold value</div></div>' for t,v,icon in vals)
    x=pd.to_datetime(daily.health_date)
    f1=go.Figure(); f1.add_scatter(x=x,y=daily.steps,mode='lines+markers',name='Steps',line={'color':BLUE,'width':3}); f1.add_scatter(x=x,y=daily.steps.rolling(7,min_periods=1).mean(),mode='lines',name='7-day average',line={'color':CYAN,'dash':'dot','width':2}); style(f1,245)
    f2=go.Figure(go.Bar(x=pd.to_datetime(sleep_daily.health_date),y=sleep_daily.sleep_minutes/60,marker={'color':BLUE},text=(sleep_daily.sleep_minutes/60).round(1),textposition='outside')); f2.add_hline(y=7,line_dash='dot',line_color=CYAN); style(f2,245,False)
    hr=fetch_df("SELECT event_time_utc,numeric_value FROM silver_metrics WHERE metric_type='heart_rate' ORDER BY event_time_utc DESC LIMIT 160").sort_values('event_time_utc')
    f3=go.Figure(); f3.add_scatter(x=pd.to_datetime(hr.event_time_utc),y=hr.numeric_value,mode='lines',fill='tozeroy',fillcolor='rgba(40,168,255,.08)',line={'color':CYAN,'width':2}); style(f3,245,False)
    stage=[float(sleep_row.get(c) or 0) for c in ['deep_sleep_minutes','light_sleep_minutes','rem_sleep_minutes','awake_sleep_minutes']]
    f4=go.Figure(go.Pie(labels=['Deep','Light','REM','Awake'],values=stage,hole=.67,marker={'colors':['#1468ff',BLUE,PURPLE,'#9db0d0']},textinfo='label+percent')); f4.add_annotation(text=f'<b>{sum(stage)/60:.1f}h</b><br><span style="font-size:10px">Total sleep</span>',x=.5,y=.5,showarrow=False,font={'color':'white','size':18}); style(f4,245,False,dict(l=5,r=5,t=5,b=5))
    latest_event=fetch_df('SELECT MAX(ingestion_time_utc) t FROM silver_metrics').iloc[0,0]
    seconds=max(0,int((datetime.now(timezone.utc)-pd.to_datetime(latest_event,utc=True).to_pydatetime()).total_seconds()))
    runs=int(fetch_df("SELECT COUNT(*) c FROM pipeline_runs WHERE substr(completed_utc,1,10)=date('now')").iloc[0,0])
    dq=int(fetch_df("SELECT COUNT(*) c FROM data_quality WHERE status='FAIL' AND check_time_utc=(SELECT MAX(check_time_utc) FROM data_quality)").iloc[0,0])
    wm=str(fetch_df("SELECT watermark_utc FROM pipeline_state").iloc[0,0]).replace('T',' ')[:19]
    body=f'''<section class="kpis">{kpis}</section><section class="grid"><div class="panel p7"><div class="panel-title">Daily Steps Trend</div>{fig_html(f1)}</div><div class="panel p5"><div class="panel-title">Sleep Duration</div>{fig_html(f2)}</div><div class="panel p7"><div class="panel-title">Heart Rate — Recent Events</div>{fig_html(f3)}</div><div class="panel p5"><div class="panel-title">Sleep Stages</div>{fig_html(f4)}</div></section><section class="ops-strip"><div class="mini"><div class="mini-label">Data Freshness</div><div class="mini-value green">{seconds} sec ago</div><div class="muted">Latest Silver event</div></div><div class="mini"><div class="mini-label">Pipeline Runs</div><div class="mini-value">{runs}</div><div class="muted">Successful today</div></div><div class="mini"><div class="mini-label">Failed Quality Checks</div><div class="mini-value green">{dq}</div><div class="muted">Latest validation</div></div><div class="mini"><div class="mini-label">Current Watermark</div><div class="mini-value cyan" style="font-size:14px">{wm} UTC</div><div class="muted">30-minute safety overlap</div></div></section>'''
    return document(body,'Overview','Health Overview','Near-real-time Galaxy Ring telemetry and daily trends')


def build_explorer():
    df=fetch_df("SELECT record_id,metric_type,event_time_utc,numeric_value,unit,source_last_modified_utc,ingestion_time_utc FROM silver_metrics WHERE metric_type='heart_rate' ORDER BY event_time_utc DESC LIMIT 120")
    chart=df.sort_values('event_time_utc')
    fig=go.Figure(); fig.add_scatter(x=pd.to_datetime(chart.event_time_utc),y=chart.numeric_value,mode='lines+markers',line={'color':CYAN,'width':2},marker={'color':BLUE,'size':5}); style(fig,390,False)
    rows=''.join('<tr>'+''.join(f'<td>{html_lib.escape(str(v))}</td>' for v in row)+'</tr>' for row in df.head(11).itertuples(index=False,name=None))
    headers=''.join(f'<th>{c.replace("_"," ").title()}</th>' for c in df.columns)
    body=f'''<div class="filter"><div class="filterbox"><div class="filterlabel">METRIC</div><div class="filtervalue">Heart Rate</div></div><div class="filterbox"><div class="filterlabel">WINDOW</div><div class="filtervalue">All recent events</div></div><div class="filterbox"><div class="filterlabel">BUSINESS KEY</div><div class="filtervalue">record_id + metric_type</div></div></div><div class="panel"><div class="panel-title">Metric Timeline</div>{fig_html(fig)}</div><div class="panel" style="margin-top:13px"><div class="panel-title">Latest Event Records</div><table class="table"><thead><tr>{headers}</tr></thead><tbody>{rows}</tbody></table></div>'''
    return document(body,'Metric Explorer','Metric Explorer','Inspect event-level measurements and recent source changes')


def build_operations():
    bronze=int(fetch_df('SELECT COUNT(*) c FROM bronze_events').iloc[0,0]); silver=int(fetch_df('SELECT COUNT(*) c FROM silver_metrics').iloc[0,0])
    runs=fetch_df('SELECT * FROM pipeline_runs ORDER BY completed_utc DESC LIMIT 40').sort_values('completed_utc')
    recent_runs=runs[runs.input_rows < 500]
    if len(recent_runs) >= 8:
        runs=recent_runs.tail(30)
    last=runs.iloc[-1]
    cards=[('Bronze Events',f'{bronze:,}','Raw immutable events'),('Silver Records',f'{silver:,}','Current trusted state'),('Latest Upserts',f'{int(last.upsert_rows):,}','Last pipeline run'),('Latest Deletes',f'{int(last.delete_rows):,}','Source corrections')]
    cardhtml=''.join(f'<div class="opcard"><div class="oplabel">{a}</div><div class="opvalue">{b}</div><div class="muted">{c}</div></div>' for a,b,c in cards)
    x=pd.to_datetime(runs.completed_utc)
    f1=go.Figure(); f1.add_scatter(x=x,y=runs.input_rows,mode='lines+markers',name='Input',line={'color':BLUE}); f1.add_scatter(x=x,y=runs.deduplicated_rows,mode='lines+markers',name='After dedupe',line={'color':CYAN}); style(f1,270)
    f2=go.Figure(go.Bar(x=x,y=runs.duration_ms,marker={'color':PURPLE})); style(f2,270,False)
    f3=go.Figure(); f3.add_bar(x=x,y=runs.upsert_rows,name='Upserts',marker={'color':GREEN}); f3.add_bar(x=x,y=runs.delete_rows,name='Deletes',marker={'color':RED}); f3.update_layout(barmode='stack'); style(f3,270)
    dq=fetch_df("SELECT check_name,status,failed_rows FROM data_quality WHERE check_time_utc=(SELECT MAX(check_time_utc) FROM data_quality)")
    f4=go.Figure(go.Bar(x=dq.failed_rows,y=dq.check_name,orientation='h',marker={'color':[GREEN if s=='PASS' else RED for s in dq.status]},text=dq.status,textposition='outside')); style(f4,270,False,dict(l=155,r=35,t=20,b=35))
    code='''watermark − 30 min overlap → deduplicate(record_id, metric_type)\n→ MERGE newest source modification into Silver\n→ UPSERT current state | propagate DELETE\n→ aggregate Gold → quality checks → advance watermark'''
    body=f'''<div class="cards4">{cardhtml}</div><div class="grid"><div class="panel p7"><div class="panel-title">Pipeline Throughput</div>{fig_html(f1)}</div><div class="panel p5"><div class="panel-title">Run Duration (ms)</div>{fig_html(f2)}</div><div class="panel p7"><div class="panel-title">Upserts vs Deletes</div>{fig_html(f3)}</div><div class="panel p5"><div class="panel-title">Data Quality</div>{fig_html(f4)}</div></div><div class="panel" style="margin-top:13px"><div class="panel-title">Incremental Processing Logic</div><div class="codebox">{code}</div></div>'''
    return document(body,'Pipeline Operations','Pipeline Operations','Watermarks, upserts, deletes, quality checks, and throughput')


def capture_html(page, html, output):
    page.set_content(html, wait_until='load', timeout=120000)
    page.wait_for_selector('.js-plotly-plot', timeout=120000)
    page.wait_for_timeout(2000)
    page.screenshot(path=str(output), full_page=False)


def code_card(source_path: Path, output: Path, title: str, start: int, end: int, language='python'):
    lines=source_path.read_text(encoding='utf-8').splitlines()
    selected='\n'.join(lines[start-1:end])
    lexer=PythonLexer() if language=='python' else TextLexer()
    formatter=HtmlFormatter(style='monokai', linenos='table', noclasses=True, nowrap=False)
    formatted=highlight(selected,lexer,formatter)
    css='''html,body{margin:0;background:radial-gradient(circle at 80% 0,#10345d,#050d18 60%);color:white;font-family:Inter,Segoe UI,Arial;height:100%}.frame{width:1600px;height:900px;padding:55px 65px}.eyebrow{color:#20e3ff;font-size:18px;letter-spacing:2px}.title{font-size:44px;font-weight:800;margin:10px 0 28px}.code{background:#071729;border:1px solid #28547d;border-radius:18px;padding:25px;box-shadow:0 20px 55px rgba(0,0,0,.35);font-size:18px;line-height:1.55;max-height:700px;overflow:hidden}.footer{margin-top:18px;color:#87a4c4;font-size:15px}.footer b{color:#28a8ff}pre{margin:0!important;white-space:pre-wrap}table{border-spacing:0}.linenos{padding-right:20px!important;color:#52708f!important}'''
    content=f'<html><head><style>{css}</style></head><body><div class="frame"><div class="eyebrow">GALAXY RING DATA ENGINEERING</div><div class="title">{html_lib.escape(title)}</div><div class="code">{formatted}</div><div class="footer"><b>Actual project source:</b> {source_path.name} · lines {start}–{end}</div></div></body></html>'
    return content


def export_powerbi_data():
    tables={
        'gold_daily_health':'SELECT * FROM gold_daily_health ORDER BY health_date',
        'silver_metrics':'SELECT * FROM silver_metrics ORDER BY event_time_utc',
        'pipeline_runs':'SELECT * FROM pipeline_runs ORDER BY completed_utc',
        'data_quality':'SELECT * FROM data_quality ORDER BY check_time_utc',
        'bronze_events_sample':'SELECT * FROM bronze_events ORDER BY ingestion_time_utc DESC LIMIT 1000',
    }
    for name,q in tables.items():
        fetch_df(q).to_csv(PBI_DATA/f'{name}.csv',index=False)
    dates=pd.date_range(fetch_df('SELECT MIN(health_date) m FROM gold_daily_health').iloc[0,0],fetch_df('SELECT MAX(health_date) m FROM gold_daily_health').iloc[0,0])
    dim=pd.DataFrame({'Date':dates})
    dim['Year']=dim.Date.dt.year; dim['Month']=dim.Date.dt.month; dim['Month Name']=dim.Date.dt.strftime('%b'); dim['Day']=dim.Date.dt.day; dim['Weekday']=dim.Date.dt.strftime('%a')
    dim.to_csv(PBI_DATA/'date_dimension.csv',index=False)


def main():
    export_powerbi_data()
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1920,'height':1080},device_scale_factor=1)
        capture_html(page,build_overview(),SCREEN/'overview.png')
        capture_html(page,build_explorer(),SCREEN/'metric_explorer.png')
        capture_html(page,build_operations(),SCREEN/'pipeline_operations.png')
        code_specs=[
            (ROOT/'simulator.py',CODE/'01_live_event_simulator.png','Live Event Production + Corrections',28,78,'python'),
            (ROOT/'db.py',CODE/'02_watermark_and_dedupe.png','Watermark, Overlap, and Deduplication',222,266,'python'),
            (ROOT/'db.py',CODE/'03_upsert_and_delete.png','Idempotent Upserts + Delete Propagation',252,314,'python'),
            (ROOT/'db.py',CODE/'04_gold_and_quality.png','Gold Aggregation + Data Quality',325,386,'python'),
            (ROOT/'powerbi'/'measures.dax',CODE/'05_powerbi_dax.png','Power BI Measures',1,30,'text'),
            (ROOT/'fabric'/'notebooks'/'01_bronze_to_silver_incremental.py',CODE/'06_fabric_watermark_dedupe.png','Fabric PySpark: Watermark + Deduplication',17,50,'python'),
            (ROOT/'fabric'/'notebooks'/'01_bronze_to_silver_incremental.py',CODE/'07_fabric_delta_merge.png','Fabric Delta Lake MERGE',52,105,'python'),
        ]
        for src,out,title,start,end,lang in code_specs:
            page.set_content(code_card(src,out,title,start,end,lang),wait_until='load')
            page.wait_for_timeout(500)
            page.screenshot(path=str(out),full_page=False)
        browser.close()
    print('Generated screenshots, code images, and Power BI data.')

if __name__=='__main__':
    main()
