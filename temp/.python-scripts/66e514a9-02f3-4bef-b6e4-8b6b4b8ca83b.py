import importlib.util, warnings
import pandas as pd
warnings.filterwarnings('ignore')
spec = importlib.util.spec_from_file_location("a_stock_data", r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
k = m.tencent_kline('002178', period='day', count=30)
c = k['close'].astype(float)
print(f"延华智能: close={c.iloc[-1]:.2f} MA5={c.rolling(5).mean().iloc[-1]:.2f} MA10={c.rolling(10).mean().iloc[-1]:.2f} MA20={c.rolling(20).mean().iloc[-1]:.2f}")
print("今日LOW:", k['low'].iloc[-1], "前收:", k['close'].iloc[-2])