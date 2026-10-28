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

breadth_map = df.groupby('yw').apply(lambda x: pd.Series({'breadth': (x['pct']>0).mean()}), include_groups=False).reset_index()
print('breadth_map columns:', breadth_map.columns.tolist())
print('breadth_map head:', breadth_map.head(8).to_string())
breadth_d = dict(zip(breadth_map['yw'], breadth_map['breadth']))
print('breadth_d sample keys:', list(breadth_d.items())[:8])

sel_df = df[df[factor_cols].notna().all(axis=1)].copy()
print('\nsel_df yw range: min', sel_df['yw'].min(), 'max', sel_df['yw'].max())
print('sel_df rows per early yw:')
print(sel_df.groupby('yw').size().head(15))

week_list = df.groupby('yw')['date'].max().sort_values().index.tolist()
print('\nweek_list head:', week_list[:8])
print('week_list tail:', week_list[-5:])
print('week count:', len(week_list))

# 检查: 每周都有因子完整的股票吗?
all_yw = sorted(set(df['yw'].unique()))
sel_yw = set(sel_df['yw'].unique())
missing = [w for w in all_yw if w not in sel_yw]
print('\n因子完整数据缺失的周数:', len(missing), '前10:', missing[:10])

# 检查 breadth<=0.45 的周里有多少没有 sel 数据
b_le45 = [w for w in all_yw if breadth_d.get(w, 0.5) <= 0.45]
b_missing = [w for w in b_le45 if w not in sel_yw]
print('广度<=0.45 的周:', len(b_le45), '其中无因子数据:', len(b_missing))
print('缺失周:', b_missing[:20])
