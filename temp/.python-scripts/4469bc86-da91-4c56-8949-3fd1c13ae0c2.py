import requests, re
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
r = requests.get('https://gbfek.dfcfw.com/deploy/rank_web/work/rank_home.js?v=22', headers=UA, timeout=10)
js = r.text
# 找 M 函数定义: i.M=function 或 t.M= 在 CryptoJS 库初始化里
# 搜 "M" 赋值处。CryptoJS 定义中常见: i.M=function(t,e){...}
for pat in [r'\.M\s*=\s*function', r'M:function', r'\.M=function', r',M=function']:
    for m in re.finditer(pat, js):
        s = m.start()
        print('--- pat', pat, 'at', s, '---')
        print(js[max(0,s-200):s+900])
        print()
        break
