# -*- coding: utf-8 -*-
"""
迭代2资金流增强验证 v2 (iter7_dragon_feat.py 重写)
==================================================
1) 由 dragon_hist.json 构建 (code,date) 资金流特征(滚动窗口, 对每只股票全部交易日生效):
   - drg_cnt5 近5交易日上榜次数(不含T日)
   - drg_net5 近5交易日龙虎榜净买入合计(亿元)
   - drg_pos5 近5交易日净买入>0的天数
   - drg_net1 T-1日净买入(亿元, 0=未上榜)
2) 在候选信号上叠加资金流过滤, 输出增强前后对比
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
    long = long.sort_values(['code', 'date']).reset_index(drop=True)
    print('长表', len(long), '耗时', round(time.time()-t0, 1))

    # 上榜事件表
    hist = json.load(open(TEMP + r'\dragon_hist.json', encoding='utf-8'))
    ev_rows = []
    for d, v in hist.items():
        for code, row in v.items():
            ev_rows.append({'code': code, 'date': d, 'net': (row['BILLBOARD_NET_AMT'] or 0) / 1e8})
    ev = pd.DataFrame(ev_rows)
    print('上榜事件', len(ev))

    # merge 到长表 (每个 code,date 有 net, 未上榜=NaN)
    long = long.merge(ev, on=['code', 'date'], how='left')
    long['net'] = long['net'].fillna(0.0)
    long['on_board'] = (long['net'] != 0).astype(int)

    g = long.groupby('code')
    long['drg_cnt5'] = g['on_board'].transform(lambda s: s.rolling(5, min_periods=1).sum().shift(1)).fillna(0).astype(int)
    long['drg_net5'] = g['net'].transform(lambda s: s.rolling(5, min_periods=1).sum().shift(1)).fillna(0.0)
    long['drg_pos5'] = g['net'].transform(lambda s: (s > 0).rolling(5, min_periods=1).sum().shift(1)).fillna(0).astype(int)
    long['drg_net1'] = g['net'].transform(lambda s: s.shift(1)).fillna(0.0)
    print('特征构建完成 耗时', round(time.time()-t0, 1))

    def stats(mask, name):
        m = mask & long['next_ret'].notna() & tradeable(long, 0)
        df = long[['next_ret', 'date']][m]
        if len(df) == 0:
            print(f'{name}: N=0')
            return
        net = df['next_ret'] - COST
        ex = df[~df['date'].str[:7].isin(BAN)]
        exnet = ex['next_ret'] - COST if len(ex) else pd.Series(dtype=float)
        print(f"{name:<46} N={len(df):>5} win={float((net>0).mean())*100:>5.1f}% net={net.mean():>6.3f} | 剔月N={len(ex):>4} win={float((exnet>0).mean())*100 if len(ex) else 0:>5.1f}% net={exnet.mean() if len(ex) else 0:>6.3f}")

    B4_sh = (long['ret20'] <= -15) & (long['vol_ratio'] <= 0.6) & (long['pct'] >= -2) & (long['pct'] <= 2) & (long['depth'] == '浅熊') & (long['sent_proxy'] == '亢奋')
    B4_md = (long['ret20'] <= -15) & (long['vol_ratio'] <= 0.6) & (long['pct'] >= -2) & (long['pct'] <= 2) & (long['depth'] == '中熊') & (long['sent_proxy'] == '亢奋')

    print('\n===== 资金流增强验证 =====')
    stats(B4_sh, 'B4浅熊亢奋(基准)')
    stats(B4_sh & (long['drg_cnt5'] >= 1), 'B4浅熊亢奋 + 近5日上榜>=1')
    stats(B4_sh & (long['drg_net5'] > 0), 'B4浅熊亢奋 + 近5日净买入>0')
    stats(B4_sh & (long['drg_pos5'] >= 2), 'B4浅熊亢奋 + 近5日净买入正天数>=2')
    stats(B4_sh & (long['drg_net1'] > 0), 'B4浅熊亢奋 + T-1日净买入>0')
    stats(B4_sh & (long['drg_cnt5'] == 0), 'B4浅熊亢奋 + 近5日未上榜')
    stats(B4_sh & (long['drg_net5'] < 0), 'B4浅熊亢奋 + 近5日净买入<0')
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
