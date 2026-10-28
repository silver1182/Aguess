import requests, re
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
r = requests.get('https://gbfek.dfcfw.com/deploy/rank_web/work/rank_home.js?v=22', headers=UA, timeout=10)
js = r.text
# 全局找 M=function / M:function 定义（宽松）
for m in re.finditer(r'M\s*[=:]\s*function', js):
    print('at', m.start())
    print(js[m.start()-150:m.start()+500])
    print('====')
