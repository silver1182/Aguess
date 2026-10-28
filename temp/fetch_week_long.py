import sys, importlib.util, json, time, os
from concurrent.futures import ThreadPoolExecutor, as_completed

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
spec = importlib.util.spec_from_file_location('asd', base + r'\temp\a_stock_data.py')
asd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asd)

with open(base + r'\temp\kline_cache_em.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)
codes = list(cache.keys())

def norm_code(code):
    # 腾讯接口需要带前缀
    if code.startswith('6'):
        return 'sh' + code
    else:
        return 'sz' + code

def fetch(code):
    try:
        bars = asd.tencent_kline(norm_code(code), period='week', start='2022-01-01', end='2026-10-26')
        if len(bars) == 0:
            return code, []
        return code, bars.to_dict('records')
    except Exception as e:
        return code, [('ERR', str(e))]

# 分批执行，每批 300 只，16 并发
out_path = base + r'\temp\week_kline_long.json'
results = {}
if os.path.exists(out_path):
    with open(out_path, 'r', encoding='utf-8') as f:
        results = json.load(f)
    print('已有缓存:', len(results))

remaining = [c for c in codes if c not in results]
print('待拉取:', len(remaining))

batch_size = 300
for bi in range(0, len(remaining), batch_size):
    batch = remaining[bi:bi+batch_size]
    t0 = time.time()
    done = 0
    with ThreadPoolExecutor(max_workers=16) as ex:
        futs = {ex.submit(fetch, c): c for c in batch}
        for fut in as_completed(futs):
            code, bars = fut.result()
            results[code] = bars
            done += 1
    print(f'批次{bi//batch_size+1}: {done} 只, 耗时 {time.time()-t0:.1f}s, 累计 {len(results)}')
    # 每批落盘
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False)

# 统计
errs = [c for c, b in results.items() if b and isinstance(b[0], list) and b[0][0] == 'ERR']
ok = [c for c, b in results.items() if b and not (isinstance(b[0], list) and b[0][0] == 'ERR')]
print(f'完成: 成功{len(ok)} 失败{len(errs)}')
print('失败示例:', errs[:5])