import sys, importlib.util, time, json
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
spec = importlib.util.spec_from_file_location('asd', base + r'\temp\a_stock_data.py')
asd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asd)

# 测试拉取一只股票 3 年日K的速度
codes = ['000001', '600519', '000858', '601318', '002594']
t0 = time.time()
for code in codes[:3]:
    try:
        bars = asd.tencent_kline(code, period='day', start='2022-01-01', end='2026-10-26')
        print(f'{code}: {len(bars)} 根, 耗时 {time.time()-t0:.1f}s')
    except Exception as e:
        print(f'{code}: 失败 {e}')
print(f'总耗时 {time.time()-t0:.1f}s')
# 打印样例
bars = asd.tencent_kline('000001', period='day', start='2022-01-01', end='2026-10-26')
print('样例:', bars[0], bars[-1])