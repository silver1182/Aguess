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

# 向量化 merge 取买入周信息（一次哈希join，避免循环set_index）
buy_meta = df[['code','yw','open','low','tail']].rename(columns={'yw':'buy_yw','open':'buy_open','low':'week_low','tail':'hold_tail'})
sel = sel_df.merge(buy_meta, on=['code','buy_yw'], how='left')
sel = sel[['yw','buy_yw','code','close','buy_open','week_low','hold_tail'] + factor_cols].dropna(subset=['buy_open']).copy()
for c in factor_cols:
    sel[c] = rank_std(sel.groupby('yw')[c].transform(lambda x: x))
sel['score'] = (
    + sel['shrink_up'] - sel['amount_20d'] - sel['max_up_20d'] + sel['expand_down']
    - sel['tail_return'] - sel['vol_chg_std'] - sel['overnight_gap']
) / 7
sel['buy_open'] = sel['buy_open'].astype(float)
sel['week_low'] = sel['week_low'].astype(float)
sel['hold_tail'] = sel['hold_tail'].astype(float)

breadth_d = df.groupby('yw').apply(lambda x: pd.Series({'breadth': (x['pct']>0).mean()}), include_groups=False).reset_index()
breadth_d = dict(zip(breadth_d['yw'], breadth_d['breadth']))

def apply_sl(row, sl):
    if sl == 0:
        return row.hold_tail
    if row.week_low <= row.buy_open * (1 - sl):
        return -sl
    return row.hold_tail

def run_weekly(topn, timing='none', th=0.45, cost=0.0, sl=0.0):
    picks = sel.sort_values(['yw','score'], ascending=[True,False]).groupby('yw').head(topn).reset_index(drop=True)
    picks['breadth'] = picks['yw'].map(breadth_d)
    if sl > 0:
        picks['ret0'] = picks.apply(lambda r: apply_sl(r, sl), axis=1)
    else:
        picks['ret0'] = picks['hold_tail']
    picks['active'] = (picks['breadth'] <= th) if timing == 'lt' else True
    picks['ret'] = np.where(picks['active'], picks['ret0'] - cost, 0.0)
    wk = picks.groupby('yw').agg(ret=('ret','mean'), active=('active','first'), n=('code','nunique')).reset_index()
    nav = (1 + wk['ret']).cumprod()
    mdd = ((nav / nav.cummax()) - 1).min()
    n = len(wk)
    cagr = nav.iloc[-1] ** (52/n) - 1
    return nav.iloc[-1], mdd, cagr, wk

def fmt_row(label, nav, mdd, cagr, wk):
    return f'{label:<26} 累计{(nav-1)*100:>7.1f}% 年化{cagr*100:>6.1f}% 回撤{mdd*100:>6.1f}% 周均{wk["ret"].mean()*100:>6.2f}% 持仓{(wk["active"].mean()*100):>3.0f}%'

print('========== A. 周频·持有一整周·0成本 ==========')
for topn in [2,3,4,5]:
    for timing in ['none','lt']:
        nav, mdd, cagr, wk = run_weekly(topn, timing, 0.45, 0.0, 0.0)
        print(fmt_row(f'Top{topn} {"无择时" if timing=="none" else "反向≤0.45"}', nav, mdd, cagr, wk))

print('\n========== B. 周频·持有一整周·0.25%成本 ==========')
for topn in [2,3,4,5]:
    for timing in ['none','lt']:
        nav, mdd, cagr, wk = run_weekly(topn, timing, 0.45, 0.0025, 0.0)
        print(fmt_row(f'Top{topn} {"无择时" if timing=="none" else "反向≤0.45"}', nav, mdd, cagr, wk))

print('\n========== C. 周频·止损(0.25%成本, 无择时) ==========')
for topn in [3,4,5]:
    for sl in [0.0, 0.05, 0.08]:
        nav, mdd, cagr, wk = run_weekly(topn, 'none', 0.45, 0.0025, sl)
        print(fmt_row(f'Top{topn} 止损{sl*100:.0f}%', nav, mdd, cagr, wk))

print('\n========== C2. 成本上浮档(无择时) ==========')
for cost in [0.003, 0.0035]:
    for topn, sl in [(5, 0.0), (5, 0.05), (5, 0.08), (4, 0.05), (3, 0.05)]:
        nav, mdd, cagr, wk = run_weekly(topn, 'none', 0.45, cost, sl)
        print(fmt_row(f'Top{topn} 止损{sl*100:.0f}% 成本{cost*100:.2f}%', nav, mdd, cagr, wk))

print('\n========== D. 周频·止损(0.25%成本, 反向择时) ==========')
for topn in [3,4,5]:
    for sl in [0.0, 0.05, 0.08]:
        nav, mdd, cagr, wk = run_weekly(topn, 'lt', 0.45, 0.0025, sl)
        print(fmt_row(f'Top{topn} 止损{sl*100:.0f}%', nav, mdd, cagr, wk))

# 2周频
print('\n========== E. 2周频(每2周选股持2周, 0成本) ==========')
tail_map = df.set_index(['code','yw'])['tail'].to_dict()
sel_weeks = week_list[::2]
picks2 = sel[sel['yw'].isin(sel_weeks)].sort_values(['yw','score'], ascending=[True,False]).groupby('yw').head(5).reset_index(drop=True)
wk2 = []
for i, yw in enumerate(sel_weeks[:-2]):
    nxt = sel_weeks[i+1]
    sub = picks2[picks2['yw']==yw]
    if len(sub) == 0:
        wk2.append({'yw': yw, 'ret': 0.0, 'active': False, 'n': 0})
        continue
    nxt2 = week_list[week_list.index(nxt)+1]
    rets = [(1 + tail_map.get((r.code, nxt), 0.0)) * (1 + tail_map.get((r.code, nxt2), 0.0)) - 1 for r in sub.itertuples()]
    wk2.append({'yw': yw, 'ret': np.mean(rets), 'active': True, 'n': len(sub)})
wk2 = pd.DataFrame(wk2)
nav = (1 + wk2['ret']).cumprod()
mdd = ((nav/nav.cummax())-1).min()
n2 = len(wk2)
cagr = nav.iloc[-1] ** (52/(n2*2)) - 1
print(f'2周频Top5: 累计{(nav.iloc[-1]-1)*100:>7.1f}% 年化{cagr*100:>6.1f}% 回撤{mdd*100:>6.1f}% 期均{wk2["ret"].mean()*100:>6.2f}%')

# 月频
print('\n========== F. 月频·持有一整月(0成本) ==========')
month_list = df.groupby('ym')['date'].max().sort_values().index.tolist()
ym_to_next = {m: month_list[i+1] for i, m in enumerate(month_list[:-1])}
sel_df2 = df[df[factor_cols].notna().all(axis=1)].copy()
sel_df2['buy_ym'] = sel_df2['ym'].map(ym_to_next)
last_week_of_month = df.groupby('ym')['yw'].max()
sel_month = sel_df2[sel_df2['yw'] == sel_df2['ym'].map(last_week_of_month)].copy()
mo_open = df.groupby(['code','ym'])['open'].first().reset_index().rename(columns={'ym':'buy_ym','open':'buy_open'})
mo_close = df.groupby(['code','ym'])['close'].last().reset_index().rename(columns={'ym':'buy_ym','close':'sell_close'})
sel_m = sel_month.merge(mo_open, on=['code','buy_ym'], how='left').merge(mo_close, on=['code','buy_ym'], how='left')
sel_m = sel_m[sel_m['buy_open'].notna() & sel_m['sell_close'].notna()].copy()
for c in factor_cols:
    sel_m[c] = rank_std(sel_m.groupby('ym')[c].transform(lambda x: x))
sel_m['score'] = (
    + sel_m['shrink_up'] - sel_m['amount_20d'] - sel_m['max_up_20d'] + sel_m['expand_down']
    - sel_m['tail_return'] - sel_m['vol_chg_std'] - sel_m['overnight_gap']
) / 7
for topn in [3,5,8]:
    picks_m = sel_m.sort_values(['ym','score'], ascending=[True,False]).groupby('ym').head(topn).reset_index(drop=True)
    picks_m['ret'] = picks_m['sell_close'] / picks_m['buy_open'] - 1
    wk_m = picks_m.groupby('ym').agg(ret=('ret','mean'), n=('code','nunique')).reset_index()
    nav = (1 + wk_m['ret']).cumprod()
    mdd = ((nav/nav.cummax())-1).min()
    n_m = len(wk_m)
    cagr = nav.iloc[-1] ** (12/n_m) - 1
    print(f'月频Top{topn}: 累计{(nav.iloc[-1]-1)*100:>7.1f}% 年化{cagr*100:>6.1f}% 回撤{mdd*100:>6.1f}% 月均{wk_m["ret"].mean()*100:>6.2f}%')

print('\n========== G. 分年度: Top5 无择时 + 0.25%成本 ==========')
nav, mdd, cagr, wk = run_weekly(5, 'none', 0.45, 0.0025, 0.0)
wk['year'] = wk['yw'].str[:4]
for y, sub in wk.groupby('year'):
    nav_y = (1 + sub['ret']).cumprod()
    print(f'{y}: 年度{(nav_y.iloc[-1]-1)*100:>7.1f}% 周均{sub["ret"].mean()*100:>6.2f}% 胜率{((sub["ret"]>0).mean()*100):>3.0f}%')

print('\n========== H. 最新周候选(2026-42截面) ==========')
last_yw = week_list[-2]
sub = sel[sel['yw']==last_yw].sort_values('score', ascending=False).head(8)
for r in sub.itertuples():
    print(f'{r.code}: score {r.score:>8.3f} buy_open {r.buy_open:>7.2f} 下周tail {r.hold_tail*100:>6.2f}%')
