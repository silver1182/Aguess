import json
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
with open(base + r'\temp\kline_cache_em.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)
codes = list(cache.keys())
print('缓存股票数:', len(codes))
print('前10个:', codes[:10])
# 检查格式: 是纯数字还是带前缀
print('带前缀示例:', [c for c in codes if not c.isdigit()][:5])