import importlib.util, time, warnings
warnings.filterwarnings('ignore')
spec = importlib.util.spec_from_file_location("a_stock_data", r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

print('===== 1. tencent_quote 腾讯实时行情(茅台+上证指数) =====')
try:
    q = m.tencent_quote(["600519", "sh000001"])
    for row in q:
        print(row if isinstance(row, dict) else row)
except Exception as e:
    print('ERR:', repr(e)[:200])

print('\n===== 2. tencent_kline 腾讯日K(茅台近5日) =====')
try:
    k = m.tencent_kline("600519", period="day", count=5)
    if hasattr(k, 'tail'):
        print(k[['date','close']].tail(5).to_string() if 'date' in k.columns else k.tail(5).to_string())
    else:
        print(k[-5:])
except Exception as e:
    print('ERR:', repr(e)[:200])