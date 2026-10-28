# -*- coding: utf-8 -*-
"""
中熊/浅熊适配策略挖掘回测 (backtest_signals.py)
=================================================
在 2024-2026 全市场主板日K缓存上, 对每个交易日打市况标签(牛/震荡/深熊/中熊/浅熊),
对候选信号分层回测次日收益 r1 (双边成本 0.3%), 输出各信号×市况档统计。

市况分层 (与 mkt_state_daily.build_index 一致):
  state: 牛(idx>ma20且ma20上行) / 熊(idx<ma20且ma20下行) / 震荡
  深度:  深熊 dev<-6% / 中熊 -6~-3% / 浅熊 -3~0

候选信号:
  A2变体: A2_base + 放宽/收紧阈值网格
  超跌反弹: B1-B4
  涨停次日回踩低吸: C1-C4 (T涨停, T+1回踩, T+2尾盘买入)
  断板反包/整理: D1
  平台突破: D2
  情绪分层: 用历史涨停家数代理情绪, 对通过信号做中熊/浅熊 亢奋vs冷淡 对比

验收: N>=30 且 胜率>=55% 且 平均r1扣0.3%双边成本后>0
可成交性: 买入日 涨幅>8% 或一字板(high==low且pct>=9.5) 视为不可买, 剔除
"""
import json, os, sys, time, warnings
import pandas as pd
import numpy as np
warnings.filterwarnings('ignore')

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

BASE = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
TEMP = BASE + r'\temp'
LONG = TEMP + r'\kline_day_long.json'
RESULT = TEMP + r'\backtest_signals_result.json'

COST = 0.3   # 双边成本 % (0.15%*2)
N_MIN = 30
WIN_MIN = 55.0
RET_MIN = 0.0  # 扣成本后平均r1 > 0


def build_long(data):
    """构建长表: 每只股票一行一交易日, 含特征列与future偏移列"""
    frames = []
    for code, bars in data.items():
        if not code.startswith(('60', '00')) or code.startswith(('30', '688')):
            continue
        if len(bars) < 40:
            continue
        df = pd.DataFrame(bars)
        for c in ['open', 'high', 'low', 'close', 'volume', 'amount']:
            df[c] = df[c].astype(float)
        df['code'] = code
        df['pct'] = df['close'].pct_change() * 100
        df['prev_pct'] = df['pct'].shift(1)
        df['prev2_pct'] = df['pct'].shift(2)
        df['prev3_pct'] = df['pct'].shift(3)
        df['ma5'] = df['close'].rolling(5).mean()
        df['ma10'] = df['close'].rolling(10).mean()
        df['ma20'] = df['close'].rolling(20).mean()
        df['vol5'] = df['volume'].rolling(5).mean()
        df['vol_ratio'] = df['volume'] / df['vol5']
        df['ret20'] = (df['close'] / df['close'].shift(20) - 1) * 100
        df['high20_prev'] = df['high'].shift(1).rolling(20).max()
        df['is_limit'] = (df['pct'] >= 9.5).astype(int)
        df['is_yizi'] = ((df['high'] == df['low']) & (df['pct'] >= 9.5)).astype(int)
        # future 偏移 (信号日T视角)
        df['next_ret'] = df['close'].shift(-1) / df['close'] * 100 - 100
        df['next_pct'] = df['pct'].shift(-1)
        df['next_vol_ratio'] = df['vol_ratio'].shift(-1)
        df['next_ma5'] = df['ma5'].shift(-1)
        df['next_close'] = df['close'].shift(-1)
        df['nn_ret'] = df['next_ret'].shift(-2)          # T+2 行的次日收益(=T+3涨跌) 用于C类
        df['nn_pct'] = df['pct'].shift(-2)               # T+2 当日涨幅
        df['nn_vol_ratio'] = df['vol_ratio'].shift(-2)   # T+2 量比
        df['nn_is_yizi'] = df['is_yizi'].shift(-2)
        # 涨停日一半涨幅位 = 涨停日收盘*1.05 (回踩不破位判断)
        df['half_up'] = df['close'] * 1.05
        frames.append(df[['code', 'date', 'open', 'high', 'low', 'close', 'volume', 'amount',
                          'pct', 'prev_pct', 'prev2_pct', 'prev3_pct',
                          'ma5', 'ma10', 'ma20', 'vol5', 'vol_ratio', 'ret20', 'high20_prev',
                          'is_limit', 'is_yizi',
                          'next_ret', 'next_pct', 'next_vol_ratio', 'next_ma5', 'next_close',
                          'nn_ret', 'nn_pct', 'nn_vol_ratio', 'nn_is_yizi', 'half_up']])
    long = pd.concat(frames, ignore_index=True)
    return long


def add_mkt_labels(long, data):
    """用 mkt_state_daily.build_index 逻辑打每个交易日市况标签"""
    import mkt_state_daily as msd
    mkt_df = msd.build_index(data)
    lbl = mkt_df[['date', 'state', 'depth', 'dev']].copy()
    long = long.merge(lbl, on='date', how='left')
    # 剔除初始/无标签
    long = long[long['depth'].notna() & (long['depth'] != '初始')].copy()
    return long, mkt_df


def add_sentiment_proxy(long):
    """历史情绪代理: 每日全市场涨停家数 (含近似炸板), 分位划冷热"""
    lu_daily = long.groupby('date')['is_limit'].sum()
    n = lu_daily.quantile(0.75)
    c = lu_daily.quantile(0.25)
    long['n_limit'] = long['date'].map(lu_daily)
    long['sent_proxy'] = np.where(long['n_limit'] >= n, '亢奋',
                          np.where(long['n_limit'] <= c, '冷淡', '中性'))
    return long, lu_daily, n, c


def sig_a2(long, vol_max=0.6, pct_lo=-2, pct_hi=1, prev2_min=9.5, need_ma5=True):
    cond = (long['prev2_pct'] >= prev2_min) & (long['vol_ratio'] <= vol_max) & \
           (long['pct'] >= pct_lo) & (long['pct'] <= pct_hi)
    if need_ma5:
        cond &= (long['close'] > long['ma5'])
    return cond


def sig_over(long, r20_max=-15, vol_max=0.8, pct_lo=None, pct_hi=None):
    cond = (long['ret20'] <= r20_max) & (long['vol_ratio'] <= vol_max) & (long['close'] > long['ma5'])
    if pct_lo is not None:
        cond &= (long['pct'] >= pct_lo)
    if pct_hi is not None:
        cond &= (long['pct'] <= pct_hi)
    return cond


def sig_pullback(long, mode=1):
    """T日涨停, T+1缩量回踩不破关键位, T+2尾盘买入"""
    t_limit = long['is_limit'] == 1
    # T+1 回踩条件 (用 next_ 列)
    if mode == 1:
        back = (long['next_pct'] <= 0) & (long['next_vol_ratio'] <= 0.8) & (long['next_close'] > long['next_ma5'])
    elif mode == 2:
        back = (long['next_close'] >= long['half_up']) & (long['next_vol_ratio'] <= 0.8)
    elif mode == 3:
        back = (long['next_pct'] >= -6) & (long['next_pct'] <= 0) & (long['next_vol_ratio'] <= 0.8)
    else:  # mode 4 = C1 + T+2再缩量
        back = (long['next_pct'] <= 0) & (long['next_vol_ratio'] <= 0.8) & (long['next_close'] > long['next_ma5']) & \
               (long['nn_vol_ratio'] <= 0.8)
    return t_limit & back


def sig_broken(long):
    """T-2涨停 且 T-1断板 且 T缩量整理企稳"""
    return (long['prev2_pct'] >= 9.5) & (long['prev_pct'] < 9.5) & \
           (long['vol_ratio'] <= 0.8) & (long['close'] > long['ma5']) & \
           (long['pct'] >= -2) & (long['pct'] <= 2)


def sig_breakout(long):
    """平台突破: 创20日新高 + 放量 + 涨幅3~8%"""
    return (long['close'] > long['high20_prev']) & (long['vol_ratio'] >= 1.2) & \
           (long['pct'] >= 3) & (long['pct'] <= 8) & (long['close'] > long['ma20'])


# 信号注册表: name -> (sig_mask_func, buy_offset)  buy_offset: 0=信号日收盘买, 2=T+2买
SIGNALS = {
    'A2_base(对照)': (lambda L: sig_a2(L), 0),
    'A2_v1 volr<=0.8 pct[-3,2]': (lambda L: sig_a2(L, vol_max=0.8, pct_lo=-3, pct_hi=2), 0),
    'A2_v2 volr<=1.0 pct[-3,2]': (lambda L: sig_a2(L, vol_max=1.0, pct_lo=-3, pct_hi=2), 0),
    'A2_v3 volr<=1.0 pct[-2,1]': (lambda L: sig_a2(L, vol_max=1.0), 0),
    'A2_v4 prev2>=8 volr<=0.8': (lambda L: sig_a2(L, prev2_min=8, vol_max=0.8, pct_lo=-3, pct_hi=2), 0),
    'A2_v5 去ma5 volr<=0.8': (lambda L: sig_a2(L, vol_max=0.8, pct_lo=-3, pct_hi=2, need_ma5=False), 0),
    'A2_v6 prev<=3 volr<=0.8': (lambda L: sig_a2(L, vol_max=0.8, pct_lo=-3, pct_hi=2) & (L['prev_pct'] <= 3), 0),
    '超跌B1 r20<=-15 volr<=0.8 pct>0': (lambda L: sig_over(L, -15, 0.8, pct_lo=0), 0),
    '超跌B2 r20<=-15 volr<=0.8 pct[-2,2]': (lambda L: sig_over(L, -15, 0.8, -2, 2), 0),
    '超跌B3 r20<=-20 volr<=0.7 pct[-2,2]': (lambda L: sig_over(L, -20, 0.7, -2, 2), 0),
    '超跌B4 r20<=-15 volr<=0.6 pct[-2,2]': (lambda L: sig_over(L, -15, 0.6, -2, 2), 0),
    '回踩C1 5日线不破': (lambda L: sig_pullback(L, 1), 2),
    '回踩C2 涨停半价不破': (lambda L: sig_pullback(L, 2), 2),
    '回踩C3 温和回踩-6~0': (lambda L: sig_pullback(L, 3), 2),
    '回踩C4 C1+T2再缩量': (lambda L: sig_pullback(L, 4), 2),
    '断板D1 断板后企稳': (lambda L: sig_broken(L), 0),
    '突破D2 平台放量突破': (lambda L: sig_breakout(L), 0),
}


def tradeable(long, buy_offset):
    """买入日可成交性: 非涨停/非一字/涨幅<=8%"""
    if buy_offset == 0:
        return (long['pct'] <= 8) & (long['is_yizi'] == 0)
    else:  # buy_offset == 2, 买入日 T+2
        return (long['nn_pct'] <= 8) & (long['nn_is_yizi'] == 0) & long['nn_pct'].notna()


def eval_signal(long, mask, buy_offset, depth_filter, tag=''):
    m = mask & long['depth'].isin(depth_filter)
    buy = tradeable(long, buy_offset)
    m = m & buy
    if buy_offset == 0:
        r1 = long['next_ret']
    else:
        r1 = long['nn_ret']
    df = pd.DataFrame({'r1': r1, 'date': long['date'], 'code': long['code']})[m]
    df = df.dropna(subset=['r1'])
    if len(df) == 0:
        return {'tag': tag, 'depth': ','.join(depth_filter), 'N': 0}
    r1_net = df['r1'] - COST
    eq = (1 + r1_net / 100).cumprod()
    peak = eq.cummax()
    dd = (eq / peak - 1).min() * 100
    return {
        'tag': tag, 'depth': ','.join(depth_filter),
        'N': int(len(df)),
        'win_rate': round(float((r1_net > 0).mean()) * 100, 1),
        'mean_r1': round(float(df['r1'].mean()), 3),
        'mean_r1_net': round(float((df['r1'] - COST).mean()), 3),
        'median_r1': round(float(df['r1'].median()), 3),
        'max_dd': round(float(dd), 2),
        'worst_day': round(float(df['r1'].min()), 3),
        'pass': bool(len(df) >= N_MIN and (r1_net > 0).mean() * 100 >= WIN_MIN and r1_net.mean() > RET_MIN),
    }


def main():
    t0 = time.time()
    data = json.load(open(LONG, encoding='utf-8'))
    print(f'[数据] {len(data)} 只股票')
    long = build_long(data)
    print(f'[长表] {len(long)} 行, 日期 {long["date"].min()} ~ {long["date"].max()}')
    long, mkt_df = add_mkt_labels(long, data)
    long, lu_daily, n_hot, n_cold = add_sentiment_proxy(long)
    print(f'[市况] 交易日 {long["date"].nunique()} 天')
    print(long.groupby('depth').size().to_string())
    print(f'[情绪代理] 涨停家数 亢奋>={n_hot:.0f} 冷淡<={n_cold:.0f}')

    depth_groups = {
        '深熊': ['深熊'], '中熊': ['中熊'], '浅熊': ['浅熊'],
        '震荡': ['震荡'], '牛': ['牛'], '全样本': ['深熊', '中熊', '浅熊', '震荡', '牛'],
    }
    results = []
    for name, (mk, offset) in SIGNALS.items():
        mask = mk(long)
        for gname, dl in depth_groups.items():
            if gname == '全样本':
                continue  # 全样本在最后单独加
            r = eval_signal(long, mask, offset, dl, tag=name)
            results.append(r)
        # 全样本
        r = eval_signal(long, mask, offset, depth_groups['全样本'], tag=name)
        results.append(r)

    # 情绪分层: 对每个已注册信号在中熊/浅熊下按情绪代理分冷热
    sent_results = []
    for name, (mk, offset) in SIGNALS.items():
        mask = mk(long)
        for d in ['中熊', '浅熊']:
            for sp in ['亢奋', '冷淡']:
                m = mask & (long['depth'] == d) & (long['sent_proxy'] == sp)
                buy = tradeable(long, offset)
                m = m & buy
                r1 = long['nn_ret'] if offset == 2 else long['next_ret']
                df = pd.DataFrame({'r1': r1, 'date': long['date'], 'code': long['code']})[m].dropna(subset=['r1'])
                if len(df) == 0:
                    sent_results.append({'tag': name, 'depth': d, 'sent': sp, 'N': 0})
                    continue
                sent_results.append({
                    'tag': name, 'depth': d, 'sent': sp, 'N': int(len(df)),
                    'win_rate': round(float((df['r1'] > 0).mean()) * 100, 1),
                    'mean_r1': round(float(df['r1'].mean()), 3),
                    'mean_r1_net': round(float((df['r1'] - COST).mean()), 3),
                    'median_r1': round(float(df['r1'].median()), 3),
                    'worst_day': round(float(df['r1'].min()), 3),
                    'pass': bool(len(df) >= N_MIN and ((df['r1'] - COST) > 0).mean() * 100 >= WIN_MIN and (df['r1'] - COST).mean() > RET_MIN),
                })

    out = {
        'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'sample_range': [long['date'].min(), long['date'].max()],
        'cost': COST, 'n_min': N_MIN, 'win_min': WIN_MIN, 'ret_min': RET_MIN,
        'mkt_days': long.groupby('depth').size().to_dict(),
        'sent_proxy': {'hot_q75': float(n_hot), 'cold_q25': float(n_cold)},
        'signals': results,
        'sentiment_layers': sent_results,
    }
    with open(RESULT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f'[结果] {RESULT}')

    # 控制台摘要: 中熊/浅熊 通过项
    print('\n===== 中熊档 =====')
    for r in results:
        if r['depth'] == '中熊' and r['N'] > 0:
            mark = 'PASS' if r['pass'] else ''
            print(f"{r['tag']:<36} N={r['N']:>4} 胜率={r['win_rate']:>5.1f}% mean_r1={r['mean_r1']:>6.3f} net={r['mean_r1_net']:>6.3f} med={r['median_r1']:>6.3f} dd={r['max_dd']:>6.2f} 最差={r['worst_day']:>6.3f} {mark}")
    print('\n===== 浅熊档 =====')
    for r in results:
        if r['depth'] == '浅熊' and r['N'] > 0:
            mark = 'PASS' if r['pass'] else ''
            print(f"{r['tag']:<36} N={r['N']:>4} 胜率={r['win_rate']:>5.1f}% mean_r1={r['mean_r1']:>6.3f} net={r['mean_r1_net']:>6.3f} med={r['median_r1']:>6.3f} dd={r['max_dd']:>6.2f} 最差={r['worst_day']:>6.3f} {mark}")
    print(f'\n耗时 {time.time() - t0:.1f}s')


if __name__ == '__main__':
    main()
