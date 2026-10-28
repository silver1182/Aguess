import requests, re
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
r = requests.get('https://gbfek.dfcfw.com/deploy/rank_web/work/rank_home.js?v=22', headers=UA, timeout=10)
js = r.text
# 全局 d 的定义: 找 'd=' 或 'd =' 不在 webpack 内的
for mm in re.finditer(r'(?:window\.)?d\s*[=:]\s*(?:function|\(|\w)', js):
    s = mm.start()
    seg = js[s-120:s+250]
    # 跳过 webpack 的 d
    if 'defineProperty' in seg:
        continue
    print('---', mm.group(0)[:60])
    print(seg)
    print()
