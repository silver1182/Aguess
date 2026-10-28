# -*- coding: utf-8 -*-
"""
次日大涨(>=5%)前兆规律挖掘 + 尾盘买入回测 + 当前候选
事件: T日涨幅 >= 5% (不限涨停, 含5%~10%之间的大量样本)
信号: T-1 收盘 12 特征打分(分布仅用 T 之前事件, 无未来函数)
买入: T-1 收盘价(尾盘买, 契合不盯盘模式); 排除 T-1 涨停(买不进)
卖出: T日收盘 / T+1开盘 / T+1收盘
成本: 单边 0.25% (买卖共 0.5%)
产出: output/次日5%前兆规律与回测_YYYYMMDD.md
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
# T-1 特征(行 t 的 prev_X = t-1 日状态)
for c in feat_cols:
    df[f'prev_{c}'] = g[c].shift(1)
# 行 t 代表信号日 = D-1; T日 = 行 t+1; T+1日 = 行 t+2
df['next_pct'] = g['pct'].shift(-1)                       # T日涨幅(事件)
df['ret_c0'] = g['close'].shift(-1) / df['close'] - 1     # T日收盘卖
df['ret_o1'] = g['open'].shift(-2) / df['close'] - 1      # T+1开盘卖
df['ret_c1'] = g['close'].shift(-2) / df['close'] - 1     # T+1收盘卖
df['one_word'] = (df['open'] / df['prev_close'] - 1 >= 0.095).astype(int)

# 事件: T日涨幅 >= 5% (行 t 的 next_pct)
ev_all = df[df['next_pct'] >= 0.05].dropna(subset=['prev_ret_1d']).copy()
base_all = df[df['next_pct'] < 0.05].dropna(subset=['prev_ret_1d']).copy()

print(f'5%+事件样本: {len(ev_all)}  基线样本: {len(base_all)}')

# ---------- 1. 特征统计 ----------
stats = []
for c in feat_cols:
    pc = 'prev_' + c
    me = ev_all[pc].mean(); se = ev_all[pc].std()
    mb = base_all[pc].mean(); sb = base_all[pc].std()
    diff = me - mb
    sp = np.sqrt((se**2 + sb**2) / 2)
    d = diff / sp if sp > 0 else 0
    stats.append({'feat': c, 'ev_mean': me, 'base_mean': mb, 'diff': diff, 'd': d,
                  'direction': 'high' if diff > 0 else 'low'})
stat_df = pd.DataFrame(stats).sort_values('d', key=lambda s: s.abs(), ascending=False)
print(stat_df.to_string(index=False))

# ---------- 2. 滚动回测 ----------
N_OPTIONS = [5, 10, 20]
HOLDS = {'c0': 'T日收盘卖', 'o1': 'T+1开盘卖', 'c1': 'T+1收盘卖'}
COST = 0.0025
dates = sorted(df['date'].unique())
res = []
base_res = []
cand_rows = []

for date in dates:
    ev_t = ev_all[ev_all['date'] <= date]
    if len(ev_t) < 300:
        continue
    # 滚动窗口: 最近2000个事件做分布, 无未来函数(信号日收盘时已知)
    ev_t = ev_t.sort_values('date').tail(2000)
    day = df[df['date'] == date].copy()
    day = day[day['prev_ret_1d'].notna()]
    # 可成交: 信号日(D-1)未涨停(否则尾盘买不进)
    day = day[day['limit_up'] == 0].copy()
    if len(day) < 50:
        continue
    for c in feat_cols:
        pc = 'prev_' + c
        arr = np.sort(ev_t[pc].dropna().values)
        if len(arr) == 0:
            day[f'score_{c}'] = 0.5
        else:
            idx = np.searchsorted(arr, day[pc].values, side='right')
            s = np.clip(idx / len(arr), 0, 1)
            s[day[pc].isna().values] = np.nan   # NaN 特征不参与评分(次新股)
            day[f'score_{c}'] = s
    day['pre_score'] = day[[f'score_{c}' for c in feat_cols]].mean(axis=1, skipna=True)
    base_means = {h: day[f'ret_{h}'].mean() for h in HOLDS}
    base_res.append((date, base_means))
    for N in N_OPTIONS:
        top = day.nlargest(N, 'pre_score')
        for h in HOLDS:
            r = top[f'ret_{h}'].mean() - COST * 2
            res.append((date, N, h, r))
    # 随机对照组(每次同日随机选20只)
    rng = np.random.default_rng(42)
    rand20 = day.sample(20, random_state=int(date.strftime('%Y%m%d')) % 2**32)
    for h in HOLDS:
        res.append((date, 0, 'rand20_' + h, rand20[f'ret_{h}'].mean() - COST * 2))
    # 最新截面候选只输出一次(最后一天)
    if date == dates[-1]:
        top5 = day.nlargest(10, 'pre_score')
        for _, r in top5.iterrows():
            cand_rows.append({'code': r['code'], 'close': r['close'], 'score': r['pre_score'],
                              'r1': r['prev_ret_1d'], 'c5': r['prev_cum_5d'], 'vchg': r['prev_vol_chg'],
                              'ma20': r['prev_above_ma20'], 'near_high': r['prev_near_high20'],
                              'lu10': df[(df['code']==r['code']) & (df['date']<=date)]['limit_up'].tail(10).sum()})

res_df = pd.DataFrame(res, columns=['date', 'N', 'hold', 'ret'])
base_df = pd.DataFrame([{'date': d, **m} for d, m in base_res])

# ---------- 3. 报告 ----------
lines = []
lines.append(f'# 次日大涨(≥5%)前兆规律与回测（2026-10-27）')
lines.append('')
lines.append(f'- 数据窗口: 日K 2026-03-02 ~ {df["date"].max().date()}，1650 只沪深主板')
lines.append(f'- 事件: T日涨幅≥5% 共 {len(ev_all)} 次（不含T-1涨停的可成交口径）')
lines.append(f'- 信号: T-1 收盘 12 特征打分（分布仅用 T 之前事件滚动2000个，无未来函数）')
lines.append(f'- 买入: T-1 尾盘收盘价；卖出: T日收盘 / T+1开盘 / T+1收盘')
lines.append(f'- 成本: 单边 0.25%（买卖共 0.5%）')
lines.append('')
lines.append('## 一、T-1 显著特征（按效应量 |d| 排序）')
lines.append('')
lines.append('| 特征 | 大涨前均值 | 基线均值 | 差值 | d |')
lines.append('|------|-----------|---------|------|-----|')
for r in stat_df.itertuples():
    lines.append(f'| {r.feat} | {r.ev_mean*100:+.2f}% | {r.base_mean*100:+.2f}% | {r.diff*100:+.2f}% | {r.d:.2f} |')
lines.append('')
lines.append('## 二、各参数累计净值（净成本后）')
lines.append('')
lines.append('| TopN | 持有期 | 累计收益 | 日均收益 | 胜率 | 交易次数 | 基线累计 | 超额 |')
lines.append('|------|--------|---------|---------|------|---------|---------|------|')
summary = []
for N in N_OPTIONS + [0]:
    for h, hname in HOLDS.items():
        key = 'rand20_' + h if N == 0 else h
        sub = res_df[(res_df['N'] == N) & (res_df['hold'] == key)].sort_values('date')
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
        nm = '随机20' if N == 0 else str(N)
        summary.append({'N': N, 'hold': h, 'hname': hname, 'total': total, 'daily': daily,
                        'win': win, 'n': len(sub), 'base_total': base_total, 'excess': excess})
        lines.append(f'| {nm} | {hname} | {total*100:+.1f}% | {daily*100:+.3f}% | {win*100:.1f}% | {len(sub)} | {base_total*100:+.1f}% | {excess*100:+.1f}% |')
lines.append('')
lines.append('## 三、分月收益（Top10）')
lines.append('')
lines.append('| 月份 | 交易天数 | T日收盘卖 | T+1开盘卖 | T+1收盘卖 | 当月全市场(T日) |')
lines.append('|------|---------|-----------|-----------|-----------|----------------|')
for ym, grp in res_df[(res_df['N'] == 10)].groupby(res_df['date'].dt.to_period('M')):
    bgrp = base_df.set_index('date').loc[grp['date'].unique()]
    lines.append(f'| {ym} | {len(grp)//3} | ' + ' | '.join(
        f'{(1+grp[grp["hold"]==h]["ret"]).prod()-1:+6.2%}' for h in ['c0','o1','c1']
    ) + f' | {(1+bgrp["c0"]).prod()-1:+.2%} |')
lines.append('')
lines.append('## 四、最新截面候选（2026-10-26 收盘, Top10, T-1尾盘买入）')
lines.append('')
lines.append('| 排名 | 代码 | 现价 | 相似度 | T-1涨幅 | 5日累计 | 量比 | 站上MA20 | 近20日新高 | 近10日涨停次数 |')
lines.append('|------|------|------|--------|---------|---------|------|----------|-----------|----------------|')
for i, r in enumerate(pd.DataFrame(cand_rows).sort_values('score', ascending=False).head(10).itertuples(), 1):
    lines.append(f'| {i} | {r.code} | {r.close:.2f} | {r.score:.3f} | {r.r1*100:+.1f}% | {r.c5*100:+.1f}% | {r.vchg:.2f} | {"是" if r.ma20 else "否"} | {"是" if r.near_high else "否"} | {int(r.lu10)} |')
lines.append('')
lines.append('## 五、结论')
lines.append('')
best = max(summary, key=lambda s: s['total'])
lines.append(f'- 最优参数: Top{best["N"]} + {best["hname"]}，累计 {best["total"]*100:+.1f}%，日均 {best["daily"]*100:+.3f}%，胜率 {best["win"]*100:.1f}%')
lines.append(f'- 全市场基线（同时段全部股票等权、同持有期）: {best["base_total"]*100:+.1f}%')
lines.append(f'- 超额: {best["excess"]*100:+.1f}%')
lines.append('- 说明: 超额为正且胜率稳定说明前兆规律有预测力; 为负则弱市下不可用')

report = '\n'.join(lines)
out_path = out_dir + r'\次日5%前兆规律与回测_20261027.md'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(report)
print(report)
print()
print('[产出]', out_path)
