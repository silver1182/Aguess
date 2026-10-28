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
df['vol_ma10'] = df.groupby('code')['volume'].transform(lambda x: x.rolling(10).mean())
df['vol_ratio'] = df['volume'] / df['vol_ma10']
df['dist_ma20'] = (df['close'] / df['ma20'] - 1) * 100
df['dist_ma10'] = (df['close'] / df['ma10'] - 1) * 100
df['ma20_up'] = df['ma20'] > df.groupby('code')['ma20'].shift(5)
df['ret10'] = df.groupby('code')['close'].pct_change(10) * 100

g = df.groupby('code')
df['open_nx'] = g['open'].shift(-1)
for h in [3, 5, 10, 20]:
    df[f'buyh{h}'] = (g['open'].shift(-(1+h)) / df['open_nx'] - 1) * 100

sig = df[(df['date'] >= '2026-07-01') & (df['date'] <= '2026-10-23')].dropna(subset=['buyh5', 'buyh10']).copy()
sig['date'] = sig['date'].dt.date

def split_check(name, mask):
    t = sig[mask]
    n = len(t)
    print(f'\n{name}: 总信号 {n}')
    for lo, hi in [('2026-07-01','2026-08-31'), ('2026-09-01','2026-10-23')]:
        sub = t[(t['date'] >= pd.Timestamp(lo).date()) & (t['date'] <= pd.Timestamp(hi).date())]
        if len(sub) < 10:
            print(f'  {lo}~{hi}: 样本{len(sub)}过少')
            continue
        for h in [5, 10]:
            m, w = sub[f'buyh{h}'].mean(), (sub[f'buyh{h}']>0).mean()*100
            bm = sig[(sig['date'] >= pd.Timestamp(lo).date()) & (sig['date'] <= pd.Timestamp(hi).date())][f'buyh{h}'].mean()
            print(f'  {lo}~{hi} 持有{h}日: 均值 {m:.2f}%  胜率 {w:.1f}%  超额 {m-bm:+.2f}%  (n={len(sub)})')

# 各策略分时段检验
split_check('A1 趋势回踩MA20', (sig['close']>sig['ma20']) & sig['ma20_up'] & sig['dist_ma20'].between(-3,1) & (sig['vol_ratio']<1.2))
split_check('A4 破MA20回调低吸', sig['ma20_up'] & sig['dist_ma20'].between(-4,-1) & (sig['vol_ratio']<1.0))
g20 = sig.groupby('code')['pct'].transform(lambda x: x.rolling(20).max())
split_check('C2 大涨基因回调MA10', (g20>=7) & sig['dist_ma10'].between(-3,1) & (sig['vol_ratio']<1.2))
split_check('C3 强势深度回调MA20(10日涨>10%, dist_ma20 -5~0, vol<1.0)', (sig['ret10']>10) & sig['dist_ma20'].between(-5,0) & (sig['vol_ratio']<1.0))
split_check('C3a放宽(10日涨>10%, dist_ma20 -7~1, vol<1.5)', (sig['ret10']>10) & sig['dist_ma20'].between(-7,1) & (sig['vol_ratio']<1.5))
split_check('C3b(10日涨>8%, dist_ma20 -5~0, vol<1.2)', (sig['ret10']>8) & sig['dist_ma20'].between(-5,0) & (sig['vol_ratio']<1.2))