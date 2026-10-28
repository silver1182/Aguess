import json, pandas as pd, numpy as np

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
with open(base + r'\temp\kline_cache_em.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

# 构造每只股票的日K索引
records = {}
for code, bars in cache.items():
    for i in range(len(bars)):
        records[(code, bars[i]['date'])] = (i, bars)

# 涨停池样本：回测涨停日的次日可执行性
zt = pd.read_csv(base + r'\temp\backtest_long.csv')
zt['is_yizi'] = zt['board_type'].astype(str).str.contains('一字', na=False)
zt = zt[~zt['is_yizi']].copy()

rows = []
for _, row in zt.iterrows():
    code = str(row['code']).zfill(6)
    d = row['date']
    key = (code, d)
    if key not in records: continue
    i, bars = records[key]
    if i+2 >= len(bars): continue  # 需要 T+2
    b1 = bars[i+1]; b2 = bars[i+2]  # 次日、再次日
    rows.append({
        'date': d, 'code': code, 'name': row['name'],
        'lb': row['high_days'], 'break_times': row['break_times'],
        'open1': b1['open'], 'high1': b1['high'], 'low1': b1['low'], 'close1': b1['close'],
        'open2': b2['open'], 'close0': row['close_t'] if pd.notna(row['close_t']) else bars[i]['close'],
    })
df = pd.DataFrame(rows)
print('可模拟样本:', len(df))

# 模式1：次日竞价买入（开盘价），次日冲高+3%止盈/-3%止损（条件单）
def cond(row, tp=3.0, sl=-3.0):
    buy = row['open1']  # 竞价买入价=次日开盘
    h, l, c1 = row['high1'], row['low1'], row['close1']
    tp_px = buy * (1 + tp/100); sl_px = buy * (1 + sl/100)
    if h >= tp_px and l <= sl_px:  # 都触达，先触达谁不好说，保守按先止损
        return sl
    if h >= tp_px: return tp
    if l <= sl_px: return sl
    return (c1 / buy - 1) * 100

# 模式2：次日竞价买入，持有到再次日开盘卖
df['mode1'] = df.apply(lambda r: cond(r), axis=1)
df['mode2'] = (df['open2'] / df['open1'] - 1) * 100

def bt(sub, label, col='mode1'):
    if len(sub) < 10: return None
    r = sub[col]
    daily = sub.groupby('date')[col].mean()
    nav = (1 + daily/100).prod() - 1
    return {'模式': label, '样本': len(sub), '均值%': round(r.mean(),2), '胜率%': round((r>0).mean()*100,1),
            '复利%': round(nav*100,1), '正收益日': f"{(daily>0).sum()}/{len(daily)}", '最大单笔%': round(r.min(),1)}

results = []
# 过滤高开幅度：竞价买入只买高开<=X%的（太高不追）
df['gap'] = (df['open1'] / df['close0'] - 1) * 100
results.append(bt(df, '次日竞价买+当日条件单(全部)'))
results.append(bt(df[df['gap']<=5], '竞价买高开<=5%+条件单'))
results.append(bt(df[df['gap']<=3], '竞价买高开<=3%+条件单'))
results.append(bt(df[df['gap']<=0], '竞价买平开低开+条件单'))
results.append(bt(df[df['gap'].between(0,5)], '竞价买高开0~5%+条件单'))
results.append(bt(df[df['gap'].between(0,5)], '竞价买高开0~5%+持有2日', 'mode2'))
results.append(bt(df[df['gap']<=3], '竞价买高开<=3%+持有2日', 'mode2'))
results.append(bt(df, '竞价买全部+持有2日', 'mode2'))

res = pd.DataFrame([r for r in results if r])
pd.set_option('display.max_rows', None); pd.set_option('display.width', 250)
print(res.to_string(index=False))