# -*- coding: utf-8 -*-
"""
多逻辑批量回测: 找可成交(尾盘买/主板/无未来函数)的正期望短线信号
信号在 T-1 收盘确定, T-1 尾盘买入, 卖出 T收盘 / T+1开盘 / T+1收盘
成本 0.5%; 对比不过滤 vs 市况过滤(市场>20日均线才交易) 两版
"""
import json, os
import pandas as pd
import numpy as np

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
temp_dir = base + r'\temp'
out_dir = base + r'\output'
os.makedirs(out_dir, exist_ok=True)

with open(temp_dir + r'\kline_cache_em.json', encoding='utf-8') as f:
    k = json.load(f)
rows = []
for code, bars in k.items():
    for b in bars:
        b['code'] = code
        rows.append(b)
df = pd.DataFrame(rows)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['code', 'date']).reset_index(drop=True)
df = df[df['close'].notna()].copy()

g = df.groupby('code')
df['prev_close'] = g['close'].shift(1)
df['prev_vol'] = g['volume'].shift(1)
df['pct'] = df['close'] / df['prev_close'] - 1
df['vol_chg'] = df['volume'] / df['prev_vol']
df['ma5'] = g['close'].transform(lambda x: x.rolling(5).mean())
df['ma10'] = g['close'].transform(lambda x: x.rolling(10).mean())
df['ma20'] = g['close'].transform(lambda x: x.rolling(20).mean())
df['ret_1d'] = df['close'] / g['close'].shift(1) - 1
df['cum_5d'] = df['close'] / g['close'].shift(5) - 1
df['bias_ma20'] = df['close'] / df['ma20'] - 1
df['above_ma20'] = (df['close'] > df['ma20']).astype(int)
df['limit_up'] = (df['pct'] >= 0.095).astype(int)
df['vol_chg_max5'] = g['vol_chg'].transform(lambda x: x.rolling(5).max())
df['close_pos'] = (df['close'] - df['low']) / (df['high'] - df['low']).replace(0, np.nan)
df['prev_limit_up'] = g['limit_up'].shift(1)
df['lu_5d'] = g['limit_up'].transform(lambda x: x.rolling(5).sum())
# 未来收益(行 t=信号日T-1; T日=t+1, T+1日=t+2)
df['ret_c0'] = g['close'].shift(-1) / df['close'] - 1
df['ret_o1'] = g['open'].shift(-2) / df['close'] - 1
df['ret_c1'] = g['close'].shift(-2) / df['close'] - 1
# 市场指数近似(每日截面等权) + 20日均线
mkt = df.groupby('date')['close'].mean().sort_index()
mkt_ma = mkt.rolling(20).mean()
df['mkt'] = df['date'].map(mkt)
df['mkt_ma20'] = df['date'].map(mkt_ma)
df['mkt_bull'] = (df['mkt'] > df['mkt_ma20']).astype(int)

signals = {
    'S1超跌反弹(当日跌3%+)': lambda d: d['ret_1d'] <= -0.03,
    'S2深度超跌(5日跌8%+)': lambda d: (d['cum_5d'] <= -0.08) & (d['ret_1d'] < 0),
    'S3缩量回调': lambda d: (d['ret_1d'] < 0) & (d['vol_chg'] < 0.8),
    'S4回踩MA20缩量': lambda d: (d['above_ma20'] == 1) & (d['bias_ma20'] >= -0.03) & (d['bias_ma20'] <= 0.01) & (d['vol_chg'] < 1.2),
    'S5低位首次放量': lambda d: (d['above_ma20'] == 1) & (d['vol_chg'] > 1.5) & (d['vol_chg_max5'] < 1.2),
    'S6跌后缩量企稳': lambda d: (d['cum_5d'] <= -0.05) & (d['ret_1d'] > -0.01) & (d['vol_chg'] < 0.9),
    'S7小阳蓄势': lambda d: (d['ret_1d'] > 0) & (d['ret_1d'] <= 0.02) & (d['vol_chg'] >= 0.8) & (d['vol_chg'] <= 1.5) & (d['above_ma20'] == 1),
    'S8强势放量(追强)': lambda d: (d['ret_1d'] >= 0.03) & (d['vol_chg'] >= 1.2) & (d['above_ma20'] == 1),
    'S9极端反转(跌5%+)': lambda d: d['ret_1d'] <= -0.05,
    'S10温和上涨企稳': lambda d: (d['ret_1d'] > 0) & (d['ret_1d'] <= 0.03) & (d['vol_chg'] >= 0.8) & (d['vol_chg'] <= 2.0) & (d['bias_ma20'] >= -0.02),
    'S11尾盘强收': lambda d: (d['close_pos'] >= 0.9) & (d['ret_1d'] > 0) & (d['vol_chg'] >= 1.0),
    'S12断板反包(近5日涨停今回调)': lambda d: (d['lu_5d'] >= 1) & (d['ret_1d'] < 0) & (d['ret_1d'] > -0.05) & (d['above_ma20'] == 1),
    'S13涨停次日缩量回调': lambda d: (d['prev_limit_up'] == 1) & (d['ret_1d'] < 0) & (d['vol_chg'] < 1.0),
}

HOLDS = {'c0': 'T收盘', 'o1': 'T+1开盘', 'c1': 'T+1收盘'}
COST = 0.0025
dates = sorted(df['date'].unique())
# 预热: 跳过前25天(均线/分布未就绪)
dates = [d for d in dates if d >= dates[20]]

results = []
for date in dates:
    day = df[df['date'] == date].copy()
    day = day[day['ret_1d'].notna() & day['cum_5d'].notna() & day['bias_ma20'].notna()]
    # 可成交: 信号日未涨停(尾盘买不进)
    day = day[day['limit_up'] == 0]
    if len(day) < 50:
        continue
    bull = bool(day['mkt_bull'].iloc[0])
    for name, cond in signals.items():
        sel = day[cond(day)]
        if len(sel) == 0:
            continue
        for flt_name, use_filter in [('不过滤', False), ('市况过滤', True)]:
            if use_filter and not bull:
                # 空仓: 记0收益
                for h in HOLDS:
                    results.append((date, name, flt_name, h, 0.0, 0))
                continue
            for h in HOLDS:
                r = sel[f'ret_{h}'].mean() - COST * 2
                results.append((date, name, flt_name, h, r, len(sel)))

res_df = pd.DataFrame(results, columns=['date', 'signal', 'flt', 'hold', 'ret', 'n'])

# 汇总
rows_out = []
for name in signals:
    for flt_name in ['不过滤', '市况过滤']:
        for h, hname in HOLDS.items():
            sub = res_df[(res_df['signal'] == name) & (res_df['flt'] == flt_name) & (res_df['hold'] == h)].sort_values('date')
            if len(sub) == 0:
                continue
            nav = (1 + sub['ret']).cumprod()
            total = nav.iloc[-1] - 1
            daily = sub['ret'].mean()
            win = (sub['ret'] > 0).mean()
            avg_n = sub[sub['n'] > 0]['n'].mean()
            rows_out.append({'signal': name, 'flt': flt_name, 'hold': hname, 'total': total,
                             'daily': daily, 'win': win, 'avg_n': avg_n, 'days': len(sub)})
out = pd.DataFrame(rows_out).sort_values('total', ascending=False)
pd.set_option('display.width', 200)
print(out.to_string(index=False))

# 存 CSV
out.to_csv(out_dir + r'\多逻辑批量回测_20261027.csv', index=False, encoding='utf-8-sig')
print()
print('[产出]', out_dir + r'\多逻辑批量回测_20261027.csv')
