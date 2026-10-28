# -*- coding: utf-8 -*-
"""thsdk 增量补齐 kline_day_long.json: 只拉缺失日期(>=2026-10-27), 保留已有历史"""
import json, time
from thsdk import api

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
LONG = base + r'\temp\kline_day_long.json'

with open(LONG, encoding='utf-8') as f:
    data = json.load(f)
codes = list(data.keys())
print('股票数:', len(codes))

api.auth()
def ths_code(code):
    return ('USHA' if code.startswith('6') else 'USZA') + code

updated = 0
new_days = set()
for i, code in enumerate(codes):
    try:
        df = api.get_price(ths_code(code), start_date='2026-10-27', end_date='2026-10-28')
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
                    new_days.add(b['date'])
            if added:
                data[code] = sorted(old_by_date.values(), key=lambda x: x['date'])
                updated += 1
    except Exception as e:
        print('ERR', code, str(e)[:50])
    time.sleep(0.02)

with open(LONG, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)
print(f'完成: 更新{updated} 新增日期{sorted(new_days)}')
