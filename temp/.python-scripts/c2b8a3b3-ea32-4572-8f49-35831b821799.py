# -*- coding: utf-8 -*-
# A2 条件拆解诊断: 看每个条件的命中数, 定位瓶颈
import json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import pandas as pd, numpy as np

TEMP = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp'
with open(TEMP + r'\kline_day_long.json', encoding='utf-8') as f:
    data = json.load(f)

as_of = max(bars[-1]['date'] for bars in data.values() if bars)
print('as_of:', as_of)

n_total = n_cur = n_prev2 = n_volr = n_ma5 = n_pct = n_price = 0
prev2_list = []
for code, bars in data.items():
    if not (code.startswith(('60', '00'))) or code.startswith(('30', '688')):
        continue
    if len(bars) < 8 or bars[-1]['date'] != as_of:
        continue
    n_total += 1
    df = pd.DataFrame(bars)
    for c in ['open','high','low','close','volume','amount']:
        df[c] = df[c].astype(float)
    df['pct'] = df['close'].pct_change() * 100
    df['prev2_pct'] = df['pct'].shift(2)
    df['ma5'] = df['close'].rolling(5).mean()
    df['vol5'] = df['volume'].rolling(5).mean()
    df['vol_ratio'] = df['volume'] / df['vol5']
    s = df.iloc[-1]
    if not (np.isfinite(s['prev2_pct']) and np.isfinite(s['vol_ratio']) and np.isfinite(s['ma5'])):
        continue
    n_cur += 1
    if s['prev2_pct'] >= 9.5:
        n_prev2 += 1
        prev2_list.append((code, round(s['prev2_pct'],2), round(s['vol_ratio'],2), round(s['close'],2), round(s['ma5'],2), round(s['pct'],2)))
        if s['vol_ratio'] <= 0.6:
            n_volr += 1
            if s['close'] > s['ma5']:
                n_ma5 += 1
                if -2 <= s['pct'] <= 1:
                    n_pct += 1
                    if s['close'] <= 20:
                        n_price += 1

print(f'主板且数据当日: {n_total}, 可计算: {n_cur}, prev2_pct>=9.5: {n_prev2}')
print(f'  其中 vol_ratio<=0.6: {n_volr}, 再 close>ma5: {n_ma5}, 再 pct∈[-2,1]: {n_pct}, 再 close<=20: {n_price}')
print('prev2 命中股前30:', prev2_list[:30])
