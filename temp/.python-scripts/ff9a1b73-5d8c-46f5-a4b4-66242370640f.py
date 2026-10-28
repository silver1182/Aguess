import requests, re
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
r = requests.get('https://guba.eastmoney.com/rank/', headers=UA, timeout=10)
html = r.text
print('len:', len(html))
# 找 script 里的数据变量
for pat in ['popularityList', 'var rankData', 'window\\.\\w+\\s*=', 'rankData', 'jsonData']:
    ms = re.findall(r'[\w\.]{0,60}' + pat + r'[\s\S]{0,200}', html)
    if ms:
        print('---', pat, '---')
        for m in ms[:3]:
            print(m[:250])
# 找直接含股票列表的区域
m = re.search(r'<script[^>]*>([\s\S]{500,3000})</script>', html)
if m:
    print('===first big script===')
    print(m.group(1)[:2000])
