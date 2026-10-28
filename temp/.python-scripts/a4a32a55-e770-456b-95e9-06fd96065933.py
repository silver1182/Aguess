import requests, json, time, os

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
codes = json.load(open(base + r'\temp\backtest_codes_ext.json'))
cache_file = base + r'\temp\kline_cache_em.json'
cache = json.load(open(cache_file, encoding='utf-8'))

s = requests.Session(); s.trust_env = False
def em_kline(code, n=160):
    secid = ('1.' if code.startswith('6') else '0.') + code
    url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get'
    params = {'secid': secid, 'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
              'fields1': 'f1,f2,f3,f4,f5,f6',
              'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
              'klt': '101', 'fqt': '1', 'end': '20500101', 'lmt': str(n)}
    headers = {'User-Agent':'Mozilla/5.0','Referer':'https://quote.eastmoney.com/'}
    r = s.get(url, params=params, headers=headers, timeout=10)
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

empty_codes = [c for c in codes if not cache.get(c) or len(cache.get(c,[]))<=20]
print('需重拉:', len(empty_codes))
ok = 0
for i, code in enumerate(empty_codes[:250]):
    try:
        k = em_kline(code)
        if k and len(k) > 20:
            cache[code] = k; ok += 1
        else:
            cache[code] = []
    except Exception as e:
        cache[code] = []
    if (i+1) % 100 == 0:
        json.dump(cache, open(cache_file,'w',encoding='utf-8'), ensure_ascii=False)
        print(f'进度 {i+1}/{min(250,len(empty_codes))} 本批成功 {ok}')
    time.sleep(0.08)
json.dump(cache, open(cache_file,'w',encoding='utf-8'), ensure_ascii=False)
have = sum(1 for v in cache.values() if v and len(v) > 20)
print('批次完成, 总有效:', have, '/', len(codes))