# -*- coding: utf-8 -*-
"""拉取1650只主板股 2024-01-01 至今日K (东财接口)"""
import json, time, requests, urllib3
urllib3.disable_warnings()

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
with open(base + r'\temp\kline_cache_em.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)
codes = list(cache.keys())
print('待拉股票数:', len(codes))

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
    bars = []
    for line in kl:
        p = line.split(',')
        # date, open, close, high, low, volume, amount, amplitude
        bars.append({'date': p[0], 'open': float(p[1]), 'close': float(p[2]),
                     'high': float(p[3]), 'low': float(p[4]),
                     'volume': float(p[5]), 'amount': float(p[6])})
    return bars

long_cache = {}
fail = []
for i, code in enumerate(codes):
    try:
        bars = em_kline(code)
        if bars:
            long_cache[code] = bars
    except Exception as e:
        fail.append((code, str(e)[:60]))
    if (i+1) % 200 == 0:
        print(f'进度 {i+1}/{len(codes)} 成功{len(long_cache)} 失败{len(fail)}')
        time.sleep(0.5)

with open(base + r'\temp\kline_day_long.json', 'w', encoding='utf-8') as f:
    json.dump(long_cache, f, ensure_ascii=False)
print(f'完成: 成功{len(long_cache)} 失败{len(fail)}')
if fail: print('失败示例:', fail[:5])
