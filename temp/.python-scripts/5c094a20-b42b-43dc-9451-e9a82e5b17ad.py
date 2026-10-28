import json, random
p = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\kline_day_long.json'
with open(p, encoding='utf-8') as f:
    data = json.load(f)
codes = list(data.keys())
print('股票数', len(codes))
# 抽样10只看日期范围
for c in random.sample(codes, 8):
    bars = data[c]
    print(c, len(bars), bars[0]['date'], bars[-1]['date'])
# 整体日期范围：取每只首末日期太慢，抽样估计
all_dates = set()
for c in codes[:50]:
    for b in data[c]:
        all_dates.add(b['date'])
print('抽样50只的日期数', len(all_dates), 'min', min(all_dates), 'max', max(all_dates))
