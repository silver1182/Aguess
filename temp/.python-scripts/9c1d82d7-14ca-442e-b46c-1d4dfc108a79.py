import sys, time, json
sys.path.insert(0, r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp')
import importlib.util
spec = importlib.util.spec_from_file_location('asd', r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py')
asd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asd)

# 测10只股票批量行情
t0 = time.time()
r = asd.tencent_quote(['600519','000001','600094','000559','002178'])
print('耗时', round(time.time()-t0, 3), 's')
for k, v in r.items():
    print(k, v)
