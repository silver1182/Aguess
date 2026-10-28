import requests, re
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
r = requests.get('https://gbfek.dfcfw.com/deploy/rank_web/work/rank_home.js?v=22', headers=UA, timeout=10)
js = r.text
# 全局搜 "M(" 赋值, 比如 "M=function(t){" 或 "M:function(t)"
for pat in ['M=function(t)', 'M:function(t)', 'M=function (t)', 'M:function (t)']:
    for m in re.finditer(re.escape(pat), js):
        print('pat:', pat, 'at', m.start())
        print(js[m.start()-200:m.start()+700])
        print('====')
# 也搜 "i.M" 或 "n.M" 被赋值
for m in re.finditer(r'\.M\s*=\s*', js):
    print('dot M assign at', m.start(), js[m.start()-100:m.start()+300])
