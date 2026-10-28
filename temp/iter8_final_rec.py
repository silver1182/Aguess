# -*- coding: utf-8 -*-
"""
迭代2最终推荐验证 (iter8_final_rec.py)
======================================
最终推荐策略候选验证 + 逐年/逐月稳健性, 产出 final_recommendation_v2.json
候选:
  R1 浅熊B4亢奋+score>=5   (打分制高分组)
  R2 浅熊B4亢奋+F2_bias<=-12 (提纯网格较优)
  R3 浅熊B4亢奋(基准)      对照
  R4 中熊A2冷淡            对照
输出: 全样本/剔反弹月/逐年/月份集中度
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
    long['ma20_bias'] = (long['close'] / long['ma20'] - 1) * 100
    long['score'] = ((long['vol_ratio'] <= 0.6).astype(int) + (long['ret20'] <= -15).astype(int) +
                     (long['close'] > long['ma5']).astype(int) + (long['pct'] > 0).astype(int) +
                     (long['sent_proxy'] == '亢奋').astype(int) +
                     ((long['prev2_pct'] >= 9.5) & (long['vol_ratio'] <= 0.6) & (long['close'] > long['ma5']) & (long['pct'] >= -2) & (long['pct'] <= 1)).astype(int))

    B4_sh = (long['ret20'] <= -15) & (long['vol_ratio'] <= 0.6) & (long['pct'] >= -2) & (long['pct'] <= 2) & (long['depth'] == '浅熊') & (long['sent_proxy'] == '亢奋')
    sigs = {
        'R3 浅熊B4亢奋(基准)': B4_sh,
        'R1 浅熊B4+score>=5': B4_sh & (long['score'] >= 5),
        'R2 浅熊B4+bias<=-12': B4_sh & (long['ma20_bias'] <= -12),
        'R4 中熊A2冷淡': (long['prev2_pct'] >= 9.5) & (long['vol_ratio'] <= 0.6) & (long['close'] > long['ma5']) & (long['pct'] >= -2) & (long['pct'] <= 2) & (long['depth'] == '中熊') & (long['sent_proxy'] == '冷淡'),
    }

    out = {}
    print(f"{'策略':<28} {'N':>4} {'win%':>6} {'net':>7} | {'剔月N':>4} {'剔月win%':>7} {'剔月net':>7} | 逐年win")
    for name, mask in sigs.items():
        m = mask & long['next_ret'].notna() & tradeable(long, 0)
        df = long[['next_ret', 'date']][m].copy()
        if len(df) == 0:
            print(name, 'N=0')
            continue
        net = df['next_ret'] - COST
        df['ym'] = df['date'].str[:7]
        df['yr'] = df['date'].str[:4]
        ex = df[~df['ym'].isin(BAN)]
        exnet = ex['next_ret'] - COST if len(ex) else pd.Series(dtype=float)
        yrs = {yr: {'N': int(v), 'win': round(float(((df.loc[df.yr == yr, 'next_ret'] - COST) > 0).mean()) * 100, 1)}
               for yr, v in df.groupby('yr').size().items()}
        top_m = dict(sorted(df.groupby('ym').size().items(), key=lambda x: -x[1])[:4])
        rec = {
            'N': int(len(df)), 'win': round(float((net > 0).mean()) * 100, 1), 'net': round(float(net.mean()), 3),
            'ex_ban_N': int(len(ex)),
            'ex_ban_win': round(float((exnet > 0).mean()) * 100, 1) if len(ex) else None,
            'ex_ban_net': round(float(exnet.mean()), 3) if len(ex) else None,
            'years': yrs, 'top_months': top_m,
        }
        out[name] = rec
        print(f"{name:<28} {rec['N']:>4} {rec['win']:>6.1f} {rec['net']:>7.3f} | {rec['ex_ban_N']:>4} {str(rec['ex_ban_win']):>7} {str(rec['ex_ban_net']):>7} | {yrs}")
        print(f"{'':<28} 月份TOP4: {top_m}")

    with open(TEMP + r'\final_recommendation_v2.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('saved final_recommendation_v2.json 耗时', round(time.time()-t0, 1), 's')


if __name__ == '__main__':
    main()
