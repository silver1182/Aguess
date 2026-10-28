# -*- coding: utf-8 -*-
"""v9 统一口径最终网格: 周内截面rank(组内fillna中位数), TopN×止损×择时 + 分年度"""
import json, pandas as pd, numpy as np

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
with open(base + r'\temp\week_kline_long.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

all_bars = []
for code, bars in cache.items():
    for b in bars:
        b['code'] = code
        all_bars.append(b)
df = pd.DataFrame(all_bars)
df['date'] = pd.to_datetime(df['date'])
df = df[df['close'].notna()].sort_values(['code','date']).reset_index(drop=True)
g = df.groupby('code')
df['prev_close'] = g['close'].shift(1)
df['prev_vol'] = g['volume'].shift(1)
df['pct'] = df['close']/df['prev_close']-1
df['gap'] = df['open']/df['prev_close']-1
df['tail'] = df['close']/df['open']-1
df['vol_chg'] = df['volume']/df['prev_vol']
df['shrink_up'] = ((df['pct']>0)&(df['vol_chg']<1)).groupby(df['code']).transform(lambda x: x.rolling(10).mean())
df['amount_20d'] = g['volume'].transform(lambda x: x.rolling(20).mean())
df['max_up_20d'] = g['pct'].transform(lambda x: x.rolling(20).max())
df['expand_down'] = ((df['pct']<0)&(df['vol_chg']>1.2)).groupby(df['code']).transform(lambda x: x.rolling(10).mean())
df['tail_return'] = g['tail'].transform(lambda x: x.rolling(20).mean())
df['vol_chg_std'] = g['vol_chg'].transform(lambda x: x.rolling(20).std())
df['overnight_gap'] = g['gap'].transform(lambda x: x.rolling(20).mean())
df['yw'] = df['date'].dt.strftime('%Y-%U')
F = ['shrink_up','amount_20d','max_up_20d','expand_down','tail_return','vol_chg_std','overnight_gap']
sel_df = df[df[F].notna().all(axis=1)].copy()
week_list = df.groupby('yw')['date'].max().sort_values().index.tolist()
yw_to_next = {w: week_list[i+1] for i, w in enumerate(week_list[:-1])}
sel_df['buy_yw'] = sel_df['yw'].map(yw_to_next)
buy_info = df[['code','yw','open','close','low']].rename(columns={'open':'buy_open','close':'sell_close','low':'buy_low'})
sel = sel_df.merge(buy_info.rename(columns={'yw':'buy_yw'}), on=['code','buy_yw'], how='left')
sel = sel[['yw','buy_yw','code','buy_open','sell_close','buy_low']+F].dropna(subset=['buy_open']).copy()
for c in F:
    sel[c] = sel.groupby('yw')[c].transform(lambda s: (s.fillna(s.median()).rank(pct=True)-0.5)*2)
sel['score'] = (+sel['shrink_up']-sel['amount_20d']-sel['max_up_20d']+sel['expand_down']-sel['tail_return']-sel['vol_chg_std']-sel['overnight_gap'])/7
sel['ret0'] = sel['sell_close']/sel['buy_open']-1
sel['week_low_ret'] = sel['buy_low']/sel['buy_open']-1
breadth_d = dict(df.groupby('yw').apply(lambda x: (x['pct']>0).mean(), include_groups=False))
sel['breadth'] = sel['yw'].map(breadth_d)
COST = 0.0025

def run(topn, sl, timing='none', th=0.45):
    picks = sel.sort_values(['yw','score'], ascending=[True,False]).groupby('yw').head(topn).reset_index(drop=True)
    rets = []
    for r in picks.itertuples():
        ret = -sl if (sl>0 and r.week_low_ret < -sl) else r.ret0
        if timing=='lt' and r.breadth > th: ret = 0.0
        elif timing=='gt' and r.breadth < th: ret = 0.0
        rets.append(ret - COST)
    picks['ret'] = rets
    wk = picks.groupby('yw').agg(ret=('ret','mean')).reset_index()
    nav = (1+wk['ret']).cumprod()
    mdd = ((nav/nav.cummax())-1).min()
    cagr = nav.iloc[-1] ** (52/len(wk)) - 1 if len(wk)>0 else 0
    return nav, wk, mdd, cagr

rows = []
for topn in [3,4,5,6,8]:
    for sl in [0.0,0.03,0.05,0.08,0.10,0.12,0.15]:
        for timing, th in [('none',0.45),('lt',0.42),('lt',0.45),('lt',0.48),('gt',0.50),('gt',0.55)]:
            nav, wk, mdd, cagr = run(topn, sl, timing, th)
            rows.append({'topn':topn,'sl':sl,'timing':timing,'th':th,
                         'total':nav.iloc[-1]-1,'cagr':cagr,'mdd':mdd,
                         'wk_ret':wk['ret'].mean(),'win':(wk['ret']>0).mean()})
res = pd.DataFrame(rows).sort_values('cagr', ascending=False).reset_index(drop=True)
print('=== 统一口径 全窗口 Top12 ===')
print(res.head(12).to_string(index=False))

print('\n=== Top12 各配置 2023/2026 表现 ===')
for i in range(12):
    r = res.iloc[i]
    nav, wk, _, _ = run(int(r['topn']), r['sl'], r['timing'], r['th'])
    parts = []
    for y in ['2023','2026']:
        sub = wk[wk['yw'].str[:4]==y]
        if len(sub)>0:
            nv = (1+sub['ret']).cumprod().iloc[-1]-1
            parts.append(f'{y}:{nv*100:+.1f}%')
    print(f"Top{int(r['topn'])} 止损{r['sl']*100:.0f}% {r['timing']}{r['th']:.2f}: {' '.join(parts)}")

print('\n=== 基线 vs 最优 分年度 ===')
for tag, cfg in [('基线 Top5/8%', dict(topn=5, sl=0.08)), ('最优 Top5/12%', dict(topn=5, sl=0.12))]:
    nav, wk, mdd, cagr = run(cfg['topn'], cfg['sl'])
    parts = []
    for y, sub in wk.groupby(wk['yw'].str[:4]):
        nv = (1+sub['ret']).cumprod().iloc[-1]-1
        parts.append(f'{y}:{nv*100:+.1f}%')
    print(f'{tag}: {" ".join(parts)} | 全期{(nav.iloc[-1]-1)*100:+.1f}% 年化{cagr*100:+.1f}% 回撤{mdd*100:.1f}%')

res.to_csv(base + r'\output\v9优化网格_统一口径_20261027.csv', index=False, encoding='utf-8-sig')
print('\n[产出]', base + r'\output\v9优化网格_统一口径_20261027.csv')
