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

df['yw'] = df['date'].dt.strftime('%Y-%U')
week_info = df.groupby('yw').agg(sel_date=('date','max'), buy_date=('date','min')).reset_index()
week_info['buy_yw'] = week_info['yw'].shift(-1)
week_map = week_info.dropna(subset=['buy_yw'])[['yw','buy_yw']]

sel_df = df.merge(week_info[['yw','sel_date']], on='yw', how='left')
sel_df = sel_df[sel_df['date'] == sel_df['sel_date']]
sel_df = sel_df.merge(week_map, on='yw', how='left')
buy_df = df.merge(week_info[['yw','buy_date']], on='yw', how='left')
buy_df = buy_df[buy_df['date'] == buy_df['buy_date']][['code','yw','open']].rename(columns={'open':'buy_open'})
sel_df = sel_df.merge(buy_df.rename(columns={'yw':'buy_yw'}), on=['code','buy_yw'], how='left')

wk_pct = df.merge(week_info[['yw','sel_date']], on='yw', how='left')
wk_pct = wk_pct[wk_pct['date'] == wk_pct['sel_date']]
breadth = wk_pct.groupby('yw').apply(lambda x: pd.Series({'breadth': (x['pct']>0).mean(), 'n': len(x)}), include_groups=False).reset_index()

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

def backtest(topn, breadth_mode='none', breadth_th=0.48, stop_loss=None, max_hold_weeks=1):
    picks = sel.sort_values(['yw','score'], ascending=[True,False]).groupby('yw').head(topn).reset_index(drop=True)
    trades = picks.merge(breadth[['yw','breadth']], on='yw', how='left')
    trades['ret'] = trades['close'] / trades['buy_open'] - 1
    if stop_loss:
        trades['ret'] = np.where(trades['ret'] < -stop_loss, -stop_loss, trades['ret'])
    if breadth_mode == 'gt':
        trades['active'] = trades['breadth'] >= breadth_th
        trades['ret'] = np.where(trades['active'], trades['ret'], 0.0)
    elif breadth_mode == 'lt':
        # 弱市反向: 广度低时满仓(超跌反弹), 广度极高时空仓(见顶)
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

print('=== 敏感性测试 (Top4, 39周) ===')
configs = [
    ('无择时', 'none', None),
    ('无择时+5%止损', 'none', 0.05),
    ('无择时+8%止损', 'none', 0.08),
    ('广度>0.48', 'gt', None),
    ('广度>0.60', 'gt', None),
    ('广度<0.48反向', 'lt', None),
    ('广度<0.60反向', 'lt', None),
]
for lbl, bm, sl in configs:
    wk_ret, _ = backtest(4, breadth_mode=bm, breadth_th=0.48 if '0.48' in lbl else 0.60, stop_loss=sl)
    nav, mdd, cagr = to_nav(wk_ret)
    active_pct = wk_ret['active'].mean() * 100
    print(f'{lbl}: 累计{(nav.iloc[-1]-1)*100:>6.1f}% 年化{cagr*100:>6.1f}% 回撤{mdd*100:>6.1f}% 周均{wk_ret["ret"].mean()*100:>6.2f}% 胜率{(wk_ret["ret"]>0).mean()*100:>4.0f}% 持仓周占比{active_pct:>4.0f}%')

print('\n=== 分阶段表现 (Top4 无择时, 2026-02~04 / 05~07 / 08~10) ===')
wk_ret, _ = backtest(4, breadth_mode='none')
wk_ret['month'] = wk_ret['yw'].str[5:].astype(int)
wk_ret['period'] = np.where(wk_ret['month']<=16, '02-04', np.where(wk_ret['month']<=30, '05-07', '08-10'))
for p in ['02-04','05-07','08-10']:
    sub = wk_ret[wk_ret['period']==p]
    print(f'{p}: 周数{len(sub)} 累计{(sub["ret"]+1).prod()*100-100:>6.1f}% 周均{sub["ret"].mean()*100:>6.2f}%')

# 全市场同分段
base_wk = wk_pct.groupby('yw')['pct'].mean().reset_index().rename(columns={'pct':'ret'})
base_wk['month'] = base_wk['yw'].str[5:].astype(int)
base_wk['period'] = np.where(base_wk['month']<=16, '02-04', np.where(base_wk['month']<=30, '05-07', '08-10'))
print('\n全市场同分段:')
for p in ['02-04','05-07','08-10']:
    sub = base_wk[base_wk['period']==p]
    print(f'{p}: 周数{len(sub)} 累计{(sub["ret"]+1).prod()*100-100:>6.1f}% 周均{sub["ret"].mean()*100:>6.2f}%')

# 最新一期选股明细
wk_ret, trades = backtest(4, breadth_mode='none')
last_yw = trades['yw'].max()
print(f'\n=== 最新选股 ({last_yw}) ===')
print(trades[trades['yw']==last_yw][['code','score','buy_open','close','ret','breadth']].to_string(index=False))
