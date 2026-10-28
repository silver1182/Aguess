# -*- coding: utf-8 -*-
"""
涨停前兆规律回测 backtest_pre_limitup.py
信号: D-1收盘按12特征经验分位打分(分布只用D之前涨停事件, 无未来函数)
买入: D日开盘(排除D-1涨停、D日一字开盘)
卖出: D+1开盘 / D+1收盘 / D+3收盘 三种持有期
组合: 每日截面 Top5/Top10/Top20 等权, 每日换仓
成本: 单边0.25%(买+卖共0.5%)
产出: output/涨停前兆规律回测_YYYYMMDD.md
"""
import json, os
from datetime import datetime
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
df['ma5'] = g['close'].transform(lambda x: x.rolling(5).mean())
df['ma10'] = g['close'].transform(lambda x: x.rolling(10).mean())
df['ma20'] = g['close'].transform(lambda x: x.rolling(20).mean())
df['ret_1d'] = df['close'] / g['close'].shift(1) - 1
df['ret_2d'] = df['close'] / g['close'].shift(2) - 1
df['ret_3d'] = df['close'] / g['close'].shift(3) - 1
df['cum_5d'] = df['close'] / g['close'].shift(5) - 1
df['max_up_5d'] = g['pct'].transform(lambda x: x.rolling(5).max())
df['above_ma5'] = (df['close'] > df['ma5']).astype(int)
df['above_ma10'] = (df['close'] > df['ma10']).astype(int)
df['above_ma20'] = (df['close'] > df['ma20']).astype(int)
df['bias_ma20'] = df['close'] / df['ma20'] - 1
df['shrink_retreat'] = ((df['pct'] < 0) & (df['vol_chg'] < 1)).astype(int)
df['high_20'] = g['high'].transform(lambda x: x.rolling(20).max())
df['near_high20'] = (df['close'] >= df['high_20'] * 0.99).astype(int)
df['limit_up'] = (df['pct'] >= 0.095).astype(int)

feat_cols = ['ret_1d', 'ret_2d', 'ret_3d', 'cum_5d', 'max_up_5d', 'vol_chg',
             'above_ma5', 'above_ma10', 'above_ma20', 'bias_ma20',
             'shrink_retreat', 'near_high20']
# T-1 特征(信号日D-1状态 = 行t的prev_*)
for c in feat_cols:
    df[f'prev_{c}'] = g[c].shift(1)
df['prev_limit_up'] = g['limit_up'].shift(1)   # D-1是否涨停(排除)
# 未来价格: D日开盘买, D+1开/收卖, D+3收卖
df['buy_open'] = df['open']
df['open_gap'] = df['open'] / df['prev_close'] - 1  # D日开盘涨幅(一字过滤)
df['sell_o1'] = g['open'].shift(-1)
df['sell_c1'] = g['close'].shift(-1)
df['sell_c3'] = g['close'].shift(-3)
df['ret_o1'] = df['sell_o1'] / df['buy_open'] - 1
df['ret_c1'] = df['sell_c1'] / df['buy_open'] - 1
df['ret_c3'] = df['sell_c3'] / df['buy_open'] - 1

limitup_df = df[df['limit_up'] == 1]
dates = sorted(df['date'].unique())
N_OPTIONS = [5, 10, 20]
HOLDS = {'o1': '次日开盘卖', 'c1': '次日收盘卖', 'c3': '后3日收盘卖'}
COST = 0.0025

# 滚动分布评分(仅用D之前涨停事件)
res = []  # (date, N, hold, ret)
base_res = []  # (date, hold, 全市场均值)

for date in dates:
    ev_t = limitup_df[limitup_df['date'] < date]
    if len(ev_t) < 300:
        continue
    day = df[df['date'] == date].copy()
    day = day[day['prev_ret_1d'].notna()]
    # 可成交过滤
    day = day[(day['prev_limit_up'] == 0) & (day['open_gap'] < 0.095)].copy()
    if len(day) < 50:
        continue
    for c in feat_cols:
        pc = 'prev_' + c
        arr = np.sort(ev_t[pc].dropna().values)
        if len(arr) == 0:
            day[f'score_{c}'] = 0.5
        else:
            idx = np.searchsorted(arr, day[pc].values, side='right')
            day[f'score_{c}'] = np.clip(idx / len(arr), 0, 1)
    day['pre_score'] = day[[f'score_{c}' for c in feat_cols]].mean(axis=1)
    # 基线: 全市场当日平均收益
    base_means = {h: day[f'ret_{h}'].mean() for h in HOLDS}
    base_res.append((date, base_means))
    for N in N_OPTIONS:
        top = day.nlargest(N, 'pre_score')
        for h in HOLDS:
            r = top[f'ret_{h}'].mean() - COST * 2
            res.append((date, N, h, r))

res_df = pd.DataFrame(res, columns=['date', 'N', 'hold', 'ret'])
base_df = pd.DataFrame([{'date': d, **m} for d, m in base_res])

lines = []
lines.append(f'# 涨停前兆规律回测报告（2026-10-27）')
lines.append('')
lines.append(f'- 数据窗口: 日K 2026-03-02 ~ {df["date"].max().date()}，1650 只沪深主板')
lines.append(f'- 信号: D-1 收盘按 12 特征前兆规律打分（分布仅用 D 之前涨停事件，无未来函数）')
lines.append(f'- 买入: D 日开盘；排除 D-1 涨停、D 日一字开盘（可成交约束）')
lines.append(f'- 组合: 每日 TopN 等权、每日换仓；成本 单边 0.25%（买卖共 0.5%）')
lines.append('')

lines.append('## 一、各参数累计净值（净成本后）')
lines.append('')
lines.append('| TopN | 持有期 | 累计收益 | 日均收益 | 胜率 | 交易次数 | 基线累计 | 超额 |')
lines.append('|------|--------|---------|---------|------|---------|---------|------|')
summary = []
for N in N_OPTIONS:
    for h, hname in HOLDS.items():
        sub = res_df[(res_df['N'] == N) & (res_df['hold'] == h)].sort_values('date')
        sub = sub.dropna(subset=['ret'])
        if len(sub) == 0:
            continue
        nav = (1 + sub['ret']).cumprod()
        total = nav.iloc[-1] - 1
        daily = sub['ret'].mean()
        win = (sub['ret'] > 0).mean()
        base_nav = (1 + base_df[h].dropna()).cumprod()
        base_total = base_nav.iloc[-1] - 1
        excess = total - base_total
        summary.append({'N': N, 'hold': h, 'hname': hname, 'total': total, 'daily': daily,
                        'win': win, 'n': len(sub), 'base_total': base_total, 'excess': excess})
        lines.append(f'| {N} | {hname} | {total*100:+.1f}% | {daily*100:+.3f}% | {win*100:.1f}% | {len(sub)} | {base_total*100:+.1f}% | {excess*100:+.1f}% |')
lines.append('')

lines.append('## 二、分月收益（Top10 · 三种持有期）')
lines.append('')
lines.append('| 月份 | 交易天数 | 次日开盘卖 | 次日收盘卖 | 后3日收盘卖 | 当月全市场(次日开盘卖) |')
lines.append('|------|---------|-----------|-----------|-------------|------------------------|')
for ym, grp in res_df[(res_df['N'] == 10)].groupby(res_df['date'].dt.to_period('M')):
    bgrp = base_df.set_index('date').loc[grp['date'].unique()]
    lines.append(f'| {ym} | {len(grp)//3} | ' + ' | '.join(
        f'{(1+grp[grp["hold"]==h]["ret"]).prod()-1:+6.2%}' for h in ['o1','c1','c3']
    ) + f' | {(1+bgrp["o1"]).prod()-1:+.2%} |')
lines.append('')

lines.append('## 三、结论')
lines.append('')
best = max(summary, key=lambda s: s['total'])
lines.append(f'- 最优参数: Top{best["N"]} + {best["hname"]}，累计 {best["total"]*100:+.1f}%，日均 {best["daily"]*100:+.3f}%，胜率 {best["win"]*100:.1f}%')
lines.append(f'- 全市场基线（同时段全部股票等权、同持有期）: {best["base_total"]*100:+.1f}%')
lines.append(f'- 超额: {best["excess"]*100:+.1f}%')
lines.append('- 说明: 若超额为正且胜率稳定，说明前兆规律在样本期内有预测力；若为负，说明该规律在弱市下不可用')

report = '\n'.join(lines)
out_path = out_dir + r'\涨停前兆规律回测_20261027.md'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(report)
print(report)
print()
print('[产出]', out_path)
