import requests, re
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
r = requests.get('https://gbfek.dfcfw.com/deploy/rank_web/work/rank_home.js?v=22', headers=UA, timeout=10)
js = r.text
# getData 的调用上下文
m = re.search(r'getData=function\(\)\{[\s\S]{0,1200}', js)
print(m.group(0)[:1200])
print('=====')
# 找 path: 形式的字符串
for mm in re.finditer(r'path[\"\\\':]{1,3}([^\"\\\',\)]{3,80})', js):
    print('path-like:', mm.group(1))
