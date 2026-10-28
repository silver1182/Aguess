# -*- coding: utf-8 -*-
"""
迭代2打分制: 多信号打分验证高分组胜率单调性 (iter5_scoring.py)
=============================================================
在 中熊/浅熊 市况下, 对候选池(全市场 / 超跌池) 内个股计算 0-6 分:
  f1 缩量 vol_ratio<=0.6
  f2 超跌 ret20<=-15
  f3 站上5日线 close>ma5
  f4 当日收阳 pct>0
  f5 情绪亢奋 sent_proxy=='亢奋'
  f6 A2家族 prev2_pct>=9.5 & vol_ratio<=0.6 & close>ma5 & pct∈[-2,1]
按分数分组统计: N / 胜率(扣成本) / mean_net / 剔反弹月后胜率
验证高分组胜率是否单调提升。
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

COST = 0.3
BAN = ['2022-05', '2024-02']


def main():
    t0 = time.time()
    data = json.load(open(TEMP + r'\kline_day_long_v2.json', encoding='utf-8'))
    long = build_long(data)
    long, mkt_df = add_mkt_labels(long, data)
    long, lu_daily, n_hot, n_cold = add_sentiment_proxy(long)

    long['f1_shrink'] = (long['vol_ratio'] <= 0.6).astype(int)
    long['f2_over'] = (long['ret20'] <= -15).astype(int)
    long['f3_ma5'] = (long['close'] > long['ma5']).astype(int)
    long['f4_up'] = (long['pct'] > 0).astype(int)
    long['f5_hot'] = (long['sent_proxy'] == '亢奋').astype(int)
    long['f6_a2'] = ((long['prev2_pct'] >= 9.5) & (long['vol_ratio'] <= 0.6) & (long['close'] > long['ma5']) & (long['pct'] >= -2) & (long['pct'] <= 1)).astype(int)
    long['score'] = long[['f1_shrink', 'f2_over', 'f3_ma5', 'f4_up', 'f5_hot', 'f6_a2']].sum(axis=1)
    long = long[long['next_ret'].notna()].copy()
    long['ym'] = long['date'].str[:7]

    results = []
    for depth in ['中熊', '浅熊']:
        for pool_name, pool in [('全市场', long['depth'] == depth), ('超跌池', (long['depth'] == depth) & (long['ret20'] <= -15))]:
            m = pool & tradeable(long, 0)
            df = long[m][['next_ret', 'score', 'ym', 'date', 'code']].copy()
            rows = []
            for s in range(7):
                sub = df[df['score'] == s]
                if len(sub) == 0:
                    rows.append({'score': s, 'N': 0})
                    continue
                net = sub['next_ret'] - COST
                ex = sub[~sub['ym'].isin(BAN)]
                exnet = ex['next_ret'] - COST if len(ex) else pd.Series(dtype=float)
                rows.append({
                    'score': s, 'N': int(len(sub)),
                    'win': round(float((net > 0).mean()) * 100, 1),
                    'net': round(float(net.mean()), 3),
                    'ex_ban_N': int(len(ex)),
                    'ex_ban_win': round(float((exnet > 0).mean()) * 100, 1) if len(ex) else None,
                    'ex_ban_net': round(float(exnet.mean()), 3) if len(ex) else None,
                })
            results.append({'depth': depth, 'pool': pool_name, 'groups': rows})

    print('===== 打分制分组结果 =====')
    for r in results:
        print(f"\n--- {r['depth']} / {r['pool']} ---")
        print(f"{'score':>5} {'N':>6} {'win%':>6} {'net':>7} | {'剔月N':>5} {'剔月win%':>7} {'剔月net':>7}")
        for g in r['groups']:
            if g['N'] == 0:
                continue
            print(f"{g['score']:>5} {g['N']:>6} {g['win']:>6.1f} {g['net']:>7.3f} | {g['ex_ban_N']:>5} {str(g['ex_ban_win']):>7} {str(g['ex_ban_net']):>7}")
        # 高分组合并(>=4)
        hi = [g for g in r['groups'] if g['score'] >= 4 and g['N'] > 0]
        if hi:
            N = sum(g['N'] for g in hi)
            w = sum(g['win'] * g['N'] for g in hi) / N
            n = sum(g['net'] * g['N'] for g in hi) / N
            eN = sum(g['ex_ban_N'] for g in hi)
            print(f"合计>=4分: N={N} win={w:.1f} net={n:.3f} | 剔月N={eN}")

    with open(TEMP + r'\scoring_v2_result.json', 'w', encoding='utf-8') as f:
        json.dump({'results': results, 'ban': BAN}, f, ensure_ascii=False, indent=1)
    print('saved scoring_v2_result.json 耗时', round(time.time()-t0, 1), 's')


if __name__ == '__main__':
    main()
