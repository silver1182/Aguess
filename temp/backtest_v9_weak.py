# -*- coding: utf-8 -*-
"""
v9 周频策略在 2026-03~10 弱市窗口的表现确认(用3年周K缓存)
对照: 全窗口(2022-01~2026-10) vs 弱市窗口(2026-03~2026-10)
七因子(原版): shrink_up / amount_20d / max_up_20d / expand_down /
              tail_return / vol_chg_std / overnight_gap
"""
import json, os
import pandas as pd
import numpy as np

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
temp_dir = base + r'\temp'
out_dir = base + r'\output'
os.makedirs(out_dir, exist_ok=True)

with open(temp_dir + r'\week_kline_long.json', encoding='utf-8') as f:
    k = json.load(f)
rows = []
for code, bars in k.items():
    for b in bars:
        b['code'] = code
        rows.append(b)
df = pd.DataFrame(rows)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['code', 'date']).reset_index(drop=True)
df = df[df['close'].notna()].copy()

g = df.groupby('code')
df['prev_close'] = g['close'].shift(1)
df['prev_vol'] = g['volume'].shift(1)
df['pct'] = df['close'] / df['prev_close'] - 1
df['vol_chg'] = df['volume'] / df['prev_vol']
df['ret_1w'] = df['pct']
# 七因子(周频原版)
df['shrink_up'] = ((df['pct'] > 0) & (df['vol_chg'] < 1)).astype(int)
df['amount'] = df['close'] * df['volume']
df['amount_20d'] = g['amount'].transform(lambda x: x.rolling(20).mean())
df['max_up_20d'] = g['pct'].transform(lambda x: x.rolling(20).max())
df['expand_down'] = ((df['pct'] < -0.03) & (df['vol_chg'] > 1.5)).astype(int)
df['tail_return'] = g['pct'].transform(lambda x: x.rolling(5).mean()) * 0  # 无分钟数据置0
df['vol_chg_std'] = g['vol_chg'].transform(lambda x: x.rolling(20).std())
df['overnight_gap'] = 0.0
# 未来收益: 本周收盘信号 → 下周一开盘买(近似用下周开盘) → 下周五收盘卖
df['next_open'] = g['open'].shift(-1)
df['next_close'] = g['close'].shift(-1)
df['ret_week'] = df['next_close'] / df['next_open'] - 1   # 持有整周(下周开盘→收盘)
df['ret_week_c'] = df['next_close'] / df['close'] - 1     # 本周收盘买→下周收盘卖(近似)

FACTOR_DIR = {
    'shrink_up': 'high',
    'amount_20d': 'high',
    'max_up_20d': 'bell',
    'expand_down': 'low',
    'tail_return': 'high',
    'vol_chg_std': 'low',
    'overnight_gap': 'high',
}

def pct_rank(arr, x):
    arr = np.sort(arr)
    if len(arr) == 0:
        return 0.5
    return np.clip(np.searchsorted(arr, x, side='right') / len(arr), 0, 1)

COST = 0.0025
dates = sorted(df['date'].unique())
# 全窗口回测(滚动前60周样本)
def run_backtest(df, dates, label, topn=5, stop=None, mkt_filter=None):
    rows_out = []
    for i, date in enumerate(dates):
        day = df[df['date'] == date].copy()
        day = day.dropna(subset=['shrink_up', 'amount_20d', 'max_up_20d', 'expand_down', 'vol_chg_std'])
        if len(day) < 200:
            continue
        hist = df[(df['date'] < date)].tail(3000)
        hist = hist.dropna(subset=['shrink_up', 'amount_20d', 'max_up_20d', 'expand_down', 'vol_chg_std'])
        score = np.zeros(len(day))
        for c, direction in FACTOR_DIR.items():
            r = pct_rank(hist[c].values, day[c].values)
            s = r if direction == 'high' else (1 - r if direction == 'low' else 1 - np.abs(r - 0.5) * 2)
            score += s
        day['v9'] = score / len(FACTOR_DIR)
        if mkt_filter:
            mkt = day['close'].mean()
            mkt_prev = df[df['date'] < date]['close'].groupby(df[df['date'] < date]['code']).mean().mean()
            if mkt <= mkt_prev:
                rows_out.append({'date': date, 'ret': 0.0, 'n': 0})
                continue
        top = day.nlargest(topn, 'v9')
        r = top['ret_week'].mean() - COST * 2
        rows_out.append({'date': date, 'ret': r, 'n': len(top)})
    rdf = pd.DataFrame(rows_out).dropna(subset=['ret'])
    nav = (1 + rdf['ret']).cumprod()
    print(f'[{label}] 周数{len(rdf)} 累计{nav.iloc[-1]-1:+.1%} 周均{rdf["ret"].mean():+.3%} 胜率{(rdf["ret"]>0).mean():.1%}')
    return rdf

# 全窗口
r_full = run_backtest(df, dates, '全窗口2022-01~2026-10')
# 弱市窗口
weak = [d for d in dates if d >= pd.Timestamp('2026-03-01')]
r_weak = run_backtest(df, weak, '弱市2026-03~10')
# 弱市+市况过滤
r_weak_f = run_backtest(df, weak, '弱市+市况过滤', mkt_filter=True)

# 周K缓存里2026-10数据到哪
print('最近周K日期:', df['date'].max())
