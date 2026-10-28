import sys, json, time, os
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
sys.path.insert(0, base + r'\temp')
import a_stock_data as a

codes = json.load(open(base + r'\temp\backtest_codes_ext.json'))
cache_file = base + r'\temp\kline_cache_ext.json'
if os.path.exists(cache_file):
    cache = json.load(open(cache_file, encoding='utf-8'))
else:
    cache = {}
todo = [c for c in codes if c not in cache]
print('待拉取:', len(todo), '已缓存:', len(cache))

# 分批拉，每批存一次，防止中途失败丢失
for i, code in enumerate(todo):
    try:
        k = a.tencent_kline(code, period='day', count=120)
        if k is not None and len(k) > 0:
            # 转为记录列表
            recs = k.to_dict('records')
            cache[code] = recs
        else:
            cache[code] = []
    except Exception as e:
        print('ERR', code, e)
        cache[code] = []
    if (i+1) % 200 == 0:
        json.dump(cache, open(cache_file,'w',encoding='utf-8'), ensure_ascii=False)
        print(f'进度 {i+1}/{len(todo)}')
    time.sleep(0.15)

json.dump(cache, open(cache_file,'w',encoding='utf-8'), ensure_ascii=False)
have = sum(1 for v in cache.values() if v)
print('完成, 有K线股票数:', have, '/', len(cache))