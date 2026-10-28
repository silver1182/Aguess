import requests, json, time, sys
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
sys.path.insert(0, base + r'\temp')
import a_stock_data as a

# 测腾讯恢复
try:
    k = a.tencent_kline('600246', period='day', count=5)
    print('腾讯恢复:', 'OK' if k is not None and len(k)>0 else 'empty')
except Exception as e:
    print('腾讯仍限流')

time.sleep(30)
s = requests.Session(); s.trust_env = False
for code in ['600246','600250','600261','600262']:
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
        kl = (j.get('data') or {}).get('klines')
        print(code, 'OK' if kl else 'FAIL', len(kl) if kl else 0)
    except Exception as e:
        print(code, 'EXC', str(e)[:60])
    time.sleep(1)