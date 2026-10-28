import json, pandas as pd, numpy as np

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
df = pd.read_csv(base + r'\temp\backtest_long.csv')
cache = json.load(open(base + r'\temp\kline_cache_em.json', encoding='utf-8'))

# 计算 RSI14 / chg5 / chg2（涨停日收盘时点）
def rsi(closes, n=14):
    if len(closes) < n+1: return None
    c = pd.Series(closes)
    delta = c.diff()
    up = delta.clip(lower=0).rolling(n).mean()
    down = (-delta.clip(upper=0)).rolling(n).mean()
    rs = up / down.replace(0, np.nan)
    return float((100 - 100/(1+rs)).iloc[-1])

def chg_n(closes, n):
    if len(closes) < n+1: return None
    return float((closes[-1]/closes[-1-n] - 1)*100)

rsi_vals, c5, c2 = [], [], []
for _, row in df.iterrows():
    kl = cache.get(str(row['code']))
    if kl:
        closes = [x['close'] for x in kl]
        # 找到涨停日的 index
        idx = next((i for i,x in enumerate(kl) if x['date']==row['date']), None)
        if idx is not None and idx >= 14:
            closes_up_to = closes[:idx+1]
            rsi_vals.append(rsi(closes_up_to))
            c5.append(chg_n(closes_up_to, 5))
            c2.append(chg_n(closes_up_to, 2))
        else:
            rsi_vals.append(None); c5.append(None); c2.append(None)
    else:
        rsi_vals.append(None); c5.append(None); c2.append(None)

df['rsi'] = rsi_vals; df['chg5'] = c5; df['chg2'] = c2
print(df[['rsi','chg5','chg2']].describe())
df.to_csv(base + r'\temp\backtest_long.csv', index=False)
print('saved')