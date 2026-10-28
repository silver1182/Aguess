# -*- coding: utf-8 -*-
"""
v9 周频: 弱市窗口(2026-03~10) 专项验证 - 向量化快速版
口径与 v9_final 一致: 周五截面选股 → 下周一开盘买 → 下周五收盘卖(持有整周)
因子方向: +shrink_up -amount_20d -max_up_20d +expand_down -tail_return -vol_chg_std -overnight_gap
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
df = df[df['close'].notna()]
df = df.sort_values(['code', 'date']).reset_index(drop=True)

g = df.groupby('code')
df['prev_close'] = g['close'].shift(1)
df['prev_vol'] = g['volume'].shift(1)
df['pct'] = df['close'] / df['prev_close'] - 1
df['gap'] = df['open'] / df['prev_close'] - 1
df['tail'] = df['close'] / df['open'] - 1
df['vol_chg'] = df['volume'] / df['prev_vol']

cond_shrink = (df['pct']>0) & (df['vol_chg']<1)
df['shrink_up'] = cond_shrink.groupby(df['code']).transform(lambda x: x.rolling(10).mean())
df['amount_20d'] = g['volume'].transform(lambda x: x.rolling(20).mean())
df['max_up_20d'] = g['pct'].transform(lambda x: x.rolling(20).max())
cond_expand = (df['pct']<0) & (df['vol_chg']>1.2)
df['expand_down'] = cond_expand.groupby(df['code']).transform(lambda x: x.rolling(10).mean())
df['tail_return'] = g['tail'].transform(lambda x: x.rolling(20).mean())
df['vol_chg_std'] = g['vol_chg'].transform(lambda x: x.rolling(20).std())
df['overnight_gap'] = g['gap'].transform(lambda x: x.rolling(20).mean())

df['yw'] = df['date'].dt.strftime('%Y-%U')
factor_cols = ['shrink_up','amount_20d','max_up_20d','expand_down','tail_return','vol_chg_std','overnight_gap']
sel_df = df[df[factor_cols].notna().all(axis=1)].copy()

def rank_std(s):
    s = s.fillna(s.median())
    r = s.rank(pct=True)
    return (r - 0.5) * 2

week_list = df.groupby('yw')['date'].max().sort_values().index.tolist()
yw_to_next = {w: week_list[i+1] for i, w in enumerate(week_list[:-1])}
sel_df['buy_yw'] = sel_df['yw'].map(yw_to_next)
# 向量化: 下一周 open / close / low
buy_info = df[['code','yw','open','close','low']].rename(columns={'open':'buy_open','close':'sell_close','low':'buy_low'})
sel = sel_df.merge(buy_info.rename(columns={'yw':'buy_yw'}), on=['code','buy_yw'], how='left')
sel = sel[['yw','buy_yw','code','buy_open','sell_close','buy_low'] + factor_cols].dropna(subset=['buy_open']).copy()
for c in factor_cols:
    sel[c] = rank_std(sel.groupby('yw')[c].transform(lambda x: x))
sel['score'] = (
    + sel['shrink_up'] - sel['amount_20d'] - sel['max_up_20d'] + sel['expand_down']
    - sel['tail_return'] - sel['vol_chg_std'] - sel['overnight_gap']
) / 7
# 持有整周收益 + 止损
sel['ret0'] = sel['sell_close'] / sel['buy_open'] - 1
sel['week_low_ret'] = sel['buy_low'] / sel['buy_open'] - 1
# 广度
breadth = df.groupby('yw').apply(lambda x: pd.Series({'breadth': (x['pct']>0).mean()}), include_groups=False).reset_index()
breadth_d = dict(zip(breadth['yw'], breadth['breadth']))
sel['breadth'] = sel['yw'].map(breadth_d)

COST = 0.0025
def run(topn, sl, timing='none', th=0.45):
    picks = sel.sort_values(['yw','score'], ascending=[True,False]).groupby('yw').head(topn).reset_index(drop=True)
    rets = []
    for r in picks.itertuples():
        if sl > 0 and r.week_low_ret < -sl:
            ret = -sl
        else:
            ret = r.ret0
        if timing == 'lt' and r.breadth > th:
            ret = 0.0
        rets.append(ret - COST)
    picks['ret'] = rets
    wk = picks.groupby('yw').agg(ret=('ret','mean'), n=('code','nunique')).reset_index()
    return wk

def summarize(wk, label):
    nav = (1 + wk['ret']).cumprod()
    print(f'{label:<30} 周数{len(wk):>3} 累计{(nav.iloc[-1]-1)*100:>7.1f}% 周均{wk["ret"].mean()*100:>6.2f}% 胜率{(wk["ret"]>0).mean()*100:>3.0f}%')

print('=== 全窗口(2022-04~2026-10) ===')
for topn, sl in [(4, 0.0), (5, 0.08), (5, 0.05)]:
    wk = run(topn, sl)
    summarize(wk, f'Top{topn} 止损{sl*100:.0f}% 无择时')
for topn, sl in [(5, 0.08)]:
    wk = run(topn, sl, timing='lt')
    summarize(wk, f'Top{topn} 止损8% 反向≤0.45')

print('=== 2026-03~10 弱市窗口 ===')
weak = [w for w in week_list if w >= '2026-09']
weak = [w for w in week_list if w[:4] == '2026']
for topn, sl in [(4, 0.0), (5, 0.08), (5, 0.05), (5, 0.0)]:
    wk = run(topn, sl)
    wk = wk[wk['yw'].isin(weak)]
    summarize(wk, f'Top{topn} 止损{sl*100:.0f}% 无择时(2026)')

print('=== 分年度 Top5 止损8% ===')
wk = run(5, 0.08)
wk['year'] = wk['yw'].str[:4]
for y, sub in wk.groupby('year'):
    nav_y = (1 + sub['ret']).cumprod()
    print(f'{y}: 累计{(nav_y.iloc[-1]-1)*100:>7.1f}% 周均{sub["ret"].mean()*100:>6.2f}% 胜率{((sub["ret"]>0).mean()*100):>3.0f}% 周数{len(sub)}')

# 全市场基准 2026
base_wk = df.groupby('yw').apply(lambda x: pd.Series({'ret': x['pct'].mean()}), include_groups=False).reset_index()
base_wk = base_wk[base_wk['yw'].str[:4] == '2026']
nav_b = (1 + base_wk['ret']).cumprod()
print(f'全市场等权 2026: 累计{(nav_b.iloc[-1]-1)*100:>7.1f}% 周均{base_wk["ret"].mean()*100:>6.2f}%')
