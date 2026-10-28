import json, pandas as pd, numpy as np

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
with open(base + r'\temp\kline_cache_em.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

rows = []
for code, bars in cache.items():
    for i in range(1, len(bars)-12):
        prev = bars[i-1]; b = bars[i]
        if b['date'] < '2026-06-20': continue
        pct = (b['close'] / prev['close'] - 1) * 100
        rec = {'date': b['date'], 'code': code, 'pct': pct, 'close': b['close'], 'vol': b['volume'], 'amount': b.get('amount', 0)}
        for h in [3, 5, 10]:
            if i+h < len(bars):
                rec[f'ret{h}'] = (bars[i+h]['close'] / b['close'] - 1) * 100
        rows.append(rec)
df = pd.DataFrame(rows)
print('样本:', len(df))

def bt(sub, label, col='ret3'):
    if len(sub) < 20: return None
    r = sub[col]
    daily = sub.groupby('date')[col].mean()
    nav = (1 + daily/100).prod() - 1
    return {'规则': label, '样本': len(sub), '均值%': round(r.mean(),2), '胜率%': round((r>0).mean()*100,1),
            '复利%': round(nav*100,1), '正收益日': f"{(daily>0).sum()}/{len(daily)}", '最大单笔%': round(r.min(),1)}

results = []
# 全市场基准
results.append(bt(df, '全市场3日', 'ret3'))
results.append(bt(df, '全市场5日', 'ret5'))
results.append(bt(df, '全市场10日', 'ret10'))

# 买入强势股（当日涨幅5~9.8%非涨停）
s = df[(df['pct']>=5) & (df['pct']<9.8)]
results.append(bt(s, '涨5-9.8%买→3日', 'ret3'))
results.append(bt(s, '涨5-9.8%买→5日', 'ret5'))
results.append(bt(s, '涨5-9.8%买→10日', 'ret10'))
# 涨停买不进，看昨日涨停今日0-5%的
yzt = df[df['pct'].between(0,5)]
# 需昨日涨停标记，重建
rows2 = []
for code, bars in cache.items():
    for i in range(1, len(bars)-12):
        prev = bars[i-1]; b = bars[i]
        if b['date'] < '2026-06-20': continue
        prev_pct = (b['close'] / prev['close'] - 1) * 100
        if prev_pct < 9.8: continue  # 昨日涨停
        rec = {'date': b['date'], 'code': code, 'pct': (b['close']/prev['close']-1)*100}
        for h in [3,5,10]:
            if i+h < len(bars):
                rec[f'ret{h}'] = (bars[i+h]['close'] / b['close'] - 1) * 100
        rows2.append(rec)
df2 = pd.DataFrame(rows2)
print('昨日涨停后样本:', len(df2))
results.append(bt(df2[df2['pct'].between(0,5)], '昨涨停今日0-5%→3日', 'ret3'))
results.append(bt(df2[df2['pct'].between(0,5)], '昨涨停今日0-5%→5日', 'ret5'))
results.append(bt(df2[df2['pct'].between(0,5)], '昨涨停今日0-5%→10日', 'ret10'))

res = pd.DataFrame([r for r in results if r])
pd.set_option('display.max_rows', None); pd.set_option('display.width', 250)
print(res.to_string(index=False))