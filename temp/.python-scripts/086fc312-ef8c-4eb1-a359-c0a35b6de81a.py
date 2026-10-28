
import json, pandas as pd, numpy as np, warnings
warnings.filterwarnings('ignore')

DATA = r"C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\kline_day_long.json"
with open(DATA, 'r', encoding='utf-8') as f:
    data = json.load(f)
COST = 0.0015
LIMIT = 9.5

# ===== 1. 等权指数 (逐股票算pct再等权平均) =====
day_mkt = {}
for code, bars in data.items():
    df = pd.DataFrame(bars)
    df['pct'] = df['close'].astype(float).pct_change() * 100
    for d, p in zip(df['date'], df['pct']):
        day_mkt.setdefault(d, []).append(p)
mkt = {d: float(np.nanmean(v)) for d, v in day_mkt.items()}
mkt_df = pd.DataFrame({'date': list(mkt.keys()), 'mkt': list(mkt.values())}).sort_values('date').reset_index(drop=True)
mkt_df['idx'] = (1 + mkt_df['mkt'] / 100).cumprod() * 100
mkt_df['ma20'] = mkt_df['idx'].rolling(20).mean()
mkt_df['ma60'] = mkt_df['idx'].rolling(60).mean()
mkt_df['dev_ma20'] = (mkt_df['idx'] / mkt_df['ma20'] - 1) * 100
mkt_df['ret5'] = mkt_df['idx'].pct_change(5) * 100
mkt_df['ret20'] = mkt_df['idx'].pct_change(20) * 100
mkt_df['trend'] = mkt_df['ma20'].diff()

def state_of(row):
    if np.isnan(row['ma20']) or np.isnan(row['trend']):
        return '初始'
    if row['idx'] > row['ma20'] and row['trend'] > 0:
        return '牛'
    if row['idx'] < row['ma20'] and row['trend'] < 0:
        return '熊'
    return '震荡'
mkt_df['state'] = mkt_df.apply(state_of, axis=1)

last = mkt_df.iloc[-1]
print("==== 当前市况 ====")
print(f"date={last['date']} idx={last['idx']:.0f} MA20={last['ma20']:.0f} dev_ma20={last['dev_ma20']:+.2f}% state={last['state']} ret5={last['ret5']:+.2f}% ret20={last['ret20']:+.2f}%")

# ===== 2. A2 信号 =====
def prep(df):
    df = df.copy()
    for c in ['open','high','low','close','volume','amount']:
        df[c] = df[c].astype(float)
    df['pct'] = df['close'].pct_change() * 100
    df['vol5'] = df['volume'].rolling(5).mean()
    df['vol_ratio'] = df['volume'] / df['vol5']
    df['ma5'] = df['close'].rolling(5).mean()
    df['prev2_pct'] = df['pct'].shift(2)
    for k in (1, 3, 5):
        df[f'fc{k}'] = df['close'].shift(-k) / df['close'] - 1
    return df

meta = mkt_df.set_index('date')
rows = []
for code, bars in data.items():
    df = prep(pd.DataFrame(bars))
    if len(df) < 70: continue
    df.reset_index(drop=True, inplace=True)
    sig = (df['prev2_pct'] >= LIMIT) & (df['vol_ratio'] <= 0.6) & (df['close'] > df['ma5']) & (df['pct'] >= -2) & (df['pct'] <= 1) & df['fc5'].notna()
    for j in df.index[sig]:
        s = df.iloc[j]
        rows.append({'date': s['date'],
                     'dev_ma20': meta.loc[s['date'], 'dev_ma20'] if s['date'] in meta.index else np.nan,
                     'ret5': meta.loc[s['date'], 'ret5'] if s['date'] in meta.index else np.nan,
                     'ret20': meta.loc[s['date'], 'ret20'] if s['date'] in meta.index else np.nan,
                     'r1': s['fc1']*100 - COST*100, 'r3': s['fc3']*100 - COST*100, 'r5': s['fc5']*100 - COST*100})

sig_df = pd.DataFrame(rows)
print(f"\nA2信号总数: N={len(sig_df)}")

def fmt(g, name):
    if len(g) == 0:
        print(f"{name:<16} 无信号")
        return
    r1, r3, r5 = g['r1'], g['r3'], g['r5']
    print(f"{name:<16} N={len(g):>4}  r1={r1.mean():+.2f}%  胜率={(r1>0).mean()*100:.1f}%  r3={r3.mean():+.2f}%  r5={r5.mean():+.2f}%")

print("\n==== [1] 按偏离MA20深度分档 (当前 dev=-5.2%) ====")
for lo, hi, lab in [(-999, -6, '深熊 dev<-6%'), (-6, -3, '中熊 -6~-3%'), (-3, 0, '浅熊 -3~0%'), (0, 999, '牛/上 dev>0%')]:
    g = sig_df[(sig_df['dev_ma20'] > lo) & (sig_df['dev_ma20'] <= hi)]
    fmt(g, lab)

print("\n==== [2] 按近20日跌幅分档 (当前 ret20=-8.6%) ====")
for lo, hi, lab in [(-999, -8, '20日跌>8%'), (-8, -5, '跌5~8%'), (-5, -3, '跌3~5%'), (-3, 0, '跌0~3%'), (0, 999, '20日上涨')]:
    g = sig_df[(sig_df['ret20'] > lo) & (sig_df['ret20'] <= hi)]
    fmt(g, lab)

print("\n==== [3] 按近5日方向 (当前 ret5=-1.5%) ====")
fmt(sig_df[sig_df['ret5'] > 0], '5日上涨中')
fmt(sig_df[sig_df['ret5'] <= 0], '5日下跌中')
fmt(sig_df[sig_df['ret5'] < -1], '5日跌>1%')
fmt(sig_df[sig_df['ret5'] > 1], '5日涨>1%')

print("\n==== [4] 最接近当前市况组合: 深熊(dev<-3%) + 20日跌>3% ====")
deep = sig_df[(sig_df['dev_ma20'] < -3) & (sig_df['ret20'] < -3)]
fmt(deep, '深熊+20日深跌')
sig_df['yr'] = sig_df['date'].str[:4]
for y in ['2024', '2025', '2026']:
    fmt(deep[deep['yr'] == y], f'{y} 深熊+深跌')

print("\n==== [5] 2026年深熊环境信号明细 ====")
g = deep[deep['yr'] == '2026']
if len(g):
    for _, row in g.iterrows():
        print(f"{row['date']}  dev={row['dev_ma20']:+.2f}%  ret20={row['ret20']:+.2f}%  r1={row['r1']:+.2f}%  r3={row['r3']:+.2f}%  r5={row['r5']:+.2f}%")
else:
    print("无信号")

print("\n==== [6] 深熊+深跌 信号时间分布 ====")
if len(deep):
    print(deep['date'].tolist())
