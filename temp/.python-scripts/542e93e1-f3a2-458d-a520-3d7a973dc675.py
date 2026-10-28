import requests, re
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
r = requests.get('https://gbfek.dfcfw.com/deploy/rank_web/work/rank_home.js?v=22', headers=UA, timeout=10)
js = r.text
idx = js.find('window.d_key')
# 向前找到这个模块的开始（function(t,e,n){ 开头）
# 找 d_key 之前最近的一个 ',function(t,e,n){' 
seg_before = js[:idx]
m = list(re.finditer(r',function\(t,e,n\)\{', seg_before))
start = m[-1].start()+1
seg = js[start: idx+600]
print(seg[:4000])
