# -*- coding: utf-8 -*-
"""
迭代1: 扩展历史样本至 2022-01 (iter1_extend_2022.py)
====================================================
用 thsdk 对全部主板股补拉 2022-01-01 ~ 2023-12-31 日K, 与既有 2024-2026 缓存合并,
输出新文件 kline_day_long_v2.json (不覆盖旧缓存)。按日期去重, 保留后合并排序。
"""
import json, time, sys, os
from thsdk import api

BASE = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
TEMP = BASE + r'\temp'
SRC = TEMP + r'\kline_day_long.json'
DST = TEMP + r'\kline_day_long_v2.json'

START, END = '2022-01-01', '2023-12-31'

with open(SRC, encoding='utf-8') as f:
    data = json.load(f)
codes = list(data.keys())
print('股票数:', len(codes), flush=True)

api.auth()
def ths_code(code):
    return ('USHA' if code.startswith('6') else 'USZA') + code

ok = 0; fail = []; new_bars_total = 0
for i, code in enumerate(codes):
    try:
        df = api.get_price(ths_code(code), start_date=START, end_date=END)
        if df is not None and len(df):
            bars = [{'date': str(idx)[:10], 'open': float(r['open']), 'high': float(r['high']),
                     'low': float(r['low']), 'close': float(r['close']),
                     'volume': float(r['volume']), 'amount': float(r['turnover'])}
                    for idx, r in df.iterrows()]
            old = data.get(code) or []
            old_by_date = {b['date']: b for b in old}
            added = 0
            for b in bars:
                if b['date'] not in old_by_date:
                    old_by_date[b['date']] = b
                    added += 1
            if added:
                data[code] = sorted(old_by_date.values(), key=lambda x: x['date'])
                new_bars_total += added
            ok += 1
        else:
            fail.append((code, 'empty'))
    except Exception as e:
        fail.append((code, str(e)[:60]))
    if (i + 1) % 300 == 0:
        print(f'进度 {i+1}/{len(codes)} ok={ok} fail={len(fail)} 新增K线={new_bars_total}', flush=True)
    time.sleep(0.02)

with open(DST, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)
print(f'完成: ok={ok} fail={len(fail)} 新增K线={new_bars_total}')
print('失败示例:', fail[:10])
print('输出:', DST)
