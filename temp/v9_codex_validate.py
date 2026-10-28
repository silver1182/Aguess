# -*- coding: utf-8 -*-
"""
Codex建议落地验证: 滚动样本外阈值 + 因子相关性/IC + 连续仓位 + ATR止损
"""
import json, pandas as pd, numpy as np

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
sel['year'] = sel['yw'].str[:4]
COST = 0.0025

# ---------------- 1. 因子相关性 (周截面Spearman平均) ----------------
corrs = []
for yw, sub in sel.groupby('yw'):
    if len(sub) < 30: continue
    corrs.append(sub[F].corr(method='spearman'))
corr_mean = pd.DataFrame(np.mean([c.to_numpy() for c in corrs], axis=0), index=F, columns=F)
print('=== 七因子截面Spearman相关(周均值) ===')
print(corr_mean.round(3).to_string())
dup_pairs = [(i,j) for i in range(len(F)) for j in range(i+1,len(F)) if abs(corr_mean.iloc[i,j]) > 0.5]
print('|corr|>0.5 的因子对:', [(F[i],F[j],round(corr_mean.iloc[i,j],2)) for i,j in dup_pairs] if dup_pairs else '无')

# ---------------- 2. 滚动IC / IR ----------------
ic_rows = []
for yw, sub in sel.groupby('yw'):
    if len(sub) < 30: continue
    row = {'yw': yw}
    for c in F:
        row[c] = sub[c].corr(sub['ret0'], method='spearman')
    row['score'] = sub['score'].corr(sub['ret0'], method='spearman')
    ic_rows.append(row)
ic = pd.DataFrame(ic_rows).set_index('yw')
print('\n=== 因子滚动IC (26周均值/标准差 -> IR) ===')
for c in F + ['score']:
    v = ic[c].rolling(26, min_periods=13)
    ic_mean = v.mean().iloc[-1]
    ic_std = v.std().iloc[-1]
    ir = ic_mean/ic_std if ic_std and ic_std>0 else np.nan
    print(f'{c:16s} 全期IC均值{ic[c].mean():+.4f} | 最近IC均值{ic_mean:+.4f} IR{ir:+.3f}')

# ---------------- 3. 滚动样本外验证 ----------------
def run_top5(sub, avg_thr=None):
    picks = sub.sort_values('score', ascending=False).groupby('yw').head(5)
    if avg_thr is not None:
        avg = picks.groupby('yw')['score'].mean()
        ok = avg[avg >= avg_thr].index
        picks = picks[picks['yw'].isin(ok)]
    if len(picks)==0: return 0.0, 0.0, pd.DataFrame()
    rets = []
    for r in picks.itertuples():
        ret = -0.12 if r.week_low_ret < -0.12 else r.ret0
        rets.append(ret - COST)
    picks['ret'] = rets
    wk = picks.groupby('yw').agg(ret=('ret','mean')).reset_index()
    nav = (1+wk['ret']).cumprod()
    return nav.iloc[-1]-1, ((nav/nav.cummax())-1).min(), wk

GRID = [round(0.58+i*0.02,2) for i in range(6)]  # 0.58~0.68
segs = [('2023','2024'), ('2024','2025'), ('2025','2026')]
print('\n=== 滚动样本外验证 (训练段选最优avg阈值 -> 验证段回测) ===')
for train_end, val_year in segs:
    train = sel[sel['year'].astype(int) <= int(train_end)]
    val = sel[sel['year'] == val_year]
    best_thr, best_ret = None, -1e9
    for thr in GRID:
        t, _, _ = run_top5(train, avg_thr=thr)
        if t > best_ret: best_thr, best_ret = thr, t
    v_opt, mdd_opt, _ = run_top5(val, avg_thr=best_thr)
    v_none, mdd_none, _ = run_top5(val)
    print(f'训练至{train_end}: 最优阈值avg>={best_thr}(训练累计{best_ret*100:+.1f}%) | {val_year}验证: 过滤后{v_opt*100:+.1f}%(回撤{mdd_opt*100:.1f}%) vs 无过滤{v_none*100:+.1f}%(回撤{mdd_none*100:.1f}%)')

# ---------------- 4. 连续仓位 vs 硬阈值 (全期对比) ----------------
print('\n=== 连续仓位 vs 硬阈值 (全期225周) ===')
def run_continuous(topn=5, lo=0.55, hi=0.64, maxpos=1.0):
    picks = sel.sort_values(['yw','score'], ascending=[True,False]).groupby('yw').head(topn).reset_index(drop=True)
    avg = picks.groupby('yw')['score'].mean()
    pos = avg.clip(lo, hi).apply(lambda x: (x-lo)/(hi-lo) if hi>lo else 0).clip(0, maxpos)
    pos_map = pos.to_dict()
    rows = []
    for r in picks.itertuples():
        p = pos_map.get(r.yw, 0.0)
        ret = -0.12 if r.week_low_ret < -0.12 else r.ret0
        rows.append({'yw': r.yw, 'ret': (ret - COST) * p})
    wk = pd.DataFrame(rows).groupby('yw')['ret'].mean().reset_index()
    nav = (1+wk['ret']).cumprod()
    return nav.iloc[-1]-1, ((nav/nav.cummax())-1).min(), wk
cont_total, cont_mdd, _ = run_continuous()
print(f'连续仓位(0.55~0.64): 累计{cont_total*100:+.1f}% 回撤{cont_mdd*100:.1f}%')

# ---------------- 5. ATR波动率止损 vs 固定12% (avg>=0.64) ----------------
print('\n=== ATR波动率止损 vs 固定12% (avg>=0.64过滤) ===')
# 用买入周前的20周平均振幅作为个股ATR代理: ATR = mean(|high-low|/prev_close) 20周
df['hl'] = (df['high']-df['low'])/df['prev_close']
df['atr20'] = g['hl'].transform(lambda x: x.rolling(20).mean())
sel_atr = sel.merge(df[['code','yw','atr20']], on=['code','yw'], how='left')
def run_atr(topn=5, stop_mode='fixed', stop=0.12, thr=0.64):
    picks = sel_atr.sort_values('score', ascending=False).groupby('yw').head(topn)
    avg = picks.groupby('yw')['score'].mean()
    ok = avg[avg >= thr].index
    picks = picks[picks['yw'].isin(ok)].copy()
    if len(picks)==0: return 0.0, 0.0
    rets = []
    for r in picks.itertuples():
        if stop_mode == 'fixed':
            sl = stop
        else:  # atr倍数
            sl = min(0.20, max(0.05, r.atr20 * stop))
        ret = -sl if r.week_low_ret < -sl else r.ret0
        rets.append(ret - COST)
    picks['ret'] = rets
    wk = picks.groupby('yw')['ret'].mean().reset_index()
    nav = (1+wk['ret']).cumprod()
    return nav.iloc[-1]-1, ((nav/nav.cummax())-1).min()
for mode, tag, stop in [('fixed','固定12%',0.12), ('atr','ATR*3(5%~20%夹)',3.0), ('atr','ATR*2(5%~20%夹)',2.0)]:
    t, m = run_atr(stop_mode=mode, stop=stop)
    print(f'{tag}: 累计{t*100:+.1f}% 回撤{m*100:.1f}%')

# ---------------- 6. 成本压力测试 (avg>=0.64, 固定12%) ----------------
print('\n=== 成本压力测试 (avg>=0.64, 固定12%) ===')
for cst in [0.001, 0.0025, 0.005, 0.01]:
    picks = sel.sort_values('score', ascending=False).groupby('yw').head(5)
    avg = picks.groupby('yw')['score'].mean()
    ok = avg[avg >= 0.64].index
    picks = picks[picks['yw'].isin(ok)]
    rets = []
    for r in picks.itertuples():
        ret = -0.12 if r.week_low_ret < -0.12 else r.ret0
        rets.append(ret - cst)
    picks['ret'] = rets
    wk = picks.groupby('yw')['ret'].mean().reset_index()
    nav = (1+wk['ret']).cumprod()
    print(f'成本{cst*100:.2f}%: 累计{(nav.iloc[-1]-1)*100:+.1f}% 回撤{((nav/nav.cummax())-1).min()*100:.1f}%')
