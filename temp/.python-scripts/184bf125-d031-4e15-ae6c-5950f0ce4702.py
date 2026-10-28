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

for w in [5, 10, 20, 60]:
    df[f'ma{w}'] = df.groupby('code')['close'].transform(lambda x: x.rolling(w).mean())
df['pct'] = df.groupby('code')['close'].pct_change() * 100
df['vol_ma20'] = df.groupby('code')['volume'].transform(lambda x: x.rolling(20).mean())
df['vol_ratio'] = df['volume'] / df['vol_ma20']
df['dist_ma20'] = (df['close'] / df['ma20'] - 1) * 100
df['dist_ma10'] = (df['close'] / df['ma10'] - 1) * 100
df['dist_ma5'] = (df['close'] / df['ma5'] - 1) * 100
df['ma20_up'] = df['ma20'] > df.groupby('code')['ma20'].shift(5)
df['max5'] = df.groupby('code')['close'].transform(lambda x: x.pct_change(5) * 100)

bt_df = df[(df['date'] >= '2026-07-01') & (df['date'] <= '2026-10-23')].copy()
print('回测样本:', len(bt_df), '日期:', bt_df['date'].min().date(), '~', bt_df['date'].max().date())

for h in [3, 5, 10, 20]:
    bt_df[f'fwd{h}'] = (bt_df.groupby('code')['close'].shift(-h) / bt_df['close'] - 1) * 100

# ============ A策略：趋势跟随/回调 ============
# 条件：价格站上MA20 + MA20向上 + 回踩到MA20附近(±3%) + 有量能配合
a_cond = (bt_df['close'] > bt_df['ma20']) & (bt_df['ma20_up']) & (bt_df['dist_ma20'].between(-3, 3)) & (bt_df['vol_ratio'] > 0.8)
a_trades = bt_df[a_cond].dropna(subset=['fwd5', 'fwd10', 'fwd20']).copy()
print('\n=== A策略(趋势回调买MA20附近, MA20向上) ===')
print('信号数:', len(a_trades), ' 涉及股票:', a_trades['code'].nunique())
for h in [5, 10, 20]:
    if len(a_trades):
        print(f'持有{h}日: 均值 {a_trades[f"fwd{h}"].mean():.2f}%  胜率 {(a_trades[f"fwd{h}"]>0).mean()*100:.1f}%')

# ============ C策略：强势股回调低吸 ============
# 条件：近期强势(近5日涨幅>5%或曾大涨) + 今日回调(跌幅>1%) + 回踩到MA5/MA10附近不破
c_cond = (bt_df['max5'] > 5) & (bt_df['pct'] < -0.5) & (bt_df['pct'] > -8) & ((bt_df['dist_ma5'].between(-2, 2)) | (bt_df['dist_ma10'].between(-2, 2)))
c_trades = bt_df[c_cond].dropna(subset=['fwd3', 'fwd5']).copy()
print('\n=== C策略(强势股回调到MA5/MA10附近) ===')
print('信号数:', len(c_trades), ' 涉及股票:', c_trades['code'].nunique())
for h in [3, 5, 10]:
    if len(c_trades):
        print(f'持有{h}日: 均值 {c_trades[f"fwd{h}"].mean():.2f}%  胜率 {(c_trades[f"fwd{h}"]>0).mean()*100:.1f}%')

# A策略不同持有期、C策略不同持有期，打印示例
print('\nA策略示例:')
print(a_trades[['date', 'code', 'close', 'dist_ma20', 'fwd10']].tail(8).to_string(index=False))
print('\nC策略示例:')
print(c_trades[['date', 'code', 'close', 'pct', 'max5', 'dist_ma5', 'dist_ma10', 'fwd5']].tail(8).to_string(index=False))