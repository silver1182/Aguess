import requests, re
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
r = requests.get('https://gbfek.dfcfw.com/deploy/rank_web/work/rank_home.js?v=22', headers=UA, timeout=10)
js = r.text
idx = js.find('window.d_key')
# 向前找最近的模块起始 function(t,e,n){ 但要确保是包含 CryptoJS 的大模块
# 直接取 idx 前 30000 字符内所有 a=/s= 定义, 找含 parse 的
before = js[max(0,idx-30000):idx]
for m in re.finditer(r'(?:var )?[as]\s*=\s*[^;]{5,200};', before):
    seg = m.group(0)
    if 'parse' in seg or 'Utf8' in seg or 'Hex' in seg or 'Latin1' in seg:
        print(seg[:250])
        print('----')
