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

tail_map = df.set_index(['code','yw'])['tail'].to_dict()
breadth_d = df.groupby('yw').apply(lambda x: pd.Series({'breadth': (x['pct']>0).mean()}), include_groups=False).reset_index()
breadth_d = dict(zip(breadth_d['yw'], breadth_d['breadth']))

picks = sel.sort_values(['yw','score'], ascending=[True,False]).groupby('yw').head(3).reset_index(drop=True)
picks['breadth'] = picks['yw'].map(breadth_d)
picks['ret'] = [tail_map.get((r.code, r.buy_yw), 0.0) for r in picks.itertuples()]
picks['active_lt'] = picks['breadth'] <= 0.45
print('picks active 统计: active_lt True:', picks['active_lt'].sum(), '总行:', len(picks), '占比:', picks['active_lt'].mean())
print('breadth NaN 数量:', picks['breadth'].isna().sum())
print('ret 非零行:', (picks['ret'] != 0).sum())

wk_all = picks.groupby('yw').agg(ret_all=('ret','mean')).reset_index()
ret_lt = np.where(picks['active_lt'], picks['ret'], 0.0)
wk_lt = picks.assign(ret_lt=ret_lt).groupby('yw').agg(ret_lt=('ret_lt','mean')).reset_index()
cmp = wk_all.merge(wk_lt, on='yw', how='outer').fillna(0)
diff = (cmp['ret_all'] - cmp['ret_lt']).abs()
print('逐周收益差异: max diff', diff.max(), '非零差异周数', (diff > 1e-9).sum(), '总周数', len(cmp))
print(cmp.head(10).to_string())
nav_all = (1 + cmp['ret_all']).cumprod()
nav_lt = (1 + cmp['ret_lt']).cumprod()
print('无择时终值:', nav_all.iloc[-1], '择时终值:', nav_lt.iloc[-1])
