# -*- coding: utf-8 -*-
"""中熊专项补充网格挖掘 + 浅熊稳健性对照"""
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
COST = 0.3

import backtest_signals as bt
from backtest_signals import build_long, add_mkt_labels, add_sentiment_proxy, tradeable, eval_signal

def sig_ub(long, r20, volmax, pct_lo, pct_hi=None, extra=None):
    cond = (long['ret20'] <= r20) & (long['vol_ratio'] <= volmax) & (long['close'] > long['ma5']) & \
           (long['pct'] > pct_lo)
    if pct_hi is not None:
        cond &= (long['pct'] <= pct_hi)
    if extra:
        cond &= extra(long)
    return cond

def main():
    data = json.load(open(LONG, encoding='utf-8'))
    long = build_long(data)
    long, mkt_df = add_mkt_labels(long, data)
    long, lu_daily, n_hot, n_cold = add_sentiment_proxy(long)
    long = long[(long['depth'].isin(['中熊', '浅熊']))].copy()
    print('rows:', len(long))

    grid = []
    # 中熊超跌网格
    configs = [
        ('UB r20<=-12 v0.8 p>0', -12, 0.8, 0.0),
        ('UB r20<=-15 v0.8 p>0 (B1)', -15, 0.8, 0.0),
        ('UB r20<=-18 v0.8 p>0', -18, 0.8, 0.0),
        ('UB r20<=-20 v0.8 p>0', -20, 0.8, 0.0),
        ('UB r20<=-25 v0.8 p>0', -25, 0.8, 0.0),
        ('UB r20<=-15 v0.7 p>0', -15, 0.7, 0.0),
        ('UB r20<=-15 v0.6 p>0', -15, 0.6, 0.0),
        ('UB r20<=-15 v0.8 p>=1', -15, 0.8, 1.0),
        ('UB r20<=-15 v0.8 p>=2', -15, 0.8, 2.0),
        ('UB r20<=-15 v0.8 p>0 ma10', -15, 0.8, 0.0, lambda L: L['close'] > L['ma10']),
        ('UB r20<=-20 v0.8 p>0 ma10', -20, 0.8, 0.0, lambda L: L['close'] > L['ma10']),
        ('UB r20<=-15 v0.8 p>0 量缩5日最低', -15, 0.8, 0.0, lambda L: L['volume'] < L['vol5'] * 0.5),
    ]
    # 中熊+冷淡
    cold = long['sent_proxy'] == '冷淡'
    configs.append(('UB r20<=-15 v0.8 p>0 冷淡', -15, 0.8, 0.0, lambda L: L['sent_proxy'] == '冷淡'))
    configs.append(('UB r20<=-18 v0.8 p>0 冷淡', -18, 0.8, 0.0, lambda L: L['sent_proxy'] == '冷淡'))
    configs.append(('UB r20<=-20 v0.7 p>0 冷淡', -20, 0.7, 0.0, lambda L: L['sent_proxy'] == '冷淡'))
    configs.append(('UB r20<=-15 v0.6 p>0 冷淡', -15, 0.6, 0.0, lambda L: L['sent_proxy'] == '冷淡'))
    # 中熊+亢奋
    hot = long['sent_proxy'] == '亢奋'
    configs.append(('UB r20<=-15 v0.8 p>0 亢奋', -15, 0.8, 0.0, lambda L: L['sent_proxy'] == '亢奋'))

    results = []
    for name, r20, vmax, plo, *rest in configs:
        extra = rest[0] if rest else None
        mask = sig_ub(long, r20, vmax, plo, extra=extra)
        for d in ['中熊', '浅熊']:
            res = eval_signal(long, mask, 0, [d], tag=name)
            res['depth'] = d
            results.append(res)
            if res['N'] > 0:
                print(f"{name:<38} {d} N={res['N']:>5} 胜率={res['win_rate']:>5.1f}% mean={res['mean_r1']:>6.3f} net={res['mean_r1_net']:>6.3f} med={res['median_r1']:>6.3f} dd={res['max_dd']:>6.2f} 最差={res['worst_day']:>6.3f} {'PASS' if res['pass'] else ''}")

    out = {'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'), 'cost': COST, 'grid': results}
    with open(TEMP + r'\backtest_grid_result.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('saved', TEMP + r'\backtest_grid_result.json')

if __name__ == '__main__':
    main()
