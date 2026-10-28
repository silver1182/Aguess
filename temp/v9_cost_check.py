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
buy_df = df[['code','yw','open']].rename(columns={'open':'buy_open'})
sel = sel_df.merge(buy_df.rename(columns={'yw':'buy_yw'}), on=['code','buy_yw'], how='left')
sel = sel[['yw','buy_yw','code','close','buy_open'] + factor_cols].dropna(subset=['buy_open']).copy()
for c in factor_cols:
    sel[c] = rank_std(sel.groupby('yw')[c].transform(lambda x: x))
sel['score'] = (
    + sel['shrink_up'] - sel['amount_20d'] - sel['max_up_20d'] + sel['expand_down']
    - sel['tail_return'] - sel['vol_chg_std'] - sel['overnight_gap']
) / 7
sel['sell_close'] = sel['close']
breadth = df.groupby('yw').apply(lambda x: pd.Series({'breadth': (x['pct']>0).mean()}), include_groups=False).reset_index()

def backtest(topn, breadth_mode='lt', breadth_th=0.45, cost_weekly=0.0):
    picks = sel.sort_values(['yw','score'], ascending=[True,False]).groupby('yw').head(topn).reset_index(drop=True)
    trades = picks.merge(breadth, on='yw', how='left')
    trades['ret'] = trades['sell_close'] / trades['buy_open'] - 1
    if breadth_mode == 'lt':
        trades['active'] = trades['breadth'] <= breadth_th
    else:
        trades['active'] = True
    trades['ret'] = np.where(trades['active'], trades['ret'] - cost_weekly, 0.0)
    wk_ret = trades.groupby('yw').agg(ret=('ret','mean'), n=('code','nunique'), active=('active','first')).reset_index()
    nav = (1 + wk_ret['ret']).cumprod()
    mdd = ((nav / nav.cummax()) - 1).min()
    n = len(wk_ret)
    cagr = nav.iloc[-1] ** (52/n) - 1 if n > 0 else 0
    return nav, mdd, cagr, wk_ret

# 成本口径：周频每周全换仓（买入佣金 + 卖出佣金+印花税 + 滑点）
# A股现状: 佣金万2.5双边(最低5元), 印花税卖出0.05%(2023.8后), 单边滑点0.1%估算
# 每笔买入成本≈佣金0.025%+滑点0.1% = 0.125%; 卖出≈佣金0.025%+印花税0.05%+滑点0.1% = 0.175%
# 每周双边合计 ≈ 0.30%（小资金按最低5元佣金上浮，取0.30%~0.40%档）
print('=== 周频 反向0.45 成本敏感性 ===')
for cost_lbl, cost in [('0成本', 0.0), ('0.10%', 0.001), ('0.20%', 0.002), ('0.30%', 0.003), ('0.40%', 0.004)]:
    row = []
    for topn in [2, 3, 4, 5]:
        nav, mdd, cagr, wk = backtest(topn, 'lt', 0.45, cost)
        row.append(f'Top{topn}:累计{(nav.iloc[-1]-1)*100:>6.1f}% 年化{cagr*100:>5.1f}% 回撤{mdd*100:>5.1f}%')
    print(f'{cost_lbl:>6}: ' + ' | '.join(row))

# 月频成本对照（每月换仓一次，双边约0.30%*12≈3.6%/年）
print('\n=== 月度持有 vs 周频的年度换手成本参考 ===')
print('周频(52次/年) 0.30%/次 ≈ 15.6%/年; 月频(12次/年) 0.30%/次 ≈ 3.6%/年')

# 择时阈值精扫（Top3/Top4, 0.30%成本）
print('\n=== 0.30%成本下 阈值精扫 ===')
for th in [0.40, 0.42, 0.45, 0.48, 0.50]:
    row = []
    for topn in [3, 4]:
        nav, mdd, cagr, wk = backtest(topn, 'lt', th, 0.003)
        row.append(f'Top{topn}:累计{(nav.iloc[-1]-1)*100:>6.1f}% 年化{cagr*100:>5.1f}% 回撤{mdd*100:>5.1f}% 持仓{(wk["active"].mean()*100):>3.0f}%')
    print(f'广度≤{th}: ' + ' | '.join(row))

# 最优档分年度(含0.30%成本)
print('\n=== Top3 反向0.45 + 0.30%成本 分年度 ===')
_, _, _, wk = backtest(3, 'lt', 0.45, 0.003)
wk['year'] = wk['yw'].str[:4]
for y, sub in wk.groupby('year'):
    nav_y = (1 + sub['ret']).cumprod()
    print(f'{y}: 年度{(nav_y.iloc[-1]-1)*100:>7.1f}% 持仓{(sub["active"].mean()*100):>3.0f}% 周均{sub["ret"].mean()*100:>6.2f}%')

# 全市场基准（周频，含成本近似忽略）
base_wk = df.groupby('yw')['pct'].mean().reset_index().rename(columns={'pct':'ret'})
nav_b = (1+base_wk['ret']).cumprod()
mdd_b = ((nav_b/nav_b.cummax())-1).min()
cagr_b = nav_b.iloc[-1] ** (52/len(base_wk)) - 1
print(f'\n全市场等权基准: 累计{(nav_b.iloc[-1]-1)*100:>7.1f}% 年化{cagr_b*100:>6.1f}% 回撤{mdd_b*100:>6.1f}%')
