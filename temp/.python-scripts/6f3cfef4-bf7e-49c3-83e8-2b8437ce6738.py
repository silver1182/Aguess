import json

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
with open(base + r'\temp\kline_cache_em.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

codes = list(cache.keys())[:3]
for c in codes:
    item = cache[c]
    print(c, type(item).__name__)
    if isinstance(item, list) and item:
        print('  样本行:', item[0])
        print('  行数:', len(item))
    elif isinstance(item, dict):
        print('  keys:', list(item.keys())[:10])
        v = item.get('klines') or item.get('data') or item.get('kline')
        if v: print('  样本行:', v[0] if isinstance(v, list) else v)
print('总股票数:', len(cache))