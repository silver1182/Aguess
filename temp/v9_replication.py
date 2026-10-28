import json, pandas as pd, numpy as np

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
with open(base + r'\temp\kline_cache_em.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

all_bars = []
for code, bars in cache.items():
    for b in bars:
        b['code'] = code
        all_bars.append(b)
df = pd.DataFrame(all_bars)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['code', 'date']).reset_index(drop=True)

# ===== 因子计算 =====
g = df.groupby('code')
df['prev_close'] = g['close'].shift(1)
df['prev_vol'] = g['volume'].shift(1)
df['pct'] = df['close'] / df['prev_close'] - 1
df['gap'] = df['open'] / df['prev_close'] - 1
df['tail'] = df['close'] / df['open'] - 1
df['vol_chg'] = df['volume'] / df['prev_vol']

df['shrink_up'] = g[['pct','vol_chg']].apply(lambda x: ((x['pct']>0) & (x['vol_chg']<1)).rolling(10).mean())
df['amount_20d'] = g['volume'].transform(lambda x: x.rolling(20).mean())
df['max_up_20d'] = g['pct'].transform(lambda x: x.rolling(20).max())
df['expand_down'] = g[['pct','vol_chg']].apply(lambda x: ((x['pct']<0) & (x['vol_chg']>1.2)).rolling(10).mean())
df['tail_return'] = g['tail'].transform(lambda x: x.rolling(20).mean())
df['vol_chg_std'] = g['vol_chg'].transform(lambda x: x.rolling(20).std())
df['overnight_gap'] = g['gap'].transform(lambda x: x.rolling(20).mean())

# 周标记
df['yw'] = df['date'].dt.strftime('%Y-%U')

# 每周最后一个交易日（选股日）与第一个交易日（下周一开盘日）
week_info = df.groupby('yw').agg(sel_date=('date','max'), buy_date=('date','min')).reset_index()
# 选股周 -> 下一周（买入周）
week_info['buy_yw'] = week_info['yw'].shift(-1)
week_map = week_info.dropna(subset=['buy_yw'])[['yw','buy_yw']]

# 选股日截面
sel_df = df.merge(week_info[['yw','sel_date']], on='yw', how='left')
sel_df = sel_df[sel_df['date'] == sel_df['sel_date']]
sel_df = sel_df.merge(week_map, on='yw', how='left')
# 买入日开盘价（下一周）
buy_df = df.merge(week_info[['yw','buy_date']], on='yw', how='left')
buy_df = buy_df[buy_df['date'] == buy_df['buy_date']][['code','yw','open']].rename(columns={'open':'buy_open'})
# 卖出价：直接用选股日收盘（持有1周，周五收盘估值，简化）
sel_df = sel_df.merge(buy_df.rename(columns={'yw':'buy_yw'}), on=['code','buy_yw'], how='left')

# ===== 广度: 每周五上涨家数占比 =====
wk_pct = df.merge(week_info[['yw','sel_date']], on='yw', how='left')
wk_pct = wk_pct[wk_pct['date'] == wk_pct['sel_date']]
breadth = wk_pct.groupby('yw').apply(lambda x: pd.Series({'breadth': (x['pct']>0).mean(), 'n': len(x)}), include_groups=False).reset_index()

# ===== 打分 =====
def rank_std(s):
    s = s.fillna(s.median())
    r = s.rank(pct=True)
    return (r - 0.5) * 2

factor_cols = ['shrink_up','amount_20d','max_up_20d','expand_down','tail_return','vol_chg_std','overnight_gap']
sel = sel_df[['yw','buy_yw','code','close','buy_open'] + factor_cols].dropna(subset=['buy_open']).copy()
for c in factor_cols:
    sel[c] = rank_std(sel.groupby('yw')[c].transform(lambda x: x))  # 每周截面rank

sel['score'] = (
    + sel['shrink_up']          # +
    - sel['amount_20d']         # -
    - sel['max_up_20d']         # -
    + sel['expand_down']        # +
    - sel['tail_return']        # -
    - sel['vol_chg_std']        # -
    - sel['overnight_gap']      # -
) / 7

# ===== 回测 =====
def backtest(topn, use_breadth=True, breadth_th=0.48):
    picks = sel.sort_values(['yw','score'], ascending=[True,False]).groupby('yw').head(topn).reset_index(drop=True)
    trades = picks.merge(breadth[['yw','breadth']], on='yw', how='left')
    trades['ret'] = trades['close'] / trades['buy_open'] - 1
    if use_breadth:
        trades['active'] = trades['breadth'] >= breadth_th
        trades['ret'] = np.where(trades['active'], trades['ret'], 0.0)
    else:
        trades['active'] = True
    wk_ret = trades.groupby('yw').agg(ret=('ret','mean'), n=('code','nunique'), active=('active','first'), breadth=('breadth','first')).reset_index()
    return wk_ret, trades

def to_nav(wk_ret):
    nav = (1 + wk_ret['ret']).cumprod()
    mdd = ((nav / nav.cummax()) - 1).min()
    n = len(wk_ret)
    cagr = nav.iloc[-1] ** (52/n) - 1 if n > 0 else 0
    return nav, mdd, cagr

print('=== 因子截面打分回测 (2026-02~2026-10) ===')
for topn in [4, 10, 20]:
    for use_b, lbl in [(True,'广度择时'), (False,'无择时')]:
        wk_ret, _ = backtest(topn, use_breadth=use_b)
        nav, mdd, cagr = to_nav(wk_ret)
        print(f'Top{topn:>2} {lbl}: 周数{len(wk_ret):>3} 累计{(nav.iloc[-1]-1)*100:>6.1f}% 年化{cagr*100:>6.1f}% 最大回撤{mdd*100:>6.1f}% 周均{wk_ret["ret"].mean()*100:>6.2f}% 胜率{(wk_ret["ret"]>0).mean()*100:>4.0f}%')

# 基准
base_wk = wk_pct.groupby('yw')['pct'].mean().reset_index().rename(columns={'pct':'ret'})
nav_b, mdd_b, cagr_b = to_nav(base_wk)
print(f'全市场等权基准: 周数{len(base_wk):>3} 累计{(nav_b.iloc[-1]-1)*100:>6.1f}% 年化{cagr_b*100:>6.1f}% 最大回撤{mdd_b*100:>6.1f}% 周均{base_wk["ret"].mean()*100:>6.2f}% 胜率{(base_wk["ret"]>0).mean()*100:>4.0f}%')

print('\n=== 广度分布 ===')
print(breadth['breadth'].describe().to_string())

# 输出每周明细(Top4+择时)
wk_ret4, trades4 = backtest(4, use_breadth=True)
print('\n=== Top4+择时 周度明细 ===')
print(wk_ret4.tail(15).to_string(index=False))
