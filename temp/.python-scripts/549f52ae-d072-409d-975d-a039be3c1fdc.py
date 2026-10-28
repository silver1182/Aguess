import requests, re
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
r = requests.get('https://gbfek.dfcfw.com/deploy/rank_web/work/rank_home.js?v=22', headers=UA, timeout=10)
js = r.text
# 找 sendHost 定义 / gbcdnHost
m = re.search(r'sendHost[^}]{0,600}', js)
print('sendHost:', m.group(0)[:600] if m else None)
print('---')
# GetData.aspx 上下文
for mm in re.finditer(r'.{300}GetData\.aspx.{300}', js, re.S):
    print(mm.group(0))
    print('====')
