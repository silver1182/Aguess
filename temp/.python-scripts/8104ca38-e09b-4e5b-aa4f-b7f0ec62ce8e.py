import requests, json
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
cache_file = base + r'\temp\kline_cache_em.json'
cache = json.load(open(cache_file, encoding='utf-8'))
empty_codes = [c for c,v in cache.items() if not v or len(v)<=20]
print('空记录:', len(empty_codes), empty_codes[:15])

s = requests.Session(); s.trust_env = False
for code in empty_codes[:6]:
    secid = ('1.' if code.startswith('6') else '0.') + code
    url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get'
    params = {'secid': secid, 'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
              'fields1': 'f1,f2,f3,f4,f5,f6',
              'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
              'klt': '101', 'fqt': '1', 'end': '20500101', 'lmt': '160'}
    headers = {'User-Agent':'Mozilla/5.0','Referer':'https://quote.eastmoney.com/'}
    try:
        r = s.get(url, params=params, headers=headers, timeout=10)
        j = r.json()
        klines = (j.get('data') or {}).get('klines')
        print(code, 'rc=', j.get('rc'), 'data?', bool(klines), '行数', len(klines) if klines else 0)
    except Exception as e:
        print(code, 'EXC', str(e)[:80])