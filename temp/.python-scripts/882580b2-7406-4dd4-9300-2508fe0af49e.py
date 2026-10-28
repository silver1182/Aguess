import requests, re
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
r = requests.get('https://gbfek.dfcfw.com/deploy/rank_web/work/rank_home.js?v=22', headers=UA, timeout=10)
js = r.text
idx = js.find('window.d_key')
# 该模块起点：window.d_key 之前最近的 ,function(t,e,n){
before = js[:idx]
starts = [m.start() for m in re.finditer(r',function\(t,e,n\)\{', before)]
start = starts[-1] + 1
end = js.find('},function(t,e,n){', start)  # 下一个模块起点
mod = js[start:end if end>0 else idx+200]
print('模块长度:', len(mod))
print(mod[:5000])
