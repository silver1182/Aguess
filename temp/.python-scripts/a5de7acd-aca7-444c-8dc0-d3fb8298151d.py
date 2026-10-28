# -*- coding: utf-8 -*-
import json, os
import pandas as pd
import numpy as np

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
temp_dir = base + r'\temp'

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
for c in feat_cols:
    df[f'prev_{c}'] = g[c].shift(1)
df['prev_limit_up'] = g['limit_up'].shift(1)
df['buy_open'] = df['open']
df['open_gap'] = df['open'] / df['prev_close'] - 1
df['sell_o1'] = g['open'].shift(-1)
df['sell_c1'] = g['close'].shift(-1)
df['sell_c3'] = g['close'].shift(-3)
df['ret_o1'] = df['sell_o1'] / df['buy_open'] - 1
df['ret_c1'] = df['sell_c1'] / df['buy_open'] - 1
df['ret_c3'] = df['sell_c3'] / df['buy_open'] - 1
df['limit_up_next'] = g['limit_up'].shift(-1)   # D+1 是否涨停
df['open_ret_d'] = df['close'] / df['open'] - 1  # D日日内

limitup_df = df[df['limit_up'] == 1]
dates = sorted(df['date'].unique())

picks = []   # 每个交易日 Top5 选中的候选
base_stats = []
for date in dates:
    ev_t = limitup_df[limitup_df['date'] < date]
    if len(ev_t) < 300:
        continue
    day = df[df['date'] == date].copy()
    day = day[day['prev_ret_1d'].notna()]
    day = day[(day['prev_limit_up'] == 0) & (day['open_gap'] < 0.095)].copy()
    if len(day) < 50:
        continue
    for c in feat_cols:
        pc = 'prev_' + c
        arr = np.sort(ev_t[pc].dropna().values)
        idx = np.searchsorted(arr, day[pc].values, side='right')
        day[f'score_{c}'] = np.clip(idx / len(arr), 0, 1)
    day['pre_score'] = day[[f'score_{c}' for c in feat_cols]].mean(axis=1)
    top5 = day.nlargest(5, 'pre_score')
    for _, r in top5.iterrows():
        picks.append({
            'date': date,
            'code': r['code'],
            'gap_d': r['open_gap'],          # D日开盘高开幅度
            'intraday_d': r['open_ret_d'],   # D日日内
            'ret_o1': r['ret_o1'],
            'ret_c1': r['ret_c1'],
            'lu_d': r['limit_up'],           # D日是否涨停
            'lu_next': r['limit_up_next'],   # D+1 是否涨停
        })

p = pd.DataFrame(picks)
print('候选总数(交易日x5):', len(p))

# 1) 次日(D日) 真正涨停占比
print('\n=== 命中率 ===')
print(f'D日当天涨停占比: {p["lu_d"].mean()*100:.2f}%')
print(f'D+1 涨停占比:    {p["lu_next"].mean()*100:.2f}%')
print(f'两天内任意一天涨停: {((p["lu_d"]==1)|(p["lu_next"]==1)).mean()*100:.2f}%')

# 全市场 D 日涨停比例(可比截面)
base_lu = []
for date in dates:
    ev_t = limitup_df[limitup_df['date'] < date]
    if len(ev_t) < 300: continue
    day = df[df['date'] == date].copy()
    day = day[day['prev_ret_1d'].notna()]
    day = day[(day['prev_limit_up']==0)&(day['open_gap']<0.095)]
    if len(day) < 50: continue
    base_lu.append(day['limit_up'].mean())
print(f'同期全市场 D日涨停占比均值: {np.mean(base_lu)*100:.2f}%')

# 2) 买入成本与收益拆解
print('\n=== 收益拆解(Top5) ===')
print(f'D日开盘平均高开:   {p["gap_d"].mean()*100:+.2f}%')
print(f'D日日内平均(开->收): {p["intraday_d"].mean()*100:+.2f}%')
print(f'次日开盘卖平均(净):  {(p["ret_o1"]-0.005).mean()*100:+.2f}%')
print(f'次日收盘卖平均(净):  {(p["ret_c1"]-0.005).mean()*100:+.2f}%')

# 3) 命中涨停 vs 未命中的收益
hit = p[p['lu_d']==1]
miss = p[p['lu_d']==0]
print('\n=== 命中 vs 未命中 ===')
print(f'命中组(D日涨停): 次日开盘卖 {(hit["ret_o1"].mean()-0.005)*100:+.2f}% (n={len(hit)})')
print(f'未命中组(D日未涨停): 次日开盘卖 {(miss["ret_o1"].mean()-0.005)*100:+.2f}% (n={len(miss)})')
print(f'未命中组 D日日内平均: {miss["intraday_d"].mean()*100:+.2f}%')

# 4) 分月命中率与收益
print('\n=== 分月(Top5) ===')
for ym, grp in p.groupby(p['date'].dt.to_period('M')):
    print(f'{ym}: D日涨停率 {grp["lu_d"].mean()*100:5.1f}% | 次日开卖净 {((grp["ret_o1"]-0.005).mean())*100:+6.2f}% | n={len(grp)}')

# 5) 强弱市对比
print('\n=== 强弱市对比(以全市场当日均值分组) ===')
p['mkt_ret'] = np.nan
for date in dates:
    day = df[df['date']==date]
    if len(day)==0: continue
    p.loc[p['date']==date, 'mkt_ret'] = day['ret_c1'].mean()  # 用当日全市场收益近似
strong = p[p['mkt_ret'] > p['mkt_ret'].median()]
weak = p[p['mkt_ret'] <= p['mkt_ret'].median()]
print(f'偏强市({len(strong)}笔): 次日开卖净 {(strong["ret_o1"].mean()-0.005)*100:+.2f}% | D日涨停率 {strong["lu_d"].mean()*100:.1f}%')
print(f'偏弱市({len(weak)}笔): 次日开卖净 {(weak["ret_o1"].mean()-0.005)*100:+.2f}% | D日涨停率 {weak["lu_d"].mean()*100:.1f}%')
