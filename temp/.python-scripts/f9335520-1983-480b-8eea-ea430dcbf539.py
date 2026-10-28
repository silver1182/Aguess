import json, requests, urllib3
urllib3.disable_warnings()
sess = requests.Session()
sess.verify = False
sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

# 1. 检查 a_stock_data 中 cls_telegraph 位置
import re
p = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py'
src = open(p, encoding='utf-8').read()
print('cls_telegraph in a_stock_data:', 'cls_telegraph' in src)
print('wallstreetcn_lives in a_stock_data:', 'wallstreetcn_lives' in src)

# 2. 测试财联社电报(直接复制逻辑)
print('\n=== 财联社电报 ===')
import hashlib
try:
    params = {'appName': 'CailianpressWeb', 'os': 'web', 'sv': '7.7.5', 'last_time': '', 'refresh_type': '1', 'rn': '5'}
    qs = '&'.join((f'{k}={params[k]}' for k in sorted(params)))
    sign = hashlib.md5(hashlib.sha1(qs.encode()).hexdigest().encode()).hexdigest()
    url = f'https://www.cls.cn/v1/roll/get_roll_list?{qs}&sign={sign}'
    r = sess.get(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.cls.cn/'}, timeout=10)
    d = r.json()
    rows = (d.get('data') or {}).get('roll_data') or []
    for item in rows[:3]:
        print('•', (item.get('title') or '')[:60], '|', (item.get('content') or '')[:60])
    print('共', len(rows), '条')
except Exception as e:
    print('cls err:', e)

# 3. 股吧热度替代: 试 guba 主站人气排行接口
print('\n=== 股吧人气排行(替代) ===')
for u in ['https://gbapi.eastmoney.com/guba/list?code=0&flag=3&page=1&num=5&sort=1',
          'https://guba.eastmoney.com/rank/default,1_1.html']:
    try:
        r = sess.get(u, timeout=10, headers={'Referer': 'https://guba.eastmoney.com/'})
        print(u[:60], '->', r.status_code, 'len', len(r.text))
        if r.status_code == 200 and 'gbapi' in u:
            print(r.text[:200])
    except Exception as e:
        print(u[:60], 'err:', e)
