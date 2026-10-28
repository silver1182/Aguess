import requests, os
print('session proxies:', requests.Session().proxies)
print('trust_env:', requests.Session().trust_env)
# 尝试禁用代理
s = requests.Session()
s.trust_env = False
r = s.get('https://push2his.eastmoney.com/api/qt/stock/kline/get',
    params={'secid':'1.600000','ut':'fa5fd1943c7b386f172d6893dbfba10b','fields1':'f1,f2,f3,f4,f5,f6','fields2':'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61','klt':'101','fqt':'1','end':'20500101','lmt':'5'},
    headers={'User-Agent':'Mozilla/5.0','Referer':'https://quote.eastmoney.com/'}, timeout=8)
print('status:', r.status_code, r.text[:100])