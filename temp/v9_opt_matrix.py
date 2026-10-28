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
print('总行数:', len(df), '股票数:', df['code'].nunique(), '日期:', df['date'].min().date(), '~', df['date'].max().date())

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
df['ym'] = df['date'].dt.strftime('%Y-%m')

factor_cols = ['shrink_up','amount_20d','max_up_20d','expand_down','tail_return','vol_chg_std','overnight_gap']
sel_df = df[df[factor_cols].notna().all(axis=1)].copy()

def rank_std(s):
    s = s.fillna(s.median())
    r = s.rank(pct=True)
    return (r - 0.5) * 2

def to_nav(wk_ret):
    nav = (1 + wk_ret['ret']).cumprod()
    mdd = ((nav / nav.cummax()) - 1).min()
    n = len(wk_ret)
    cagr = nav.iloc[-1] ** (52/n) - 1 if n > 0 else 0
    return nav, mdd, cagr

def to_nav_m(wk_ret):
    nav = (1 + wk_ret['ret']).cumprod()
    mdd = ((nav / nav.cummax()) - 1).min()
    n = len(wk_ret)
    cagr = nav.iloc[-1] ** (12/n) - 1 if n > 0 else 0
    return nav, mdd, cagr

def run_backtest(sel, freq_col, buy_col, sell_close_col, breadth_map, topn, breadth_mode='none', breadth_th=0.45, stop_loss=None):
    picks = sel.sort_values([freq_col,'score'], ascending=[True,False]).groupby(freq_col).head(topn).reset_index(drop=True)
    trades = picks.merge(breadth_map, on=freq_col, how='left')
    trades['ret'] = trades[sell_close_col] / trades['buy_open'] - 1
    if stop_loss:
        trades['ret'] = np.where(trades['ret'] < -stop_loss, -stop_loss, trades['ret'])
    if breadth_mode == 'gt':
        trades['active'] = trades['breadth'] >= breadth_th
        trades['ret'] = np.where(trades['active'], trades['ret'], 0.0)
    elif breadth_mode == 'lt':
        trades['active'] = trades['breadth'] <= breadth_th
        trades['ret'] = np.where(trades['active'], trades['ret'], 0.0)
    else:
        trades['active'] = True
    wk_ret = trades.groupby(freq_col).agg(ret=('ret','mean'), n=('code','nunique'), active=('active','first'), breadth=('breadth','first')).reset_index()
    return wk_ret, trades

# ===== 周频 =====
week_list = df.groupby('yw')['date'].max().sort_values().index.tolist()
yw_to_next = {w: week_list[i+1] for i, w in enumerate(week_list[:-1])}
sel_df['buy_yw'] = sel_df['yw'].map(yw_to_next)
buy_df = df[['code','yw','open']].rename(columns={'open':'buy_open'})
sel_w = sel_df.merge(buy_df.rename(columns={'yw':'buy_yw'}), on=['code','buy_yw'], how='left')
sel_w = sel_w[['yw','buy_yw','code','close','buy_open'] + factor_cols].dropna(subset=['buy_open']).copy()
for c in factor_cols:
    sel_w[c] = rank_std(sel_w.groupby('yw')[c].transform(lambda x: x))
sel_w['score'] = (
    + sel_w['shrink_up'] - sel_w['amount_20d'] - sel_w['max_up_20d'] + sel_w['expand_down']
    - sel_w['tail_return'] - sel_w['vol_chg_std'] - sel_w['overnight_gap']
) / 7
# 周频卖出=close(当周收盘)
sel_w['sell_close'] = sel_w['close']
breadth_w = df.groupby('yw').apply(lambda x: pd.Series({'breadth': (x['pct']>0).mean()}), include_groups=False).reset_index()

# ===== 月频 =====
# 每月最后一周截面
sel_month = sel_df.sort_values('date').groupby(['code','ym']).tail(1).copy()
month_list = df['ym'].drop_duplicates().sort_values().tolist()
ym_to_next = {m: month_list[i+1] for i, m in enumerate(month_list[:-1])}
sel_month['buy_ym'] = sel_month['ym'].map(ym_to_next)
buy_df_m = df[['code','ym','open']].rename(columns={'open':'buy_open'})
sel_m = sel_month.merge(buy_df_m.rename(columns={'ym':'buy_ym'}), on=['code','buy_ym'], how='left')
sel_m = sel_m[['ym','buy_ym','code','close','buy_open'] + factor_cols].dropna(subset=['buy_open']).copy()
for c in factor_cols:
    sel_m[c] = rank_std(sel_m.groupby('ym')[c].transform(lambda x: x))
sel_m['score'] = (
    + sel_m['shrink_up'] - sel_m['amount_20d'] - sel_m['max_up_20d'] + sel_m['expand_down']
    - sel_m['tail_return'] - sel_m['vol_chg_std'] - sel_m['overnight_gap']
) / 7
# 卖出=下月最后收盘
sell_df_m = df.groupby(['code','ym'])['close'].last().reset_index().rename(columns={'close':'sell_close'})
sel_m = sel_m.merge(sell_df_m.rename(columns={'ym':'buy_ym'}), on=['code','buy_ym'], how='left')
breadth_m = df.groupby('ym').apply(lambda x: pd.Series({'breadth': (x['pct']>0).mean()}), include_groups=False).reset_index()

print('\n========== 周频矩阵 (无止损) ==========')
for topn in [2, 3, 4, 5, 8, 10]:
    for bm, lbl in [('none','无择时'), ('lt','反向≤0.45')]:
        wk, _ = run_backtest(sel_w, 'yw', 'buy_yw', 'sell_close', breadth_w, topn, breadth_mode=bm, breadth_th=0.45)
        nav, mdd, cagr = to_nav(wk)
        print(f'Top{topn:>2} {lbl}: 周数{len(wk):>3} 累计{(nav.iloc[-1]-1)*100:>7.1f}% 年化{cagr*100:>6.1f}% 回撤{mdd*100:>6.1f}% 周均{wk["ret"].mean()*100:>6.2f}% 胜率{(wk["ret"]>0).mean()*100:>4.0f}% 持仓周{wk["active"].mean()*100:>3.0f}%')

print('\n========== 周频止损对比 (反向≤0.45) ==========')
for topn in [2, 3, 4]:
    for sl, lbl in [(None,'无止损'), (0.05,'-5%'), (0.08,'-8%')]:
        wk, _ = run_backtest(sel_w, 'yw', 'buy_yw', 'sell_close', breadth_w, topn, breadth_mode='lt', breadth_th=0.45, stop_loss=sl)
        nav, mdd, cagr = to_nav(wk)
        print(f'Top{topn} 反向 {lbl}: 累计{(nav.iloc[-1]-1)*100:>7.1f}% 年化{cagr*100:>6.1f}% 回撤{mdd*100:>6.1f}% 周均{wk["ret"].mean()*100:>6.2f}% 胜率{(wk["ret"]>0).mean()*100:>4.0f}%')

print('\n========== 月频矩阵 (无止损) ==========')
for topn in [2, 3, 4, 5, 8]:
    for bm, lbl in [('none','无择时'), ('lt','反向≤0.45')]:
        wk, _ = run_backtest(sel_m, 'ym', 'buy_ym', 'sell_close', breadth_m, topn, breadth_mode=bm, breadth_th=0.45)
        nav, mdd, cagr = to_nav_m(wk)
        print(f'Top{topn:>2} {lbl}: 月数{len(wk):>3} 累计{(nav.iloc[-1]-1)*100:>7.1f}% 年化{cagr*100:>6.1f}% 回撤{mdd*100:>6.1f}% 月均{wk["ret"].mean()*100:>6.2f}% 胜率{(wk["ret"]>0).mean()*100:>4.0f}% 持仓月{wk["active"].mean()*100:>3.0f}%')

print('\n========== 月频止损对比 (反向≤0.45) ==========')
for topn in [2, 3, 4]:
    for sl, lbl in [(None,'无止损'), (0.05,'-5%'), (0.08,'-8%')]:
        wk, _ = run_backtest(sel_m, 'ym', 'buy_ym', 'sell_close', breadth_m, topn, breadth_mode='lt', breadth_th=0.45, stop_loss=sl)
        nav, mdd, cagr = to_nav_m(wk)
        print(f'Top{topn} 反向 {lbl}: 累计{(nav.iloc[-1]-1)*100:>7.1f}% 年化{cagr*100:>6.1f}% 回撤{mdd*100:>6.1f}% 月均{wk["ret"].mean()*100:>6.2f}% 胜率{(wk["ret"]>0).mean()*100:>4.0f}%')

# 基准（周频全市场等权）
base_wk = df.groupby('yw')['pct'].mean().reset_index().rename(columns={'pct':'ret'})
nav_b, mdd_b, cagr_b = to_nav(base_wk)
print(f'\n全市场等权基准(周): 累计{(nav_b.iloc[-1]-1)*100:>7.1f}% 年化{cagr_b*100:>6.1f}% 回撤{mdd_b*100:>6.1f}%')
base_m = df.groupby('ym')['pct'].mean().reset_index().rename(columns={'pct':'ret'})
nav_bm, mdd_bm, cagr_bm = to_nav_m(base_m)
print(f'全市场等权基准(月): 累计{(nav_bm.iloc[-1]-1)*100:>7.1f}% 年化{cagr_bm*100:>6.1f}% 回撤{mdd_bm*100:>6.1f}%')

# 最优组合（周频Top3 反向0.45）分年度
print('\n========== 周频 Top3 反向0.45 分年度 ==========')
wk, trades = run_backtest(sel_w, 'yw', 'buy_yw', 'sell_close', breadth_w, 3, breadth_mode='lt', breadth_th=0.45)
wk['year'] = wk['yw'].str[:4]
for y, sub in wk.groupby('year'):
    nav_y = (1 + sub['ret']).cumprod()
    print(f'{y}: 年度{(nav_y.iloc[-1]-1)*100:>7.1f}% 持仓周占比{sub["active"].mean()*100:>4.0f}% 周均{sub["ret"].mean()*100:>6.2f}% 胜率{(sub["ret"]>0).mean()*100:>4.0f}%')

# 月频 Top3 反向0.45 分年度
print('\n========== 月频 Top3 反向0.45 分年度 ==========')
wk_m, trades_m = run_backtest(sel_m, 'ym', 'buy_ym', 'sell_close', breadth_m, 3, breadth_mode='lt', breadth_th=0.45)
wk_m['year'] = wk_m['ym'].str[:4]
for y, sub in wk_m.groupby('year'):
    nav_y = (1 + sub['ret']).cumprod()
    print(f'{y}: 年度{(nav_y.iloc[-1]-1)*100:>7.1f}% 持仓月占比{sub["active"].mean()*100:>4.0f}% 月均{sub["ret"].mean()*100:>6.2f}% 胜率{(sub["ret"]>0).mean()*100:>4.0f}%')

# 最新周/月候选
print('\n========== 最新周(2026-42) Top8 候选 ==========')
last_yw = sel_w['yw'].max()
picks = sel_w[sel_w['yw']==last_yw].sort_values('score', ascending=False).head(8)
print(picks[['code','score','buy_open','close']].to_string(index=False))
print('\n========== 最新月候选 ==========')
last_ym = sel_m['ym'].max()
picks_m = sel_m[sel_m['ym']==last_ym].sort_values('score', ascending=False).head(8)
print(picks_m[['code','score','buy_open','sell_close']].to_string(index=False))

# 存盘 trades 供进一步分析
trades.to_csv(base + r'\temp\week_top3_trades.csv', index=False, encoding='utf-8-sig')
trades_m.to_csv(base + r'\temp\month_top3_trades.csv', index=False, encoding='utf-8-sig')
print('\n已存: temp/week_top3_trades.csv, temp/month_top3_trades.csv')
