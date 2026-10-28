# -*- coding: utf-8 -*-
"""短线特征信号初筛: 稀缺特征 -> 次日开盘买可成交收益"""
import json, pandas as pd, numpy as np

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
with open(base + r'\temp\kline_cache_em.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

rows = []
for code, bars in cache.items():
    for b in bars:
        b['code'] = code
        rows.append(b)
df = pd.DataFrame(rows)
df['date'] = pd.to_datetime(df['date'])
df = df[df['close'].notna()].sort_values(['code','date']).reset_index(drop=True)
g = df.groupby('code')
df['prev_close'] = g['close'].shift(1)
df['prev_vol'] = g['volume'].shift(1)
df['pct'] = df['close']/df['prev_close']-1
df['vol_ratio'] = df['volume']/df['prev_vol']
df['ret_5d'] = df['close']/df['close'].shift(5)-1
df['high_20'] = g['close'].transform(lambda x: x.rolling(20).max().shift(1))
df['low_20'] = g['close'].transform(lambda x: x.rolling(20).min().shift(1))
df['range_20'] = (df['high_20']-df['low_20'])/df['low_20']
df['low_pct'] = df['low']/df['prev_close']-1
df['intraday_low_pct'] = df['low']/df['open']-1

# 次日开盘买入持有N日收益
nxt = df.groupby('code')[['open','close']].shift(-1)
df['nxt_open'] = nxt['open']; df['nxt_close'] = nxt['close']
df['r1'] = df['nxt_close']/df['nxt_open']-1   # 次日开盘买->次日收盘卖
# 3日收益: T+1收盘
t2 = df.groupby('code')[['close']].shift(-2)
df['r3'] = t2['close']/df['nxt_open']-1       # 次日开盘买->T+2收盘卖

# 信号定义 (信号日=当日, 次日开盘买入)
sig_defs = {
    'F1超跌反弹': lambda s: (s['ret_5d'] < -0.12) & (s['pct'] > 0.02) & (s['vol_ratio'] > 1.3),
    'F2平台突破': lambda s: (s['range_20'] < 0.20) & (s['close'] > s['high_20']) & (s['vol_ratio'] > 1.5) & (s['pct'] > 0.02),
    'F3长下影反转': lambda s: (s['low_pct'] < -0.05) & (s['close'] > s['open']) & ((s['close']-s['low'])/s['prev_close'] > 0.03),
    'F4放量异动': lambda s: (s['vol_ratio'] > 2.5) & (s['pct'] > 0.03) & (s['pct'] < 0.07),
    'F5连续阴后阳': lambda s: (s['close']/s['close'].shift(3)-1 < -0.08) & (s['pct'] > 0.03),
}

print('=== 特征信号初筛 (2026-03~10-26, 1650主板) ===')
for name, fn in sig_defs.items():
    sig = df[fn(df)].dropna(subset=['nxt_open'])
    n = len(sig)
    if n == 0:
        print(f'{name}: 0信号'); continue
    r1, r3 = sig['r1'].mean(), sig['r3'].mean()
    win1 = (sig['r1']>0).mean(); win3 = (sig['r3']>0).mean()
    # 排除涨停买不进: 次日开盘涨停(>9.5%)视为不可成交
    ok = sig[sig['nxt_open']/sig['close']-1 < 0.095]
    r1o, r3o = ok['r1'].mean(), ok['r3'].mean()
    print(f'{name}: 信号{n}个(日均{n/160:.1f}) | 次日卖 r1 {r1*100:+.2f}% 胜率{win1*100:.0f}% | 3日卖 r3 {r3*100:+.2f}% 胜率{win3*100:.0f}% | 可成交子集 n={len(ok)} r1 {r1o*100:+.2f}% r3 {r3o*100:+.2f}%')

# 随机对照: 全市场随机选同样数量股票的次日收益
all_nxt = df.dropna(subset=['nxt_open'])
rng = np.random.default_rng(42)
bench = []
for _ in range(200):
    idx = rng.choice(len(all_nxt), size=min(300, len(all_nxt)), replace=False)
    bench.append(all_nxt.iloc[idx]['r1'].mean())
print(f'\n随机对照(300样本/次,200次): 次日卖均值 {np.mean(bench)*100:+.2f}% | 全样本均值 {all_nxt["r1"].mean()*100:+.2f}%')
