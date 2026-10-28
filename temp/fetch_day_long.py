# -*- coding: utf-8 -*-
"""拉取1650只主板股 2024-01-01 至今日K，合并进 long 缓存"""
import json, time, sys
sys.path.insert(0, r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp')
from a_stock_data import tencent_kline

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
with open(base + r'\temp\kline_cache_em.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)
codes = list(cache.keys())
print('待拉股票数:', len(codes))

long_cache = {}
fail = []
for i, code in enumerate(codes):
    try:
        bars = tencent_kline(code, period='day', start='2024-01-01', end='2026-10-26')
        if bars is not None and len(bars) > 0:
            long_cache[code] = bars.to_dict('records') if hasattr(bars, 'to_dict') else bars
    except Exception as e:
        fail.append((code, str(e)[:60]))
    if (i+1) % 200 == 0:
        print(f'进度 {i+1}/{len(codes)} 成功{len(long_cache)} 失败{len(fail)}')
        time.sleep(0.5)

with open(base + r'\temp\kline_day_long.json', 'w', encoding='utf-8') as f:
    json.dump(long_cache, f, ensure_ascii=False)
print(f'完成: 成功{len(long_cache)} 失败{len(fail)}')
if fail: print('失败示例:', fail[:5])
