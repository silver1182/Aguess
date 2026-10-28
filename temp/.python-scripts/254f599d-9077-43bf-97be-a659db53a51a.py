import requests, re
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
r = requests.get('https://guba.eastmoney.com/rank/', headers=UA, timeout=10)
html = r.text
# 找 js 文件引用
js = re.findall(r'src="([^"]+\.js[^"]*)"', html)
for j in js[:20]:
    print(j)
print('---api-like---')
apis = re.findall(r'["\'](https?://[^"\']*(?:api|rank|list)[^"\']*)["\']', html)
for a in sorted(set(apis))[:30]:
    print(a)
