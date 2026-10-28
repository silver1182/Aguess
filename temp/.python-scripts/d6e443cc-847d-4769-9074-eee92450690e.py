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

for w in [5, 10, 20]:
    df[f'ma{w}'] = df.groupby('code')['close'].transform(lambda x: x.rolling(w).mean())
df['vol_ma10'] = df.groupby('code')['volume'].transform(lambda x: x.rolling(10).mean())
df['vol_ratio'] = df['volume'] / df['vol_ma10']
df['dist_ma20'] = (df['close'] / df['ma20'] - 1) * 100
df['ma20_up5'] = df['ma20'] > df.groupby('code')['ma20'].shift(5)

last_date = df['date'].max()
print('缓存最后交易日:', last_date.date())

last = df[df['date'] == last_date].copy()

# A1: 站上MA20 + MA20向上 + 回踩MA20附近(-3~1%) + 缩量
a1 = last['ma20_up5'] & (last['close']>last['ma20']) & last['dist_ma20'].between(-3,1) & (last['vol_ratio']<1.2)
# A4: MA20向上 + 破MA20 1-4% + 缩量
a4 = last['ma20_up5'] & last['dist_ma20'].between(-4,-1) & (last['vol_ratio']<1.0)
# A合并
ac = last['ma20_up5'] & last['dist_ma20'].between(-4,1) & (last['vol_ratio']<1.2)

cand1 = last[a1][['code','close','dist_ma20','vol_ratio']].sort_values('dist_ma20', ascending=False)
cand4 = last[a4][['code','close','dist_ma20','vol_ratio']].sort_values('dist_ma20')

print(f'\nA1(站上MA20回踩) 候选 {len(cand1)} 只:')
print(cand1.head(30).to_string(index=False))

print(f'\nA4(破MA20低吸) 候选 {len(cand4)} 只:')
print(cand4.head(30).to_string(index=False))

print(f'\nA合并 候选 {len(cand)} 只 (共{ac.sum()})')