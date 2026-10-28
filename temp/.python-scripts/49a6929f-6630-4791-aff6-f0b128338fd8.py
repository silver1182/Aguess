import json, pandas as pd, numpy as np

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
with open(base + r'\temp\kline_cache_em.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

rows = []
for code, bars in cache.items():
    for i in range(1, len(bars)-2):
        prev = bars[i-1]; b = bars[i]; nb = bars[i+1]; n2 = bars[i+2]
        if b['date'] < '2026-07-01': continue
        prev_pct = (b['close'] / prev['close'] - 1) * 100   # 昨日涨幅(T-1→T)
        today_pct = (nb['close'] / b['close'] - 1) * 100    # 今日涨幅(T→T+1)
        rows.append({
            'date': b['date'], 'code': code,
            'prev_pct': prev_pct,       # 昨日涨幅
            'today_pct': today_pct,     # 今日(买入日)涨幅
            'close0': b['close'],       # 昨日收盘=买入参考
            'close1': nb['close'],      # 今日收盘
            'open2': n2['open'],        # 后日开盘(卖出)
            'high2': n2['high'],
            'n_close': nb['close'],
        })
df = pd.DataFrame(rows)

# 方案：昨日涨停 → 今日尾盘买入（今日收盘价买入，可成交因为今日不一定是涨停）
# 卖出：后日开盘
df['buy'] = df['close1']  # 今日收盘买入
df['ret2open'] = (df['open2'] / df['buy'] - 1) * 100  # 后日开盘卖

# 昨日涨停池
zt = df[df['prev_pct'] >= 9.8]
print('昨日涨停样本:', len(zt))

def bt(sub, label):
    if len(sub) < 20: return None
    r = sub['ret2open']
    daily = sub.groupby('date')['ret2open'].mean()
    nav = (1 + daily/100).prod() - 1
    return {'规则': label, '样本': len(sub), '均值%': round(r.mean(),2), '胜率%': round((r>0).mean()*100,1),
            '复利%': round(nav*100,1), '正收益日': f"{(daily>0).sum()}/{len(daily)}", '最大单笔%': round(r.min(),1)}

results = []
results.append(bt(zt, '昨日涨停→今日尾盘买→后日开盘卖'))
# 今日走势分组
results.append(bt(zt[zt['today_pct']>=9.8], '昨日涨停→今日继续涨停(买不进,参考)'))
results.append(bt(zt[(zt['today_pct']>=5)&(zt['today_pct']<9.8)], '昨日涨停→今日大涨5-9.8'))
results.append(bt(zt[(zt['today_pct']>=-1)&(zt['today_pct']<5)], '昨日涨停→今日0-5%'))
results.append(bt(zt[(zt['today_pct']>=-5)&(zt['today_pct']<-1)], '昨日涨停→今日回调-1~-5%(低吸)'))
results.append(bt(zt[zt['today_pct']<-5], '昨日涨停→今日大跌<-5%(超跌)'))

res = pd.DataFrame([r for r in results if r])
pd.set_option('display.max_rows', None); pd.set_option('display.width', 250)
print(res.to_string(index=False))