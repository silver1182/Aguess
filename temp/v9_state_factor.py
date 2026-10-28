# -*- coding: utf-8 -*-
"""
好坏周状态因子挖掘: 从正收益/小亏周 vs 亏损周的市场状态差异中找过滤因子
基线: Top5/止损12% 周频 225周
特征: 广度/等权指数位置/波动率/量能/策略动量/入选评分/广度动量 等
"""
import json, pandas as pd, numpy as np
from scipy import stats

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
with open(base + r'\temp\week_kline_long.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

all_bars = []
for code, bars in cache.items():
    for b in bars:
        b['code'] = code
        all_bars.append(b)
df = pd.DataFrame(all_bars)
df['date'] = pd.to_datetime(df['date'])
df = df[df['close'].notna()].sort_values(['code','date']).reset_index(drop=True)
g = df.groupby('code')
df['prev_close'] = g['close'].shift(1)
df['prev_vol'] = g['volume'].shift(1)
df['pct'] = df['close']/df['prev_close']-1
df['gap'] = df['open']/df['prev_close']-1
df['tail'] = df['close']/df['open']-1
df['vol_chg'] = df['volume']/df['prev_vol']
df['shrink_up'] = ((df['pct']>0)&(df['vol_chg']<1)).groupby(df['code']).transform(lambda x: x.rolling(10).mean())
df['amount_20d'] = g['volume'].transform(lambda x: x.rolling(20).mean())
df['max_up_20d'] = g['pct'].transform(lambda x: x.rolling(20).max())
df['expand_down'] = ((df['pct']<0)&(df['vol_chg']>1.2)).groupby(df['code']).transform(lambda x: x.rolling(10).mean())
df['tail_return'] = g['tail'].transform(lambda x: x.rolling(20).mean())
df['vol_chg_std'] = g['vol_chg'].transform(lambda x: x.rolling(20).std())
df['overnight_gap'] = g['gap'].transform(lambda x: x.rolling(20).mean())
df['yw'] = df['date'].dt.strftime('%Y-%U')
F = ['shrink_up','amount_20d','max_up_20d','expand_down','tail_return','vol_chg_std','overnight_gap']
sel_df = df[df[F].notna().all(axis=1)].copy()
week_list = df.groupby('yw')['date'].max().sort_values().index.tolist()
yw_to_next = {w: week_list[i+1] for i, w in enumerate(week_list[:-1])}
sel_df['buy_yw'] = sel_df['yw'].map(yw_to_next)
buy_info = df[['code','yw','open','close','low']].rename(columns={'open':'buy_open','close':'sell_close','low':'buy_low'})
sel = sel_df.merge(buy_info.rename(columns={'yw':'buy_yw'}), on=['code','buy_yw'], how='left')
sel = sel[['yw','buy_yw','code','buy_open','sell_close','buy_low']+F].dropna(subset=['buy_open']).copy()
for c in F:
    sel[c] = sel.groupby('yw')[c].transform(lambda s: (s.fillna(s.median()).rank(pct=True)-0.5)*2)
sel['score'] = (+sel['shrink_up']-sel['amount_20d']-sel['max_up_20d']+sel['expand_down']-sel['tail_return']-sel['vol_chg_std']-sel['overnight_gap'])/7
sel['ret0'] = sel['sell_close']/sel['buy_open']-1
sel['week_low_ret'] = sel['buy_low']/sel['buy_open']-1
COST = 0.0025

# 基线周收益 (Top5/止损12%)
def base_week_ret(topn=5, sl=0.12):
    picks = sel.sort_values(['yw','score'], ascending=[True,False]).groupby('yw').head(topn).reset_index(drop=True)
    rets = []
    for r in picks.itertuples():
        ret = -sl if (sl>0 and r.week_low_ret < -sl) else r.ret0
        rets.append(ret - COST)
    picks['ret'] = rets
    return picks.groupby('yw').agg(ret=('ret','mean'), avg_score=('score','mean')).reset_index()

base_wk = base_week_ret()

# ===== 每周市场状态特征 =====
wk_agg = df.groupby('yw').agg(
    eq_ret=('pct','mean'),
    breadth=('pct', lambda x: (x>0).mean()),
    vol_sum=('volume','sum'),
    up_5pct=('pct', lambda x: (x>=0.05).mean()),
    down_5pct=('pct', lambda x: (x<=-0.05).mean()),
).reset_index()
wk_agg = wk_agg.sort_values('yw').reset_index(drop=True)
# 等权指数序列 (近似: 周累计)
eq_idx = (1 + wk_agg['eq_ret']).cumprod()
wk_agg['eq_ma5'] = eq_idx.rolling(5).mean()
wk_agg['eq_ma10'] = eq_idx.rolling(10).mean()
wk_agg['eq_ma20'] = eq_idx.rolling(20).mean()
wk_agg['eq_pos_ma5'] = eq_idx / wk_agg['eq_ma5'] - 1
wk_agg['eq_pos_ma10'] = eq_idx / wk_agg['eq_ma10'] - 1
wk_agg['eq_pos_ma20'] = eq_idx / wk_agg['eq_ma20'] - 1
wk_agg['eq_ret_3w'] = wk_agg['eq_ret'].rolling(3).sum()
wk_agg['eq_ret_5w'] = wk_agg['eq_ret'].rolling(5).sum()
wk_agg['vol_ratio_3w'] = wk_agg['vol_sum'] / wk_agg['vol_sum'].rolling(3).mean()
wk_agg['vol_ratio_10w'] = wk_agg['vol_sum'] / wk_agg['vol_sum'].rolling(10).mean()
wk_agg['vol_std_10w'] = wk_agg['eq_ret'].rolling(10).std()
wk_agg['breadth_ma4'] = wk_agg['breadth'].rolling(4).mean()
wk_agg['breadth_chg'] = wk_agg['breadth'] - wk_agg['breadth'].shift(1)
wk_agg['breadth_pos_ma4'] = wk_agg['breadth'] - wk_agg['breadth_ma4']
wk_agg['updown_ratio'] = wk_agg['up_5pct'] / (wk_agg['down_5pct'] + 1e-6)
# 策略自身动量 (滞后1周)
wk_agg['prev_ret'] = base_wk.set_index('yw')['ret'].reindex(wk_agg['yw']).shift(1).values
wk_agg['prev2_ret'] = base_wk.set_index('yw')['ret'].reindex(wk_agg['yw']).shift(2).values
wk_agg['avg_score'] = base_wk.set_index('yw')['avg_score'].reindex(wk_agg['yw']).values

m = wk_agg.merge(base_wk[['yw','ret']], on='yw', how='inner').reset_index(drop=True)
m = m[m['eq_pos_ma20'].notna()].copy()

FEATS = ['eq_ret','breadth','up_5pct','down_5pct','eq_pos_ma5','eq_pos_ma10','eq_pos_ma20',
         'eq_ret_3w','eq_ret_5w','vol_ratio_3w','vol_ratio_10w','vol_std_10w','breadth_ma4',
         'breadth_chg','breadth_pos_ma4','updown_ratio','prev_ret','prev2_ret','avg_score']

print(f'总周数: {len(m)}, 正收益周: {(m["ret"]>0).sum()}, 亏损周: {(m["ret"]<=0).sum()}')
print(f'基线累计: {(1+m["ret"]).cumprod().iloc[-1]-1:+.1%}  周均 {m["ret"].mean():+.3%}')

# ===== 好坏周特征对比 (好周: ret>-0.02; 差周: ret<=-0.02) =====
print('\n=== 好周(ret>-2%) vs 差周(ret<=-2%) 特征对比 (Cohen d 排序) ===')
good = m[m['ret'] > -0.02]
bad = m[m['ret'] <= -0.02]
print(f'好周 {len(good)} 个, 差周 {len(bad)} 个')
res = []
for c in FEATS:
    gm, bm = good[c].mean(), bad[c].mean()
    sp = np.sqrt(((good[c].std()**2)*(len(good)-1) + (bad[c].std()**2)*(len(bad)-1)) / (len(good)+len(bad)-2))
    d = (gm - bm) / sp if sp > 0 else 0
    t, p = stats.ttest_ind(good[c].dropna(), bad[c].dropna(), equal_var=False)
    res.append({'feat': c, 'good': gm, 'bad': bm, 'diff': gm-bm, 'cohen_d': d, 'p': p})
res = pd.DataFrame(res).sort_values('cohen_d', key=lambda s: s.abs(), ascending=False)
print(res.to_string(index=False, float_format=lambda x: f'{x:.4f}'))

# ===== 单因子过滤规则回测 =====
print('\n=== 单因子过滤规则 (持仓条件) 回测 ===')
rules = [
    ('breadth > 0.40', m['breadth'] > 0.40),
    ('breadth > 0.45', m['breadth'] > 0.45),
    ('eq_pos_ma20 > -0.02', m['eq_pos_ma20'] > -0.02),
    ('eq_pos_ma20 > 0', m['eq_pos_ma20'] > 0),
    ('eq_pos_ma10 > -0.01', m['eq_pos_ma10'] > -0.01),
    ('eq_ret_3w > -0.02', m['eq_ret_3w'] > -0.02),
    ('eq_ret_5w > -0.03', m['eq_ret_5w'] > -0.03),
    ('prev_ret > -0.03', m['prev_ret'] > -0.03),
    ('prev_ret > -0.01', m['prev_ret'] > -0.01),
    ('updown_ratio > 0.3', m['updown_ratio'] > 0.3),
    ('vol_std_10w < 0.035', m['vol_std_10w'] < 0.035),
    ('breadth_pos_ma4 > -0.03', m['breadth_pos_ma4'] > -0.03),
]
base_total = (1+m['ret']).cumprod().iloc[-1]-1
for name, cond in rules:
    hold = m[cond]
    nav = (1+hold['ret']).cumprod()
    total = nav.iloc[-1]-1 if len(hold)>0 else 0
    mdd = ((nav/nav.cummax())-1).min() if len(hold)>0 else 0
    n = len(hold)
    print(f'{name:32s} 持仓{n:3d}周 累计{total:+7.1%} 周均{hold["ret"].mean():+7.3%} 回撤{mdd:7.1%}')

print(f'\n基线(全持仓): 225周 累计{base_total:+7.1%} 周均{m["ret"].mean():+7.3%}')

# ===== 组合过滤: 最有希望的2-3个条件合并 =====
print('\n=== 组合过滤 ===')
combos = [
    ('广度>0.40 & 指数MA20>-2%', (m['breadth']>0.40) & (m['eq_pos_ma20']>-0.02)),
    ('广度>0.40 & 波动<3.5%', (m['breadth']>0.40) & (m['vol_std_10w']<0.035)),
    ('广度>0.40 & 上周>-3%', (m['breadth']>0.40) & (m['prev_ret']>-0.03)),
    ('MA20>-2% & 上周>-3%', (m['eq_pos_ma20']>-0.02) & (m['prev_ret']>-0.03)),
    ('广度>0.45 & MA20>-2%', (m['breadth']>0.45) & (m['eq_pos_ma20']>-0.02)),
]
for name, cond in combos:
    hold = m[cond]
    if len(hold)==0:
        print(f'{name}: 无持仓周')
        continue
    nav = (1+hold['ret']).cumprod()
    mdd = ((nav/nav.cummax())-1).min()
    parts = []
    for y, sub in hold.groupby(hold['yw'].str[:4]):
        nv = (1+sub['ret']).cumprod().iloc[-1]-1
        parts.append(f'{y}:{nv*100:+.1f}%')
    print(f'{name:28s} 持仓{len(hold):3d}周 累计{(nav.iloc[-1]-1):+7.1%} 周均{hold["ret"].mean():+7.3%} 回撤{mdd:7.1%} | {" ".join(parts)}')
