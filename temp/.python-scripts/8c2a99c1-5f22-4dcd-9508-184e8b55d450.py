import json, time, sys
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
sys.path.insert(0, base + r'\temp')
import a_stock_data as a

cache_file = base + r'\temp\kline_cache_em.json'
cache = json.load(open(cache_file, encoding='utf-8'))
empty_codes = [c for c,v in cache.items() if not v or len(v)<=20]
print('需重拉:', len(empty_codes))

ok = 0
for i, code in enumerate(empty_codes):
    try:
        k = a.tencent_kline(code, period='day', count=160)
        if k is not None and len(k) > 20:
            cache[code] = k.to_dict('records'); ok += 1
        else:
            cache[code] = []
    except Exception:
        cache[code] = []
    if (i+1) % 100 == 0:
        json.dump(cache, open(cache_file,'w',encoding='utf-8'), ensure_ascii=False)
        print(f'进度 {i+1} 本批成功 {ok}')
    time.sleep(0.2)
json.dump(cache, open(cache_file,'w',encoding='utf-8'), ensure_ascii=False)
have = sum(1 for v in cache.values() if v and len(v) > 20)
print('完成, 总有效:', have, '/', len(cache))