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
df['dist_ma5'] = (df['close'] / df['ma5'] - 1) * 100
df['ma20_up'] = df['ma20'] > df.groupby('code')['ma20'].shift(5)
df['ma60_up'] = df['ma60'] > df.groupby('code')['ma60'].shift(5)
df['ret10'] = df.groupby('code')['close'].pct_change(10) * 100
df['ret20'] = df.groupby('code')['close'].pct_change(20) * 100

g = df.groupby('code')
df['open_nx'] = g['open'].shift(-1)
for h in [3, 5, 10, 20]:
    df[f'buyh{h}'] = (g['open'].shift(-(1+h)) / df['open_nx'] - 1) * 100

sig = df[(df['date'] >= '2026-07-01') & (df['date'] <= '2026-10-23')].dropna(subset=['buyh5', 'buyh10']).copy()
sig['date'] = sig['date'].dt.date

def run(name, mask, hlist=[5,10,20], min_trades=50):
    t = sig[mask].dropna(subset=[f'buyh{h}' for h in hlist])
    if len(t) < min_trades:
        print(f'=== {name} === 信号数 {len(t)} (不足,跳过)')
        return None
    print(f'=== {name} === 信号数:{len(t)} 股票:{t["code"].nunique()}')
    for h in hlist:
        m, w = t[f'buyh{h}'].mean(), (t[f'buyh{h}']>0).mean()*100
        bm = sig[f'buyh{h}'].mean()
        print(f'  持有{h}日: 均值 {m:.2f}%  胜率 {w:.1f}%  超额 {m-bm:+.2f}%')
    return t

# C4 补跑
g10 = sig.groupby('code')['pct'].transform(lambda x: x.rolling(10).max())
t4 = run('C4 涨停后回调MA5/MA10(近10日涨停+)',
    (g10>=9.5) & ((sig['dist_ma5'].between(-3,1)) | (sig['dist_ma10'].between(-3,1))) & (sig['vol_ratio']<1.2))

# C3 参数敏感度：放宽回调深度/缩量阈值，扩大样本
print('\n---- C3 参数敏感度(验证稳健性) ----')
run('C3a 深度回调MA20放宽(10日涨>10%, dist_ma20 -7~1, vol<1.5)',
    (sig['ret10']>10) & sig['dist_ma20'].between(-7,1) & (sig['vol_ratio']<1.5))
run('C3b 深度回调MA20(10日涨>8%, dist_ma20 -5~0, vol<1.2)',
    (sig['ret10']>8) & sig['dist_ma20'].between(-5,0) & (sig['vol_ratio']<1.2))
run('C3c 深度回调MA20(20日涨>15%, dist_ma20 -5~0, vol<1.0)',
    (sig['ret20']>15) & sig['dist_ma20'].between(-5,0) & (sig['vol_ratio']<1.0))
run('C3d 深度回调MA20(10日涨>15%, dist_ma20 -8~0, vol<1.5)',
    (sig['ret10']>15) & sig['dist_ma20'].between(-8,0) & (sig['vol_ratio']<1.5))

# 分时段检验：7-8月 vs 9-10月
print('\n---- 分时段稳健性检验 ----')
for name, mask in [
    ('A1 趋势回踩MA20', (sig['close']>sig['ma20']) & sig['ma20_up'] & sig['dist_ma20'].between(-3,1) & (sig['vol_ratio']<1.2)),
    ('A4 破MA20回调低吸', sig['ma20_up'] & sig['dist_ma20'].between(-4,-1) & (sig['vol_ratio']<1.0)),
    ('C2 大涨基因回调MA10', (sig.groupby('code')['pct'].transform(lambda x: x.rolling(20).max())>=7) & sig['dist_ma10'].between(-3,1) & (sig['vol_ratio']<1.2)),
    ('C3 强势深度回调MA20', (sig['ret10']>10) & sig['dist_ma20'].between(-5,0) & (sig['vol_ratio']<1.0)),
]:
    t = sig[mask]
    print(f'\n{name}: 总{n:.0f}'.replace('n', str(len(t))))
    for lo, hi in [('2026-07-01','2026-08-31'), ('2026-09-01','2026-10-23')]:
        sub = t[(t['date'] >= pd.Timestamp(lo).date()) & (t['date'] <= pd.Timestamp(hi).date())]
        if len(sub) < 10:
            print(f'  {lo}~{hi}: 样本{len(sub)}过少')
            continue
        for h in [5, 10]:
            m, w = sub[f'buyh{h}'].mean(), (sub[f'buyh{h}']>0).mean()*100
            print(f'  {lo}~{hi} 持有{h}日: 均值 {m:.2f}%  胜率 {w:.1f}%  (n={len(sub)})')