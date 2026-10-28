import json, pandas as pd, numpy as np

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
with open(base + r'\temp\kline_cache_em.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

rows = []
for code, bars in cache.items():
    for i in range(1, len(bars)-1):
        prev = bars[i-1]; b = bars[i]; nb = bars[i+1]
        if b['date'] < '2026-07-01': continue
        pct = (b['close'] / prev['close'] - 1) * 100
        rows.append({
            'date': b['date'], 'code': code, 'pct': pct,
            'close': b['close'], 'vol': b['volume'],
            'next_open': nb['open'], 'next_close': nb['close'], 'next_high': nb['high'], 'next_low': nb['low'],
        })
df = pd.DataFrame(rows)

# 全市场基准
df['ro'] = (df['next_open'] / df['close'] - 1) * 100
df['rh'] = (df['next_high'] / df['close'] - 1) * 100
df['rc'] = (df['next_close'] / df['close'] - 1) * 100
print('全市场基准: 开盘卖均值 %.2f%% | 冲高卖均值 %.2f%% | 收盘卖均值 %.2f%%' % (df['ro'].mean(), df['rh'].mean(), df['rc'].mean()))
print('样本量:', len(df))

# 条件单模拟：次日+3%止盈回落卖出 / -3%止损（开盘卖）
def cond_sell(row, tp=3.0, sl=-3.0):
    o, h, l, c = row['next_open'], row['next_high'], row['next_low'], row['next_close']
    base_px = row['close']
    tp_px = base_px * (1 + tp/100)
    sl_px = base_px * (1 + sl/100)
    # 盘中先触达哪个？用高低点近似：若 h>=tp 且 (先触tp或l没到sl) 假设在tp卖
    if h >= tp_px:
        return tp  # 简化：触达止盈
    if l <= sl_px:
        return sl  # 触达止损
    # 都没触达，收盘卖
    return (c / base_px - 1) * 100

df['cond_ret'] = df.apply(cond_sell, axis=1)

def bt(sub, label):
    if len(sub) < 10: return None
    r = sub['cond_ret']
    daily = sub.groupby('date')['cond_ret'].mean()
    nav = (1 + daily/100).prod() - 1
    return {'规则': label, '样本': len(sub), '条件单均值%': round(r.mean(),2), '胜率%': round((r>0).mean()*100,1),
            '复利%': round(nav*100,1), '正收益日': f"{(daily>0).sum()}/{len(daily)}", '最大单笔%': round(r.min(),1)}

s7 = df[(df['pct']>=7) & (df['pct']<9.9)]
s5 = df[(df['pct']>=5) & (df['pct']<7)]
s4 = df[(df['pct']>=4) & (df['pct']<7)]
s_neg = df[(df['pct']>=-2) & (df['pct']<0)]

results = []
results.append(bt(df, '全市场基准'))
results.append(bt(s7, 'T日涨7~9.9%尾盘买'))
results.append(bt(s5, 'T日涨5~7%尾盘买'))
results.append(bt(s4, 'T日涨4~7%尾盘买'))
results.append(bt(s_neg, 'T日跌0~2%尾盘买'))

res = pd.DataFrame([r for r in results if r])
pd.set_option('display.max_rows', None); pd.set_option('display.width', 250)
print(res.to_string(index=False))