import json, glob, os
temp = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp'
merged = {}
for p in sorted(glob.glob(temp + r'\kline_day_ths_part_*.json'), key=lambda x: int(x.split('part_')[1].split('.')[0])):
    with open(p, encoding='utf-8') as f:
        d = json.load(f)
    merged.update(d)
out = temp + r'\kline_day_long.json'
with open(out, 'w', encoding='utf-8') as f:
    json.dump(merged, f, ensure_ascii=False)
print('总股票数:', len(merged))
# 样本检查
c = '600519'
print(c, merged[c][0]['date'], merged[c][-1]['date'], '根数:', len(merged[c]))
# 统计每只根数分布
lens = [len(v) for v in merged.values()]
import statistics
print('根数 min/med/max:', min(lens), statistics.median(lens), max(lens))
