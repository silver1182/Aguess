# -*- coding: utf-8 -*-
"""用thsdk批量拉取主板两年日K, 分批落盘续传"""
import json, time, sys, os
from thsdk import api

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
temp = base + r'\temp'
BATCH = 200
START_ARG = int(sys.argv[1]) if len(sys.argv) > 1 else 0

with open(temp + r'\kline_cache_em.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)
codes = list(cache.keys())

api.auth()
def ths_code(code):
    return ('USHA' if code.startswith('6') else 'USZA') + code

end = min(START_ARG + BATCH, len(codes))
out = {}
fail = []
for i in range(START_ARG, end):
    code = codes[i]
    try:
        df = api.get_price(ths_code(code), start_date='2024-01-01', end_date='2026-10-26')
        if df is not None and len(df):
            bars = [{'date': str(idx)[:10], 'open': float(r['open']), 'high': float(r['high']),
                     'low': float(r['low']), 'close': float(r['close']),
                     'volume': float(r['volume']), 'amount': float(r['turnover'])}
                    for idx, r in df.iterrows()]
            out[code] = bars
        else:
            fail.append((code, 'empty'))
    except Exception as e:
        fail.append((code, str(e)[:60]))
    time.sleep(0.05)

with open(temp + f'\kline_day_ths_part_{START_ARG}.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False)
with open(temp + r'\kline_day_ths_progress.txt', 'a', encoding='utf-8') as f:
    f.write(f'{START_ARG}:{end} ok={len(out)} fail={len(fail)}\n')
print(f'批 {START_ARG}-{end} 完成: 成功{len(out)} 失败{len(fail)} 示例:{fail[:3]}')
