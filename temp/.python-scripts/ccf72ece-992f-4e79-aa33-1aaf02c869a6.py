import requests, re
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
r = requests.get('https://gbfek.dfcfw.com/deploy/rank_web/work/rank_home.js?v=22', headers=UA, timeout=10)
js = r.text
# 找 CJS 对象上 M 的定义: "CJS.M" 或 "i.M=" 之类，用宽松模式
for m in re.finditer(r'\.M\s*=\s*[a-zA-Z_]', js):
    print('at', m.start())
    print(js[m.start()-120:m.start()+200])
    print('====')
# 也可能 M 定义在 window.CJS=i 之后立即出现
idx = js.find('window.CJS=i')
print('CJS at', idx)
print(js[idx:idx+1500])
