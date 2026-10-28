import json, requests, urllib3, re
urllib3.disable_warnings()
sess = requests.Session()
sess.verify = False
sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

# 1. 雪球热帖
print('=== 雪球热帖 ===')
try:
    url = 'https://xueqiu.com/statuses/hot/listV2.json?since_id=-1&max_id=-1&size=10'
    r = sess.get(url, timeout=10, headers={'Referer': 'https://xueqiu.com/'})
    print('status', r.status_code, 'len', len(r.text))
    if r.status_code == 200:
        d = r.json()
        items = d.get('items') or []
        for it in items[:3]:
            s = it.get('original_status') or {}
            print('•', (s.get('title') or s.get('description') or '')[:60])
except Exception as e:
    print('err:', e)

# 2. 雪球股票热度榜
print('\n=== 雪球热度榜 ===')
try:
    url = 'https://xueqiu.com/query/v1/symbol/search_rank.json?size=10&type=0&code='
    r = sess.get(url, timeout=10, headers={'Referer': 'https://xueqiu.com/'})
    print('status', r.status_code, 'len', len(r.text))
    if r.status_code == 200:
        print(r.text[:200])
except Exception as e:
    print('err:', e)

# 3. 东财个股人气榜另一接口
print('\n=== 东财人气榜 alt ===')
for u in ['https://emappdata.eastmoney.com/stockrank/getAllCurrentList',
          'https://push2.eastmoney.com/api/qt/stock/rank/get?secid=1.600519&sort=0&order=desc&fields=f12,f14,f2,f3&page=1&pagesize=10']:
    try:
        if 'emappdata' in u:
            r = sess.post(u, json={'appId':'appId01','globalId':'786e4c21-70dc-435a-93bb-38','pageNo':1,'pageSize':10}, timeout=10, headers={'Referer':'https://data.eastmoney.com/'})
        else:
            r = sess.get(u, timeout=10)
        print(u[:60], '->', r.status_code, 'len', len(r.text))
        if r.status_code == 200:
            print(r.text[:200])
    except Exception as e:
        print(u[:60], 'err:', e)
