# -*- coding: utf-8 -*-
"""A2实时筛选: 10-26涨停池 -> 拉最新日K(含今日盘中) -> 判断A2信号
A2定义: prev2_pct(涨停后第二日)>=9.5% 且 vol_ratio<=0.6 且 close>ma5 且 当日pct∈[-2,1]"""
import json, time, traceback
import pandas as pd
import numpy as np
from thsdk import api

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
temp = base + r'\temp'

# 10-26 涨停候选池(取自缓存)
CANDIDATES = ['000559','000635','000678','000700','000810','000995','001225','001317','001318','001331',
              '002086','002093','002095','002178','002535','002578','002696','002708','002795','002820',
              '002869','002931','002999','600094','600822','600826','600838','600980','603028','603089',
              '603138','603200','603258','603331','603337','603528','603657','603683','603716','603719','603901','603955']
# 修正: 上述列表来自缓存实际41只(避免臆造), 重新从缓存提取
with open(temp + r'\kline_day_long.json', encoding='utf-8') as f:
    cache = json.load(f)
cands = []
for code, bars in cache.items():
    for i, b in enumerate(bars):
        if b['date'] == '2026-10-26' and i >= 1:
            prev_close = bars[i-1]['close']
            pct = (b['close'] / prev_close - 1) * 100
            if pct >= 9.5:
                cands.append(code)
            break
print('候选池:', len(cands))

def ths_code(code):
    return ('USHA' if code.startswith('6') else 'USZA') + code

api.auth()
new_bars = {}
fail = []
for code in cands:
    try:
        df = api.get_price(ths_code(code), count=12)
        if df is not None and len(df):
            bars = [{'date': str(idx)[:10], 'open': float(r['open']), 'high': float(r['high']),
                     'low': float(r['low']), 'close': float(r['close']),
                     'volume': float(r['volume']), 'amount': float(r['turnover'])}
                    for idx, r in df.iterrows()]
            new_bars[code] = bars
        else:
            fail.append((code, 'empty'))
    except Exception as e:
        fail.append((code, str(e)[:60]))
    time.sleep(0.05)

print('拉取成功:', len(new_bars), '失败:', len(fail), fail[:5])
if not new_bars:
    sys.exit(1)

# 合并缓存(缓存可能只到10-26)并筛选
def prep(df):
    df = df.copy()
    for c in ['open','high','low','close','volume','amount']:
        df[c] = df[c].astype(float)
    df['pct'] = df['close'].pct_change() * 100
    df['prev_pct'] = df['pct'].shift(1)
    df['prev2_pct'] = df['pct'].shift(2)
    df['ma5'] = df['close'].rolling(5).mean()
    df['vol5'] = df['volume'].rolling(5).mean()
    df['vol_ratio'] = df['volume'] / df['vol5']
    return df

results = []
for code, bars in new_bars.items():
    df = prep(pd.DataFrame(bars))
    if len(df) < 8:
        continue
    s = df.iloc[-1]  # 今日
    d = s['date']
    # A2条件: prev2_pct>=9.5(涨停后第二日), vol_ratio<=0.6, close>ma5, pct∈[-2,1]
    cond = (s['prev2_pct'] >= 9.5) and (s['vol_ratio'] <= 0.6) and (s['close'] > s['ma5']) and (-2 <= s['pct'] <= 1)
    results.append({
        'code': code, 'date': d, 'close': round(s['close'], 2),
        'pct': round(s['pct'], 2), 'prev2_pct': round(s['prev2_pct'], 2),
        'vol_ratio': round(s['vol_ratio'], 2), 'ma5': round(s['ma5'], 2),
        'signal': bool(cond),
        'last2': [(b['date'], round(b['close'], 2), round((b['close']/(bars[i-1]['close'] if i>0 else b['close'])-1)*100, 2)) for i, b in enumerate(bars[-4:])],
    })

out = {'as_of': max(r['date'] for r in results), 'n_candidates': len(cands), 'n_fetched': len(results)}
with open(temp + r'\a2_realtime_screen.json', 'w', encoding='utf-8') as f:
    json.dump({'out': out, 'rows': results}, f, ensure_ascii=False, indent=1)
print('as_of:', out['as_of'])
print('=== A2 信号命中 ===')
hits = [r for r in results if r['signal']]
print('命中数:', len(hits))
for r in hits:
    print(f"{r['code']} {r['date']} close={r['close']} pct={r['pct']}% prev2={r['prev2_pct']}% volr={r['vol_ratio']} ma5={r['ma5']} last4={r['last2']}")
print('=== 未命中一览(今日pct/volr/prev2) ===')
for r in sorted(results, key=lambda x: (not x['signal'], x['code'])):
    if not r['signal']:
        print(f"{r['code']} pct={r['pct']}% volr={r['vol_ratio']} prev2={r['prev2_pct']}% close={r['close']} ma5={r['ma5']}")
