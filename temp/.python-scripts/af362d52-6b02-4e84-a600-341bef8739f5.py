
import json, pandas as pd, numpy as np

DATA = r"C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\kline_day_long.json"
with open(DATA, 'r', encoding='utf-8') as f:
    raw = json.load(f)
if isinstance(raw, dict):
    rows = []
    for code, arr in raw.items():
        for d in arr:
            d['code'] = code
            rows.append(d)
    df = pd.DataFrame(rows)
else:
    df = pd.DataFrame(raw)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['code', 'date'])
df['pct'] = (df['close'] / df['close'].shift(1) - 1) * 100
df['vol_ratio'] = df['volume'] / df['volume'].rolling(5).mean()

daily = df.groupby('date').apply(lambda g: g['pct'].mean(), include_groups=False).rename('eq_pct').reset_index()
daily['eq_idx'] = (1 + daily['eq_pct'] / 100).cumprod() * 100
daily['ma20'] = daily['eq_idx'].rolling(20).mean()
daily['dev_ma20'] = (daily['eq_idx'] / daily['ma20'] - 1) * 100
daily['ret5'] = daily['eq_idx'] / daily['eq_idx'].shift(5) - 1
daily['ret20'] = daily['eq_idx'] / daily['eq_idx'].shift(20) - 1

df['prev2_pct'] = df.groupby('code')['pct'].shift(1)
df['ma5'] = df.groupby('code')['close'].transform(lambda s: s.rolling(5).mean())
sig = df[(df['prev2_pct'] >= 9.5) & (df['vol_ratio'] <= 0.6) & (df['close'] > df['ma5']) & (df['pct'] >= -2) & (df['pct'] <= 1)].copy()
sig = sig.set_index(['code', 'date'])
sig['r1'] = (sig.groupby('code')['close'].shift(-1) / sig['close'] - 1) * 100
sig['r3'] = (sig.groupby('code')['close'].shift(-3) / sig['close'] - 1) * 100
sig['r5'] = (sig.groupby('code')['close'].shift(-5) / sig['close'] - 1) * 100
sig = sig.reset_index().merge(daily[['date', 'eq_idx', 'ma20', 'dev_ma20', 'ret5', 'ret20']], on='date', how='left')
sig = sig.dropna(subset=['r1'])

def fmt(g):
    if len(g) == 0: return None
    return (len(g), g['r1'].mean(), (g['r1'] > 0).mean() * 100, g['r3'].mean(), g['r5'].mean())

last = daily.iloc[-1]
print("==== 当前市况 ====")
print("eq_idx=%.0f  MA20=%.0f  dev_ma20=%.2f%%  ret5=%.2f%%  ret20=%.2f%%" % (
    last['eq_idx'], last['ma20'], last['dev_ma20'], last['ret5'] * 100, last['ret20'] * 100))

print("\n==== [1] 按偏离MA20深度分档 ====")
for lo, hi, lab in [(-999, -6, '深熊 dev<-6%'), (-6, -3, '中熊 -6~-3%'), (-3, 0, '浅熊 -3~0%'), (0, 999, '牛/上 dev>0%')]:
    g = sig[(sig['dev_ma20'] > lo) & (sig['dev_ma20'] <= hi)]
    r = fmt(g)
    if r: print(f"{lab:<14} N={r[0]:>4}  r1={r[1]:+.2f}%  胜率={r[2]:.1f}%  r3={r[3]:+.2f}%  r5={r[4]:+.2f}%")

print("\n==== [2] 按近20日跌幅分档 ====")
for lo, hi, lab in [(-999, -8, '20日跌>8%'), (-8, -5, '跌5~8%'), (-5, -3, '跌3~5%'), (-3, 0, '跌0~3%'), (0, 999, '20日上涨')]:
    g = sig[(sig['ret20'] * 100 > lo) & (sig['ret20'] * 100 <= hi)]
    r = fmt(g)
    if r: print(f"{lab:<12} N={r[0]:>4}  r1={r[1]:+.2f}%  胜率={r[2]:.1f}%  r3={r[3]:+.2f}%  r5={r[4]:+.2f}%")

print("\n==== [3] 按近5日方向 ====")
g = sig[sig['ret5'] > 0]; r = fmt(g)
if r: print(f"{'5日上涨中':<12} N={r[0]:>4}  r1={r[1]:+.2f}%  胜率={r[2]:.1f}%  r3={r[3]:+.2f}%  r5={r[4]:+.2f}%")
g = sig[sig['ret5'] <= 0]; r = fmt(g)
if r: print(f"{'5日下跌中':<12} N={r[0]:>4}  r1={r[1]:+.2f}%  胜率={r[2]:.1f}%  r3={r[3]:+.2f}%  r5={r[4]:+.2f}%")

print("\n==== [4] 深熊+20日跌>3% (最接近当前) 分年 ====")
deep = sig[(sig['dev_ma20'] < -3) & (sig['ret20'] * 100 < -3)]
for y in [2024, 2025, 2026]:
    g = deep[deep['date'].dt.year == y]
    r = fmt(g)
    if r: print(f"{y}  N={r[0]:>4}  r1={r[1]:+.2f}%  胜率={r[2]:.1f}%  r3={r[3]:+.2f}%  r5={r[4]:+.2f}%")

print("\n==== [5] 2026年深熊环境信号明细 ====")
g = deep[deep['date'].dt.year == 2026]
if len(g):
    for _, row in g.iterrows():
        print(f"{row['date'].date()}  {row['code']}  当日pct={row['pct']:+.2f}%  vol_ratio={row['vol_ratio']:.2f}  r1={row['r1']:+.2f}%  r3={row['r3']:+.2f}%  r5={row['r5']:+.2f}%")
else:
    print("无信号")
