import importlib.util, warnings, time
import pandas as pd, numpy as np
warnings.filterwarnings('ignore')
spec = importlib.util.spec_from_file_location("a_stock_data", r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

focus = [('300031','宝通科技'),('001979','招商蛇口'),('601857','中国石油'),('688111','金山办公'),('300976','达瑞电子'),('002578','闽发铝业'),('603200','上海洗霸'),('000995','皇台酒业')]
for code, name in focus:
    k = m.tencent_kline(code, period='day', count=30)
    c = k['close'].astype(float)
    ma5, ma10, ma20 = c.rolling(5).mean().iloc[-1], c.rolling(10).mean().iloc[-1], c.rolling(20).mean().iloc[-1]
    print(f"{name}({code}): close={c.iloc[-1]:.2f} MA5={ma5:.2f} MA10={ma10:.2f} MA20={ma20:.2f}")
    time.sleep(0.05)