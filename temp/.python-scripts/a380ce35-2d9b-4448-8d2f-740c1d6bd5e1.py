import json, os
TEMP = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp'
p = TEMP + r'\dragon_hist.json'
print('size(MB):', round(os.path.getsize(p)/1e6, 2))
hist = json.load(open(p, encoding='utf-8'))
print('交易日覆盖:', len(hist))
# 数据量统计
total_rows = sum(len(v) for v in hist.values())
print('总记录数:', total_rows)
# 每交易日条数分布
import statistics
cnts = [len(v) for v in hist.values()]
print('每日条数 min/median/max:', min(cnts), statistics.median(cnts), max(cnts))
# 空交易日
empty = [d for d, v in hist.items() if not v]
print('空交易日数:', len(empty), empty[:10])
# 抽样看结构
import itertools
d = '2024-02-05'
print('2024-02-05 条数:', len(hist.get(d, {})), '示例:', list(hist[d].items())[:2] if hist.get(d) else None)
