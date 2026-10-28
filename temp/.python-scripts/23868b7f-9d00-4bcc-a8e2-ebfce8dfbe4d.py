
import json, pandas as pd, numpy as np

DATA = r"C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\kline_day_long.json"
with open(DATA, 'r', encoding='utf-8') as f:
    raw = json.load(f)
print("raw type:", type(raw))
if isinstance(raw, dict):
    codes = list(raw.keys())
    print("codes sample:", codes[:5], "total codes:", len(codes))
    rows = []
    for code, arr in raw.items():
        for d in arr:
            d['code'] = code
            rows.append(d)
    df = pd.DataFrame(rows)
else:
    df = pd.DataFrame(raw)
print("df shape:", df.shape)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['code', 'date'])
df['pct'] = (df['close'] / df['close'].shift(1) - 1) * 100
df['vol_ratio'] = df['volume'] / df['volume'].rolling(5).mean()

# 边界检查：shift(1) 未按 code 分组，跨股票边界行 pct 异常，应先用 groupby
df2 = df.copy()
df2['pct_g'] = df2.groupby('code')['close'].pct_change() * 100
df2['vol_ratio_g'] = df2.groupby('code')['volume'].transform(lambda s: s / s.rolling(5).mean())

# 对比两种算法
print("\n[边界对比] 未分组 vs 分组 pct (前6只股票首行)")
chg = df2[df2.groupby('code').cumcount() == 0][['code', 'date', 'pct', 'pct_g']].head(6)
print(chg.to_string(index=False))

print("\n信号筛选（用分组算法）:")
sig = df2[(df2['pct_g'] >= 9.5) & (df2['vol_ratio_g'] <= 0.6)].copy()
print("涨停+缩量:", len(sig))
sig = df2[(df2['pct_g'] >= 9.5) & (df2['vol_ratio_g'] <= 0.6)].copy()
print("prev2 列检查")
# prev2 = 前一日涨停
df2['prev2_pct'] = df2.groupby('code')['pct_g'].shift(1)
df2['ma5'] = df2.groupby('code')['close'].transform(lambda s: s.rolling(5).mean())
sig = df2[(df2['prev2_pct'] >= 9.5) & (df2['vol_ratio_g'] <= 0.6) & (df2['close'] > df2['ma5']) & (df2['pct_g'] >= -2) & (df2['pct_g'] <= 1)]
print("A2完整条件信号数:", len(sig))
