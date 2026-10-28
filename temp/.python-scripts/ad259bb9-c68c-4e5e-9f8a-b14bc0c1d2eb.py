import re
p = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py'
src = open(p, encoding='utf-8').read()
# 找所有函数名
names = re.findall(r'^def (\w+)', src, re.M)
print('全部函数:', names)
# 看新闻/公告/热度相关
for kw in ['news', 'news', 'guba', 'stock', 'hot', 'rank', 'announce', 'search', 'em_', 'info']:
    hits = [n for n in names if kw.lower() in n.lower()]
    if hits:
        print(kw, '->', hits)
