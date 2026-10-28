import json
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
with open(base + r'\temp\kline_cache_em.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)
print('股票数:', len(cache))
codes = list(cache.keys())[:3]
for c in codes:
    bars = cache[c]
    print(c, 'bars:', len(bars), '首日:', bars[0]['date'], '末日:', bars[-1]['date'])
    print('  示例bar:', {k:v for k,v in bars[-1].items() if k != 'code'})
