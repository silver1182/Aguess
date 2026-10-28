# -*- coding: utf-8 -*-
"""v9 优化稳健性验证: 关键候选分年度 + 择时变体 + 2023亏损归因"""
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
    sel[c] = (sel.groupby('yw')[c].transform(lambda x: x.rank(pct=True)) - 0.5) * 2
sel['score'] = (+sel['shrink_up']-sel['amount_20d']-sel['max_up_20d']+sel['expand_down']-sel['tail_return']-sel['vol_chg_std']-sel['overnight_gap'])/7
sel['ret0'] = sel['sell_close']/sel['buy_open']-1
sel['week_low_ret'] = sel['buy_low']/sel['buy_open']-1
breadth_d = dict(df.groupby('yw').apply(lambda x: (x['pct']>0).mean(), include_groups=False))
sel['breadth'] = sel['yw'].map(breadth_d)
COST = 0.0025

def run(topn, sl, timing='none', th=0.45, yfilter=None):
    picks = sel.sort_values(['yw','score'], ascending=[True,False]).groupby('yw').head(topn).reset_index(drop=True)
    if yfilter:
        picks = picks[picks['yw'].str[:4] == yfilter]
    rets = []
    for r in picks.itertuples():
        ret = -sl if (sl>0 and r.week_low_ret < -sl) else r.ret0
        if timing=='lt' and r.breadth > th: ret = 0.0
        elif timing=='gt' and r.breadth < th: ret = 0.0
        rets.append(ret - COST)
    picks['ret'] = rets
    wk = picks.groupby('yw').agg(ret=('ret','mean')).reset_index()
    nav = (1+wk['ret']).cumprod()
    return nav, wk

print('=== Top5 关键止损档 分年度 ===')
for sl in [0.08, 0.10, 0.12, 0.15]:
    nav, wk = run(5, sl)
    parts = []
    for y, sub in wk.groupby(wk['yw'].str[:4]):
        nv = (1+sub['ret']).cumprod().iloc[-1]-1
        parts.append(f'{y}:{nv*100:+.1f}%')
    mdd = ((nav/nav.cummax())-1).min()
    print(f'止损{sl*100:.0f}%: {" ".join(parts)} | 全期{(nav.iloc[-1]-1)*100:+.1f}% 回撤{mdd*100:.1f}%')

print('\n=== 择时变体(Top5/止损12%) 全期与2023 ===')
for timing, th in [('none',0.45),('lt',0.42),('lt',0.45),('lt',0.48),('gt',0.50),('gt',0.55)]:
    nav, wk = run(5, 0.12, timing, th)
    wk23 = wk[wk['yw'].str[:4]=='2023']
    nav23 = (1+wk23['ret']).cumprod()
    mdd = ((nav/nav.cummax())-1).min()
    print(f'{timing}{th:.2f}: 全期{(nav.iloc[-1]-1)*100:+7.1f}% 回撤{mdd*100:6.1f}% | 2023 {(nav23.iloc[-1]-1)*100:+6.1f}%')

print('\n=== 2023 亏损归因(Top5/止损12%) ===')
nav, wk = run(5, 0.12)
wk23 = wk[wk['yw'].str[:4]=='2023'].copy()
wk23['date'] = wk23['yw'].astype(str).str[4:].astype(int)
wk23 = wk23.sort_values('date')
print('2023 各周收益(前10差):')
print(wk23.sort_values('ret').head(10).to_string(index=False))
print(f'2023 亏损周数: {(wk23["ret"]<0).sum()}/{len(wk23)}  最大单周亏: {wk23["ret"].min()*100:.1f}%')
neg = wk23[wk23['ret']<0]['ret']
print(f'亏损周均值: {neg.mean()*100:.2f}%  (总周均: {wk23["ret"].mean()*100:.2f}%)')

# 2023 极端弱市: 试持有期减半(周一买周三卖近似)不可行; 改试 Top3 在2023
print('\n=== 2023 弱市专项: TopN对比 ===')
for topn in [3,5,8,10]:
    nav, wk = run(topn, 0.12)
    wk23 = wk[wk['yw'].str[:4]=='2023']
    nav23 = (1+wk23['ret']).cumprod()
    print(f'Top{topn}: 2023 {(nav23.iloc[-1]-1)*100:+6.1f}% 全期{(nav.iloc[-1]-1)*100:+6.1f}%')
