# -*- coding: utf-8 -*-
"""
迭代1稳健性: 候选信号剔除反弹月检验 (iter3_robust_check.py)
=========================================================
针对扩展样本下胜率最高的候选(B3/B4 中熊亢奋, B4 浅熊亢奋, A2_v1 中熊冷淡等),
做:
  1) 分月分布(看是否集中于2022-05/2024-02)
  2) 剔除反弹月(2022-05, 2024-02)后的胜率/均值
  3) 逐年胜率
结果: robust_check_v2_result.json
"""
import json, sys, time, warnings
import pandas as pd
import numpy as np
warnings.filterwarnings('ignore')
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

BASE = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
TEMP = BASE + r'\temp'
sys.path.insert(0, TEMP)
from backtest_signals import build_long, add_mkt_labels, add_sentiment_proxy, tradeable
import backtest_signals as bt

COST = 0.3
BAN = ['2022-05', '2024-02']  # 疑似反弹月


def full_stats(long, mask, depth, sent=None):
    m = mask & (long['depth'] == depth)
    if sent:
        m &= (long['sent_proxy'] == sent)
    m &= tradeable(long, 0)
    df = long[['next_ret', 'date', 'code']][m].dropna(subset=['next_ret'])
    if len(df) == 0:
        return {'N': 0}
    df['ym'] = df['date'].str[:7]
    df['yr'] = df['date'].str[:4]
    net = df['next_ret'] - COST
    ym_stat = df.groupby('ym')['next_ret'].agg(['count', lambda s: round(float((s - COST > 0).mean()) * 100, 1)])
    ym_stat.columns = ['N', 'win_net']
    return {
        'N': int(len(df)),
        'win_rate': round(float((net > 0).mean()) * 100, 1),
        'mean_r1_net': round(float(net.mean()), 3),
        'months': df.groupby('ym').size().to_dict(),
        'years': {yr: {'N': int(v), 'win': round(float(((df.loc[df.yr == yr, 'next_ret'] - COST) > 0).mean()) * 100, 1)} for yr, v in df.groupby('yr').size().items()},
        'by_ym': ym_stat.to_dict('index'),
    }


def ex_ban(long, mask, depth, sent=None):
    m = mask & (long['depth'] == depth)
    if sent:
        m &= (long['sent_proxy'] == sent)
    m &= tradeable(long, 0)
    m &= ~long['date'].str[:7].isin(BAN)
    df = long[['next_ret', 'date']][m].dropna(subset=['next_ret'])
    if len(df) == 0:
        return {'N': 0}
    net = df['next_ret'] - COST
    return {'N': int(len(df)), 'win_rate': round(float((net > 0).mean()) * 100, 1),
            'mean_r1_net': round(float(net.mean()), 3)}


def main():
    t0 = time.time()
    data = json.load(open(TEMP + r'\kline_day_long_v2.json', encoding='utf-8'))
    long = build_long(data)
    long, mkt_df = add_mkt_labels(long, data)
    long, lu_daily, n_hot, n_cold = add_sentiment_proxy(long)

    sigs = {
        'B3 中熊亢奋': (bt.sig_over(long, -20, 0.7, -2, 2), '中熊', '亢奋'),
        'B4 中熊亢奋': (bt.sig_over(long, -15, 0.6, -2, 2), '中熊', '亢奋'),
        'B4 浅熊亢奋': (bt.sig_over(long, -15, 0.6, -2, 2), '浅熊', '亢奋'),
        'B4 中熊全量': (bt.sig_over(long, -15, 0.6, -2, 2), '中熊', None),
        'A2v1 中熊冷淡': (bt.sig_a2(long, 0.8, -3, 2), '中熊', '冷淡'),
        'B1 中熊亢奋': (bt.sig_over(long, -15, 0.8, 0, None), '中熊', '亢奋'),
    }
    out = {}
    print('候选                                                          全样本(N/win/net)              剔反弹月(N/win/net)')
    for name, (mask, depth, sent) in sigs.items():
        fs = full_stats(long, mask, depth, sent)
        ex = ex_ban(long, mask, depth, sent)
        out[name] = {'full': fs, 'ex_ban': ex}
        if fs['N']:
            print(f"{name:<32} {fs['N']:>5} {fs['win_rate']:>5.1f}% {fs['mean_r1_net']:>6.3f}   ->   {ex['N']:>5} {ex['win_rate']:>5.1f}% {ex['mean_r1_net']:>6.3f}")
            print('   月份TOP5:', dict(sorted(fs['months'].items(), key=lambda x: -x[1])[:5]))
            print('   逐年:', {k: v['win'] for k, v in fs['years'].items()})
    with open(TEMP + r'\robust_check_v2_result.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('saved robust_check_v2_result.json')


if __name__ == '__main__':
    main()
