import requests, urllib3, json
urllib3.disable_warnings()

# 测试腾讯
try:
    r = requests.get('https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh600519,day,2024-01-01,2026-10-26,640,qfq', timeout=10, verify=False)
    print('腾讯状态:', r.status_code, '长度:', len(r.text), r.text[:120])
except Exception as e:
    print('腾讯失败:', str(e)[:120])

# 测试东财
try:
    url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get'
    params = {'secid': '1.600519', 'fields1': 'f1,f2,f3,f4,f5,f6',
              'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58',
              'klt': '101', 'fqt': '1', 'beg': '20240101', 'end': '20261026'}
    r2 = requests.get(url, params=params, timeout=10, verify=False,
                      headers={'User-Agent': 'Mozilla/5.0'})
    print('东财状态:', r2.status_code, '长度:', len(r2.text), r2.text[:120])
except Exception as e:
    print('东财失败:', str(e)[:120])
