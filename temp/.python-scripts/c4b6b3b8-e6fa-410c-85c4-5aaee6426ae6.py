import json
temp = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp'
with open(temp + r'\kline_day_long.json', encoding='utf-8') as f:
    merged = json.load(f)
print('总数:', len(merged))
ks = list(merged.keys())
print('前10键:', ks[:10])
print('后10键:', ks[-10:])
# 找600519
hit = [k for k in ks if '600519' in k]
print('600519命中:', hit)
c = ks[0]
print('样本', c, merged[c][0]['date'], merged[c][-1]['date'], '根数:', len(merged[c]))
import statistics
lens = [len(v) for v in merged.values()]
print('根数 min/med/max:', min(lens), statistics.median(lens), max(lens))
