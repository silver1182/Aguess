import sys, pandas as pd, numpy as np
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
sys.path.insert(0, base + r'\temp')
import a_stock_data as a

def analyze(code, name):
    k = a.tencent_kline(code, period='day', count=80)
    c = k['close'].astype(float)
    rsi14 = None
    if len(c) >= 15:
        delta = c.diff()
        up = delta.clip(lower=0).rolling(14).mean()
        down = (-delta.clip(upper=0)).rolling(14).mean()
        rs = up / down.replace(0, np.nan)
        rsi14 = float((100 - 100/(1+rs)).iloc[-1])
    chg5 = float((c.iloc[-1]/c.iloc[-6]-1)*100) if len(c)>=6 else None
    ma5 = float(c.iloc[-5:].mean())
    ma10 = float(c.iloc[-10:].mean())
    ma20 = float(c.iloc[-20:].mean())
    print(f'--- {code} {name} ---')
    print(f'收盘: {float(c.iloc[-1])} | RSI14: {rsi14:.1f} | 5日涨幅: {chg5:+.1f}%')
    print(f'MA5: {ma5:.2f} MA10: {ma10:.2f} MA20: {ma20:.2f}')
    print(f'收盘 vs MA5: {(float(c.iloc[-1])/ma5-1)*100:+.1f}% vs MA10: {(float(c.iloc[-1])/ma10-1)*100:+.1f}%')
    print(f'近5日收盘: {[round(x,2) for x in c.iloc[-5:].tolist()]}')

analyze('603138', '海量数据')
analyze('603337', '杰克科技')