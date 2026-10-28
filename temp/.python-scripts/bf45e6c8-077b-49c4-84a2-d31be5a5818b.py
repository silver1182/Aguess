import requests, re
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
r = requests.get('https://gbfek.dfcfw.com/deploy/rank_web/work/rank_home.js?v=22', headers=UA, timeout=10)
js = r.text
# 找 api 地址
apis = re.findall(r'["\'](https?://[^"\']+)["\']', js)
for a in sorted(set(apis))[:40]:
    print(a)
print('---guba rank api patterns---')
g = re.findall(r'["\']([^"\']*(?:guba|rank|hot|list)[^"\']*)["\']', js)
for a in sorted(set(g))[:40]:
    print(a)
