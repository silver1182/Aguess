import sys, importlib.util, time
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
spec = importlib.util.spec_from_file_location('asd', base + r'\temp\a_stock_data.py')
asd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asd)

t0 = time.time()
bars = asd.tencent_kline('000001', period='week', start='2022-01-01', end='2026-10-26')
print(type(bars), '形状:', getattr(bars, 'shape', None))
print('列:', list(bars.columns) if hasattr(bars,'columns') else None)
print('周K数量:', len(bars))
print('耗时:', time.time()-t0)
print(bars.head(3).to_string() if hasattr(bars,'head') else bars[:3])