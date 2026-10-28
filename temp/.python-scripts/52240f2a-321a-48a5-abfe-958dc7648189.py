import requests, json, time, os

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
codes = json.load(open(base + r'\temp\backtest_codes_ext.json'))
cache_file = base + r'\temp\kline_cache_em.json'
cache = json.load(open(cache_file, encoding='utf-8'))

empty_codes = [c for c in codes if c not in cache or not cache.get(c)]
print('空记录数:', len(empty_codes))

def em_kline(code, n=160):
    secid = ('1.' if code.startswith('6') else '0.') + code
    url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get'
    params = {'secid': secid, 'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
              'fields1': 'f1,f2,f3,f4,f5,f6',
              'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
              'klt': '101', 'fqt': '1', 'end': '20500101', 'lmt': str(n)}
    headers = {'User-Agent':'Mozilla/5.0','Referer':'https://quote.eastmoney.com/'}
    r = requests.get(url, params=params, headers=headers, timeout=8)
    j = r.json()
    if j.get('data') and j['data'].get('klines'):
        out = []
        for x in j['data']['klines']:
            p = x.split(',')
            out.append({'date': p[0], 'open': float(p[1]), 'close': float(p[2]),
                        'high': float(p[3]), 'low': float(p[4]),
                        'volume': float(p[5]), 'amount': float(p[6]), 'pct': float(p[8])})
        return out
    return None

# 测试前10个空记录
for c in empty_codes[:10]:
    k = em_kline(c, 5)
    print(c, 'OK' if k else 'FAIL')
    time.sleep(0.15)