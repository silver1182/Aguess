import json, pandas as pd, numpy as np

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
with open(base + r'\temp\kline_cache_em.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

all_bars = []
for code, bars in cache.items():
    for b in bars:
        b['code'] = code
        all_bars.append(b)
df = pd.DataFrame(all_bars)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['code', 'date']).reset_index(drop=True)

for w in [5, 10, 20]:
    df[f'ma{w}'] = df.groupby('code')['close'].transform(lambda x: x.rolling(w).mean())
df['pct'] = df.groupby('code')['close'].pct_change() * 100
df['vol_ma10'] = df.groupby('code')['volume'].transform(lambda x: x.rolling(10).mean())
df['vol_ratio'] = df['volume'] / df['vol_ma10']
df['dist_ma20'] = (df['close'] / df['ma20'] - 1) * 100
df['ma20_up5'] = df['ma20'] > df.groupby('code')['ma20'].shift(5)

g = df.groupby('code')
df['open_nx'] = g['open'].shift(-1)
for h in [5, 10, 15]:
    df[f'buyh{h}'] = (g['open'].shift(-(1+h)) / df['open_nx'] - 1) * 100

sig = df[(df['date'] >= '2026-07-01') & (df['date'] <= '2026-10-23')].dropna(subset=['buyh5', 'buyh10']).copy()
sig['date'] = sig['date'].dt.date

# 最终策略定义：A合并 = MA20向上5日 + 收盘价在MA20下方4%到上方1%之间 + 缩量(量比<1.2)
final_mask = sig['ma20_up5'] & sig['dist_ma20'].between(-4,1) & (sig['vol_ratio'] < 1.2)
t = sig[final_mask].dropna(subset=['buyh10']).copy()
print(f'最终策略信号数: {len(t)}, 涉及股票 {t["code"].nunique()}')

# 分持有期
print('\n持有期对比(最终策略):')
for h in [5, 10, 15]:
    m, w = t[f'buyh{h}'].mean(), (t[f'buyh{h}']>0).mean()*100
    bm = sig[f'buyh{h}'].mean()
    print(f'  持有{h}日: 均值 {m:+.2f}%  胜率 {w:.1f}%  超额 {m-bm:+.2f}%')

# 分时段
print('\n分时段(持有10日):')
for lo, hi, name in [('2026-07-01','2026-08-31','7-8月'), ('2026-09-01','2026-10-23','9-10月')]:
    sub = t[(t['date'] >= pd.Timestamp(lo).date()) & (t['date'] <= pd.Timestamp(hi).date())]
    bs = sig[(sig['date'] >= pd.Timestamp(lo).date()) & (sig['date'] <= pd.Timestamp(hi).date())]
    if len(sub) >= 10:
        print(f'  {name}: n={len(sub)} 均值 {sub["buyh10"].mean():+.2f}% 胜率 {(sub["buyh10"]>0).mean()*100:.0f}% 超额 {sub["buyh10"].mean()-bs["buyh10"].mean():+.2f}%')

# 月度
print('\n月度(持有10日):')
t['month'] = t['date'].astype(str).str[:7]
for m, sub in t.groupby('month'):
    print(f'  {m}: n={len(sub)} 均值 {sub["buyh10"].mean():+.2f}% 胜率 {(sub["buyh10"]>0).mean()*100:.0f}%')

# 最近3个交易日的信号（当前可关注）
print('\n===== 最近3个交易日候选信号(当前实盘可参考) =====')
recent_dates = sorted(t['date'].unique())[-3:]
recent = t[t['date'].isin(recent_dates)][['date','code','close','dist_ma20','vol_ratio','buyh10']]
for d in recent_dates:
    sub = recent[recent['date'] == d]
    print(f'\n{d} 信号{len(sub)}只:')
    print(sub.to_string(index=False))

# 检查缓存是否有名称字段
print('\n缓存字段示例:', list(cache[list(cache.keys())[0]][0].keys()))