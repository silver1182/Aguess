import json, os
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
cache_file = base + r'\temp\kline_cache_em.json'
cache = json.load(open(cache_file, encoding='utf-8')) if os.path.exists(cache_file) else {}
codes = json.load(open(base + r'\temp\backtest_codes_ext.json'))
have = sum(1 for v in cache.values() if v and len(v) > 20)
print('已缓存:', len(cache), '有效:', have, '/', len(codes))
# 查看是否有空记录(失败的)
empty = [c for c,v in cache.items() if not v]
print('空记录数:', len(empty), empty[:10])