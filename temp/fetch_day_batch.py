# -*- coding: utf-8 -*-
"""东财日K续传拉取: 每次拉一批(默认250只), 进度存 progress.txt, 数据存 part_N.json"""
import json, os, time, sys, requests, urllib3
urllib3.disable_warnings()

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
temp = base + r'\temp'
BATCH = 250
START_ARG = int(sys.argv[1]) if len(sys.argv) > 1 else 0

with open(temp + r'\kline_cache_em.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)
codes = list(cache.keys())

sess = requests.Session()
sess.verify = False
sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

def em_kline(code, start='20240101', end='20261026'):
    secid = ('1.' if code.startswith('6') else '0.') + code
    url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get'
    params = {'secid': secid, 'fields1': 'f1,f2,f3,f4,f5,f6',
              'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58',
              'klt': '101', 'fqt': '1', 'beg': start, 'end': end}
    r = sess.get(url, params=params, timeout=15)
    data = r.json()
    kl = data.get('data', {}).get('klines') or []
    return [{'date': p[0], 'open': float(p[1]), 'close': float(p[2]),
             'high': float(p[3]), 'low': float(p[4]),
             'volume': float(p[5]), 'amount': float(p[6])}
            for p in (line.split(',') for line in kl)]

end = min(START_ARG + BATCH, len(codes))
out = {}
fail = []
for i in range(START_ARG, end):
    code = codes[i]
    try:
        bars = em_kline(code)
        if bars: out[code] = bars
        else: fail.append((code, 'empty'))
    except Exception as e:
        fail.append((code, str(e)[:60]))
    time.sleep(0.05)

with open(temp + f'\kline_day_part_{START_ARG}.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False)
with open(temp + r'\kline_day_progress.txt', 'a', encoding='utf-8') as f:
    f.write(f'{START_ARG}:{end} ok={len(out)} fail={len(fail)}\n')
print(f'批 {START_ARG}-{end} 完成: 成功{len(out)} 失败{len(fail)} 示例:{fail[:3]}')
