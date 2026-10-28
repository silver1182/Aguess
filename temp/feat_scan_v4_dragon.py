# -*- coding: utf-8 -*-
"""F2深化验证 + 龙回头特征家族扩展"""
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
    df['ma20'] = df['close'].rolling(20).mean()
    df['vol5'] = df['volume'].rolling(5).mean()
    df['vol_ratio'] = df['volume'] / df['vol5']
    df['zt_open'] = df['open'].shift(1)  # 涨停日开盘
    df['zt_close'] = df['close'].shift(1)  # 涨停日收盘
    df['zt_low'] = df['low'].shift(1)
    df['zt_high'] = df['high'].shift(1)
    df['zt_vol'] = df['volume'].shift(1)
    df['ret2'] = df['close'].pct_change(2) * 100
    df['ret3'] = df['close'].pct_change(3) * 100
    df['ret5_'] = df['close'].pct_change(5) * 100
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

# 龙回头特征家族(涨停日T, 信号日T+n)
FEATS = {
    # 核心F2: T+1极度缩量站MA5
    'A核心F2(T+1缩量0.6+MA5+pct-2~1)': lambda df, i: (df['prev_pct'].iloc[i] >= LIMIT) and (df['vol_ratio'].iloc[i] <= 0.6) and (df['close'].iloc[i] > df['ma5'].iloc[i]) and (-2 <= df['pct'].iloc[i] <= 1),
    # 变体B: T+1极度缩量收跌但站MA10
    'B T+1缩量0.6+MA10+收跌': lambda df, i: (df['prev_pct'].iloc[i] >= LIMIT) and (df['vol_ratio'].iloc[i] <= 0.6) and (df['close'].iloc[i] > df['ma10'].iloc[i]) and (-4 <= df['pct'].iloc[i] <= 0),
    # 变体C: T+1缩量0.8+不破涨停日收盘(强势整理)
    'C T+1缩量0.8+不破涨停收盘': lambda df, i: (df['prev_pct'].iloc[i] >= LIMIT) and (df['vol_ratio'].iloc[i] <= 0.8) and (df['close'].iloc[i] > df['zt_close'].iloc[i]) and (df['low'].iloc[i] > df['zt_close'].iloc[i]),
    # 变体D: T+2回调后缩量企稳(两日等待)
    'D T+2缩量0.8+站MA5+pct-2~1': lambda df, i: (df['prev_pct'].shift(-1).iloc[i] >= LIMIT if i+1 < len(df) else False) and (df['vol_ratio'].iloc[i] <= 0.8) and (df['close'].iloc[i] > df['ma5'].iloc[i]) and (-2 <= df['pct'].iloc[i] <= 1),
    # 变体E: 涨停后3日缩量平台(横盘不深跌)
    'E T+1~T+3缩量横盘(均量<0.9+最低>涨停收盘*0.95)': lambda df, i: (df['prev_pct'].iloc[i] >= LIMIT) and (df['vol_ratio'].iloc[i] <= 0.9) and (df['low'].iloc[i] >= df['zt_close'].iloc[i] * 0.95),
    # 变体F: 涨停次日长下影探底回升
    'F T+1长下影(下影>50%)+缩量+收阳': lambda df, i: (df['prev_pct'].iloc[i] >= LIMIT) and (df['vol_ratio'].iloc[i] <= 1.0) and (df['close'].iloc[i] > df['open'].iloc[i]) and ((min(df['open'].iloc[i], df['close'].iloc[i]) - df['low'].iloc[i]) / max(df['high'].iloc[i]-df['low'].iloc[i], 1e-9) > 0.5),
    # 变体G: 涨停后首次缩量分歧(非连板, 量能缩至50%)
    'G T+1缩量0.5(任意回踩幅度)+MA5': lambda df, i: (df['prev_pct'].iloc[i] >= LIMIT) and (df['vol_ratio'].iloc[i] <= 0.5) and (df['close'].iloc[i] > df['ma5'].iloc[i]),
}

def evaluate(name, fn, min_win=None, max_win=None):
    rows = []
    for code, bars in data.items():
        df = prep(pd.DataFrame(bars))
        if len(df) < 70:
            continue
        df.reset_index(drop=True, inplace=True)
        for i in range(1, len(df) - 5):
            try:
                ok = fn(df, i)
            except Exception:
                continue
            if ok:
                s = df.iloc[i]
                rows.append({'code': code, 'date': s['date'], 'mkt': mkt_map.get(s['date']),
                             'mkt5': mkt5_map.get(s['date']), 'pct': s['pct'],
                             'r1': (df['close'].iloc[i+1] / s['close'] - 1) * 100 - COST * 100,
                             'r2': (df['close'].iloc[i+2] / s['close'] - 1) * 100 - COST * 100,
                             'r3': (df['close'].iloc[i+3] / s['close'] - 1) * 100 - COST * 100,
                             'r5': (df['close'].iloc[i+5] / s['close'] - 1) * 100 - COST * 100})
    return rows

print('=' * 100)
print('龙回头特征家族 | 全部信号')
for name, fn in FEATS.items():
    rows = evaluate(name, fn)
    if not rows:
        print(f'{name}: 0信号')
        continue
    r1 = np.array([r['r1'] for r in rows])
    r3 = np.array([r['r3'] for r in rows])
    r5 = np.array([r['r5'] for r in rows])
    strong = np.array([r['r1'] for r in rows if r['mkt'] is not None and r['mkt'] > 0])
    weak = np.array([r['r1'] for r in rows if r['mkt'] is not None and r['mkt'] <= 0])
    strong5 = np.array([r['r1'] for r in rows if r['mkt5'] is not None and r['mkt5'] > 0])
    weak5 = np.array([r['r1'] for r in rows if r['mkt5'] is not None and r['mkt5'] <= 0])
    uniq_dates = len(set(r['date'] for r in rows))
    uniq_codes = len(set(r['code'] for r in rows))
    print(f'\n【{name}】N={len(rows)} 覆盖{uniq_codes}只/ {uniq_dates}个交易日')
    print(f'  r1 均值{r1.mean():+.2f}% 中位{np.median(r1):+.2f}% 胜率{(r1>0).mean()*100:.1f}%')
    print(f'  r3 均值{r3.mean():+.2f}% 胜率{(r3>0).mean()*100:.1f}% | r5 均值{r5.mean():+.2f}% 胜率{(r5>0).mean()*100:.1f}%')
    print(f'  市况(当日>0): 强市N={len(strong)} r1={strong.mean() if len(strong) else 0:+.2f}% | 弱市N={len(weak)} r1={weak.mean() if len(weak) else 0:+.2f}%')
    print(f'  市况(5日均>0): 强市N={len(strong5)} r1={strong5.mean() if len(strong5) else 0:+.2f}% | 弱市N={len(weak5)} r1={weak5.mean() if len(weak5) else 0:+.2f}%')
    # 分年
    for yr in ('2024', '2025', '2026'):
        yr_r1 = np.array([r['r1'] for r in rows if r['date'].startswith(yr)])
        if len(yr_r1):
            print(f'  {yr}: N={len(yr_r1)} r1={yr_r1.mean():+.2f}% 胜率{(yr_r1>0).mean()*100:.1f}%')
    # 分收益分位
    print('  r1分布: p25=%.2f%% p50=%.2f%% p75=%.2f%%' % (np.percentile(r1,25), np.percentile(r1,50), np.percentile(r1,75)))
