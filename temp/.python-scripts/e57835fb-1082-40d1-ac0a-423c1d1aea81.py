# -*- coding: utf-8 -*-
import json, pandas as pd, numpy as np
temp = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp'
with open(temp + r'\kline_day_long.json', encoding='utf-8') as f:
    data = json.load(f)

LIMIT = 9.5
cnt = {}
def prep(df):
    df = df.copy()
    for c in ['open','high','low','close','volume','amount']:
        df[c] = df[c].astype(float)
    df['pct'] = df['close'].pct_change() * 100
    df['prev_pct'] = df['pct'].shift(1)
    df['ma5'] = df['close'].rolling(5).mean()
    df['vol5'] = df['volume'].rolling(5).mean()
    df['vol_ratio'] = df['volume'] / df['vol5']
    return df

all_cnt = {k:0 for k in ['total_days','prev_zt','prev_zt_vol06','prev_zt_vol06_ma5','prev_zt_vol06_ma5_pct2to1']}
for code, bars in data.items():
    df = prep(pd.DataFrame(bars))
    if len(df) < 70: continue
    df = df.iloc[5:]  # 去掉ma/vol窗口
    all_cnt['total_days'] += len(df)
    m1 = df['prev_pct'] >= LIMIT
    all_cnt['prev_zt'] += int(m1.sum())
    m2 = m1 & (df['vol_ratio'] <= 0.6)
    all_cnt['prev_zt_vol06'] += int(m2.sum())
    m3 = m2 & (df['close'] > df['ma5'])
    all_cnt['prev_zt_vol06_ma5'] += int(m3.sum())
    m4 = m3 & (df['pct'] >= -2) & (df['pct'] <= 1)
    all_cnt['prev_zt_vol06_ma5_pct2to1'] += int(m4.sum())

print(all_cnt)
# 看几只看板: 找一只涨停较多的票
for code in ['000002','000006']:
    df = prep(pd.DataFrame(data[code])).iloc[5:]
    zt = df[df['prev_pct'] >= LIMIT]
    print(f'\n{code} 涨停次日行数:', len(zt))
    print(zt[['date','pct','prev_pct','vol_ratio','close','ma5']].head(8).to_string())
