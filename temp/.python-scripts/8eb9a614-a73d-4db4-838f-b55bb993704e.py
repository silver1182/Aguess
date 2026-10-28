# -*- coding: utf-8 -*-
import json, pandas as pd, numpy as np
temp = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp'
with open(temp + r'\kline_day_long.json', encoding='utf-8') as f:
    data = json.load(f)
LIMIT = 9.5; COST = 0.0015

def prep(df):
    df = df.copy()
    for c in ['open','high','low','close','volume','amount']:
        df[c] = df[c].astype(float)
    df['pct'] = df['close'].pct_change() * 100
    df['prev_pct'] = df['pct'].shift(1)
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma10'] = df['close'].rolling(10).mean()
    df['vol5'] = df['volume'].rolling(5).mean()
    df['vol_ratio'] = df['volume'] / df['vol5']
    df['zt_close'] = df['close'].shift(1)
    return df

# ===== 方式1: v3精确逻辑 (wait=1, vol<=0.6, pct[-2,1], ma5) =====
n1 = 0; samples = []
for code, bars in data.items():
    df = prep(pd.DataFrame(bars))
    if len(df) < 70: continue
    df.reset_index(drop=True, inplace=True)
    zt_idx = list(df.index[df['prev_pct'] >= LIMIT])
    for i in zt_idx:
        j = i + 1
        if j >= len(df): continue
        s = df.iloc[j]
        if s['vol_ratio'] <= 0.6 and -2 <= s['pct'] <= 1 and s['close'] > s['ma5']:
            n1 += 1
            if len(samples) < 5:
                samples.append((code, s['date'], round(s['prev_pct'],2), round(s['pct'],2), round(s['vol_ratio'],2), round(s['close'],2), round(s['ma5'],2)))
print('方式1(v3逻辑) N =', n1)
for s in samples: print('  样本:', s)

# ===== 抽样检查C变体信号 =====
nC = 0; c_samples = []
for code, bars in data.items():
    df = prep(pd.DataFrame(bars))
    if len(df) < 70: continue
    df.reset_index(drop=True, inplace=True)
    for i in range(1, len(df)-5):
        s = df.iloc[i]
        if df['prev_pct'].iloc[i] >= LIMIT and df['vol_ratio'].iloc[i] <= 0.8 and df['close'].iloc[i] > df['zt_close'].iloc[i] and df['low'].iloc[i] > df['zt_close'].iloc[i]:
            nC += 1
            if len(c_samples) < 8:
                r1 = (df['close'].iloc[i+1] / s['close'] - 1) * 100 - COST*100
                c_samples.append((code, s['date'], round(s['prev_pct'],2), round(s['pct'],2), round(s['vol_ratio'],2), round(s['close'],2), round(df['zt_close'].iloc[i],2), round(r1,2)))
print('\nC变体信号数 =', nC)
for s in c_samples: print('  样本: code=%s date=%s prev_pct=%s pct=%s volr=%s close=%s zt_close=%s r1=%s' % s)
