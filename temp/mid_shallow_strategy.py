# -*- coding: utf-8 -*-
"""
中熊/浅熊适配策略最终定义与一键回测验证 (mid_shallow_strategy.py)
=================================================================
基于 backtest_signals.py / quick_grid.py 挖掘结果, 固化两个通过验收的策略:

  中熊策略 M1 (超跌企稳-深): r20<=-20 且 vol_ratio<=0.8 且 close>ma5 且 close>ma10 且 当日pct>0
  浅熊策略 S1 (超跌企稳-标准): r20<=-15 且 vol_ratio<=0.8 且 close>ma5 且 close>ma10 且 当日pct>0
  深熊对照 A2 (既有): prev2_pct>=9.5 且 vol_ratio<=0.6 且 close>ma5 且 当日pct∈[-2,1]

买入: 信号日收盘价; 卖出: 次日收盘价 (r1); 双边成本 0.3%; 可成交性: 信号日涨幅<=8% 且非一字板。
验收: N>=30 且 扣成本胜率>=55% 且 扣成本平均r1>0。
输出: temp\final_strategy_result.json (含分档统计 + 月度/股票集中度检查)
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
COST = 0.3
N_MIN, WIN_MIN, RET_MIN = 30, 55.0, 0.0

import backtest_signals as bt
from backtest_signals import build_long, add_mkt_labels, add_sentiment_proxy, tradeable, eval_signal


def sig_M1(L):
    return (L['ret20'] <= -20) & (L['vol_ratio'] <= 0.8) & (L['close'] > L['ma5']) & \
           (L['close'] > L['ma10']) & (L['pct'] > 0)


def sig_S1(L):
    return (L['ret20'] <= -15) & (L['vol_ratio'] <= 0.8) & (L['close'] > L['ma5']) & \
           (L['close'] > L['ma10']) & (L['pct'] > 0)


def sig_A2(L):
    return (L['prev2_pct'] >= 9.5) & (L['vol_ratio'] <= 0.6) & (L['close'] > L['ma5']) & \
           (L['pct'] >= -2) & (L['pct'] <= 1)


def dist_check(long, mask, buy_offset, depth_filter):
    """样本的时间分布与股票集中度检查"""
    m = mask & long['depth'].isin(depth_filter) & tradeable(long, buy_offset)
    df = long[['date', 'code']][m].copy()
    if len(df) == 0:
        return {'N': 0}
    df['ym'] = df['date'].str[:7]
    mdist = df.groupby('ym').size().to_dict()
    n_stock = df['code'].nunique()
    per_stock = df.groupby('code').size().sort_values(ascending=False).head(8).to_dict()
    return {'N': int(len(df)), 'months': mdist, 'n_distinct_stock': int(n_stock), 'top_stock': per_stock}


def main():
    data = json.load(open(LONG, encoding='utf-8'))
    long = build_long(data)
    long, mkt_df = add_mkt_labels(long, data)
    long, lu_daily, n_hot, n_cold = add_sentiment_proxy(long)

    sigs = {'M1_中熊策略_超跌企稳深': sig_M1, 'S1_浅熊策略_超跌企稳标准': sig_S1, 'A2_深熊对照': sig_A2}
    depths = ['深熊', '中熊', '浅熊', '震荡', '牛', '全样本']
    all_depth = ['深熊', '中熊', '浅熊', '震荡', '牛']
    results = []
    for name, mk in sigs.items():
        mask = mk(long)
        for d in depths:
            dl = all_depth if d == '全样本' else [d]
            res = eval_signal(long, mask, 0, dl, tag=name)
            res['depth'] = d
            res['dist'] = dist_check(long, mask, 0, dl) if d in ('中熊', '浅熊') else {}
            results.append(res)
            if res['N'] > 0:
                print(f"{name:<30} {d} N={res['N']:>5} 胜率={res['win_rate']:>5.1f}% mean={res['mean_r1']:>6.3f} net={res['mean_r1_net']:>6.3f} med={res['median_r1']:>6.3f} dd={res['max_dd']:>6.2f} 最差={res['worst_day']:>6.3f} {'PASS' if res['pass'] else ''}")

    out = {'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'), 'cost': COST, 'strategies': results}
    with open(TEMP + r'\final_strategy_result.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('saved', TEMP + r'\final_strategy_result.json')


if __name__ == '__main__':
    main()
