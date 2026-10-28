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

sel_df = df[df[['shrink_up','amount_20d','max_up_20d','expand_down','tail_return','vol_chg_std','overnight_gap']].notna().all(axis=1)].copy()
breadth = df.groupby('yw').apply(lambda x: pd.Series({'breadth': (x['pct']>0).mean(), 'n': len(x)}), include_groups=False).reset_index()

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

def backtest(topn, breadth_mode='none', breadth_th=0.48, stop_loss=None, min_amount=None):
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

print('=== 反向择时阈值扫描 (Top4) ===')
for th in [0.35, 0.40, 0.45, 0.48, 0.50, 0.55]:
    wk_ret, _ = backtest(4, breadth_mode='lt', breadth_th=th)
    nav, mdd, cagr = to_nav(wk_ret)
    print(f'广度<={th}: 累计{(nav.iloc[-1]-1)*100:>6.1f}% 年化{cagr*100:>5.1f}% 回撤{mdd*100:>5.1f}% 持仓周占比{wk_ret["active"].mean()*100:>4.0f}%')

print('\n=== 反向择时+止损组合 (Top4) ===')
for th, sl in [(0.48, 0.05), (0.48, 0.08), (0.45, 0.05), (0.40, 0.05)]:
    wk_ret, _ = backtest(4, breadth_mode='lt', breadth_th=th, stop_loss=sl)
    nav, mdd, cagr = to_nav(wk_ret)
    print(f'广度<={th}+止损{sl}: 累计{(nav.iloc[-1]-1)*100:>6.1f}% 年化{cagr*100:>5.1f}% 回撤{mdd*100:>5.1f}% 持仓周占比{wk_ret["active"].mean()*100:>4.0f}%')

print('\n=== 反向择时 分年度 (Top4, 广度<=0.48) ===')
wk_ret, _ = backtest(4, breadth_mode='lt', breadth_th=0.48)
wk_ret['year'] = wk_ret['yw'].str[:4]
for y, sub in wk_ret.groupby('year'):
    nav_y = (1 + sub['ret']).cumprod()
    print(f'{y}: 年度{(nav_y.iloc[-1]-1)*100:>6.1f}% 持仓占比{sub["active"].mean()*100:>4.0f}% 周均{sub["ret"].mean()*100:>5.2f}%')

print('\n=== 2026弱市: 无择时 vs 反向择时 ===')
wk_ret_none, _ = backtest(4, breadth_mode='none')
wk_ret_lt, _ = backtest(4, breadth_mode='lt', breadth_th=0.48)
wk_ret_none['year'] = wk_ret_none['yw'].str[:4]
wk_ret_lt['year'] = wk_ret_lt['yw'].str[:4]
for y in ['2026']:
    sub1 = wk_ret_none[wk_ret_none['year']==y]
    sub2 = wk_ret_lt[wk_ret_lt['year']==y]
    print(f'{y}: 无择时累计{(1+sub1["ret"]).prod()*100-100:>6.1f}% | 反向择时累计{(1+sub2["ret"]).prod()*100-100:>6.1f}%')

# 最新候选
print('\n=== 最新周(2026-42) Top15 候选 ===')
last_yw = sel['yw'].max()
picks = sel[sel['yw']==last_yw].sort_values('score', ascending=False).head(15)
print(picks[['code','score','buy_open','close']].to_string(index=False))
