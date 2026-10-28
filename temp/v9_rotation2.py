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
df = df[df['close'].notna()]
df = df.sort_values(['code', 'date']).reset_index(drop=True)

g = df.groupby('code')
df['prev_close'] = g['close'].shift(1)
df['prev_vol'] = g['volume'].shift(1)
df['pct'] = df['close'] / df['prev_close'] - 1
df['gap'] = df['open'] / df['prev_close'] - 1
df['tail'] = df['close'] / df['open'] - 1   # 周一开盘买入->周五收盘卖出 = 持有整周收益
df['vol_chg'] = df['volume'] / df['prev_vol']

cond_shrink = (df['pct']>0) & (df['vol_chg']<1)
df['shrink_up'] = cond_shrink.groupby(df['code']).transform(lambda x: x.rolling(10).mean())
df['amount_20d'] = g['volume'].transform(lambda x: x.rolling(20).mean())
df['max_up_20d'] = g['pct'].transform(lambda x: x.rolling(20).max())
cond_expand = (df['pct']<0) & (df['vol_chg']>1.2)
df['expand_down'] = cond_expand.groupby(df['code']).transform(lambda x: x.rolling(10).mean())
df['tail_return'] = g['tail'].transform(lambda x: x.rolling(20).mean())
df['vol_chg_std'] = g['vol_chg'].transform(lambda x: x.rolling(20).std())
df['overnight_gap'] = g['gap'].transform(lambda x: x.rolling(20).mean())

df['yw'] = df['date'].dt.strftime('%Y-%U')
factor_cols = ['shrink_up','amount_20d','max_up_20d','expand_down','tail_return','vol_chg_std','overnight_gap']
sel_df = df[df[factor_cols].notna().all(axis=1)].copy()

def rank_std(s):
    s = s.fillna(s.median())
    r = s.rank(pct=True)
    return (r - 0.5) * 2

week_list = df.groupby('yw')['date'].max().sort_values().index.tolist()
yw_to_next = {w: week_list[i+1] for i, w in enumerate(week_list[:-1])}
sel_df['buy_yw'] = sel_df['yw'].map(yw_to_next)
buy_df = df[['code','yw','open']].rename(columns={'open':'buy_open'})
sel = sel_df.merge(buy_df.rename(columns={'yw':'buy_yw'}), on=['code','buy_yw'], how='left')
sel = sel[['yw','buy_yw','code','close','buy_open'] + factor_cols].dropna(subset=['buy_open']).copy()
for c in factor_cols:
    sel[c] = rank_std(sel.groupby('yw')[c].transform(lambda x: x))
sel['score'] = (
    + sel['shrink_up'] - sel['amount_20d'] - sel['max_up_20d'] + sel['expand_down']
    - sel['tail_return'] - sel['vol_chg_std'] - sel['overnight_gap']
) / 7

# 持有周收益 = buy_yw 周的 tail
tail_map = df.set_index(['code','yw'])['tail'].to_dict()
breadth_map = df.groupby('yw').apply(lambda x: pd.Series({'breadth': (x['pct']>0).mean()}), include_groups=False).reset_index()
breadth_d = dict(zip(breadth_map['yw'], breadth_map['breadth']))

def full_turn(topn, breadth_mode='lt', breadth_th=0.45, cost_weekly=0.0):
    """每周全换：周五截面选TopN -> 下周开盘买 -> 下周收盘卖(持有一整周)"""
    picks = sel.sort_values(['yw','score'], ascending=[True,False]).groupby('yw').head(topn).reset_index(drop=True)
    picks['breadth'] = picks['yw'].map(breadth_d)
    picks['ret'] = picks['buy_yw'].map(lambda y: 0.0)  # placeholder
    picks['ret'] = [tail_map.get((r.code, r.buy_yw), 0.0) for r in picks.itertuples()]
    if breadth_mode == 'lt':
        picks['active'] = picks['breadth'] <= breadth_th
    else:
        picks['active'] = True
    picks['ret'] = np.where(picks['active'], picks['ret'] - cost_weekly, 0.0)
    wk = picks.groupby('yw').agg(ret=('ret','mean'), n=('code','nunique'), active=('active','first')).reset_index()
    nav = (1 + wk['ret']).cumprod()
    mdd = ((nav / nav.cummax()) - 1).min()
    return nav.iloc[-1], mdd, wk

def rotation(topn, breadth_mode='lt', breadth_th=0.45, buy_cost=0.001, sell_cost=0.0015):
    """连续持仓轮动：目标=每周TopN，只换跌出TopN的票，重合部分免成本。持有周=next_yw"""
    picks_by_yw = {}
    for yw in week_list:
        sub = sel[sel['yw']==yw].sort_values('score', ascending=False).head(topn)
        picks_by_yw[yw] = set(sub['code'].tolist())
    cur_hold = set()
    nav = 1.0; peak = 1.0; mdd = 0.0
    recs = []
    for i, yw in enumerate(week_list[:-1]):
        next_yw = week_list[i+1]
        b = breadth_d.get(yw, 0.5)
        active = (b <= breadth_th) if breadth_mode=='lt' else True
        if not active:
            cur_hold = set()
            nav *= 1.0
            recs.append((yw, 0.0, 0, b, 0, 0, 0))
            peak = max(peak, nav); mdd = min(mdd, nav/peak - 1)
            continue
        target = picks_by_yw[yw]
        n_sell = len(cur_hold - target)
        n_buy = len(target - cur_hold)
        total = len(target) if target else 1
        hold_ret = np.mean([tail_map.get((c, next_yw), 0.0) for c in target]) if target else 0.0
        cost_rate = (n_sell/total)*sell_cost + (n_buy/total)*buy_cost if total>0 else 0
        ret = hold_ret - cost_rate
        nav *= (1 + ret)
        recs.append((yw, ret, len(target), b, len(cur_hold & target), n_sell, n_buy))
        cur_hold = target
        peak = max(peak, nav); mdd = min(mdd, nav/peak - 1)
    return nav, mdd, recs

print('=== 修正语义：每周全换(持有一整周) 0成本 ===')
for topn in [2,3,4,5,8]:
    nav, mdd, wk = full_turn(topn, cost_weekly=0.0)
    n = len(wk); cagr = nav ** (52/n) - 1
    print(f'Top{topn} 无择时: 累计{(nav-1)*100:>7.1f}% 年化{cagr*100:>6.1f}% 回撤{mdd*100:>6.1f}% 周均{wk["ret"].mean()*100:>6.2f}%')
for topn in [2,3,4,5,8]:
    nav, mdd, wk = full_turn(topn, 'lt', 0.45, 0.0)
    n = len(wk); cagr = nav ** (52/n) - 1
    print(f'Top{topn} 反向≤0.45: 累计{(nav-1)*100:>7.1f}% 年化{cagr*100:>6.1f}% 回撤{mdd*100:>6.1f}% 周均{wk["ret"].mean()*100:>6.2f}% 持仓{(wk["active"].mean()*100):>3.0f}%')

print('\n=== 每周全换 + 0.25%成本(持有一整周) ===')
for topn in [2,3,4,5]:
    nav, mdd, wk = full_turn(topn, 'lt', 0.45, 0.0025)
    n = len(wk); cagr = nav ** (52/n) - 1
    print(f'Top{topn} 反向≤0.45: 累计{(nav-1)*100:>7.1f}% 年化{cagr*100:>6.1f}% 回撤{mdd*100:>6.1f}% 周均{wk["ret"].mean()*100:>6.2f}%')

print('\n=== 连续持仓轮动 (买入0.10% 卖出0.15%) ===')
for topn in [2,3,4,5]:
    nav, mdd, recs = rotation(topn)
    n = len(recs); cagr = nav ** (52/n) - 1
    n_sell = sum(r[5] for r in recs); n_buy = sum(r[6] for r in recs)
    total_slots = sum(r[2] for r in recs)
    turnover = (n_sell + n_buy) / max(total_slots,1)
    print(f'Top{topn}: 累计{(nav-1)*100:>7.1f}% 年化{cagr*100:>6.1f}% 回撤{mdd*100:>6.1f}% 换手率{turnover*100:>4.0f}%')

print('\n=== Top3 轮动: 每周明细(前25周) ===')
_, _, recs = rotation(3)
for r in recs[:25]:
    yw, ret, n, b, keep, ns, nb = r
    print(f'{yw}: 收益{ret*100:>6.2f}% 持仓{n} 广度{b:.2f} 保留{keep} 卖{ns} 买{nb}')

# 分年度（最优档：轮动Top3 或全换Top3+0.25%）
print('\n=== 轮动Top3 分年度 ===')
_, _, recs = rotation(3)
rec_df = pd.DataFrame(recs, columns=['yw','ret','n','breadth','keep','nsell','nbuy'])
rec_df['year'] = rec_df['yw'].str[:4]
for y, sub in rec_df.groupby('year'):
    nav_y = (1 + sub['ret']).cumprod()
    print(f'{y}: 年度{(nav_y.iloc[-1]-1)*100:>7.1f}% 周均{sub["ret"].mean()*100:>6.2f}% 换手率{sub["nsell"].sum()+sub["nbuy"].sum():>4d}笔')

# 基准（全市场等权，持有一周）
base_wk = df.groupby('yw')['tail'].mean().reset_index().rename(columns={'tail':'ret'})
nav_b = (1+base_wk['ret']).cumprod()
mdd_b = ((nav_b/nav_b.cummax())-1).min()
cagr_b = nav_b.iloc[-1] ** (52/len(base_wk)) - 1
print(f'\n全市场等权基准(持有整周): 累计{(nav_b.iloc[-1]-1)*100:>7.1f}% 年化{cagr_b*100:>6.1f}% 回撤{mdd_b*100:>6.1f}%')
