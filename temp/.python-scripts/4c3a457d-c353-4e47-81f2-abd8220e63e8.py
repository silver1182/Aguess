import requests, re
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
r = requests.get('https://gbfek.dfcfw.com/deploy/rank_web/work/rank_home.js?v=22', headers=UA, timeout=10)
js = r.text
idx = js.find('window.d_key')
before = js[max(0,idx-30000):idx]
# 看 a=CJS.enc.Utf8.parse(o) 上下文, o 从哪来
m = re.search(r'.{600}a=CJS\.enc\.Utf8\.parse\(o\).{200}', before)
if m:
    print(m.group(0))
print('====')
# 找 s 在 d 函数前的定义：s=CJS.enc.Utf8.parse(...) 
for m in re.finditer(r'.{200}s=CJS\.enc\.Utf8\.parse\([^)]*\).{100}', before):
    print(m.group(0))
    print('----')
