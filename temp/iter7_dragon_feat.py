# -*- coding: utf-8 -*-
"""
迭代2资金流增强验证 (iter7_dragon_feat.py)
==========================================
1) 由 dragon_hist.json 构建 (code,date) 资金流特征:
   - drg_cnt5   近5交易日上榜次数(不含T日, 因T日晚披露)
   - drg_net5   近5交易日龙虎榜净买入合计(亿元)
   - drg_pos5   近5交易日净买入>0的天数
   - drg_net1   最近1交易日净买入(亿元)  (0=未上榜)
2) 在 候选信号 上叠加资金流过滤, 输出增强前后对比
   重点: B4浅熊亢奋 / B4中熊亢奋 / score5分组
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


def build_dragon_feat(long_dates):
    """构建 (code, date) -> feat dict"""
    hist = json.load(open(TEMP + r'\dragon_hist.json', encoding='utf-8'))
    # 交易日有序列表
    tds = sorted(long_dates)
    tdi = {d: i for i, d in enumerate(tds)}
    # 每个交易日: {code: net_amt}
    net_by_day = {}
    for d, v in hist.items():
        if d in tdi:
            net_by_day[d] = {code: (row['BILLBOARD_NET_AMT'] or 0) for code, row in v.items()}
    feat = {}
    # 近5日窗口 (i-5 .. i-1)
    for i, d in enumerate(tds):
        if d not in net_by_day:
            continue
        wstart = max(0, i - 5)
        wins = tds[wstart:i]
        agg = {}
        for wd in wins:
            wv = net_by_day.get(wd, {})
            for code, net in wv.items():
                a = agg.get(code, [0, 0.0, 0])
                a[0] += 1
                a[1] += net / 1e8
                if net > 0:
                    a[2] += 1
                agg[code] = a
        # 仅保留当日上榜的股票(特征主要服务于信号候选)
        for code, net in net_by_day[d].items():
            a = agg.get(code, [0, 0.0, 0])
            feat[(code, d)] = {'drg_cnt5': a[0], 'drg_net5': round(a[1], 4), 'drg_pos5': a[2], 'drg_net1': round(net / 1e8, 4)}
    return feat, tdi, net_by_day


def main():
    t0 = time.time()
    data = json.load(open(TEMP + r'\kline_day_long_v2.json', encoding='utf-8'))
    long = build_long(data)
    long, mkt_df = add_mkt_labels(long, data)
    long, lu_daily, n_hot, n_cold = add_sentiment_proxy(long)
    print('长表', len(long), '耗时', round(time.time()-t0, 1))

    # 资金流特征
    feat, tdi, net_by_day = build_dragon_feat(sorted(set(long['date'])))
    print('资金流特征条数:', len(feat), '耗时', round(time.time()-t0, 1))

    # 合并到长表
    long['drg_cnt5'] = long.apply(lambda r: feat.get((r['code'], r['date']), {}).get('drg_cnt5', 0), axis=1)
    long['drg_net5'] = long.apply(lambda r: feat.get((r['code'], r['date']), {}).get('drg_net5', 0.0), axis=1)
    long['drg_pos5'] = long.apply(lambda r: feat.get((r['code'], r['date']), {}).get('drg_pos5', 0), axis=1)
    long['drg_net1'] = long.apply(lambda r: feat.get((r['code'], r['date']), {}).get('drg_net1', 0.0), axis=1)
    print('特征合并完成 耗时', round(time.time()-t0, 1))

    def stats(mask, name):
        m = mask & long['next_ret'].notna() & tradeable(long, 0)
        df = long[['next_ret', 'date']][m]
        if len(df) == 0:
            print(f'{name}: N=0')
            return
        net = df['next_ret'] - COST
        ex = df[~df['date'].str[:7].isin(BAN)]
        exnet = ex['next_ret'] - COST if len(ex) else pd.Series(dtype=float)
        print(f"{name:<44} N={len(df):>5} win={float((net>0).mean())*100:>5.1f}% net={net.mean():>6.3f} | 剔月N={len(ex):>4} win={float((exnet>0).mean())*100 if len(ex) else 0:>5.1f}% net={exnet.mean() if len(ex) else 0:>6.3f}")

    # 基础信号
    B4_sh = (long['ret20'] <= -15) & (long['vol_ratio'] <= 0.6) & (long['pct'] >= -2) & (long['pct'] <= 2) & (long['depth'] == '浅熊') & (long['sent_proxy'] == '亢奋')
    B4_md = (long['ret20'] <= -15) & (long['vol_ratio'] <= 0.6) & (long['pct'] >= -2) & (long['pct'] <= 2) & (long['depth'] == '中熊') & (long['sent_proxy'] == '亢奋')

    print('\n===== 资金流增强验证 =====')
    stats(B4_sh, 'B4浅熊亢奋(基准)')
    stats(B4_sh & (long['drg_cnt5'] >= 1), 'B4浅熊亢奋 + 近5日上榜>=1')
    stats(B4_sh & (long['drg_net5'] > 0), 'B4浅熊亢奋 + 近5日净买入>0')
    stats(B4_sh & (long['drg_pos5'] >= 2), 'B4浅熊亢奋 + 近5日净买入正天数>=2')
    stats(B4_sh & (long['drg_net1'] > 0), 'B4浅熊亢奋 + T-1日净买入>0')
    stats(B4_sh & (long['drg_cnt5'] == 0), 'B4浅熊亢奋 + 近5日未上榜')
    print()
    stats(B4_md, 'B4中熊亢奋(基准)')
    stats(B4_md & (long['drg_cnt5'] >= 1), 'B4中熊亢奋 + 近5日上榜>=1')
    stats(B4_md & (long['drg_net5'] > 0), 'B4中熊亢奋 + 近5日净买入>0')
    stats(B4_md & (long['drg_pos5'] >= 2), 'B4中熊亢奋 + 近5日净买入正天数>=2')
    stats(B4_md & (long['drg_cnt5'] == 0), 'B4中熊亢奋 + 近5日未上榜')

    long.to_json(TEMP + r'\long_v2_with_dragon.json', orient='records', force_ascii=False)
    print('saved long_v2_with_dragon.json 耗时', round(time.time()-t0, 1), 's')


if __name__ == '__main__':
    main()
