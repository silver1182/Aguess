# -*- coding: utf-8 -*-
import json, os, collections

BASE = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
TEMP = BASE + r'\temp'
OUT = BASE + r'\output'

with open(TEMP + r'\kline_day_long.json', encoding='utf-8') as f:
    data = json.load(f)

print('股票数:', len(data))
sample_code = next(iter(data))
sample = data[sample_code]
print('样本代码:', sample_code, '根数:', len(sample))
print('样本字段:', list(sample[0].keys()))
print('样本首根:', sample[0])
print('样本末根:', sample[-1])

# 最新日期统计
last_dates = collections.Counter()
for code, bars in data.items():
    if bars:
        last_dates[bars[-1]['date']] += 1
print('最新日期分布:', dict(last_dates.most_common(5)))

# 主板筛选统计
codes = list(data.keys())
main_board = [c for c in codes if c.startswith(('60','00')) and not c.startswith(('688','30'))]
print('主板60/00(排除30/688)数量:', len(main_board))

# 检查是否有name字段
has_name = any('name' in b for b in data[sample_code][:1])
print('缓存含name字段:', has_name)

# 检查 output 目录
os.makedirs(OUT, exist_ok=True)
print('output 存在:', os.path.isdir(OUT))
print('最新 mkt_state_latest.json 存在:', os.path.exists(TEMP + r'\mkt_state_latest.json'))
print('最新 mkt_sentiment_latest.json 存在:', os.path.exists(TEMP + r'\mkt_sentiment_latest.json'))
