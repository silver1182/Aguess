# -*- coding: utf-8 -*-
"""龙回头特征家族: T+1/T+2 双窗口, 一次prep全市场统一评估 (修正版)"""
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
    df['prev_pct'] = df['pct'].shift(1)      # 昨日涨幅
    df['prev2_pct'] = df['pct'].shift(2)     # 前日涨幅
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma10'] = df['close'].rolling(10).mean()
    df['vol5'] = df['volume'].rolling(5).mean()
    df['vol_ratio'] = df['volume'] / df['vol5']
    df['zt_close'] = df['close'].shift(1)
    # 未来收益(向量化, 不含cost)
    for k in (1, 2, 3, 5):
        df[f'fc{k}'] = df['close'].shift(-k) / df['close'] - 1
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

print('prep中...')
all_dfs = {}
for code, bars in data.items():
    df = prep(pd.DataFrame(bars))
    if len(df) >= 70:
        df.reset_index(drop=True, inplace=True)
        all_dfs[code] = df
print(f'prep完成, {len(all_dfs)}只')

# 特征定义: 返回布尔Series(信号日行=买入日)
BASE1 = lambda df: df['prev_pct'] >= LIMIT          # T+1 涨停次日
BASE2 = lambda df: df['prev2_pct'] >= LIMIT         # T+2 涨停后第二日
LT = lambda df, cap: df['vol_ratio'] <= cap
PCT = lambda df, lo, hi: (df['pct'] >= lo) & (df['pct'] <= hi)

FEATS = {
    # ---- T+1 涨停次日 (原始v4 A-G 家族) ----
    'A T+1缩量0.6+MA5+pct-2~1':      lambda df: BASE1(df) & LT(df, 0.6) & (df['close'] > df['ma5']) & PCT(df, -2, 1),
    'B T+1缩量0.6+MA10+收跌-4~0':    lambda df: BASE1(df) & LT(df, 0.6) & (df['close'] > df['ma10']) & PCT(df, -4, 0),
    'C T+1缩量0.8+不破涨停收盘':      lambda df: BASE1(df) & LT(df, 0.8) & (df['close'] > df['zt_close']) & (df['low'] > df['zt_close']),
    'E T+1缩量0.9+低点>=涨停收盘95%': lambda df: BASE1(df) & LT(df, 0.9) & (df['low'] >= df['zt_close'] * 0.95),
    'F T+1长下影>50%+缩量1.0+收阳':   lambda df: BASE1(df) & LT(df, 1.0) & (df['close'] > df['open']) & ((df[['open','close']].min(axis=1) - df['low']) / (df['high'] - df['low']).clip(lower=1e-9) > 0.5),
    'G T+1缩量0.5+MA5':              lambda df: BASE1(df) & LT(df, 0.5) & (df['close'] > df['ma5']),
    # ---- T+2 涨停后第二日 (网格最优对照) ----
    'D T+2缩量0.8+MA5+pct-2~1':      lambda df: BASE2(df) & LT(df, 0.8) & (df['close'] > df['ma5']) & PCT(df, -2, 1),
    'A2 T+2缩量0.6+MA5+pct-2~1(网格最优)': lambda df: BASE2(df) & LT(df, 0.6) & (df['close'] > df['ma5']) & PCT(df, -2, 1),
}

def evaluate(name, fn):
    rows = []
    for code, df in all_dfs.items():
        try:
            sig = fn(df)
        except Exception:
            continue
        idx = df.index[sig & df['fc5'].notna()]
        for j in idx:
            s = df.iloc[j]
            rows.append({'code': code, 'date': s['date'], 'pct': s['pct'],
                         'mkt': mkt_map.get(s['date']), 'mkt5': mkt5_map.get(s['date']),
                         'r1': s['fc1'] * 100 - COST * 100,
                         'r3': s['fc3'] * 100 - COST * 100,
                         'r5': s['fc5'] * 100 - COST * 100})
    return rows

print('=' * 105)
print('龙回头特征家族 | T+1/T+2 双窗口全样本')
for name, fn in FEATS.items():
    rows = evaluate(name, fn)
    if not rows:
        print(f'\n【{name}】0信号'); continue
    r1 = np.array([r['r1'] for r in rows]); r3 = np.array([r['r3'] for r in rows]); r5 = np.array([r['r5'] for r in rows])
    strong = np.array([r['r1'] for r in rows if r['mkt'] is not None and r['mkt'] > 0])
    weak   = np.array([r['r1'] for r in rows if r['mkt'] is not None and r['mkt'] <= 0])
    strong5 = np.array([r['r1'] for r in rows if r['mkt5'] is not None and r['mkt5'] > 0])
    weak5   = np.array([r['r1'] for r in rows if r['mkt5'] is not None and r['mkt5'] <= 0])
    uniq_dates = len(set(r['date'] for r in rows)); uniq_codes = len(set(r['code'] for r in rows))
    print(f'\n【{name}】N={len(rows)} 覆盖{uniq_codes}只/{uniq_dates}交易日')
    print(f'  r1 均值{r1.mean():+.2f}% 中位{np.median(r1):+.2f}% 胜率{(r1>0).mean()*100:.1f}% | r3 {r3.mean():+.2f}% 胜{(r3>0).mean()*100:.1f}% | r5 {r5.mean():+.2f}% 胜{(r5>0).mean()*100:.1f}%')
    print(f'  当日市况: 强N={len(strong)} r1={strong.mean() if len(strong) else 0:+.2f}% | 弱N={len(weak)} r1={weak.mean() if len(weak) else 0:+.2f}%')
    print(f'  5日市况:  强N={len(strong5)} r1={strong5.mean() if len(strong5) else 0:+.2f}% | 弱N={len(weak5)} r1={weak5.mean() if len(weak5) else 0:+.2f}%')
    for yr in ('2024', '2025', '2026'):
        yr_r1 = np.array([r['r1'] for r in rows if r['date'].startswith(yr)])
        if len(yr_r1):
            print(f'  {yr}: N={len(yr_r1)} r1={yr_r1.mean():+.2f}% 胜率{(yr_r1>0).mean()*100:.1f}%')
    print(f'  r1分布: p25={np.percentile(r1,25):.2f}% p50={np.percentile(r1,50):.2f}% p75={np.percentile(r1,75):.2f}%')
