import json, pandas as pd, numpy as np

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
with open(base + r'\temp\kline_cache_em.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

# 构造日K数据框，计算均线
all_bars = []
for code, bars in cache.items():
    for b in bars:
        b['code'] = code
        all_bars.append(b)
df = pd.DataFrame(all_bars)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['code', 'date']).reset_index(drop=True)

# 计算均线和涨跌幅
for w in [5, 10, 20, 60]:
    df[f'ma{w}'] = df.groupby('code')['close'].transform(lambda x: x.rolling(w).mean())
df['pct'] = df.groupby('code')['close'].pct_change() * 100
df['vol_ma20'] = df.groupby('code')['volume'].transform(lambda x: x.rolling(20).mean())
df['vol_ratio'] = df['volume'] / df['vol_ma20']
df['dist_ma20'] = (df['close'] / df['ma20'] - 1) * 100
df['dist_ma10'] = (df['close'] / df['ma10'] - 1) * 100
df['dist_ma5'] = (df['close'] / df['ma5'] - 1) * 100
df['ma20_up'] = df['ma20'] > df.groupby('code')['ma20'].shift(5)

# 近期最大涨幅（近5日）
df['max5'] = df.groupby('code')['close'].transform(lambda x: x.pct_change(5) * 100)

# 回测区间
bt_df = df[(df['date'] >= '2026-07-01') & (df['date'] <= '2026-10-23')].copy()
print('回测样本:', len(bt_df), '日期:', bt_df['date'].min().date(), '~', bt_df['date'].max().date())

# 未来N日收益
for h in [3, 5, 10, 20]:
    bt_df[f'fwd{h}'] = bt_df.groupby('code')['close'].pct_change(-h) * -100 * -1
    # 正确定义：未来h日收益率 = (close[t+h]/close[t]-1)*100
    bt_df[f'fwd{h}'] = bt_df.groupby('code')['close'].shift(-h) / bt_df['close'] - 1) * 100

print(bt_df[['date', 'code', 'close', 'ma5', 'ma10', 'ma20', 'fwd5']].dropna().head().to_string(index=False))