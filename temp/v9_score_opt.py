# -*- coding: utf-8 -*-
"""
评分强度优化: avg_score 周级过滤 + 高分池截断选股 + 动态TopN
"""
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
COST = 0.0025

def run(topn=5, sl=0.12, min_score=None, min_avg=None, dynamic=False):
    pool = sel if min_score is None else sel[sel['score'] >= min_score]
    picks = pool.sort_values(['yw','score'], ascending=[True,False]).groupby('yw').head(topn).reset_index(drop=True)
    if dynamic:
        # 按周 avg_score 分位决定持仓数: 高分位5只, 中分位3只, 低分位0只(空仓)
        asc = picks.groupby('yw')['score'].mean().reset_index().sort_values('score')
        q33, q66 = asc['score'].quantile([0.33, 0.66])
        dyn = asc.copy()
        dyn['topn'] = np.where(asc['score'] > q66, 5, np.where(asc['score'] > q33, 3, 0))
        dyn_map = dict(zip(dyn['yw'], dyn['topn']))
        keep = []
        for yw, sub in picks.groupby('yw'):
            n = dyn_map.get(yw, 0)
            keep.append(sub.head(n) if n > 0 else sub.iloc[0:0])
        picks = pd.concat(keep) if keep else picks.iloc[0:0]
    if min_avg is not None:
        avg = picks.groupby('yw')['score'].mean()
        ok_yw = avg[avg >= min_avg].index
        picks = picks[picks['yw'].isin(ok_yw)]
    if len(picks) == 0:
        return 0.0, 0.0, 0.0, pd.DataFrame()
    rets = []
    for r in picks.itertuples():
        ret = -sl if (sl>0 and r.week_low_ret < -sl) else r.ret0
        rets.append(ret - COST)
    picks['ret'] = rets
    wk = picks.groupby('yw').agg(ret=('ret','mean'), n=('code','nunique')).reset_index()
    nav = (1+wk['ret']).cumprod()
    mdd = ((nav/nav.cummax())-1).min()
    return nav.iloc[-1]-1, mdd, wk['ret'].mean(), wk

print('=== 基线: Top5/止损12% ===')
total, mdd, wm, wk = run()
print(f'累计{total:+.1%} 回撤{mdd:.1%} 周均{wm:+.3%} 持仓周{len(wk)}')

print('\n=== A. 高分池截断 (只从 score>=阈值 的股票选Top5) ===')
for thr in [0.55, 0.60, 0.65, 0.70]:
    total, mdd, wm, wk = run(min_score=thr)
    print(f'min_score>={thr:.2f}: 累计{total:+.1%} 回撤{mdd:.1%} 周均{wm:+.3%} 持仓周{len(wk)}')

print('\n=== B. avg_score 周级过滤 (avg>=阈值才持仓, 否则空仓) ===')
for thr in [0.62, 0.64, 0.66, 0.68]:
    total, mdd, wm, wk = run(min_avg=thr)
    if len(wk)>0:
        yparts = []
        for y, sub in wk.groupby(wk['yw'].str[:4]):
            nv = (1+sub['ret']).cumprod().iloc[-1]-1
            yparts.append(f'{y}:{nv*100:+.1f}%')
        print(f'avg>={thr:.2f}: 累计{total:+.1%} 回撤{mdd:.1%} 周均{wm:+.3%} 持仓{len(wk)}周 | {" ".join(yparts)}')

print('\n=== C. 动态持仓数 (按avg_score分位: 高5/中3/低0) ===')
total, mdd, wm, wk = run(dynamic=True)
yparts = []
for y, sub in wk.groupby(wk['yw'].str[:4]):
    nv = (1+sub['ret']).cumprod().iloc[-1]-1
    yparts.append(f'{y}:{nv*100:+.1f}%')
print(f'动态TopN: 累计{total:+.1%} 回撤{mdd:.1%} 周均{wm:+.3%} 持仓周{len(wk)} | {" ".join(yparts)}')

print('\n=== D. 高分池截断 + avg过滤 组合 ===')
for ms, ma in [(0.60, 0.66), (0.65, 0.66), (0.60, 0.68)]:
    total, mdd, wm, wk = run(min_score=ms, min_avg=ma)
    if len(wk)>0:
        yparts = []
        for y, sub in wk.groupby(wk['yw'].str[:4]):
            nv = (1+sub['ret']).cumprod().iloc[-1]-1
            yparts.append(f'{y}:{nv*100:+.1f}%')
        print(f'score>={ms:.2f}&avg>={ma:.2f}: 累计{total:+.1%} 回撤{mdd:.1%} 周均{wm:+.3%} 持仓{len(wk)}周 | {" ".join(yparts)}')
