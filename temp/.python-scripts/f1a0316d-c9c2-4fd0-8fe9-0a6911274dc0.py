import requests, re
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
r = requests.get('https://gbfek.dfcfw.com/deploy/rank_web/work/rank_home.js?v=22', headers=UA, timeout=10)
js = r.text
# 找 send 调用中的 path 字符串
paths = re.findall(r'send\(["\']([^"\']+)["\']', js)
print('send paths:', sorted(set(paths)))
print('---')
# 找 GetData 调用的其它形式, 如 e.send(t, params)
calls = re.findall(r'\.send\([^)]{0,150}\)', js)
for c in calls[:30]:
    print(c)
