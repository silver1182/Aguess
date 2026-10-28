import requests, re
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
r = requests.get('https://gbfek.dfcfw.com/deploy/rank_web/work/rank_home.js?v=22', headers=UA, timeout=10)
js = r.text
# 找 i.M = function 或 M=function 的定义
for pat in [r'\.M=function', r'M=function\(t\)', r'i\.M', r'\.M\s*=\s*function']:
    for m in re.finditer(pat, js):
        s = m.start()
        print('--- at', s, '---')
        print(js[max(0,s-100):s+600])
        print()
        break
