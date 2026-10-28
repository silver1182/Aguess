import requests, json, time

def em_kline(code, n=120):
    # 东财日K：secid 0.000001(深) 1.600000(沪)
    secid = ('1.' if code.startswith('6') else '0.') + code
    url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get'
    params = {
        'secid': secid, 'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
        'fields1': 'f1,f2,f3,f4,f5,f6',
        'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
        'klt': '101', 'fqt': '1', 'end': '20500101', 'lmt': str(n)
    }
    headers = {'User-Agent':'Mozilla/5.0','Referer':'https://quote.eastmoney.com/'}
    r = requests.get(url, params=params, headers=headers, timeout=10)
    j = r.json()
    if j.get('data') and j['data'].get('klines'):
        rows = [x.split(',') for x in j['data']['klines']]
        return rows
    return None

for code in ['600000','000001','002489']:
    k = em_kline(code, 5)
    print(code, 'OK' if k else 'FAIL', k[-1] if k else '')
    time.sleep(0.2)