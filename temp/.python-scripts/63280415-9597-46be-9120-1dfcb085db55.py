import requests, re
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
r = requests.get('https://gbfek.dfcfw.com/deploy/rank_web/work/rank_home.js?v=22', headers=UA, timeout=10)
js = r.text
# 找 "M(" 与 "getUtilsFromFile" 相关定义, 全局搜 M 的定义
idx = js.find('getUtilsFromFile')
print('idx:', idx)
before = js[:idx]
# M 可能是 i.M 赋值, 在 CryptoJS 库后面定义
for m in re.finditer(r'\bM\s*=\s*function', js):
    print('M def at', m.start())
    print(js[m.start():m.start()+400])
    print('====')
