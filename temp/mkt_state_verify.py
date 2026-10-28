# -*- coding: utf-8 -*-
"""市场情绪分层验证: 构建全市场等权指数, 定义牛/熊/震荡状态, 分层统计A2表现"""
import json, warnings
import pandas as pd
import numpy as np
warnings.filterwarnings('ignore')

temp = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp'
with open(temp + r'\kline_day_long.json', encoding='utf-8') as f:
    data = json.load(f)
COST = 0.0015
LIMIT = 9.5

# ===== 1. 构建全市场等权指数 =====
day_mkt = {}
for code, bars in data.items():
    df = pd.DataFrame(bars)
    df['pct'] = df['close'].astype(float).pct_change() * 100
    for d, p in zip(df['date'], df['pct']):
        day_mkt.setdefault(d, []).append(p)
mkt = {d: float(np.nanmean(v)) for d, v in day_mkt.items()}
mkt_df = pd.DataFrame({'date': list(mkt.keys()), 'mkt': list(mkt.values())}).sort_values('date').reset_index(drop=True)
# 等权指数(累计净值)
mkt_df['idx'] = (1 + mkt_df['mkt'] / 100).cumprod() * 100
mkt_df['ma20'] = mkt_df['idx'].rolling(20).mean()
mkt_df['ma60'] = mkt_df['idx'].rolling(60).mean()
mkt_df['mkt_ma5'] = mkt_df['mkt'].rolling(5).mean()
mkt_df['trend'] = mkt_df['ma20'].diff()  # MA20斜率
mkt_df['ret5'] = mkt_df['idx'].pct_change(5) * 100
mkt_df['ret20'] = mkt_df['idx'].pct_change(20) * 100

# 市场状态: 牛=指数>MA20且MA20上行; 熊=指数<MA20且MA20下行; 震荡=其余
def state_of(row):
    if np.isnan(row['ma20']) or np.isnan(row['trend']):
        return '初始'
    if row['idx'] > row['ma20'] and row['trend'] > 0:
        return '牛'
    if row['idx'] < row['ma20'] and row['trend'] < 0:
        return '熊'
    return '震荡'
mkt_df['state'] = mkt_df.apply(state_of, axis=1)

print('==== 当前市场环境 (全市场等权指数) ====')
tail = mkt_df.tail(15)
for _, r in tail.iterrows():
    print(f"{r['date']} 等权涨跌{r['mkt']:+.2f}% 指数{r['idx']:.0f} MA20={r['ma20']:.0f} 状态={r['state']} ret5={r['ret5']:+.1f}%")
print(f"\n最近5日累计: {tail['ret5'].iloc[-1]:+.2f}% | 最近20日: {tail['ret20'].iloc[-1]:+.2f}%")
print(f"近20日市场状态分布: {tail['state'].value_counts().to_dict()}")

# 全历史状态统计
print(f"\n全历史状态占比: {mkt_df['state'].value_counts(normalize=True).to_dict()}")

# ===== 2. A2 信号分层 =====
def prep(df):
    df = df.copy()
    for c in ['open','high','low','close','volume','amount']:
        df[c] = df[c].astype(float)
    df['pct'] = df['close'].pct_change() * 100
    df['vol5'] = df['volume'].rolling(5).mean()
    df['vol_ratio'] = df['volume'] / df['vol5']
    df['ma5'] = df['close'].rolling(5).mean()
    df['prev2_pct'] = df['pct'].shift(2)
    for k in (1, 3, 5):
        df[f'fc{k}'] = df['close'].shift(-k) / df['close'] - 1
    return df

state_map = dict(zip(mkt_df['date'], mkt_df['state']))
mkt5_map = dict(zip(mkt_df['date'], mkt_df['mkt_ma5']))
ret5_map = dict(zip(mkt_df['date'], mkt_df['ret5']))
ret20_map = dict(zip(mkt_df['date'], mkt_df['ret20']))

rows = []
for code, bars in data.items():
    df = prep(pd.DataFrame(bars))
    if len(df) < 70: continue
    df.reset_index(drop=True, inplace=True)
    sig = (df['prev2_pct'] >= LIMIT) & (df['vol_ratio'] <= 0.6) & (df['close'] > df['ma5']) & (df['pct'] >= -2) & (df['pct'] <= 1) & df['fc5'].notna()
    for j in df.index[sig]:
        s = df.iloc[j]
        rows.append({'date': s['date'], 'state': state_map.get(s['date'], '?'),
                     'mkt5': mkt5_map.get(s['date']), 'ret5': ret5_map.get(s['date']), 'ret20': ret20_map.get(s['date']),
                     'r1': s['fc1']*100 - COST*100, 'r3': s['fc3']*100 - COST*100, 'r5': s['fc5']*100 - COST*100})

print(f'\n==== A2信号分层 (N={len(rows)}) ====')
print(f'{"分组":<16}{"N":>5}{"r1均%":>8}{"r1胜%":>7}{"r3均%":>8}{"r5均%":>8}')
for label, cond in [
    ('按市场状态: 牛', lambda r: r['state'] == '牛'),
    ('按市场状态: 熊', lambda r: r['state'] == '熊'),
    ('按市场状态: 震荡', lambda r: r['state'] == '震荡'),
    ('mkt5>0 (5日强)', lambda r: r['mkt5'] is not None and r['mkt5'] > 0),
    ('mkt5<=0 (5日弱)', lambda r: r['mkt5'] is not None and r['mkt5'] <= 0),
    ('近5日跌>1%', lambda r: r['ret5'] is not None and r['ret5'] < -1),
    ('近5日涨>1%', lambda r: r['ret5'] is not None and r['ret5'] > 1),
    ('近20日跌>3%', lambda r: r['ret20'] is not None and r['ret20'] < -3),
    ('近20日涨>3%', lambda r: r['ret20'] is not None and r['ret20'] > 3),
]:
    sub = [r for r in rows if cond(r)]
    if not sub: continue
    r1 = np.array([r['r1'] for r in sub]); r3 = np.array([r['r3'] for r in sub]); r5 = np.array([r['r5'] for r in sub])
    print(f'{label:<16}{len(sub):>5}{r1.mean():>+8.2f}{(r1>0).mean()*100:>7.1f}{r3.mean():>+8.2f}{r5.mean():>+8.2f}')

# 按年份输出每个状态
print('\n==== 分年×状态 ====')
for yr in ('2024','2025','2026'):
    for st in ('牛','熊','震荡'):
        sub = [r for r in rows if r['date'].startswith(yr) and r['state'] == st]
        if sub:
            r1 = np.array([r['r1'] for r in sub])
            print(f'{yr} {st}: N={len(sub)} r1={r1.mean():+.2f}% 胜率{(r1>0).mean()*100:.1f}%')

# 最新信号日期分布
print('\n==== 信号时间分布 ====')
dates = sorted(set(r['date'] for r in rows))
print('最早:', dates[0], ' 最晚:', dates[-1], ' 共', len(dates), '个交易日有信号')
for yr in ('2024','2025','2026'):
    n = sum(1 for r in rows if r['date'].startswith(yr))
    print(f'{yr}: {n} 个信号')
