# -*- coding: utf-8 -*-
"""
v9 七因子日频化回测: 把已验证正期望的周频因子改日频打分
因子(日频近似): shrink_up缩量上涨 / amount_20d活跃度 / max_up_20d弹性(钟形)
                expand_down放量下跌(惩罚) / vol_chg_std量能稳定 / close_pos尾盘强收
打分: 滚动60日全体样本分布分位, 无未来函数
买入: T-1尾盘; 卖出: T收盘/T+1开盘/T+1收盘; 成本0.5%
同时验证周内持有(周一尾盘买周五收盘卖, 对照周K结论)
"""
import json, os
import pandas as pd
import numpy as np

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
temp_dir = base + r'\temp'
out_dir = base + r'\output'
os.makedirs(out_dir, exist_ok=True)

with open(temp_dir + r'\kline_cache_em.json', encoding='utf-8') as f:
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
df['ret_1d'] = df['close'] / g['close'].shift(1) - 1
df['limit_up'] = (df['pct'] >= 0.095).astype(int)
df['shrink_up'] = ((df['pct'] > 0) & (df['vol_chg'] < 1)).astype(int)
df['amount'] = df['close'] * df['volume']
df['amount_20d'] = g['amount'].transform(lambda x: x.rolling(20).mean())
df['max_up_20d'] = g['pct'].transform(lambda x: x.rolling(20).max())
df['expand_down'] = ((df['pct'] < -0.02) & (df['vol_chg'] > 1.5)).astype(int)
df['vol_chg_std'] = g['vol_chg'].transform(lambda x: x.rolling(20).std())
df['close_pos'] = (df['close'] - df['low']) / (df['high'] - df['low']).replace(0, np.nan)
# 未来收益
df['ret_c0'] = g['close'].shift(-1) / df['close'] - 1
df['ret_o1'] = g['open'].shift(-2) / df['close'] - 1
df['ret_c1'] = g['close'].shift(-2) / df['close'] - 1
# 周五(周内持有验证): 找周最后一个交易日
df['weekday'] = df['date'].dt.weekday
last_of_week = df.groupby(df['date'].dt.to_period('W'))['date'].transform('max')
df['is_fri'] = (df['date'] == last_of_week).astype(int)
df['ret_weekend'] = g['close'].shift(-5) / df['close'] - 1   # 周一尾盘买→下周五收盘(约5交易日)

FACTOR_DIR = {
    'shrink_up': 'high',
    'amount_20d': 'high',
    'max_up_20d': 'bell',
    'expand_down': 'low',
    'vol_chg_std': 'low',
    'close_pos': 'high',
}
COST = 0.0025
HOLDS = {'c0': 'T收盘', 'o1': 'T+1开盘', 'c1': 'T+1收盘'}
dates = sorted(df['date'].unique())
dates = [d for d in dates if d >= dates[20]]

def pct_rank(arr, x):
    arr = np.sort(arr)
    if len(arr) == 0:
        return 0.5
    return np.clip(np.searchsorted(arr, x, side='right') / len(arr), 0, 1)

results = []
for date in dates:
    day = df[df['date'] == date].copy()
    day = day[day['shrink_up'].notna() & day['amount_20d'].notna() & day['max_up_20d'].notna()
              & day['vol_chg_std'].notna() & day['close_pos'].notna()]
    day = day[day['limit_up'] == 0]   # 尾盘买不进涨停
    if len(day) < 100:
        continue
    hist = df[(df['date'] < date) & (df['date'] >= date - pd.Timedelta(days=120))]
    hist = hist.dropna(subset=['shrink_up', 'amount_20d', 'max_up_20d', 'expand_down', 'vol_chg_std', 'close_pos'])
    score = np.zeros(len(day))
    for c, direction in FACTOR_DIR.items():
        r = pct_rank(hist[c].values, day[c].values)
        if direction == 'high':
            s = r
        elif direction == 'low':
            s = 1 - r
        else:  # bell 钟形
            s = 1 - np.abs(r - 0.5) * 2
        score += s
    day['v9score'] = score / len(FACTOR_DIR)
    for N in [5, 10]:
        top = day.nlargest(N, 'v9score')
        for h in HOLDS:
            r = top[f'ret_{h}'].mean() - COST * 2
            results.append((date, N, h, r))
    # 周内持有: 仅周一(weekday==0) 尾盘买
    mon = day[day['weekday'] == 0]
    if len(mon) > 0:
        topm = mon.nlargest(10, 'v9score')
        results.append((date, 10, '周内持有', topm['ret_weekend'].mean() - COST * 2))

res_df = pd.DataFrame(results, columns=['date', 'N', 'hold', 'ret'])
print('=== v9日频化 日频持有 ===')
for N in [5, 10]:
    for h, hname in HOLDS.items():
        sub = res_df[(res_df['N'] == N) & (res_df['hold'] == h)].dropna(subset=['ret']).sort_values('date')
        if len(sub) == 0:
            continue
        nav = (1 + sub['ret']).cumprod()
        print(f'Top{N} {hname}: 累计{nav.iloc[-1]-1:+.1%} 日均{sub["ret"].mean():+.3%} 胜率{(sub["ret"]>0).mean():.1%} 天数{len(sub)}')
print('=== v9日频化 周内持有(周一买下周五卖) ===')
sub = res_df[(res_df['hold'] == '周内持有')].dropna(subset=['ret']).sort_values('date')
if len(sub) > 0:
    nav = (1 + sub['ret']).cumprod()
    print(f'Top10 周内持有: 累计{nav.iloc[-1]-1:+.1%} 周均{sub["ret"].mean():+.3%} 胜率{(sub["ret"]>0).mean():.1%} 周数{len(sub)}')
else:
    print('无数据')

# 分月 Top10 T收盘
print('=== 分月 Top10 T收盘 ===')
for ym, grp in res_df[(res_df['N'] == 10) & (res_df['hold'] == 'c0')].groupby(res_df['date'].dt.to_period('M')):
    nav = (1 + grp['ret']).cumprod()
    print(f'{ym}: {(nav.iloc[-1]-1):+.2%} (n={len(grp)})')

res_df.to_csv(out_dir + r'\v9日频化回测_20261027.csv', index=False, encoding='utf-8-sig')
print()
print('[产出]', out_dir + r'\v9日频化回测_20261027.csv')
