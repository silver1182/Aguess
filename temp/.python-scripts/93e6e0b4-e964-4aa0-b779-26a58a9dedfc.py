# -*- coding: utf-8 -*-
import json, pandas as pd, numpy as np
temp = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp'
with open(temp + r'\kline_day_long.json', encoding='utf-8') as f:
    data = json.load(f)
LIMIT = 9.5

def prep(df):
    df = df.copy()
    for c in ['open','high','low','close','volume','amount']:
        df[c] = df[c].astype(float)
    df['pct'] = df['close'].pct_change() * 100
    df['prev_pct'] = df['pct'].shift(1)
    df['ma5'] = df['close'].rolling(5).mean()
    df['vol5'] = df['volume'].rolling(5).mean()
    df['vol_ratio'] = df['volume'] / df['vol5']
    df['zt_close'] = df['close'].shift(1)
    return df

def scan(cond_name, cond_fn):
    pcts = []
    for code, bars in data.items():
        df = prep(pd.DataFrame(bars))
        if len(df) < 70: continue
        df.reset_index(drop=True, inplace=True)
        for i in range(1, len(df)):
            s = df.iloc[i]
            if cond_fn(df, i):
                pcts.append(s['pct'])
    pcts = np.array(pcts)
    if len(pcts):
        print(f'{cond_name}: N={len(pcts)} 信号日pct均值{pcts.mean():+.2f}% 中位{np.median(pcts):+.2f}% '
              f'>=9.5%占比{(pcts>=9.5).mean()*100:.1f}% >=5%占比{(pcts>=5).mean()*100:.1f}% <=3%占比{(pcts<=3).mean()*100:.1f}%')

scan('C', lambda df,i: df['prev_pct'].iloc[i]>=LIMIT and df['vol_ratio'].iloc[i]<=0.8 and df['close'].iloc[i]>df['zt_close'].iloc[i] and df['low'].iloc[i]>df['zt_close'].iloc[i])
scan('E', lambda df,i: df['prev_pct'].iloc[i]>=LIMIT and df['vol_ratio'].iloc[i]<=0.9 and df['low'].iloc[i]>=df['zt_close'].iloc[i]*0.95)
scan('G', lambda df,i: df['prev_pct'].iloc[i]>=LIMIT and df['vol_ratio'].iloc[i]<=0.5 and df['close'].iloc[i]>df['ma5'].iloc[i])
scan('A2(T+2)', lambda df,i: (df['pct'].shift(2).iloc[i]>=LIMIT if i>=2 else False) and df['vol_ratio'].iloc[i]<=0.6 and df['close'].iloc[i]>df['ma5'].iloc[i] and -2<=df['pct'].iloc[i]<=1)
