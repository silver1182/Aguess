# -*- coding: utf-8 -*-
"""
热点追踪双方案回测 hot_ab_backtest.py
A. 周频板块轮动: 周五聚合近5日涨停池reason标签 -> Top3热点概念 -> 买成分中当日未涨停(涨0~6%)主板票, 周一开盘买/周五收盘卖
B. 日频涨停潮扩散: 当日涨停池Top3概念 -> 当日尾盘买成分中未涨停(收盘涨0~6%)主板票, 持2日
区间: 2026-07-01 ~ 2026-10-23 (77交易日)  成本: 单边0.25%
"""
import json, os
from collections import Counter
import pandas as pd
import numpy as np

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
temp_dir = base + r'\temp'
out_dir = base + r'\output'
os.makedirs(out_dir, exist_ok=True)
COST = 0.0025

def is_main(code):
    return code.startswith(('60', '00'))

def split_tags(x):
    if not x:
        return []
    return [t.strip() for t in str(x).split('+') if t.strip()]

# ---- 数据加载 ----
lp = json.load(open(temp_dir + r'\limitup_pools_ext.json', encoding='utf-8'))
pools_raw = lp['pools']
pools = {}
for k, v in pools_raw.items():
    pools[k[:4] + '-' + k[4:6] + '-' + k[6:8]] = v
pool_dates = sorted(pools.keys())

cache = json.load(open(temp_dir + r'\kline_cache_em.json', encoding='utf-8'))
all_bars = []
for code, bars in cache.items():
    for b in bars:
        b['code'] = code
        all_bars.append(b)
df = pd.DataFrame(all_bars)
df['date'] = pd.to_datetime(df['date'])
df = df[df['close'].notna()].sort_values(['code', 'date']).reset_index(drop=True)

trade_days = sorted(df['date'].unique())
td_str = [d.strftime('%Y-%m-%d') for d in trade_days]
td_index = {d: i for i, d in enumerate(td_str)}

# ---- 涨停池按日期 -> 标签成分/计数 ----
date_tag_codes = {}
date_tags = {}
for dt, lst in pools.items():
    tc = {}
    for x in lst:
        if not is_main(x['code']):
            continue
        for t in split_tags(x.get('reason')):
            tc.setdefault(t, set()).add(x['code'])
    date_tag_codes[dt] = tc
    date_tags[dt] = {t: len(c) for t, c in tc.items()}

# 排除财务/政策类噪音标签
noise_tags = {'中报预增', '业绩增长', '半年报增长', '半年报预增', '中报扭亏', '中报增长',
              '一季报增长', '一季报扭亏', '三季报增长', '年报增长', '年报预增', '业绩预增',
              '扭亏', '预增', '高送转', '分红', '回购', '增持', '央企', '国企改革', '上海国资',
              '深圳国资', '国资', '低价股', '次新股', '破净', 'ST', '举牌', '股权转让', '重组', '并购重组'}

def top_tags(tag_cnt, n=3):
    return [t for t, _ in tag_cnt.most_common(n * 3) if t not in noise_tags][:n]

# 快速访问日K: code -> date -> bar
kmap = {}
for r in df.itertuples():
    kmap.setdefault(r.code, {})[r.date] = r

def get_price(code, dt, field):
    b = kmap.get(code, {}).get(pd.Timestamp(dt))
    return None if b is None else getattr(b, field)

# ================= 方案A: 周频板块轮动 =================
# 涨停池日期按周分组, 取每周最后一天为选股日
pds = pd.Series(pd.to_datetime(pool_dates))
pds_yw = pds.dt.strftime('%Y-%U')
week_grp = pds.groupby(pds_yw)
week_last_dates = [g.max().strftime('%Y-%m-%d') for _, g in week_grp]

A_rows = []
for wd in week_last_dates:
    if wd not in td_index:
        continue
    buy_idx = td_index[wd] + 1
    sell_idx = buy_idx + 4
    if sell_idx >= len(td_str):
        continue  # 最后一周无卖出数据
    buy_d, sell_d = td_str[buy_idx], td_str[sell_idx]
    # 近5个涨停池交易日
    di = pool_dates.index(wd)
    win = pool_dates[max(0, di - 4): di + 1]
    tag_cnt = Counter()
    for dt in win:
        for t, c in date_tags[dt].items():
            if t in noise_tags:
                continue
            tag_cnt[t] += c
    if not tag_cnt:
        continue
    top3 = top_tags(tag_cnt, 3)
    cand = set()
    for dt in win:
        for t in top3:
            cand |= date_tag_codes[dt].get(t, set())
    zt_today = set(x['code'] for x in pools.get(wd, []))
    cand = cand - zt_today
    # 周五当日涨幅 0~6% 可成交
    picks = []
    for c in cand:
        pc = get_price(c, wd, 'pct')
        if pc is None or not (0 < pc < 6):
            continue
        po = get_price(c, buy_d, 'open')
        sc = get_price(c, sell_d, 'close')
        if po is None or sc is None or po <= 0:
            continue
        picks.append((c, pc, po, sc))
    picks.sort(key=lambda x: x[1], reverse=True)
    picks = picks[:5]
    if not picks:
        continue
    ret = np.mean([sc / po - 1 for _, _, po, sc in picks]) - 2 * COST
    # 基准: 全市场周频持有
    bret = []
    for c in kmap:
        po = get_price(c, buy_d, 'open')
        sc = get_price(c, sell_d, 'close')
        if po and sc and po > 0:
            bret.append(sc / po - 1)
    bench = np.mean(bret) - 2 * COST if bret else 0.0
    A_rows.append({'week': wd, 'top': ','.join(top3), 'n': len(picks),
                   'ret': ret, 'bench': bench, 'excess': ret - bench})

A = pd.DataFrame(A_rows)
nav = (1 + A['ret']).cumprod()
mdd = ((nav / nav.cummax()) - 1).min()
nA = len(A)
cagr = nav.iloc[-1] ** (52 / nA) - 1 if nA else 0

# ================= 方案B: 日频涨停潮扩散 =================
B_rows = []
for i, d in enumerate(pool_dates):
    if d not in td_index:
        continue
    buy_idx = td_index[d]
    sell_idx = buy_idx + 2
    if sell_idx >= len(td_str):
        continue
    buy_d, sell_d = td_str[buy_idx], td_str[sell_idx]
    tag_cnt = Counter({t: c for t, c in date_tags.get(d, {}).items() if t not in noise_tags})
    if not tag_cnt:
        continue
    top3 = top_tags(tag_cnt, 3)
    # 成分股: 近10个交易日内在该标签涨停过的主板票
    di = pool_dates.index(d)
    win10 = pool_dates[max(0, di - 9): di + 1]
    cand = set()
    for dt in win10:
        for t in top3:
            cand |= date_tag_codes.get(dt, {}).get(t, set())
    zt_day = set(x['code'] for x in pools.get(d, []))
    cand = cand - zt_day
    picks = []
    for c in cand:
        cl = get_price(c, buy_d, 'close')
        pc = get_price(c, buy_d, 'pct')
        if cl is None or pc is None or cl <= 0:
            continue
        if not (0 < pc < 6):
            continue  # 当日收盘温和可尾盘成交
        sc = get_price(c, sell_d, 'close')
        if sc is None:
            continue
        picks.append((c, pc, cl, sc))
    picks.sort(key=lambda x: x[1], reverse=True)
    picks = picks[:5]
    if not picks:
        continue
    ret = np.mean([sc / cl - 1 for _, _, cl, sc in picks]) - 2 * COST
    bret = []
    for c in kmap:
        cl = get_price(c, buy_d, 'close')
        sc = get_price(c, sell_d, 'close')
        if cl and sc and cl > 0:
            bret.append(sc / cl - 1)
    bench = np.mean(bret) - 2 * COST if bret else 0.0
    B_rows.append({'date': d, 'top': ','.join(top3), 'n': len(picks),
                   'ret': ret, 'bench': bench, 'excess': ret - bench})

B = pd.DataFrame(B_rows)
navB = (1 + B['ret']).cumprod()
mddB = ((navB / navB.cummax()) - 1).min()
nB = len(B)
# 每2个交易日一个周期 -> 年化约 250/2=125 周期/年
cagrB = navB.iloc[-1] ** (125 / nB) - 1 if nB else 0

# ================= 输出 =================
lines = []
lines.append('# 热点追踪双方案回测报告')
lines.append('')
lines.append(f'- 区间: {pool_dates[0]} ~ {pool_dates[-1]}（{len(pool_dates)}交易日）')
lines.append(f'- 样本: 沪深主板 1650 只; 涨停池 5086 条')
lines.append(f'- 成本: 单边 0.25%')
lines.append('')
lines.append('## 方案A: 周频板块轮动（Top3概念, 买涨0~6%未涨停, 周一买/周五卖, Top5）')
if nA:
    lines.append(f'- 周数: {nA}  累计: {(nav.iloc[-1]-1)*100:.1f}%  年化: {cagr*100:.1f}%  回撤: {mdd*100:.1f}%  周胜率: {(A["ret"]>0).mean()*100:.0f}%')
    lines.append(f'- 周均: {A["ret"].mean()*100:.2f}%  基准周均: {A["bench"].mean()*100:.2f}%  周均超额: {A["excess"].mean()*100:.2f}%')
    lines.append('')
    lines.append('| 选股周 | 热点概念 | 持仓数 | 组合收益 | 基准 | 超额 |')
    lines.append('|--------|----------|--------|----------|------|------|')
    for r in A.itertuples():
        lines.append(f'| {r.week} | {r.top} | {r.n} | {r.ret*100:.2f}% | {r.bench*100:.2f}% | {r.excess*100:.2f}% |')
else:
    lines.append('- 无有效周样本')
lines.append('')
lines.append('## 方案B: 日频涨停潮扩散（当日Top3概念, 当日尾盘买, 持2日, Top5）')
if nB:
    lines.append(f'- 周期数: {nB}  累计: {(navB.iloc[-1]-1)*100:.1f}%  年化: {cagrB*100:.1f}%  回撤: {mddB*100:.1f}%  周期胜率: {(B["ret"]>0).mean()*100:.0f}%')
    lines.append(f'- 周期均: {B["ret"].mean()*100:.2f}%  基准周期均: {B["bench"].mean()*100:.2f}%  周期均超额: {B["excess"].mean()*100:.2f}%')
    lines.append('')
    B['month'] = B['date'].str[:7]
    lines.append('| 月份 | 周期数 | 组合累计 | 基准累计 | 超额累计 |')
    lines.append('|------|--------|----------|----------|----------|')
    for m, sub in B.groupby('month'):
        nav_m = (1 + sub['ret']).cumprod()
        nav_bm = (1 + sub['bench']).cumprod()
        lines.append(f'| {m} | {len(sub)} | {(nav_m.iloc[-1]-1)*100:.1f}% | {(nav_bm.iloc[-1]-1)*100:.1f}% | {(nav_m.iloc[-1]-nav_bm.iloc[-1])*100:.1f}% |')
else:
    lines.append('- 无有效周期样本')

report = '\n'.join(lines)
out_path = out_dir + r'\热点追踪双方案回测_20261027.md'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(report)
print(report)
print()
print('[产出]', out_path)
