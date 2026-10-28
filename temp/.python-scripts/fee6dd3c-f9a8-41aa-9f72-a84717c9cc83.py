import json
temp = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp'
with open(temp + r'\kline_cache_em.json', encoding='utf-8') as f:
    cache = json.load(f)
ks = list(cache.keys())
print('缓存总数:', len(ks))
hit = [k for k in ks if '600519' in k]
print('600519命中:', hit)
# 600xxx 有多少
cnt6 = sum(1 for k in ks if k.startswith('6'))
cnt0 = sum(1 for k in ks if k.startswith('0'))
print('6开头:', cnt6, '0开头:', cnt0)
