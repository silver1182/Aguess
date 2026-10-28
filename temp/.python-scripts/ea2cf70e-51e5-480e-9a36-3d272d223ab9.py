import json, sys, time, importlib.util
spec = importlib.util.spec_from_file_location('asd', r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py')
asd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asd)

with open(r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\kline_day_long.json', encoding='utf-8') as f:
    codes = list(json.load(f).keys())
print('全市场股票数:', len(codes))

# 分批测试: 400只一批
t0 = time.time()
batch = codes[:400]
r = asd.tencent_quote(batch)
t1 = time.time()
print(f'400只耗时 {t1-t0:.2f}s, 返回 {len(r)} 条')
# 检查有效性
stale = sum(1 for v in r.values() if v.get('is_stale'))
no_pct = sum(1 for v in r.values() if v.get('change_pct') is None)
print('is_stale:', stale, '无涨跌幅:', no_pct)
