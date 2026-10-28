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
# 清理ERR
df = df[df['close'].notna()]
df = df.sort_values(['code', 'date']).reset_index(drop=True)
print('总行数:', len(df), '股票数:', df['code'].nunique())
print('日期范围:', df['date'].min().date(), '~', df['date'].max().date())

# ===== 周线因子 =====
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

# 每周最后交易日 = 当周截面（周K本身就是周快照，date即周五）
sel_df = df[df[['shrink_up','amount_20d','max_up_20d','expand_down','tail_return','vol_chg_std','overnight_gap']].notna().all(axis=1)].copy()

# 广度：当周上涨家数占比
breadth = df.groupby('yw').apply(lambda x: pd.Series({'breadth': (x['pct']>0).mean(), 'n': len(x)}), include_groups=False).reset_index()

# 下周买入：取下一周K线（周K的开盘即下周第一日）
week_list = df.groupby('yw')['date'].max().sort_values().index.tolist()
yw_to_next = {w: week_list[i+1] for i, w in enumerate(week_list[:-1])}
sel_df['buy_yw'] = sel_df['yw'].map(yw_to_next)
buy_df = df[['code','yw','open']].rename(columns={'open':'buy_open'})
sel_df = sel_df.merge(buy_df.rename(columns={'yw':'buy_yw'}), on=['code','buy_yw'], how='left')

def rank_std(s):
    s = s.fillna(s.median())
    r = s.rank(pct=True)
    return (r - 0.5) * 2

factor_cols = ['shrink_up','amount_20d','max_up_20d','expand_down','tail_return','vol_chg_std','overnight_gap']
sel = sel_df[['yw','buy_yw','code','close','buy_open'] + factor_cols].dropna(subset=['buy_open']).copy()
for c in factor_cols:
    sel[c] = rank_std(sel.groupby('yw')[c].transform(lambda x: x))

sel['score'] = (
    + sel['shrink_up'] - sel['amount_20d'] - sel['max_up_20d'] + sel['expand_down']
    - sel['tail_return'] - sel['vol_chg_std'] - sel['overnight_gap']
) / 7

def backtest(topn, breadth_mode='none', breadth_th=0.48, stop_loss=None):
    picks = sel.sort_values(['yw','score'], ascending=[True,False]).groupby('yw').head(topn).reset_index(drop=True)
    trades = picks.merge(breadth[['yw','breadth']], on='yw', how='left')
    trades['ret'] = trades['close'] / trades['buy_open'] - 1
    if stop_loss:
        trades['ret'] = np.where(trades['ret'] < -stop_loss, -stop_loss, trades['ret'])
    if breadth_mode == 'gt':
        trades['active'] = trades['breadth'] >= breadth_th
        trades['ret'] = np.where(trades['active'], trades['ret'], 0.0)
    elif breadth_mode == 'lt':
        trades['active'] = trades['breadth'] <= breadth_th
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

print('\n=== 3年周K长周期回测 (2022-04 ~ 2026-10) ===')
for topn in [4, 10, 20]:
    for bm, lbl in [('none','无择时'), ('gt','广度>0.48'), ('lt','广度<0.48反向')]:
        wk_ret, _ = backtest(topn, breadth_mode=bm)
        nav, mdd, cagr = to_nav(wk_ret)
        print(f'Top{topn:>2} {lbl}: 周数{len(wk_ret):>3} 累计{(nav.iloc[-1]-1)*100:>7.1f}% 年化{cagr*100:>6.1f}% 回撤{mdd*100:>6.1f}% 周均{wk_ret["ret"].mean()*100:>6.2f}% 胜率{(wk_ret["ret"]>0).mean()*100:>4.0f}%')

# 基准
base_wk = df.groupby('yw')['pct'].mean().reset_index().rename(columns={'pct':'ret'})
nav_b, mdd_b, cagr_b = to_nav(base_wk)
print(f'全市场等权基准: 周数{len(base_wk):>3} 累计{(nav_b.iloc[-1]-1)*100:>7.1f}% 年化{cagr_b*100:>6.1f}% 回撤{mdd_b*100:>6.1f}% 周均{base_wk["ret"].mean()*100:>6.2f}%')

# 分年度
print('\n=== 分年度 (Top4 无择时+5%止损) ===')
wk_ret, _ = backtest(4, breadth_mode='none', stop_loss=0.05)
wk_ret['year'] = wk_ret['yw'].str[:4]
for y, sub in wk_ret.groupby('year'):
    nav_y = (1 + sub['ret']).cumprod()
    print(f'{y}: 周数{len(sub)} 年度收益{(nav_y.iloc[-1]-1)*100:>7.1f}% 周均{sub["ret"].mean()*100:>6.2f}% 胜率{(sub["ret"]>0).mean()*100:>4.0f}%')

base_wk['year'] = base_wk['yw'].str[:4]
print('全市场分年度:')
for y, sub in base_wk.groupby('year'):
    nav_y = (1 + sub['ret']).cumprod()
    print(f'{y}: 周数{len(sub)} 年度收益{(nav_y.iloc[-1]-1)*100:>7.1f}%')

# 最新周选股
last_yw = sel['yw'].max()
picks_last = sel[sel['yw']==last_yw].sort_values('score', ascending=False).head(10)
print(f'\n=== 最新周选股 Top10 ({last_yw}) ===')
print(picks_last[['code','score','buy_open','close']].to_string(index=False))
