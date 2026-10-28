import json
p = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\kline_day_long.json'
with open(p, encoding='utf-8') as f:
    data = json.load(f)
print('total codes:', len(data))
# 看几只的结构
for code, bars in list(data.items())[:2]:
    print(code, 'len=', len(bars), 'last3=', [(b['date'], b['close']) for b in bars[-3:]])
# 全局最后日期分布
from collections import Counter
last = Counter(b[-1]['date'] for b in data.values() if b)
print('last date dist:', last.most_common(5))
# 找出10-26(周一)涨停(>=9.5%)的候选池
cands = []
for code, bars in data.items():
    if not bars: continue
    # 找10-26那根
    for i, b in enumerate(bars):
        if b['date'] == '2026-10-26' and i >= 1:
            prev_close = bars[i-1]['close']
            pct = (b['close'] / prev_close - 1) * 100
            if pct >= 9.5:
                cands.append((code, round(pct, 2)))
            break
print('10-26 涨停候选数:', len(cands))
print(cands[:50])
