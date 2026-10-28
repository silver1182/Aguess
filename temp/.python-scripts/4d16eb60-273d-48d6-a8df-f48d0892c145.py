import json, pandas as pd, numpy as np

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
with open(base + r'\temp\kline_cache_em.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

rows = []
for code, bars in cache.items():
    for i in range(1, len(bars)-2):
        prev = bars[i-1]; b = bars[i]; nb = bars[i+1]
        if b['date'] < '2026-07-01': continue
        pct = (b['close'] / prev['close'] - 1) * 100
        npct = (nb['close'] / b['close'] - 1) * 100
        nh = (nb['high'] / b['close'] - 1) * 100
        rows.append({
            'date': b['date'], 'code': code, 'pct': pct, 'npct': npct, 'nh': nh,
            'vol': b['volume'], 'close': b['close'], 'nclose': nb['close'],
        })
df = pd.DataFrame(rows)

df['n_limit'] = (df['npct'] >= 9.8).astype(int)
df['n_big'] = (df['npct'] >= 5).astype(int)
df['n_high5'] = (df['nh'] >= 5).astype(int)

print('全市场次日涨停概率: %.3f pct' % (df['n_limit'].mean()*100))
print('全市场次日大涨5pct+概率: %.2f pct' % (df['n_big'].mean()*100))
print('全市场次日盘中摸5pct概率: %.2f pct' % (df['n_high5'].mean()*100))
print()

for lo, hi, lab in [(9, 10, '昨日涨停9.8%+'), (7, 9.8, '昨日7~9.8%'), (5, 7, '昨日5~7%'), (3, 5, '昨日3~5%'), (0, 3, '昨日0~3%')]:
    sub = df[(df['pct']>=lo) & (df['pct']<hi)]
    if len(sub) < 30: continue
    print('%s: 样本%d | 次日涨停%.2f pct | 次日大涨5pct+%.2f pct | 次日盘中摸5pct+%.2f pct' % (
        lab, len(sub), sub['n_limit'].mean()*100, sub['n_big'].mean()*100, sub['n_high5'].mean()*100))