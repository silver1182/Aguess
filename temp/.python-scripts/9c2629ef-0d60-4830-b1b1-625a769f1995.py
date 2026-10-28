import json, requests, urllib3
urllib3.disable_warnings()
sess = requests.Session()
sess.verify = False
sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

# 东财人气榜(带名称)
print('=== 东财人气榜详情 ===')
try:
    url = 'https://emappdata.eastmoney.com/stockrank/getAllCurrentList'
    r = sess.post(url, json={'appId':'appId01','globalId':'786e4c21-70dc-435a-93bb-38','pageNo':1,'pageSize':20}, timeout=10,
                  headers={'Referer':'https://data.eastmoney.com/','Content-Type':'application/json'})
    d = r.json()
    data = d.get('data') or []
    print('返回条数:', len(data))
    print('示例字段:', json.dumps(data[0], ensure_ascii=False) if data else 'none')
except Exception as e:
    print('err:', e)

# 财联社电报批量拉(试拉100条, 统计提及个股)
print('\n=== 财联社电报批量 ===')
import hashlib, time
try:
    params = {'appName': 'CailianpressWeb', 'os': 'web', 'sv': '7.7.5', 'last_time': '', 'refresh_type': '1', 'rn': '100'}
    qs = '&'.join((f'{k}={params[k]}' for k in sorted(params)))
    sign = hashlib.md5(hashlib.sha1(qs.encode()).hexdigest().encode()).hexdigest()
    url = f'https://www.cls.cn/v1/roll/get_roll_list?{qs}&sign={sign}'
    r = sess.get(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.cls.cn/'}, timeout=15)
    d = r.json()
    rows = (d.get('data') or {}).get('roll_data') or []
    print('条数:', len(rows))
    if rows:
        print('首条时间:', rows[0].get('ctime'), '末条时间:', rows[-1].get('ctime'))
except Exception as e:
    print('cls err:', e)
