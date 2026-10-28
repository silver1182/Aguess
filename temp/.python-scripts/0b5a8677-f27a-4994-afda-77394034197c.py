import json, sys
import pandas as pd, numpy as np, warnings
warnings.filterwarnings('ignore')
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
BASE = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
TEMP = BASE + r'\temp'
sys.path.insert(0, TEMP)
from backtest_signals import build_long, add_mkt_labels, add_sentiment_proxy, tradeable

data = json.load(open(TEMP + r'\kline_day_long.json', encoding='utf-8'))
long = build_long(data)
long, mkt_df = add_mkt_labels(long, data)
long, lu, h, c = add_sentiment_proxy(long)
COST = 0.3

def stat(long, mask, d, ym_exclude=None):
    m = mask & (long['depth'] == d) & tradeable(long, 0)
    if ym_exclude: m &= (long['date'].str[:7] != ym_exclude)
    r1 = long['next_ret']
    df = pd.DataFrame({'r1': r1, 'ym': long['date'].str[:7]})[m].dropna(subset=['r1'])
    if len(df) == 0: return None
    net = df['r1'] - COST
    eq = (1 + net/100).cumprod(); dd = (eq/eq.cummax()-1).min()*100
    return {'N': len(df), 'win': round((net>0).mean()*100,1), 'net': round(net.mean(),3), 'dd': round(dd,2),
            'ym_counts': df.groupby('ym').size().to_dict()}

def sig_B1(L):  # 主脚本 B1: r20<=-15 volr<=0.8 pct>0 (无ma10)
    return (L['ret20'] <= -15) & (L['vol_ratio'] <= 0.8) & (L['pct'] > 0) & (L['close'] > L['ma5'])
def sig_B1c(L):  # 中熊冷淡 r20<=-20 v0.7
    return (L['ret20'] <= -20) & (L['vol_ratio'] <= 0.7) & (L['pct'] > 0) & (L['close'] > L['ma5']) & (L['sent_proxy'] == '冷淡')
def sig_B1h(L):  # 浅熊亢奋 r20<=-15 v0.8
    return (L['ret20'] <= -15) & (L['vol_ratio'] <= 0.8) & (L['pct'] > 0) & (L['close'] > L['ma5']) & (L['sent_proxy'] == '亢奋')

for name, mk in [('B1_浅熊', sig_B1), ('中熊冷淡_r20-20_v0.7', sig_B1c), ('浅熊亢奋_r20-15', sig_B1h)]:
    mask = mk(long)
    for d in (['浅熊'] if '浅熊' in name or '亢奋' in name else ['中熊']):
        full = stat(long, mask, d)
        ex = stat(long, mask, d, '2024-02')
        if full:
            print(f"{name} {d}: 全量 N={full['N']} 胜率={full['win']}% net={full['net']} dd={full['dd']} 月分布={full['ym_counts']}")
            if ex: print(f"   剔2024-02: N={ex['N']} 胜率={ex['win']}% net={ex['net']} dd={ex['dd']} {'PASS' if ex['N']>=30 and ex['win']>=55 and ex['net']>0 else 'FAIL'} 月分布={ex['ym_counts']}")

# A2深熊月份分布确认
mask = (long['prev2_pct'] >= 9.5) & (long['vol_ratio'] <= 0.6) & (long['close'] > long['ma5']) & (long['pct'] >= -2) & (long['pct'] <= 1)
m = mask & (long['depth'] == '深熊') & tradeable(long, 0)
print('\nA2深熊 月份分布:', long.loc[m, 'date'].str[:7].value_counts().to_dict())
