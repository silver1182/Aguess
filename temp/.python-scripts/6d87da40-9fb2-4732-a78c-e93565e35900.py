# -*- coding: utf-8 -*-
import json, pandas as pd, numpy as np
temp = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp'
with open(temp + r'\kline_day_long.json', encoding='utf-8') as f:
    data = json.load(f)
print('股票数:', len(data))
codes = list(data.keys())[:3]
for c in codes:
    bars = data[c]
    print('\ncode=', c, 'bars=', len(bars))
    print('前3条:', bars[:3])
    print('后3条:', bars[-3:])
# 检查日期排序
ok = 0; bad = 0
for c, bars in data.items():
    dates = [b['date'] for b in bars]
    if dates == sorted(dates): ok += 1
    else: bad += 1
print(f'\n日期升序 {ok} 只, 乱序 {bad} 只')
