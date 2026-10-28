# -*- coding: utf-8 -*-
"""F2涨停次日缩量回踩 参数网格深度扫描 + 市况(全市场等权日涨幅)过滤"""
import json
import pandas as pd
import numpy as np

temp = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp'
with open(temp + r'\kline_day_long.json', encoding='utf-8') as f:
    data = json.load(f)

COST = 0.0015
LIMIT = 9.5  # 主板涨停(接近10%)

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
    return df

# 先构建全市场等权日涨幅序列
day_mkt = {}
for code, bars in data.items():
    df = pd.DataFrame(bars)
    df['pct'] = df['close'].astype(float).pct_change() * 100
    for d, p in zip(df['date'], df['pct']):
        day_mkt.setdefault(d, []).append(p)
mkt = {d: float(np.nanmean(v)) for d, v in day_mkt.items()}
mkt_df = pd.DataFrame({'date': list(mkt.keys()), 'mkt': list(mkt.values())}).sort_values('date').reset_index(drop=True)
mkt_df['mkt_ma5'] = mkt_df['mkt'].rolling(5).mean()
# 市况标记: 强市=当日全市场平均涨幅>0且5日均>0
mkt_map = dict(zip(mkt_df['date'], mkt_df['mkt']))
mkt5_map = dict(zip(mkt_df['date'], mkt_df['mkt_ma5']))

# F2网格: 涨停后第N日 / 缩量阈值 / 回踩跌幅范围 / 是否站上MA5
grid = []
for wait in (1, 2):
    for volcap in (1.0, 0.8, 0.6):
        for lo, hi in ((-4, 0), (-3, 0), (-2, 1)):
            for ma_req in (5, 10, None):
                grid.append((wait, volcap, lo, hi, ma_req))

def collect(rows, sig_rows, df, code):
    """sig_rows: [(idx, wait)] 涨停日idx与第N日"""
    for i, wait in sig_rows:
        j = i + wait  # 信号日(回踩日)
        if j + 1 >= len(df):
            continue
        srow = df.iloc[j]
        # 回踩条件已在信号日确定, 记录信号日
        rows.append({
            'code': code, 'sig_date': srow['date'], 'mkt': mkt_map.get(srow['date']),
            'r1': (df['close'].iloc[j+1] / srow['close'] - 1) * 100 - COST * 100,
            'r3': (df['close'].iloc[j+3] / srow['close'] - 1) * 100 - COST * 100 if j+3 < len(df) else np.nan,
        })

results = {g: [] for g in grid}
for code, bars in data.items():
    df = prep(pd.DataFrame(bars))
    if len(df) < 70:
        continue
    df.reset_index(drop=True, inplace=True)
    zt_idx = list(df.index[df['prev_pct'] >= LIMIT])  # 涨停日(前一交易日涨停)
    for wait, volcap, lo, hi, ma_req in grid:
        sig_rows = []
        for i in zt_idx:
            j = i + wait
            if j >= len(df):
                continue
            s = df.iloc[j]
            cond = (s['vol_ratio'] <= volcap) and (lo <= s['pct'] <= hi)
            if ma_req == 5:
                cond = cond and (s['close'] > s['ma5'])
            elif ma_req == 10:
                cond = cond and (s['close'] > s['ma10'])
            if cond:
                sig_rows.append((i, wait))
        collect(results[(wait, volcap, lo, hi, ma_req)], sig_rows, df, code)

print('=' * 90)
print('F2涨停次日/后日缩量回踩 网格扫描 | 全部信号(不限市况)')
print(f'{"网格(wait,vol,lo,hi,ma)":<28}{"N":>5}{"r1均%":>8}{"r1胜%":>7}{"r3均%":>8}{"N强":>5}{"强市r1%":>8}{"N弱":>5}{"弱市r1%":>8}')
for g in grid:
    rows = results[g]
    if not rows:
        continue
    r1 = [r['r1'] for r in rows]
    r3 = [r['r3'] for r in rows if not np.isnan(r['r3'])]
    strong = [r['r1'] for r in rows if r['mkt'] is not None and r['mkt'] > 0]
    weak = [r['r1'] for r in rows if r['mkt'] is not None and r['mkt'] <= 0]
    label = f'{g[0]}日 vol<={g[1]} pct[{g[2]},{g[3]}] ma{g[4]}'
    print(f'{label:<30}{len(rows):>5}{np.mean(r1):>+8.2f}{(np.array(r1)>0).mean()*100:>7.1f}'
          f'{np.mean(r3):>+8.2f}{len(strong):>5}{(np.mean(strong) if strong else 0):>+8.2f}'
          f'{len(weak):>5}{(np.mean(weak) if weak else 0):>+8.2f}')
