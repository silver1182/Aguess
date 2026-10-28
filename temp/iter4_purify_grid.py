# -*- coding: utf-8 -*-
"""
迭代2提纯网格: 在B4浅熊亢奋基础上叠加因子找高胜率子集 (iter4_purify_grid.py)
=========================================================================
基准信号: 超跌B4 (r20<=-15, vol<=0.6, pct[-2,2]) + 市况浅熊 + 情绪亢奋
叠加因子(单独+两两组合):
  F1 量能更缩: vol_ratio <= {0.35,0.4,0.45,0.5}
  F2 MA20乖离: close/ma20-1 <= {-10,-12,-15}
  F3 连跌天数: 由prev_pct/prev2_pct/prev3_pct推导 连续阴线天数 >= {2,3}
  F4 当日振幅: (high-low)/close <= {3,4,5}
  F5 前日企稳: prev_pct >= {0, 0.5}
  F6 价格区间: close <= {10, 15}
评估: 全样本 + 剔除反弹月(2022-05,2024-02) 后的 N/胜率(扣成本)/net
验收: 剔月后 N>=30 且 胜率>=65% 且 net>0
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
    print('长表', len(long), '耗时', round(time.time()-t0, 1))

    # 额外因子
    long['ma20_bias'] = (long['close'] / long['ma20'] - 1) * 100
    long['amp'] = (long['high'] - long['low']) / long['close'] * 100
    # 连续阴线天数: 当日不算, 从prev开始往前数  (简化: prev<=0 & prev2<=0 & prev3<=0 组合)
    long['consec_down'] = ((long['prev_pct'] <= 0).astype(int) + (long['prev2_pct'] <= 0).astype(int) + (long['prev3_pct'] <= 0).astype(int))

    base = (long['ret20'] <= -15) & (long['vol_ratio'] <= 0.6) & \
           (long['pct'] >= -2) & (long['pct'] <= 2) & \
           (long['depth'] == '浅熊') & (long['sent_proxy'] == '亢奋') & tradeable(long, 0)

    F = {
        'F1_vol<=0.35': long['vol_ratio'] <= 0.35,
        'F1_vol<=0.40': long['vol_ratio'] <= 0.40,
        'F1_vol<=0.45': long['vol_ratio'] <= 0.45,
        'F1_vol<=0.50': long['vol_ratio'] <= 0.50,
        'F2_bias<=-10': long['ma20_bias'] <= -10,
        'F2_bias<=-12': long['ma20_bias'] <= -12,
        'F2_bias<=-15': long['ma20_bias'] <= -15,
        'F3_down>=2': long['consec_down'] >= 2,
        'F3_down>=3': long['consec_down'] >= 3,
        'F4_amp<=3': long['amp'] <= 3,
        'F4_amp<=4': long['amp'] <= 4,
        'F5_prev>=0': long['prev_pct'] >= 0,
        'F5_prev>=0.5': long['prev_pct'] >= 0.5,
        'F6_price<=10': long['close'] <= 10,
        'F6_price<=15': long['close'] <= 15,
    }

    def stats(m):
        m = m & long['next_ret'].notna()
        df = long[['next_ret', 'date']][m]
        net = df['next_ret'] - COST
        allw = {'N': int(len(df)), 'win': round(float((net > 0).mean()) * 100, 1), 'net': round(float(net.mean()), 3)} if len(df) else {'N': 0, 'win': 0, 'net': 0}
        ex = df[~df['date'].str[:7].isin(BAN)]
        if len(ex):
            exnet = ex['next_ret'] - COST
            exw = {'N': int(len(ex)), 'win': round(float((exnet > 0).mean()) * 100, 1), 'net': round(float(exnet.mean()), 3)}
        else:
            exw = {'N': 0, 'win': 0, 'net': 0}
        return allw, exw

    rows = []
    # 单独因子
    for fname, fm in F.items():
        m = base & fm
        a, e = stats(m)
        rows.append({'combo': fname, **a, 'ex_ban_N': e['N'], 'ex_ban_win': e['win'], 'ex_ban_net': e['net']})
    # 两两组合 (只挑F1~F6有意义的, 全组合15选2=105太多, 用F1+F2+F3为主)
    combos = []
    for f1 in ['F1_vol<=0.40', 'F1_vol<=0.45', 'F1_vol<=0.50']:
        for f2 in ['F2_bias<=-10', 'F2_bias<=-12', 'F2_bias<=-15']:
            for f3 in ['F3_down>=2', 'F3_down>=3']:
                combos.append((f1, f2, f3))
    for (f1, f2, f3) in combos:
        m = base & F[f1] & F[f2] & F[f3]
        a, e = stats(m)
        rows.append({'combo': f'+'.join([f1, f2, f3]), **a, 'ex_ban_N': e['N'], 'ex_ban_win': e['win'], 'ex_ban_net': e['net']})
    # 附加: F5前日企稳/F6低价 与F1/F2组合
    for f1 in ['F1_vol<=0.45', 'F1_vol<=0.50']:
        for f2 in ['F5_prev>=0', 'F5_prev>=0.5']:
            m = base & F[f1] & F[f2]
            a, e = stats(m)
            rows.append({'combo': f'+'.join([f1, f2]), **a, 'ex_ban_N': e['N'], 'ex_ban_win': e['win'], 'ex_ban_net': e['net']})

    rdf = pd.DataFrame(rows).sort_values(['ex_ban_N', 'ex_ban_win'], ascending=[False, False])
    print('\n=== B4浅熊亢奋 提纯网格 (排序: 剔月N降序, 剔月胜率降序) ===')
    print(f"{'组合':<50} {'N':>4} {'win%':>5} {'net':>6} | {'剔月N':>4} {'剔月win%':>6} {'剔月net':>6}")
    for _, r in rdf.iterrows():
        mark = ' <<<' if r['ex_ban_N'] >= 30 and r['ex_ban_win'] >= 65 and r['ex_ban_net'] > 0 else ''
        print(f"{r['combo']:<50} {r['N']:>4} {r['win']:>5.1f} {r['net']:>6.3f} | {r['ex_ban_N']:>4} {r['ex_ban_win']:>6.1f} {r['ex_ban_net']:>6.3f}{mark}")

    rdf.to_json(TEMP + r'\purify_grid_v2_result.json', orient='records', force_ascii=False)
    print('saved purify_grid_v2_result.json  耗时', round(time.time()-t0, 1), 's')


if __name__ == '__main__':
    main()
