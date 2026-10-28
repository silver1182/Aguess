import json, sys
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
cache = json.load(open(base + r'\temp\kline_cache_em.json', encoding='utf-8'))
# 检查一条记录结构
for c, v in cache.items():
    if v:
        print(c, v[-2:])
        break