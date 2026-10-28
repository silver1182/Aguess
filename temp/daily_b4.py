"""B4 daily research scanner. Offline by default; no trade execution."""
import argparse
import json
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from html import escape
import pandas as pd
from audit_b4 import features

def route(state, depth, limit_count):
    if depth=='深熊':
        return True, '深熊：启用严格超跌企稳/A2反转规则（实验路由，轻仓）'
    if depth=='中熊':
        return True, '中熊：启用严格超跌企稳规则（实验路由，极小仓位）'
    if depth=='浅熊':
        return (limit_count>=51, '浅熊：涨停代理>=51，筛选B4+六因子>=5' if limit_count>=51 else '浅熊但涨停代理不足51家，观察')
    if state=='牛': return True, '牛市：启用趋势突破/A2强势规则'
    if state=='震荡': return True, '震荡：启用缩量超跌企稳与A2精选规则'
    return False, '市况未满足已验证路由，观察'

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',required=True,type=Path)
    p.add_argument('--as-of')
    p.add_argument('--output',type=Path,default=Path(__file__).parent)
    a=p.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(a.source)); import mkt_state_daily as msd
    raw=json.loads((a.source/'kline_day_long_v2.json').read_text(encoding='utf-8'))
    asof=a.as_of or max(b['date'] for bars in raw.values() for b in bars)
    data={c:[b for b in bars if b['date']<=asof] for c,bars in raw.items() if c.startswith(('60','00'))}
    data={c:bars for c,bars in data.items() if bars}
    market=msd.build_index(data); row=market[market.date==asof]
    if row.empty: raise ValueError('No market data for requested date')
    row=row.iloc[-1]; rows=[]
    for c,bars in data.items():
        if len(bars)>=40 and bars[-1]['date']==asof:
            rows.append(features(c,bars).iloc[-1])
    f=pd.DataFrame(rows)
    live_sent={}
    sent_path=a.source/'mkt_sentiment_latest.json'
    if sent_path.exists():
        try: live_sent=json.loads(sent_path.read_text(encoding='utf-8'))
        except Exception: live_sent={}
    live_count=live_sent.get('limit_up',{}).get('count') if isinstance(live_sent.get('limit_up'),dict) else None
    count=int(live_count if live_count is not None else (f.pct>=9.5).sum()); hot=count>=51
    f['a2']=(f.prev2_pct>=9.5)&(f.vol_ratio<=.6)&(f.close>f.ma5)&f.pct.between(-2,1)
    f['score']=(f.vol_ratio<=.6).astype(int)+(f.ret20<=-15).astype(int)+(f.close>f.ma5).astype(int)+(f.pct>0).astype(int)+int(hot)+f.a2.astype(int)
    enabled,note=route(row.state,row.depth,count)
    b4=(f.ret20<=-15)&(f.vol_ratio<=.6)&f.pct.between(-2,2)&(f.score>=5)
    breakout=(f.close>f.ma5)&(f.vol_ratio>=1.2)&f.pct.between(1,8)&(f.close<=20)
    a2=f.a2&(f.close<=20)
    if row.depth=='深熊': hit=f[(b4 | a2)].copy()
    elif row.depth=='中熊': hit=f[b4 & (f.score>=5)].copy()
    elif row.state=='牛': hit=f[(breakout|a2)].copy()
    elif row.state=='震荡': hit=f[(b4|a2)].copy()
    else: hit=f[b4].copy()
    hit=hit[hit.close.between(.01,20)]
    cols=['code','date','close','pct','ret20','vol_ratio','ma5','score']
    if enabled:
        hit=hit.sort_values(['score','ret20','vol_ratio'],ascending=[False,True,True]).head(5)
    candidates=hit[cols].to_dict('records')
    out={'as_of':asof,'generated_at':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
         'state':row.state,'depth':row.depth,'dev':float(row.dev),'coverage':len(data),
         'limit_proxy_count':count,'sentiment_score':live_sent.get('sentiment_score'),
         'sentiment_label':live_sent.get('sentiment_label'),'research_gate_passed':enabled,'gate_note':note,
         'watch_only':not enabled,'buy_candidates':candidates if enabled else [],
         'research_candidates':candidates if enabled else [],
         'max_positions':5,'per_position_budget':2000,
         'execution_status':'研究观察：收盘后信号无法成交于当日收盘，次日执行口径尚待验证',
         'proxy_scope':'缓存主板样本pct>=9.5的家数；不是全市场官方涨停池',
         'historical_reference':'旧研究剔月N84/60.7%，未含20元与组合约束，不作为本名单胜率'}
    target=a.output/f'b4_daily_{asof.replace("-","")}'
    target.with_suffix('.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    table=hit[cols].to_html(index=False,float_format=lambda v:f'{v:.3f}') if len(hit) and enabled else '<p>当前无通过路由的研究候选。</p>'
    html=f'''<!doctype html><html lang="zh"><meta charset="utf-8"><title>B4策略研究观察</title>
    <style>body{{font-family:Microsoft YaHei;margin:40px;background:#f4f6fa;color:#182033}}main{{max-width:1100px;margin:auto}}table{{border-collapse:collapse;background:white;width:100%}}td,th{{padding:12px;border-bottom:1px solid #ddd}}.notice{{padding:20px;background:#fff1db}}</style>
    <main><h1>B4 策略研究观察 · {escape(asof)}</h1><p>{escape(str(row.state))} / {escape(str(row.depth))} · 偏离MA20 {row.dev:.2f}% · 缓存覆盖 {len(data)}只 · 涨停代理 {count}家</p>
    <p class="notice">{escape(note)}。{escape(out['execution_status'])}</p>{table}<p>{escape(out['historical_reference'])}</p><p>{escape(out['proxy_scope'])}</p></main></html>'''
    target.with_suffix('.html').write_text(html,encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
