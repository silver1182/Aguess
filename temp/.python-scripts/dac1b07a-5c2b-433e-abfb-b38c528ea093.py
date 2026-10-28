import json, requests, urllib3
urllib3.disable_warnings()
sess = requests.Session()
sess.verify = False
sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

# 跌停池
print('=== 跌停池 ===')
try:
    url = 'https://push2ex.eastmoney.com/getTopicDTPool'
    params = {'ut': '7eea3edcaed734bea9cbfc24409ed989', 'dpt': 'wz.ztzt', 'Pageindex': 0, 'pagesize': 5, 'sort': 'fund:asc', 'date': '20261028'}
    d = sess.get(url, params=params, timeout=10).json()
    data = d.get('data') or {}
    print('跌停家数:', data.get('tc') if isinstance(data, dict) else '?')
    if isinstance(data, dict) and data.get('pool'):
        print('示例:', json.dumps(data['pool'][0], ensure_ascii=False)[:250])
except Exception as e:
    print('err:', e)

# 炸板池
print('\n=== 炸板池 ===')
try:
    url = 'https://push2ex.eastmoney.com/getTopicZBPool'
    params = {'ut': '7eea3edcaed734bea9cbfc24409ed989', 'dpt': 'wz.ztzt', 'Pageindex': 0, 'pagesize': 5, 'sort': 'fbt:asc', 'date': '20261028'}
    d = sess.get(url, params=params, timeout=10).json()
    data = d.get('data') or {}
    print('炸板家数:', data.get('tc') if isinstance(data, dict) else '?')
    if isinstance(data, dict) and data.get('pool'):
        print('示例:', json.dumps(data['pool'][0], ensure_ascii=False)[:250])
except Exception as e:
    print('err:', e)

# 涨停池全量行业汇总(判断热点板块)
print('\n=== 涨停池行业分布 ===')
try:
    url = 'https://push2ex.eastmoney.com/getTopicZTPool'
    params = {'ut': '7eea3edcaed734bea9cbfc24409ed989', 'dpt': 'wz.ztzt', 'Pageindex': 0, 'pagesize': 500, 'sort': 'fbt:asc', 'date': '20261028'}
    d = sess.get(url, params=params, timeout=10).json()
    pool = (d.get('data') or {}).get('pool') or []
    from collections import Counter
    ind = Counter(p.get('hybk','?') for p in pool)
    print('行业分布Top8:', ind.most_common(8))
    lbc = Counter(p.get('lbc',0) for p in pool)
    print('连板分布:', sorted(lbc.items()))
except Exception as e:
    print('err:', e)
