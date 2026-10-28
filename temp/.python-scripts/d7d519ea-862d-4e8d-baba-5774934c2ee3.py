import requests, re
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
r = requests.get('https://gbfek.dfcfw.com/deploy/rank_web/work/rank_home.js?v=22', headers=UA, timeout=10)
js = r.text
# 找所有 "M" 相关可疑定义：可能 M 是 window.i 的方法，搜索 i.M 或 .M=
for m in re.finditer(r'M\s*:\s*function', js):
    print('M:function at', m.start())
    print(js[m.start()-150:m.start()+500])
    print('====')
# 找 "M(" 调用前的定义，比如 M=n(…)
for m in re.finditer(r'[,;]\s*M\s*=\s*', js):
    print('M= at', m.start())
    print(js[m.start()-100:m.start()+300])
    print('====')
