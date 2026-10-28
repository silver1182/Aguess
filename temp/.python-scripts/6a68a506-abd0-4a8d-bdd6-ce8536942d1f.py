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

print('pct非空:', df['pct'].notna().sum())
print('vol_chg非空:', df['vol_chg'].notna().sum())
print('volume样例:', df['volume'].head(3).tolist())

# 测试 shrink_up 计算
try:
    r = g[['pct','vol_chg']].apply(lambda x: ((x['pct']>0) & (x['vol_chg']<1)).rolling(10).mean())
    print('shrink_up类型:', type(r))
    print('shrink_up形状:', r.shape if hasattr(r,'shape') else 'N/A')
    print('shrink_up非空:', r.notna().sum() if hasattr(r,'notna') else 'N/A')
except Exception as e:
    print('shrink_up错误:', e)

# 尝试 transform 方式
try:
    r2 = g[['pct','vol_chg']].transform(lambda x: ((x['pct']>0) & (x['vol_chg']<1)).rolling(10).mean())
    print('transform方式非空:', r2.notna().sum() if hasattr(r2,'notna') else 'N/A')
except Exception as e:
    print('transform方式错误:', e)