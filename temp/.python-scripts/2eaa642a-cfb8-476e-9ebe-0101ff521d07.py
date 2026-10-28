import json, requests, urllib3
urllib3.disable_warnings()
sess = requests.Session()
sess.verify = False
sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

# 1. 东财涨停池接口
print('=== 涨停池 ===')
url = 'https://push2ex.eastmoney.com/getTopicZTPool'
params = {'ut': '7eea3edcaed734bea9cbfc24409ed989', 'dpt': 'wz.ztzt', 'Pageindex': 0, 'pagesize': 10, 'sort': 'fbt:asc', 'date': '20261028'}
try:
    r = sess.get(url, params=params, timeout=10)
    d = r.json()
    print('keys:', list(d.keys()))
    data = d.get('data') or {}
    print('pool keys:', list(data.keys()) if isinstance(data, dict) else type(data))
    if isinstance(data, dict) and data.get('pool'):
        print('示例:', json.dumps(data['pool'][0], ensure_ascii=False)[:300])
        print('涨停家数:', data.get('tc'))
except Exception as e:
    print('err:', e)

# 2. 东财股吧人气榜
print('\n=== 股吧人气榜 ===')
try:
    url2 = 'https://gbapi.eastmoney.com/guba/list?code=0&flag=3&page=1&num=10&sort=1&ut='
    r2 = sess.get(url2, timeout=10)
    print('status:', r2.status_code, 'len:', len(r2.text))
    print(r2.text[:300])
except Exception as e:
    print('err2:', e)
