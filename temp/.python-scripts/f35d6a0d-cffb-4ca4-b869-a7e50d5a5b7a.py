import json, pandas as pd, numpy as np

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
with open(base + r'\temp\kline_cache_em.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

rows2 = []
for code, bars in cache.items():
    for i in range(1, len(bars)-12):
        prev = bars[i-1]; b = bars[i]
        if b['date'] < '2026-06-20': continue
        prev_pct = (b['close'] / prev['close'] - 1) * 100  # 昨日涨幅
        if prev_pct < 9.8: continue  # 昨日涨停
        today_pct = (bars[i+1]['close'] / b['close'] - 1) * 100  # 今日涨幅
        rec = {'date': b['date'], 'code': code, 'prev_pct': prev_pct, 'today_pct': today_pct, 'close': b['close']}
        for h in [2,3,5,10]:
            if i+h < len(bars):
                rec[f'ret{h}'] = (bars[i+h]['close'] / b['close'] - 1) * 100  # 从涨停日收盘持有h日
        rows2.append(rec)
df2 = pd.DataFrame(rows2)
print('昨日涨停样本:', len(df2))

def bt(sub, label, col='ret3'):
    if sub is None or len(sub) < 20: return None
    r = sub[col].dropna()
    if len(r) < 20: return None
    daily = r.groupby(sub.loc[r.index,'date']).mean()
    nav = (1 + daily/100).prod() - 1
    return {'规则': label, '样本': len(r), '均值%': round(r.mean(),2), '胜率%': round((r>0).mean()*100,1),
            '复利%': round(nav*100,1), '正收益日': f"{(daily>0).sum()}/{len(daily)}", '最大单笔%': round(r.min(),1)}

results = []
for lo, hi, lab in [(0, 5, '昨涨停今日0-5%'), (-5, 0, '昨涨停今日-5~0%')]:
    sub = df2[(df2['today_pct']>=lo) & (df2['today_pct']<hi)]
    for col, hlab in [('ret2','持2日'), ('ret3','持3日'), ('ret5','持5日'), ('ret10','持10日')]:
        r = bt(sub, f'{lab}→{hlab}(含涨停日)', col)
        if r: results.append(r)

res = pd.DataFrame(results)
pd.set_option('display.max_rows', None); pd.set_option('display.width', 250)
print(res.to_string(index=False))