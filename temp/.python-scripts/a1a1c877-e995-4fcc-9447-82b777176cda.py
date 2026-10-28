import sys, importlib.util, inspect
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
spec = importlib.util.spec_from_file_location('asd', base + r'\temp\a_stock_data.py')
asd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asd)
# 查看 tencent_kline 函数签名与用法
print('tencent_kline 签名:', inspect.signature(asd.tencent_kline))
doc = asd.tencent_kline.__doc__
print('doc前800字:', doc[:800] if doc else '无')