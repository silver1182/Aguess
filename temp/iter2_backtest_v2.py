# -*- coding: utf-8 -*-
"""
迭代1回测: 扩展样本(2022-2026)全信号分层回测 (iter2_backtest_v2.py)
================================================================
基于 kline_day_long_v2.json, 复用 backtest_signals 的信号定义与评估逻辑,
输出:
  1) 全信号×市况分档统计 (含2022+新样本)
  2) 深熊A2 分月分布 + 分年回测 (验证单月依赖是否仍成立)
  3) M1/S1 在中熊/浅熊下的新样本表现 (月度集中度检查)
结果: backtest_signals_v2_result.json
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
LONG = TEMP + r'\kline_day_long_v2.json'
RESULT = TEMP + r'\backtest_signals_v2_result.json'
sys.path.insert(0, TEMP)
import backtest_signals as bt
from backtest_signals import build_long, add_mkt_labels, add_sentiment_proxy, tradeable, eval_signal

COST = 0.3


def dist_check(long, mask, buy_offset, depth_filter):
    m = mask & long['depth'].isin(depth_filter) & tradeable(long, buy_offset)
    df = long[['date', 'code', 'next_ret']][m].copy()
    if len(df) == 0:
        return {'N': 0}
    df['ym'] = df['date'].str[:7]
    df['yr'] = df['date'].str[:4]
    mdist = df.groupby('ym').size().to_dict()
    ydist = df.groupby('yr').size().to_dict()
    by_ym_win = df.groupby('ym')['next_ret'].agg(['count', lambda s: float((s - COST > 0).mean()) * 100])
    by_ym_win.columns = ['N', 'win_net']
    return {'N': int(len(df)), 'months': mdist, 'years': ydist,
            'by_ym': by_ym_win.round(1).to_dict('index')}


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

    # ---- 1) 全信号分档回测 ----
    depth_groups = {'深熊': ['深熊'], '中熊': ['中熊'], '浅熊': ['浅熊'],
                    '震荡': ['震荡'], '牛': ['牛'], '全样本': ['深熊', '中熊', '浅熊', '震荡', '牛']}
    results = []
    for name, (mk, offset) in bt.SIGNALS.items():
        mask = mk(long)
        for gname, dl in depth_groups.items():
            r = eval_signal(long, mask, offset, dl, tag=name)
            r['depth'] = gname
            results.append(r)

    # 情绪分层 (中熊/浅熊 x 冷热)
    sent_results = []
    for name, (mk, offset) in bt.SIGNALS.items():
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
                sent_results.append({'tag': name, 'depth': d, 'sent': sp, 'N': int(len(df)),
                                     'win_rate': round(float((df['r1'] > 0).mean()) * 100, 1),
                                     'mean_r1': round(float(df['r1'].mean()), 3),
                                     'mean_r1_net': round(float((df['r1'] - COST).mean()), 3),
                                     'pass': bool(len(df) >= 30 and ((df['r1'] - COST) > 0).mean() * 100 >= 55.0 and (df['r1'] - COST).mean() > 0)})

    # ---- 2) 深熊 A2 单月依赖专项 ----
    a2_mask = bt.sig_a2(long)
    a2_dist = dist_check(long, a2_mask, 0, ['深熊'])
    a2_by_yr = {}
    for yr in ['2022', '2023', '2024', '2025', '2026']:
        m = a2_mask & (long['depth'] == '深熊') & (long['date'].str[:4] == yr) & tradeable(long, 0)
        df = long[['next_ret']][m].dropna()
        if len(df):
            a2_by_yr[yr] = {'N': int(len(df)), 'win_rate': round(float((df['next_ret'] - COST > 0).mean()) * 100, 1),
                            'mean_r1_net': round(float((df['next_ret'] - COST).mean()), 3)}
        else:
            a2_by_yr[yr] = {'N': 0}

    # ---- 3) M1/S1 扩展样本验证 ----
    sig_M1 = (long['ret20'] <= -20) & (long['vol_ratio'] <= 0.8) & (long['close'] > long['ma5']) & (long['close'] > long['ma10']) & (long['pct'] > 0)
    sig_S1 = (long['ret20'] <= -15) & (long['vol_ratio'] <= 0.8) & (long['close'] > long['ma5']) & (long['close'] > long['ma10']) & (long['pct'] > 0)
    m1_res = {'mid': eval_signal(long, sig_M1, 0, ['中熊'], 'M1_中熊'), 'shallow': eval_signal(long, sig_M1, 0, ['浅熊'], 'M1_浅熊')}
    s1_res = {'mid': eval_signal(long, sig_S1, 0, ['中熊'], 'S1_中熊'), 'shallow': eval_signal(long, sig_S1, 0, ['浅熊'], 'S1_浅熊')}
    m1_dist = {'mid': dist_check(long, sig_M1, 0, ['中熊']), 'shallow': dist_check(long, sig_M1, 0, ['浅熊'])}
    s1_dist = {'mid': dist_check(long, sig_S1, 0, ['中熊']), 'shallow': dist_check(long, sig_S1, 0, ['浅熊'])}

    out = {'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
           'sample_range': [long['date'].min(), long['date'].max()],
           'mkt_days': long.groupby('depth').size().to_dict(),
           'signals': results, 'sentiment_layers': sent_results,
           'a2_deep_dist': a2_dist, 'a2_deep_by_year': a2_by_yr,
           'M1': {'res': m1_res, 'dist': m1_dist}, 'S1': {'res': s1_res, 'dist': s1_dist}}
    with open(RESULT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('[结果]', RESULT)

    print('\n===== 深熊A2分年 =====')
    for yr, v in a2_by_yr.items():
        print(yr, v)
    print('\n===== 深熊A2分月(前12) =====')
    by_ym = a2_dist.get('by_ym', {})
    for k, v in list(by_ym.items())[:12]:
        print(k, v)
    print('\n===== M1/S1 扩展样本 =====')
    for k, v in {**m1_res, **s1_res}.items():
        print(k, v)
    print(f'\n耗时 {time.time() - t0:.1f}s')


if __name__ == '__main__':
    main()
