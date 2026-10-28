import requests, re
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
r = requests.get('https://gbfek.dfcfw.com/deploy/rank_web/work/rank_home.js?v=22', headers=UA, timeout=10)
js = r.text
# 找 d 函数定义
m = re.search(r'(?:window\.)?d\s*=\s*function[\s\S]{0,800}', js)
print('d func:', m.group(0)[:800] if m else None)
print('====')
# 找 decode/decodeURIComponent/atob 等
for kw in ['atob', 'decodeURIComponent', 'charCodeAt', 'fromCharCode', 'base64']:
    ms = re.findall(r'.{80}' + kw + r'.{80}', js)
    if ms:
        print('---', kw, '---')
        for x in ms[:2]:
            print(x)
            print()
