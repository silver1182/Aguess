import requests, re
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
r = requests.get('https://gbfek.dfcfw.com/deploy/rank_web/work/rank_home.js?v=22', headers=UA, timeout=10)
js = r.text
idx = js.find('window.d_key')
# 向后找 window.d 定义完整 + 再找这个模块里 a/s 的定义
seg = js[idx-50: idx+400]
print(seg)
print('=====')
# 找 d 定义处前面最近的 'var a=' 或 'a=n(' 等，看窗口上下文
before = js[:idx]
# 该模块起点：找 idx 之前最近的 ',function(t,e,n){"use strict";' 或 ',function(t,e,n){'
ms = list(re.finditer(r',function\(t,e,n\)\{', before))
start = ms[-1].start()+1
mod = js[start: idx+300]
# 提取模块头部 60 行内所有 var 声明
print(mod[:3000])
