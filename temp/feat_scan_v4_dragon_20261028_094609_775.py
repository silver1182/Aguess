# -*- coding: utf-8 -*-
"""龙回头特征家族: 一次prep全市场后统一评估(性能优化版)"""
import json
import pandas as pd
import numpy as np

temp = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp'
with open(temp + r'\kline_day_long.json', encoding='utf-8') as f:
    data = json.load(f)

COST = 0.0015
LIMIT = 9.5

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
    df['zt_open'] = df['open'].shift(1)
    df['zt_close'] = df['close'].shift(1)
    df['zt_low'] = df['low'].shift(1)
    df['zt_high'] = df['high'].shift(1)
    return df

# 市场日序列
day_mkt = {}
for code, bars in data.items():
    df = pd.DataFrame(bars)
    df['pct'] = df['close'].astype(float).pct_change() * 100
    for d, p in zip(df['date'], df['pct']):
        day_mkt.setdefault(d, []).append(p)
mkt = {d: float(np.nanmean(v)) for d, v in day_mkt.items()}
mkt_df = pd.DataFrame({'date': list(mkt.keys()), 'mkt': list(mkt.values())}).sort_values('date').reset_index(drop=True)
mkt_df['mkt_ma5'] = mkt_df['mkt'].rolling(5).mean()
mkt_map = dict(zip(mkt_df['date'], mkt_df['mkt']))
mkt5_map = dict(zip(mkt_df['date'], mkt_df['mkt_ma5']))

# 一次prep全部股票
print('prep中...')
all_dfs = {}
for code, bars in data.items():
    df = prep(pd.DataFrame(bars))
    if len(df) >= 70:
        df.reset_index(drop=True, inplace=True)
        all_dfs[code] = df
print(f'prep完成, {len(all_dfs)}只')

# 特征定义: 在df上直接算布尔列
def col_feat(df):
    s = pd.Series(False, index=df.index)
    zt = df['prev_pct'] >= LIMIT
    idx = df.index[zt & (df.index + 1 < len(df))]
    for i in idx:
        j = i + 1
        if j in df.index and df['vol_ratio'].iloc[j] <= 0.6 and df['close'].iloc[j] > df['ma5'].iloc[j] and -2 <= df['pct'].iloc[j] <= 1:
            s.iloc[j] = True
    return s

def evaluate(name, fn):
    rows = []
    for code, df in all_dfs.items():
        try:
            sig = fn(df)
        except Exception:
            continue
        for j in df.index[sig]:
            if j + 5 >= len(df):
                continue
            s = df.iloc[j]
            rows.append({'code': code, 'date': s['date'], 'mkt': mkt_map.get(s['date']),
                         'mkt5': mkt5_map.get(s['date']), 'pct': s['pct'],
                         'r1': (df['close'].iloc[j+1] / s['close'] - 1) * 100 - COST * 100,
                         'r2': (df['close'].iloc[j+2] / s['close'] - 1) * 100 - COST * 100,
                         'r3': (df['close'].iloc[j+3] / s['close'] - 1) * 100 - COST * 100,
                         'r5': (df['close'].iloc[j+5] / s['close'] - 1) * 100 - COST * 100})
    return rows

FEATS = {
    'A核心F2(T+1缩量0.6+MA5+pct-2~1)': lambda df: (df['prev_pct'] >= LIMIT) & (df['vol_ratio'] <= 0.6) & (df['close'] > df['ma5']) & (df['pct'] >= -2) & (df['pct'] <= 1),
    'B T+1缩量0.6+MA10+收跌-4~0': lambda df: (df['prev_pct'] >= LIMIT) & (df['vol_ratio'] <= 0.6) & (df['close'] > df['ma10']) & (df['pct'] >= -4) & (df['pct'] <= 0),
    'C T+1缩量0.8+不破涨停收盘': lambda df: (df['prev_pct'] >= LIMIT) & (df['vol_ratio'] <= 0.8) & (df['close'] > df['zt_close']) & (df['low'] > df['zt_close']),
    'E T+1缩量0.9+低点不低于涨停收盘95%': lambda df: (df['prev_pct'] >= LIMIT) & (df['vol_ratio'] <= 0.9) & (df['low'] >= df['zt_close'] * 0.95),
    'G T+1缩量0.5+MA5': lambda df: (df['prev_pct'] >= LIMIT) & (df['vol_ratio'] <= 0.5) & (df['close'] > df['ma5']),
}

print('=' * 100)
print('龙回头特征家族 | 全部信号 (T+1信号日收盘买入)')
for name, fn in FEATS.items():
    rows = evaluate(name, fn)
    if not rows:
        print(f'\n【{name}】0信号')
        continue
    r1 = np.array([r['r1'] for r in rows])
    r3 = np.array([r['r3'] for r in rows])
    r5 = np.array([r['r5'] for r in rows])
    strong = np.array([r['r1'] for r in rows if r['mkt'] is not None and r['mkt'] > 0])
    weak = np.array([r['r1'] for r in rows if r['mkt'] is not None and r['mkt'] <= 0])
    uniq_dates = len(set(r['date'] for r in rows))
    uniq_codes = len(set(r['code'] for r in rows))
    print(f'\n【{name}】N={len(rows)} 覆盖{uniq_codes}只/ {uniq_dates}个交易日')
    print(f'  r1 均值{r1.mean():+.2f}% 中位{np.median(r1):+.2f}% 胜率{(r1>0).mean()*100:.1f}% | r3 {r3.mean():+.2f}% 胜率{(r3>0).mean()*100:.1f}% | r5 {r5.mean():+.2f}% 胜率{(r5>0).mean()*100:.1f}%')
    print(f'  强市N={len(strong)} r1={strong.mean() if len(strong) else 0:+.2f}% | 弱市N={len(weak)} r1={weak.mean() if len(weak) else 0:+.2f}%')
    for yr in ('2024', '2025', '2026'):
        yr_r1 = np.array([r['r1'] for r in rows if r['date'].startswith(yr)])
        if len(yr_r1):
            print(f'  {yr}: N={len(yr_r1)} r1={yr_r1.mean():+.2f}% 胜率{(yr_r1>0).mean()*100:.1f}%')
    print('  r1分布: p25=%.2f%% p50=%.2f%% p75=%.2f%%' % (np.percentile(r1,25), np.percentile(r1,50), np.percentile(r1,75)))
