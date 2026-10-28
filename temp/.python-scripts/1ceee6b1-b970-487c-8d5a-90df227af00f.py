import requests, re
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
r = requests.get('https://gbfek.dfcfw.com/deploy/rank_web/work/rank_home.js?v=22', headers=UA, timeout=10)
js = r.text
# 搜 i.M 或 CJS.M 附近
for m in re.finditer(r'[iC]\.[JM]\s*[=:]', js):
    print('at', m.start())
    print(js[m.start()-200:m.start()+400])
    print('====')
# 也可能 M 直接是变量，比如 var M=... 
for m in re.finditer(r'var\s+M\s*=', js):
    print('var M at', m.start())
    print(js[m.start()-100:m.start()+400])
    print('====')
