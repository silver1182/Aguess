import sys, json, time, os
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
sys.path.insert(0, base + r'\temp')
import a_stock_data as a

cache_file = base + r'\temp\kline_cache_ext.json'
if os.path.exists(cache_file):
    cache = json.load(open(cache_file, encoding='utf-8'))
else:
    cache = {}
print('已缓存:', len(cache))

# 测试单个能否恢复
try:
    k = a.tencent_kline('600000', period='day', count=5)
    print('接口已恢复, 返回行数:', 0 if k is None else len(k))
except Exception as e:
    print('仍限流:', str(e)[:80])