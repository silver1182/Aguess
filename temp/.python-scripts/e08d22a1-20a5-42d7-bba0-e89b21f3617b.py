import json, pandas as pd, numpy as np

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
with open(base + r'\temp\kline_cache_em.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

# 昨日涨停 → 今日0~5% → 尾盘买 → 持2日
rows = []
for code, bars in cache.items():
    for i in range(1, len(bars)-6):
        p0 = bars[i-1]; b0 = bars[i]; b1 = bars[i+1]; b2 = bars[i+2]
        if b0['date'] < '2026-07-01': continue
        prev_pct = (b0['close'] / p0['close'] - 1) * 100
        if prev_pct < 9.8: continue  # 昨日(b0日)涨停
        today_pct = (b1['close'] / b0['close'] - 1) * 100  # 今日涨幅
        if not (0 <= today_pct < 5): continue
        ret2 = (b2['close'] / b1['close'] - 1) * 100  # 今日收盘买→后日收盘卖
        ret1 = (b2['open'] / b1['close'] - 1) * 100   # 后日开盘卖
        rows.append({
            'date': b1['date'], 'code': code, 'today_pct': today_pct,
            'vol1': b1['volume'], 'vol0': b0['volume'],
            'ret2': ret2, 'ret1': ret1,
            'gap2': (b2['open'] / b1['close'] - 1) * 100,
        })
df = pd.DataFrame(rows)
print('总样本:', len(df))

def bt(sub, label, col='ret2'):
    if len(sub) < 20: return None
    r = sub[col]
    daily = r.groupby(sub['date']).mean()
    nav = (1 + daily/100).prod() - 1
    return {'规则': label, '样本': len(sub), '均值%': round(r.mean(),2), '胜率%': round((r>0).mean()*100,1),
            '复利%': round(nav*100,1), '正收益日': f"{(daily>0).sum()}/{len(daily)}", '最大单笔%': round(r.min(),1)}

results = []
results.append(bt(df, '昨涨停今0-5%→持2日收盘卖'))
results.append(bt(df, '昨涨停今0-5%→后日开盘卖', 'ret1'))
# 今日涨幅细分
for lo, hi in [(0,1),(1,3),(3,5)]:
    results.append(bt(df[(df['today_pct']>=lo)&(df['today_pct']<hi)], f'今日涨{lo}-{hi}%'))
# 成交量过滤：今日量>昨日量
df['volup'] = df['vol1'] > df['vol0']
results.append(bt(df[df['volup']], '今日放量'))
results.append(bt(df[~df['volup']], '今日缩量'))
# 近期涨停次数(连板/首板近似)：b0 前一日是否也涨停
rows2 = []
for code, bars in cache.items():
    for i in range(1, len(bars)-6):
        p0 = bars[i-1]; b0 = bars[i]; b1 = bars[i+1]; b2 = bars[i+2]
        if b0['date'] < '2026-07-01': continue
        prev_pct = (b0['close'] / p0['close'] - 1) * 100
        if prev_pct < 9.8: continue
        today_pct = (b1['close'] / b0['close'] - 1) * 100
        if not (0 <= today_pct < 5): continue
        two_prev = (p0['close'] / bars[i-2]['close'] - 1) * 100 if i >= 2 else 0
        rows2.append({
            'date': b1['date'], 'code': code, 'prev2_zt': two_prev >= 9.8,
            'ret2': (b2['close'] / b1['close'] - 1) * 100,
        })
df2 = pd.DataFrame(rows2)
results.append(bt(df2[~df2['prev2_zt']], '昨日是首板'))
results.append(bt(df2[df2['prev2_zt']], '昨日是连板'))

res = pd.DataFrame([r for r in results if r])
pd.set_option('display.max_rows', None); pd.set_option('display.width', 250)
print(res.to_string(index=False))