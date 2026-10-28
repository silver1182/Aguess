import json, pandas as pd, numpy as np

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
with open(base + r'\temp\kline_cache_em.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

rows = []
for code, bars in cache.items():
    for i in range(len(bars)-1):
        b = bars[i]; nb = bars[i+1]
        if b['date'] < '2026-07-01': continue
        rows.append({
            'date': b['date'], 'code': code, 'pct': b['pct'],
            'close': b['close'], 'vol': b['volume'],
            'next_open': nb['open'], 'next_pct': nb['pct'],
            'next_high': nb['high'], 'next_low': nb['low'],
        })
df = pd.DataFrame(rows)
print('总样本:', len(df), '日期范围:', df['date'].min(), '~', df['date'].max())

# 尾盘买入次日卖出：T日涨幅区间 7~9.9（未涨停，收盘可买），T+1开盘卖
df['ret_open_sell'] = (df['next_open'] / df['close'] - 1) * 100
df['ret_high_sell'] = (df['next_high'] / df['close'] - 1) * 100
df['ret_close_sell'] = (df['next_close'] / df['close'] - 1) * 100

def bt(sub, label):
    if len(sub) < 10: return None
    r = sub['ret_open_sell']
    daily = sub.groupby('date')['ret_open_sell'].mean()
    nav = (1 + daily/100).prod() - 1
    return {'规则': label, '样本': len(sub), '开盘卖均值%': round(r.mean(),2), '胜率%': round((r>0).mean()*100,1),
            '冲高卖均值%': round(sub['ret_high_sell'].mean(),2), '复利%': round(nav*100,1),
            '正收益日': f"{(daily>0).sum()}/{len(daily)}", '最大单笔%': round(r.min(),1)}

# 涨幅区间
s7 = df[(df['pct']>=7) & (df['pct']<9.9)]
s5 = df[(df['pct']>=5) & (df['pct']<7)]
s3 = df[(df['pct']>=3) & (df['pct']<5)]
s_neg = df[(df['pct']>=-2) & (df['pct']<0)]
s_0 = df[(df['pct']>=0) & (df['pct']<3)]

results = []
results.append(bt(s7, 'T日涨7~9.9%尾盘买'))
results.append(bt(s7[df.loc[s7.index,'vol']>=300000], '涨7~9.9%且放量(vol>=30万手)'))
results.append(bt(s5, 'T日涨5~7%尾盘买'))
results.append(bt(s3, 'T日涨3~5%尾盘买'))
results.append(bt(s_neg, 'T日跌0~2%尾盘买'))
results.append(bt(s_0, 'T日涨0~3%尾盘买'))

res = pd.DataFrame([r for r in results if r])
pd.set_option('display.max_rows', None); pd.set_option('display.width', 250)
print(res.to_string(index=False))