import json, sys, time
import pandas as pd, numpy as np, warnings
warnings.filterwarnings('ignore')
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
BASE = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
TEMP = BASE + r'\temp'
import backtest_signals as bt
from backtest_signals import build_long, add_mkt_labels, add_sentiment_proxy, tradeable

data = json.load(open(TEMP + r'\kline_day_long.json', encoding='utf-8'))
long = build_long(data)
long, mkt_df = add_mkt_labels(long, data)
long, lu, h, c = add_sentiment_proxy(long)

def sig_M1(L):
    return (L['ret20'] <= -20) & (L['vol_ratio'] <= 0.8) & (L['close'] > L['ma5']) & (L['close'] > L['ma10']) & (L['pct'] > 0)
def sig_S1(L):
    return (L['ret20'] <= -15) & (L['vol_ratio'] <= 0.8) & (L['close'] > L['ma5']) & (L['close'] > L['ma10']) & (L['pct'] > 0)
def sig_A2(L):
    return (L['prev2_pct'] >= 9.5) & (L['vol_ratio'] <= 0.6) & (L['close'] > L['ma5']) & (L['pct'] >= -2) & (L['pct'] <= 1)

COST = 0.3
def stat(long, mask, d, ym_exclude=None):
    m = mask & (long['depth'] == d) & tradeable(long, 0)
    if ym_exclude: m &= (long['date'].str[:7] != ym_exclude)
    r1 = long['next_ret']
    df = pd.DataFrame({'r1': r1, 'ym': long['date'].str[:7]})[m].dropna(subset=['r1'])
    if len(df) == 0: return None
    net = df['r1'] - COST
    eq = (1 + net/100).cumprod(); peak = eq.cummax(); dd = (eq/peak-1).min()*100
    return {'N': len(df), 'win': round((net>0).mean()*100,1), 'mean': round(df['r1'].mean(),3), 'net': round(net.mean(),3),
            'med': round(df['r1'].median(),3), 'dd': round(dd,2), 'worst': round(df['r1'].min(),3),
            'ym_counts': df.groupby('ym').size().to_dict()}

print('===== 剔除 2024-02 稳健性 =====')
for name, mk in [('M1', sig_M1), ('S1', sig_S1), ('A2', sig_A2)]:
    mask = mk(long)
    for d in ['中熊', '浅熊', '深熊']:
        full = stat(long, mask, d)
        ex = stat(long, mask, d, '2024-02')
        if full and ex:
            print(f"{name} {d}: 全量 N={full['N']} 胜率={full['win']}% net={full['net']} | 剔2024-02 N={ex['N']} 胜率={ex['win']}% net={ex['net']} med={ex['med']} dd={ex['dd']} 最差={ex['worst']} {'PASS' if ex['N']>=30 and ex['win']>=55 and ex['net']>0 else 'FAIL'}")
        elif full:
            print(f"{name} {d}: 全量 N={full['N']} | 剔2024-02 无样本")

print('\n===== 按月胜率 (M1 中熊 / S1 浅熊) =====')
for name, mk, d in [('M1', sig_M1, '中熊'), ('S1', sig_S1, '浅熊')]:
    mask = mk(long) & (long['depth'] == d) & tradeable(long, 0)
    r1 = long['next_ret']
    df = pd.DataFrame({'r1': r1, 'ym': long['date'].str[:7]})[mask].dropna(subset=['r1'])
    print(f'--- {name}@{d} ---')
    for ym, g in df.groupby('ym'):
        net = g['r1'] - COST
        print(f"{ym}: N={len(g):>3} 胜率={round((net>0).mean()*100,1)}% mean={round(g['r1'].mean(),2)} net={round(net.mean(),2)}")
