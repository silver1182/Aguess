import json
p = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\kline_day_long.json'
with open(p, encoding='utf-8') as f:
    data = json.load(f)
# 看前几只股票的最新日期
import collections
latest = collections.Counter()
for code in list(data.keys())[:50]:
    bars = data[code]
    if bars:
        latest[bars[-1]['date']] += 1
print('前50只最新日期分布:', dict(latest))
# 全局看有几只到了10-27/10-28
cnt2728 = 0
for code in list(data.keys())[:300]:
    bars = data[code]
    if bars and bars[-1]['date'] in ('2026-10-27','2026-10-28'):
        cnt2728 += 1
print('前300只含新日期:', cnt2728)
