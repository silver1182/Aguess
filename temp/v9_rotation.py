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
df['tail'] = df['close'] / df['open'] - 1
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

# 每只股票的每周收益（用 buy_open -> close 即当周收益；但轮动回测用 close/close 相邻周收益更贴合持有）
# 用周收盘到下周收盘的收益代表"持有该股一周"的收益
ret_map = df.set_index(['code','yw'])['pct'].to_dict()  # 本周 pct 即本周收益
week_order = week_list

def rotation_backtest(topn, breadth_mode='lt', breadth_th=0.45, buy_cost=0.001, sell_cost=0.0015):
    """连续持仓轮动：目标=每周TopN，只在仓位变化时交易，重合部分免成本"""
    picks_by_yw = {}
    for yw in week_order:
        sub = sel[sel['yw']==yw].sort_values('score', ascending=False).head(topn)
        picks_by_yw[yw] = set(sub['code'].tolist())

    cur_hold = set()
    nav = 1.0
    peak = 1.0
    mdd = 0.0
    recs = []
    for i, yw in enumerate(week_order[:-1]):
        next_yw = week_order[i+1]
        # 该周是否进场（择时）
        wk_breadth = df[df['yw']==yw].groupby('yw')['pct'].apply(lambda x: (x>0).mean())
        b = wk_breadth.get(yw, 0.5)
        active = (b <= breadth_th) if breadth_mode=='lt' else True
        if not active:
            cur_hold = set()  # 空仓，清仓免成本? 空仓周不交易
            nav *= 1.0
            recs.append((yw, 0.0, 0, b, 0, 0, 0))
            peak = max(peak, nav); mdd = min(mdd, nav/peak - 1)
            continue
        target = picks_by_yw[yw]
        # 成本：卖出的票（cur-target）付sell_cost；买入的票（target-cur）付buy_cost
        n_sell = len(cur_hold - target)
        n_buy = len(target - cur_hold)
        # 持仓 = 本周实际持有 = target（新组合）; 收益 = 本周持仓股的本周收益均值
        hold_ret = np.mean([ret_map.get((c, yw), 0.0) for c in target]) if target else 0.0
        cost = n_sell*sell_cost + n_buy*buy_cost
        # 成本按组合整体占比扣减（近似：变化仓位占总仓位比例）
        total = len(target) if target else 1
        cost_rate = (n_sell + n_buy) * (0.0)  # 占位
        # 更合理：卖出 n_sell/total 部分收卖出费，买入 n_buy/total 部分收买入费
        cost_rate = (n_sell/total)*sell_cost + (n_buy/total)*buy_cost if total>0 else 0
        ret = hold_ret - cost_rate
        nav *= (1 + ret)
        recs.append((yw, ret, len(target), b, len(cur_hold & target), n_sell, n_buy))
        cur_hold = target
        peak = max(peak, nav); mdd = min(mdd, nav/peak - 1)
    return nav, mdd, recs

def full_turn_backtest(topn, breadth_mode='lt', breadth_th=0.45, cost_weekly=0.0025):
    """每周全换（对照）"""
    picks = sel.sort_values(['yw','score'], ascending=[True,False]).groupby('yw').head(topn).reset_index(drop=True)
    trades = picks.merge(df.groupby('yw').apply(lambda x: pd.Series({'breadth':(x['pct']>0).mean()}), include_groups=False).reset_index(), on='yw', how='left')
    trades['ret'] = trades['close'] / trades['buy_open'] - 1
    if breadth_mode == 'lt':
        trades['active'] = trades['breadth'] <= breadth_th
    else:
        trades['active'] = True
    trades['ret'] = np.where(trades['active'], trades['ret'] - cost_weekly, 0.0)
    wk = trades.groupby('yw').agg(ret=('ret','mean'), n=('code','nunique'), active=('active','first')).reset_index()
    nav = (1 + wk['ret']).cumprod()
    mdd = ((nav / nav.cummax()) - 1).min()
    return nav, mdd, wk

print('=== 连续持仓轮动 (买入0.10% 卖出0.15%) ===')
for topn in [2, 3, 4, 5]:
    nav, mdd, recs = rotation_backtest(topn)
    n = len(recs)
    cagr = nav ** (52/n) - 1
    n_sell = sum(r[5] for r in recs); n_buy = sum(r[6] for r in recs)
    total_slots = sum(r[2] for r in recs)
    turnover = (n_sell + n_buy) / max(total_slots,1)
    print(f'Top{topn}: 累计{(nav-1)*100:>7.1f}% 年化{cagr*100:>6.1f}% 回撤{mdd*100:>6.1f}% 换手率{turnover*100:>4.0f}%')

print('\n=== 对照: 每周全换 0.25%成本 ===')
for topn in [2, 3, 4, 5]:
    nav, mdd, wk = full_turn_backtest(topn, cost_weekly=0.0025)
    n = len(wk)
    cagr = nav ** (52/n) - 1
    print(f'Top{topn}: 累计{(nav-1)*100:>7.1f}% 年化{cagr*100:>6.1f}% 回撤{mdd*100:>6.1f}%')

# 轮动重合度观察
print('\n=== Top3 轮动: 每周换手明细(前20周) ===')
_, _, recs = rotation_backtest(3)
for r in recs[:20]:
    yw, ret, n, b, keep, ns, nb = r
    print(f'{yw}: 收益{ret*100:>6.2f}% 持仓{n} 广度{b:.2f} 保留{keep} 卖{ns} 买{nb}')

# 2周频（每两周选一次，持两周，中间周免换手）
print('\n=== 2周频（每2周选股持2周, 买入0.10%卖出0.15%）===')
picks_by_yw = {}
for yw in week_order:
    sub = sel[sel['yw']==yw].sort_values('score', ascending=False).head(4)
    picks_by_yw[yw] = set(sub['code'].tolist())
nav = 1.0; peak = 1.0; mdd = 0.0; recs2 = []
sel_weeks = week_order[::2]  # 每两周的截面周
for i, yw in enumerate(sel_weeks[:-1]):
    next_yw = sel_weeks[i+1]
    wk_breadth = df[df['yw']==yw].groupby('yw')['pct'].apply(lambda x: (x>0).mean())
    b = wk_breadth.get(yw, 0.5)
    active = (b <= 0.45)
    if not active:
        nav *= 1.0; recs2.append((yw, 0.0, 0)); peak=max(peak,nav); mdd=min(mdd,nav/peak-1); continue
    target = picks_by_yw[yw]
    # 两周收益：持有两周的收益 = 第1周pct + 第2周pct（周pct累乘）
    ret2 = 0.0; cnt = 0
    for c in target:
        r1 = ret_map.get((c, yw), 0.0)
        r2 = ret_map.get((c, next_yw), 0.0)
        ret2 += (1+r1)*(1+r2) - 1
        cnt += 1
    hold_ret = ret2/cnt if cnt>0 else 0.0
    cost_rate = 0.001 + 0.0015  # 每2周一次双边
    ret = hold_ret - cost_rate
    nav *= (1+ret)
    recs2.append((yw, ret, len(target)))
    peak=max(peak,nav); mdd=min(mdd,nav/peak-1)
n2 = len(recs2)
cagr2 = nav ** (52/(n2*2)) - 1
print(f'2周频Top4: 累计{(nav-1)*100:>7.1f}% 年化{cagr2*100:>6.1f}% 回撤{mdd*100:>6.1f}% 期数{n2}')
