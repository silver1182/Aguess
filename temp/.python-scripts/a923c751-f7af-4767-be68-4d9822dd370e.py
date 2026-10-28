import importlib.util, warnings, time
import pandas as pd
warnings.filterwarnings('ignore')
spec = importlib.util.spec_from_file_location("a_stock_data", r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

focus = ['000635','603200','000995','002578','001318','300031','003006','601857','688111','603716','300976','600838']
for code in focus:
    k = m.tencent_kline(code, period='day', count=12)
    if k is None or len(k)==0: continue
    df = k.tail(8)
    s = []
    for _, r in df.iterrows():
        chg = (r['close']/r['open']-1)*100
        s.append(f"{r['date'][5:]}:O{r['open']:.2f}H{r['high']:.2f}L{r['low']:.2f}C{r['close']:.2f}({chg:+.1f}%)")
    print(code, ' | '.join(s))
    time.sleep(0.05)