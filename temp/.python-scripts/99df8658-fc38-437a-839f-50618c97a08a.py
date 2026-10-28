import json, pandas as pd, numpy as np

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
with open(base + r'\temp\kline_cache_em.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

all_bars = []
for code, bars in cache.items():
    for b in bars:
        b['code'] = code
        all_bars.append(b)
df = pd.DataFrame(all_bars)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['code', 'date']).reset_index(drop=True)

# ===== 因子计算 =====
g = df.groupby('code')
df['prev_close'] = g['close'].shift(1)
df['prev_vol'] = g['volume'].shift(1)
df['pct'] = df['close'] / df['prev_close'] - 1
df['gap'] = df['open'] / df['prev_close'] - 1  # 隔夜跳空
df['tail'] = df['close'] / df['open'] - 1       # 日内收益(尾盘代理)
df['vol_chg'] = df['volume'] / df['prev_vol']   # 量比

# shrink_up: 近10日 上涨且量缩 的占比
def shrink_up(x):
    pct = x['pct']; vc = x['vol_chg']
    up = pct > 0
    shrink = (up & (vc < 1)).rolling(10).mean()
    return shrink
df['shrink_up'] = g[['pct','vol_chg']].apply(lambda x: ( (x['pct']>0) & (x['vol_chg']<1) ).rolling(10).mean())

# amount_20d: 20日均成交额(小市值代理, 用volume近似)
df['amount_20d'] = g['volume'].transform(lambda x: x.rolling(20).mean())

# max_up_20d: 20日最大单日涨幅
df['max_up_20d'] = g['pct'].transform(lambda x: x.rolling(20).max())

# expand_down: 近10日 放量下跌 占比
df['expand_down'] = g[['pct','vol_chg']].apply(lambda x: ( (x['pct']<0) & (x['vol_chg']>1.2) ).rolling(10).mean())

# tail_return: 20日收盘/开盘均值(日内收益)
df['tail_return'] = g['tail'].transform(lambda x: x.rolling(20).mean())

# turnover_std_20d: 换手率波动 -> 用量变化率std代理
df['vol_chg_std'] = g['vol_chg'].transform(lambda x: x.rolling(20).std())

# overnight_gap: 20日隔夜跳空均值
df['overnight_gap'] = g['gap'].transform(lambda x: x.rolling(20).mean())

# 周频标记: 每只股票按周分组(用自然周)
df['week'] = df['date'].dt.isocalendar().week.astype(int)
df['year'] = df['date'].dt.isocalendar().year.astype(int)
df['yw'] = df['year'].astype(str) + '-' + df['week'].astype(str).str.zfill(2)

# 周五收盘选股
# 找到每周最后一个交易日(近似周五)
week_last = df.groupby(['yw', 'code']).tail(1).copy()
# 但需要所有股票每周最后一个交易日对齐 —— 用整体日期取每周最后一天
week_dates = df.groupby('yw')['date'].max().reset_index()
week_last2 = week_dates.merge(df, on=['yw','date'], how='inner')

# 下周开盘买入: 取每周第一个交易日开盘
week_first = df.groupby('yw')['date'].min().reset_index()
# 构造映射: 本周选股 -> 下一周第一个交易日
week_order = week_dates.sort_values('date')['yw'].tolist()
wf2 = week_first.copy()
wf2['nxt_yw'] = wf2['yw'].shift(-1)
wf2 = wf2.dropna(subset=['nxt_yw'])
nxt_map = wf2[['yw','nxt_yw']].merge(week_first.rename(columns={'yw':'nxt_yw','date':'nxt_date'}), on='nxt_yw')
buy_prices = nxt_map.merge(df[['code','date','open']].rename(columns={'date':'nxt_date','open':'buy_open'}), on=['code','nxt_date'], how='left')

# 周五收盘价(估值用)
sell_prices = week_last2[['code','yw','close','date']].rename(columns={'close':'wk_close'})

# 选股因子: 在每周最后一个交易日打分
factors = week_last2[['yw','code','date','close','shrink_up','amount_20d','max_up_20d','expand_down','tail_return','vol_chg_std','overnight_gap']].dropna()
print('因子有效样本:', len(factors), ' 周数:', factors['yw'].nunique())

# ===== 广度指标: 每周五上涨家数占比 =====
wk = df.groupby('yw')['pct'].apply(lambda x: (x>0).sum()).reset_index(name='up_cnt')
wk_total = df.groupby('yw').size().reset_index(name='tot')
breadth = wk.merge(wk_total, on='yw')
breadth['breadth'] = breadth['up_cnt'] / breadth['tot']
breadth = breadth.merge(week_dates, on='yw')

# ===== 打分(等权, 方向对齐v9) =====
from scipy.stats import rankdata
def rank_std(s):
    r = rankdata(s) / len(s)
    return (r - 0.5) * 2  # 0-1 -> -1~1

sc = factors.copy()
sc['s_shrink'] = rank_std(sc['shrink_up'])            # +
sc['s_amount'] = -rank_std(sc['amount_20d'])          # -
sc['s_maxup'] = -rank_std(sc['max_up_20d'])           # -
sc['s_expand'] = rank_std(sc['expand_down'])          # +
sc['s_tail'] = -rank_std(sc['tail_return'])           # -
sc['s_volstd'] = -rank_std(sc['vol_chg_std'])         # -
sc['s_gap'] = -rank_std(sc['overnight_gap'])          # -
sc['score'] = sc[['s_shrink','s_amount','s_maxup','s_expand','s_tail','s_volstd','s_gap']].mean(axis=1)

# 每周选Top N
def pick_top(n):
    return sc.sort_values(['yw','score'], ascending=[True,False]).groupby('yw').head(n).reset_index(drop=True)

# ===== 回测引擎(周一开盘买入, 周五收盘卖出/估值) =====
def backtest(topn, use_breadth=True, breadth_th=0.48, stop_loss=None):
    picks = pick_top(topn)
    # 关联买入价(下一周开盘) 和 卖出价(当周收盘)
    trade = picks.merge(breadth[['yw','breadth','date']], on='yw', how='left')
    # 卖出价: 用当周最后一个交易日收盘(即选股日当天收盘, 与v9口径"周五收盘估值"一致)
    trade = trade.merge(factors[['yw','code','close']].rename(columns={'close':'sell_close'}), on=['yw','code'], how='left')
    # 买入: 下一周开盘
    trade['buy_open'] = np.nan
    rows = []
    for i, r in trade.iterrows():
        nxt = buy_prices[(buy_prices['code']==r['code']) & (buy_prices['yw']==r['yw'])]
        if len(nxt):
            rows.append(r.copy())
            rows[-1]['buy_open'] = nxt['buy_open'].iloc[0]
        # 简化: buy_prices 是按"本周选股->下周买"的, 需要更直接匹配
    # 直接用更简单方案: 选股周的下一周开盘
    trades = trade.merge(buy_prices[['code','yw','buy_open']], on=['code','yw'], how='left')
    trades = trades.dropna(subset=['buy_open','sell_close'])
    trades['ret'] = trades['sell_close'] / trades['buy_open'] - 1
    # 止损
    if stop_loss:
        trades['ret'] = np.where(trades['ret'] < -stop_loss, -stop_loss, trades['ret'])
    # 广度择时
    if use_breadth:
        trades['active'] = trades['breadth'] >= breadth_th
        trades['ret'] = np.where(trades['active'], trades['ret'], 0)
    else:
        trades['active'] = True
    # 周收益 = 组合平均
    wk_ret = trades.groupby('yw').agg(ret=('ret','mean'), n=('code','nunique'), active=('active','first')).reset_index()
    return wk_ret, trades

# 净值计算
def to_nav(wk_ret):
    nav = (1 + wk_ret['ret']).cumprod()
    mdd = ((nav / nav.cummax()) - 1).min()
    n = len(wk_ret)
    cagr = nav.iloc[-1] ** (52/n) - 1 if n > 0 else 0
    return nav, mdd, cagr

for topn in [4, 10]:
    for use_b in [True, False]:
        wk_ret, _ = backtest(topn, use_breadth=use_b)
        nav, mdd, cagr = to_nav(wk_ret)
        label = f'Top{topn} ' + ('择时' if use_b else '无择时')
        print(f'{label}: 周数{len(wk_ret)} 累计{(nav.iloc[-1]-1)*100:.1f}% 年化{cagr*100:.1f}% 最大回撤{mdd*100:.1f}% 周均{(wk_ret["ret"].mean())*100:.2f}%')

# 基准: 全市场等权周收益
base_wk = df.merge(week_dates, on='yw')[['yw','pct']].groupby('yw')['pct'].mean().reset_index()
nav_b, mdd_b, cagr_b = to_nav(base_wk)
print(f'全市场等权基准: 周数{len(base_wk)} 累计{(nav_b.iloc[-1]-1)*100:.1f}% 年化{cagr_b*100:.1f}% 最大回撤{mdd_b*100:.1f}%')

# 广度分布
print('\n广度分布:')
print(breadth['breadth'].describe().to_string())