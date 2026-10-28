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

df['shrink_up'] = g[['pct','vol_chg']].apply(lambda x: ((x['pct']>0) & (x['vol_chg']<1)).rolling(10).mean())
df['amount_20d'] = g['volume'].transform(lambda x: x.rolling(20).mean())
df['max_up_20d'] = g['pct'].transform(lambda x: x.rolling(20).max())
df['expand_down'] = g[['pct','vol_chg']].apply(lambda x: ((x['pct']<0) & (x['vol_chg']>1.2)).rolling(10).mean())
df['tail_return'] = g['tail'].transform(lambda x: x.rolling(20).mean())
df['vol_chg_std'] = g['vol_chg'].transform(lambda x: x.rolling(20).std())
df['overnight_gap'] = g['gap'].transform(lambda x: x.rolling(20).mean())

df['yw'] = df['date'].dt.strftime('%Y-%U')

# 检查因子过滤后的数据量
fc = ['shrink_up','amount_20d','max_up_20d','expand_down','tail_return','vol_chg_std','overnight_gap']
print('df行数:', len(df))
print('因子全非空:', df[fc].notna().all(axis=1).sum())

week_list = df.groupby('yw')['date'].max().sort_values().index.tolist()
print('周数:', len(week_list))
print('前5周:', week_list[:5])
print('后5周:', week_list[-5:])
yw_to_next = {w: week_list[i+1] for i, w in enumerate(week_list[:-1])}
print('最后一周映射:', week_list[-1], '->', yw_to_next.get(week_list[-1], '无'))

sel_df = df[df[fc].notna().all(axis=1)].copy()
sel_df['buy_yw'] = sel_df['yw'].map(yw_to_next)
print('sel_df行数:', len(sel_df))
print('buy_yw非空:', sel_df['buy_yw'].notna().sum())
print('sel_df yw范围:', sel_df['yw'].min(), sel_df['yw'].max())
print('sel_df buy_yw范围:', sel_df['buy_yw'].min(), sel_df['buy_yw'].max())

buy_df = df[['code','yw','open']].rename(columns={'open':'buy_open'})
sel_merged = sel_df.merge(buy_df.rename(columns={'yw':'buy_yw'}), on=['code','buy_yw'], how='left')
print('合并后行数:', len(sel_merged))
print('buy_open非空:', sel_merged['buy_open'].notna().sum())

# 每只股票数据完整性检查
cnt = df.groupby('code').size()
print('\n每只股票K线数: min', cnt.min(), 'median', cnt.median(), 'max', cnt.max())
print('K线数<30的股票数:', (cnt<30).sum())
print('K线数<25的股票数:', (cnt<25).sum())