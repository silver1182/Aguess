# -*- coding: utf-8 -*-
"""增量补齐 kline_day_long.json: 仅拉取缺失日期(2026-10-27起), 保留已有历史"""
import json, time, requests, urllib3, sys
urllib3.disable_warnings()

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
LONG = base + r'\temp\kline_day_long.json'
BEG = '20261020'   # 多拉一点兜底, 按日期去重
END = '20261028'

with open(LONG, encoding='utf-8') as f:
    data = json.load(f)
codes = list(data.keys())
print('待增量股票数:', len(codes))

sess = requests.Session()
sess.verify = False
sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

def em_kline(code, beg=BEG, end=END):
    secid = ('1.' if code.startswith('6') else '0.') + code
    url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get'
    params = {'secid': secid, 'fields1': 'f1,f2,f3,f4,f5,f6',
              'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58',
              'klt': '101', 'fqt': '1', 'beg': beg, 'end': end}
    r = sess.get(url, params=params, timeout=15)
    kl = r.json().get('data', {}).get('klines') or []
    bars = []
    for line in kl:
        p = line.split(',')
        bars.append({'date': p[0], 'open': float(p[1]), 'close': float(p[2]),
                     'high': float(p[3]), 'low': float(p[4]),
                     'volume': float(p[5]), 'amount': float(p[6])})
    return bars

updated = 0
new_days = set()
for i, code in enumerate(codes):
    try:
        bars = em_kline(code)
        if bars:
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
    if (i+1) % 300 == 0:
        print(f'进度 {i+1}/{len(codes)} 更新{updated} 新日期{len(new_days)}')
        time.sleep(0.5)

with open(LONG, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False)
print(f'完成: 更新{updated} 新增日期{sorted(new_days)}')
