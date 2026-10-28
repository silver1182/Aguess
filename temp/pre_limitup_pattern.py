# -*- coding: utf-8 -*-
"""
涨停前兆规律挖掘 + 当前候选筛选
数据: kline_cache_em.json (1650主板, 2026-03~10-26) + limitup_pools_ext.json(名称映射)
事件: 日K收盘涨幅 >= 9.5% 视为涨停(主板10%, 排除ST 5%涨停)
方法: 涨停日前一交易日(T-1)量价特征 vs 全市场非涨停日基线, 找显著前兆; 再用最新收盘截面打分
产出: output/涨停前兆规律与候选_YYYYMMDD.md
"""
import json, os
from datetime import datetime
import pandas as pd
import numpy as np

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
temp_dir = base + r'\temp'
out_dir = base + r'\output'
os.makedirs(out_dir, exist_ok=True)

# 名称映射(涨停池里的)
try:
    with open(temp_dir + r'\limitup_pools_ext.json', encoding='utf-8') as f:
        lp = json.load(f)
    name_map = {}
    for d, arr in lp['pools'].items():
        for it in arr:
            name_map.setdefault(it['code'], it['name'])
except Exception:
    name_map = {}

# ---------- 1. 日K全量 ----------
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
# T-1 特征(涨停日的前一日)
for c in feat_cols:
    df[f'prev_{c}'] = g[c].shift(1)

# ---------- 2. 涨停事件 vs 基线 ----------
ev = df[df['limit_up'] == 1].dropna(subset=['prev_ret_1d']).copy()
base_df = df[(df['limit_up'] == 0)].dropna(subset=['prev_ret_1d']).copy()

print(f'涨停事件样本: {len(ev)}  基线样本: {len(base_df)}')

stats = []
for c in feat_cols:
    pc = 'prev_' + c
    me = ev[pc].mean()
    se = ev[pc].std()
    mb = base_df[pc].mean()
    sb = base_df[pc].std()
    diff = me - mb
    # 池化效应量 Cohen's d
    sp = np.sqrt((se**2 + sb**2) / 2)
    d = diff / sp if sp > 0 else 0
    stats.append({'feat': c, 'ev_mean': me, 'base_mean': mb, 'diff': diff, 'd': d,
                  'direction': 'high' if diff > 0 else 'low'})

stat_df = pd.DataFrame(stats).sort_values('d', key=lambda s: s.abs(), ascending=False)
print(stat_df.to_string(index=False))

# ---------- 3. 前兆打分(最新截面 = 最后交易日) ----------
last_date = df['date'].max()
last = df[df['date'] == last_date].dropna(subset=['prev_ret_1d']).copy()
# 对每个特征: 计算当前值相对涨停前分布的位置(0~1), 方向按统计显著
score_cols = []
for r in stat_df.itertuples():
    c = r.feat
    pc = 'prev_' + c
    ev_arr = ev[pc].dropna().values
    x = last[pc]
    if r.direction == 'high':
        # 当前值在涨停前样本中的经验分位(越高越像涨停前)
        score = x.apply(lambda v: float((ev_arr <= v).mean()))
    else:
        score = x.apply(lambda v: float((ev_arr >= v).mean()))
    last[f'score_{c}'] = score.clip(0, 1)
    score_cols.append(f'score_{c}')

last['pre_score'] = last[score_cols].mean(axis=1)
# 近10日是否涨停过(过滤已大涨)
df['lu_10d'] = g['limit_up'].transform(lambda x: x.rolling(10).sum())
last = last.merge(df[['code', 'date', 'lu_10d']], on=['code', 'date'], how='left')

last['name'] = last['code'].map(name_map).fillna('')
cand = last.sort_values('pre_score', ascending=False).copy()

# 主榜: 近10日未涨停过的; 附榜: 已涨停过的(可能二波)
fresh = cand[cand['lu_10d'] == 0]
again = cand[cand['lu_10d'] > 0]

top_fresh = fresh.head(20)
top_again = again.head(10)

# ---------- 4. 输出报告 ----------
lines = []
lines.append(f'# 涨停前兆规律与当前候选（2026-10-27 生成）')
lines.append('')
lines.append(f'- 数据窗口: 日K 2026-03-02 ~ {last_date.date()}，1650 只沪深主板')
lines.append(f'- 涨停事件: 日涨幅≥9.5% 共 {len(ev)} 次（剔除ST 5%涨停）')
lines.append(f'- 分析方法: 涨停日前一交易日(T-1)量价特征 vs 全市场基线，Cohen d 效应量排序')
lines.append('')
lines.append('## 一、涨停前 T-1 显著特征（按效应量 |d| 排序）')
lines.append('')
lines.append('| 特征 | 含义 | 涨停前均值 | 基线均值 | 差值 | d | 方向 |')
lines.append('|------|------|-----------|---------|------|-----|------|')
for r in stat_df.itertuples():
    lines.append(f'| {r.feat} | {r.feat} | {r.ev_mean:.4f} | {r.base_mean:.4f} | {r.diff:+.4f} | {r.d:.2f} | {r.direction} |')
lines.append('')
lines.append('## 二、当前处于“大涨前节点”的候选（近10日未涨停）Top20')
lines.append('')
lines.append('| 排名 | 代码 | 名称 | 现价 | 相似度 | T-1涨幅 | 5日累计 | 量比 | 站上MA20 | 缩量回调 | 20日新高 |')
lines.append('|------|------|------|------|--------|---------|---------|------|----------|----------|----------|')
for i, r in enumerate(top_fresh.itertuples(), 1):
    lines.append(f'| {i} | {r.code} | {r.name} | {r.close:.2f} | {r.pre_score:.3f} | {r.prev_ret_1d*100:+.1f}% | {r.prev_cum_5d*100:+.1f}% | {r.prev_vol_chg:.2f} | {"是" if r.prev_above_ma20 else "否"} | {"是" if r.prev_shrink_retreat else "否"} | {"是" if r.prev_near_high20 else "否"} |')
lines.append('')
lines.append('## 三、近期已涨停但仍在相似状态的（可能二波，参考）Top10')
lines.append('')
lines.append('| 排名 | 代码 | 名称 | 现价 | 相似度 | 近10日涨停次数 | T-1涨幅 | 5日累计 | 量比 |')
lines.append('|------|------|------|------|--------|----------------|---------|---------|------|')
for i, r in enumerate(top_again.itertuples(), 1):
    lines.append(f'| {i} | {r.code} | {r.name} | {r.close:.2f} | {r.pre_score:.3f} | {int(r.lu_10d)} | {r.prev_ret_1d*100:+.1f}% | {r.prev_cum_5d*100:+.1f}% | {r.prev_vol_chg:.2f} |')
lines.append('')
lines.append('## 四、使用说明与局限')
lines.append('- 相似度 0~1：越接近 1 越像历史涨停前一夜的状态；按 12 个特征等权平均')
lines.append('- 候选基于 2026-10-26 收盘截面，实际买点需次日开盘确认，仍有回落风险')
lines.append('- 特征为统计相关而非因果；弱市环境下涨停次日溢价可能转负')
lines.append('- 仅沪深主板(60/00)，不含创业板/科创板；ST 以名称标记为准')
report = '\n'.join(lines)
out_path = out_dir + r'\涨停前兆规律与候选_20261027.md'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(report)
print(report)
print()
print('[产出]', out_path)

# 存候选便于后续
cand[['code', 'name', 'date', 'close', 'pre_score', 'lu_10d'] + ['prev_' + c for c in feat_cols]].to_json(temp_dir + r'\pre_limitup_candidates.json', orient='records', force_ascii=False)
