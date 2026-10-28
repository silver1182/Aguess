# -*- coding: utf-8 -*-
"""
v9 周频系统优化: 网格搜索 + 分年度验证
维度: TopN × 止损档 × 广度择时 × 卖出时点(周五/周四) × 频率(周/2周/月)
全部向量化, 基于 week_kline_long.json
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
df['ym'] = df['date'].dt.strftime('%Y-%m')
factor_cols = ['shrink_up','amount_20d','max_up_20d','expand_down','tail_return','vol_chg_std','overnight_gap']
sel_df = df[df[factor_cols].notna().all(axis=1)].copy()

def rank_std(s):
    s = s.fillna(s.median())
    r = s.rank(pct=True)
    return (r - 0.5) * 2

week_list = df.groupby('yw')['date'].max().sort_values().index.tolist()
yw_to_next = {w: week_list[i+1] for i, w in enumerate(week_list[:-1])}
sel_df['buy_yw'] = sel_df['yw'].map(yw_to_next)
buy_info = df[['code','yw','open','close','low']].rename(columns={'open':'buy_open','close':'sell_close','low':'buy_low'})
sel = sel_df.merge(buy_info.rename(columns={'yw':'buy_yw'}), on=['code','buy_yw'], how='left')
sel = sel[['yw','buy_yw','code','buy_open','sell_close','buy_low'] + factor_cols].dropna(subset=['buy_open']).copy()
for c in factor_cols:
    sel[c] = rank_std(sel.groupby('yw')[c].transform(lambda x: x))
sel['score'] = (
    + sel['shrink_up'] - sel['amount_20d'] - sel['max_up_20d'] + sel['expand_down']
    - sel['tail_return'] - sel['vol_chg_std'] - sel['overnight_gap']
) / 7
sel['ret0'] = sel['sell_close'] / sel['buy_open'] - 1
sel['week_low_ret'] = sel['buy_low'] / sel['buy_open'] - 1
breadth = df.groupby('yw').apply(lambda x: pd.Series({'breadth': (x['pct']>0).mean()}), include_groups=False).reset_index()
breadth_d = dict(zip(breadth['yw'], breadth['breadth']))
sel['breadth'] = sel['yw'].map(breadth_d)
# 周四卖出: 下周周一开盘→周四收盘(近似用 hold 周倒数第二根K? 周K无日内, 用下周tail近似不可行; 跳过周四, 改测持有2周)
# 行业约束用代码前缀近似: 60/00 主板; 分散约束用 code 前3位(粗略行业桶)

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
        elif timing == 'gt' and r.breadth < th:
            ret = 0.0
        rets.append(ret - COST)
    picks['ret'] = rets
    wk = picks.groupby('yw').agg(ret=('ret','mean'), n=('code','nunique')).reset_index()
    nav = (1 + wk['ret']).cumprod()
    mdd = ((nav / nav.cummax()) - 1).min()
    n = len(wk)
    cagr = nav.iloc[-1] ** (52/n) - 1 if n > 0 else 0
    return nav.iloc[-1], mdd, cagr, wk

rows = []
print('=== 网格: TopN × 止损 × 择时 ===')
for topn in [3, 4, 5, 6, 8]:
    for sl in [0.0, 0.03, 0.05, 0.08, 0.10, 0.12]:
        for timing, th in [('none', 0.45), ('lt', 0.42), ('lt', 0.48), ('gt', 0.50)]:
            nav, mdd, cagr, wk = run(topn, sl, timing, th)
            rows.append({'topn': topn, 'sl': sl, 'timing': timing, 'th': th,
                         'total': nav-1, 'cagr': cagr, 'mdd': mdd,
                         'wk_ret': wk['ret'].mean(), 'win': (wk['ret']>0).mean(), 'n': len(wk)})
res = pd.DataFrame(rows)
res = res.sort_values('cagr', ascending=False)
print(res.head(15).to_string(index=False))

print('\n=== 全窗口 Top10 ===')
print(res.head(10).to_string(index=False))

print('\n=== 弱市(2026) Top10 的窗口表现 ===')
def weak_perf(r):
    nav, mdd, cagr, wk = run(int(r['topn']), r['sl'], r['timing'], r['th'])
    wk26 = wk[wk['yw'].str[:4] == '2026']
    if len(wk26) == 0:
        return np.nan
    nav26 = (1 + wk26['ret']).cumprod()
    return nav26.iloc[-1] - 1
for _, r in res.head(10).iterrows():
    print(f"Top{r['topn']} 止损{r['sl']*100:.0f}% {r['timing']}{r['th']:.2f}: 2026累计{weak_perf(r)*100:+.1f}%")

print('\n=== 2周频 / 月频 ===')
# 2周频: 每2周选股持2周
tail_map = df.set_index(['code','yw'])['tail'].to_dict()
low_map = df.set_index(['code','yw'])['low'].to_dict()
sel_weeks = week_list[::2]
for topn in [4, 5]:
    picks2 = sel[sel['yw'].isin(sel_weeks)].sort_values(['yw','score'], ascending=[True,False]).groupby('yw').head(topn).reset_index(drop=True)
    wk2 = []
    for i, yw in enumerate(sel_weeks[:-1]):
        nxt = sel_weeks[i+1]
        sub = picks2[picks2['yw']==yw]
        if len(sub) == 0:
            wk2.append(0.0)
            continue
        rets = []
        nxt2 = yw_to_next.get(nxt, '')
        for r in sub.itertuples():
            r1 = r.ret0 if r.buy_yw == nxt else tail_map.get((r.code, nxt), 0.0)
            r2 = tail_map.get((r.code, nxt2), 0.0) if nxt2 else 0.0
            rets.append((1+r1)*(1+r2)-1)
        wk2.append(np.mean(rets) - COST)
    wk2 = pd.Series(wk2)
    nav = (1 + wk2).cumprod()
    mdd = ((nav/nav.cummax())-1).min()
    n2 = len(wk2)
    cagr = nav.iloc[-1] ** (52/(n2*2)) - 1
    print(f'2周频Top{topn}: 累计{(nav.iloc[-1]-1)*100:+.1f}% 年化{cagr*100:+.1f}% 回撤{mdd*100:.1f}% 期均{wk2.mean()*100:+.2f}% 期数{n2}')

# 月频
month_list = df.groupby('ym')['date'].max().sort_values().index.tolist()
ym_to_next = {m: month_list[i+1] for i, m in enumerate(month_list[:-1])}
sel_df2 = df[df[factor_cols].notna().all(axis=1)].copy()
sel_df2['buy_ym'] = sel_df2['ym'].map(ym_to_next)
last_week_of_month = df.groupby('ym')['yw'].max()
sel_m = sel_df2[sel_df2['yw'] == sel_df2['ym'].map(last_week_of_month)].copy()
mo_open = df.groupby(['code','ym'])['open'].first().reset_index().rename(columns={'ym':'buy_ym','open':'buy_open'})
mo_close = df.groupby(['code','ym'])['close'].last().reset_index().rename(columns={'ym':'buy_ym','close':'sell_close'})
sel_m = sel_m.merge(mo_open, on=['code','buy_ym'], how='left').merge(mo_close, on=['code','buy_ym'], how='left')
sel_m = sel_m[sel_m['buy_open'].notna() & sel_m['sell_close'].notna()].copy()
for c in factor_cols:
    sel_m[c] = rank_std(sel_m.groupby('ym')[c].transform(lambda x: x))
sel_m['score'] = (
    + sel_m['shrink_up'] - sel_m['amount_20d'] - sel_m['max_up_20d'] + sel_m['expand_down']
    - sel_m['tail_return'] - sel_m['vol_chg_std'] - sel_m['overnight_gap']
) / 7
for topn in [3, 5, 8]:
    picks_m = sel_m.sort_values(['ym','score'], ascending=[True,False]).groupby('ym').head(topn).reset_index(drop=True)
    picks_m['ret'] = picks_m['sell_close'] / picks_m['buy_open'] - 1 - COST
    wk_m = picks_m.groupby('ym').agg(ret=('ret','mean')).reset_index()
    nav = (1 + wk_m['ret']).cumprod()
    mdd = ((nav/nav.cummax())-1).min()
    n_m = len(wk_m)
    cagr = nav.iloc[-1] ** (12/n_m) - 1
    print(f'月频Top{topn}: 累计{(nav.iloc[-1]-1)*100:+.1f}% 年化{cagr*100:+.1f}% 回撤{mdd*100:.1f}% 月均{wk_m["ret"].mean()*100:+.2f}% 月数{n_m}')

# 输出最优配置分年度
print('\n=== 最优配置分年度 ===')
best = res.iloc[0]
nav, mdd, cagr, wk = run(int(best['topn']), best['sl'], best['timing'], best['th'])
wk['year'] = wk['yw'].str[:4]
for y, sub in wk.groupby('year'):
    nav_y = (1 + sub['ret']).cumprod()
    print(f'{y}: 累计{(nav_y.iloc[-1]-1)*100:+7.1f}% 周均{sub["ret"].mean()*100:+6.2f}% 胜率{(sub["ret"]>0).mean()*100:3.0f}% 周数{len(sub)}')

res.to_csv(base + r'\output\v9优化网格_20261027.csv', index=False, encoding='utf-8-sig')
print('\n[产出]', base + r'\output\v9优化网格_20261027.csv')
