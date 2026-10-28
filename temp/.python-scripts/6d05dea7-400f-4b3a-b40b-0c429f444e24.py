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

for w in [5, 10, 20, 60]:
    df[f'ma{w}'] = df.groupby('code')['close'].transform(lambda x: x.rolling(w).mean())
df['pct'] = df.groupby('code')['close'].pct_change() * 100
df['vol_ma10'] = df.groupby('code')['volume'].transform(lambda x: x.rolling(10).mean())
df['vol_ratio'] = df['volume'] / df['vol_ma10']
df['dist_ma20'] = (df['close'] / df['ma20'] - 1) * 100
df['dist_ma10'] = (df['close'] / df['ma10'] - 1) * 100
df['ma20_up5'] = df['ma20'] > df.groupby('code')['ma20'].shift(5)
df['ret10'] = df.groupby('code')['close'].pct_change(10) * 100

g = df.groupby('code')
df['open_nx'] = g['open'].shift(-1)
for h in [3, 5, 10]:
    df[f'buyh{h}'] = (g['open'].shift(-(1+h)) / df['open_nx'] - 1) * 100

sig = df[(df['date'] >= '2026-07-01') & (df['date'] <= '2026-10-23')].dropna(subset=['buyh5', 'buyh10']).copy()
sig['date'] = sig['date'].dt.date

# ===== 最终对比：A1 / A4 / C2 / C3 (持有10日) =====
g20max = sig.groupby('code')['pct'].transform(lambda x: x.rolling(20).max())
g10max = sig.groupby('code')['pct'].transform(lambda x: x.rolling(10).max())

strategies = {
    'A1 站上MA20回踩缩量(MA20向上5日, 距MA20 -3~1%, 量比<1.2)': (sig['close']>sig['ma20']) & sig['ma20_up5'] & sig['dist_ma20'].between(-3,1) & (sig['vol_ratio']<1.2),
    'A4 破MA20低吸(MA20向上5日, 距MA20 -4~-1%, 量比<1.0)': sig['ma20_up5'] & sig['dist_ma20'].between(-4,-1) & (sig['vol_ratio']<1.0),
    'A合并 距MA20 -4~1%缩量(MA20向上5日, 量比<1.2)': sig['ma20_up5'] & sig['dist_ma20'].between(-4,1) & (sig['vol_ratio']<1.2),
    'C2 大涨基因回调MA10(近20日涨7%+, 距MA10 -3~1%, 量比<1.2)': (g20max>=7) & sig['dist_ma10'].between(-3,1) & (sig['vol_ratio']<1.2),
    'C3 强势深度回调MA20(10日涨>10%, 距MA20 -5~0%, 量比<1.0)': (sig['ret10']>10) & sig['dist_ma20'].between(-5,0) & (sig['vol_ratio']<1.0),
}

summary = []
for name, mask in strategies.items():
    t = sig[mask].dropna(subset=['buyh10'])
    n = len(t)
    m5, w5 = t['buyh5'].mean(), (t['buyh5']>0).mean()*100
    m10, w10 = t['buyh10'].mean(), (t['buyh10']>0).mean()*100
    bm5, bm10 = sig['buyh5'].mean(), sig['buyh10'].mean()
    # 分时段
    sub1 = t[t['date'] <= pd.Timestamp('2026-08-31').date()]
    sub2 = t[t['date'] > pd.Timestamp('2026-08-31').date()]
    bs1 = sig[sig['date'] <= pd.Timestamp('2026-08-31').date()]
    bs2 = sig[sig['date'] > pd.Timestamp('2026-08-31').date()]
    e1 = sub1['buyh10'].mean() - bs1['buyh10'].mean() if len(sub1) >= 20 else float('nan')
    e2 = sub2['buyh10'].mean() - bs2['buyh10'].mean() if len(sub2) >= 20 else float('nan')
    daily = t.groupby('date').size()
    summary.append({
        '策略': name, '信号数': n, '日均': round(daily.mean(),1),
        '5日均值%': round(m5,2), '5日胜率%': round(w5,1), '5日超额%': round(m5-bm5,2),
        '10日均值%': round(m10,2), '10日胜率%': round(w10,1), '10日超额%': round(m10-bm10,2),
        '前段超额10%': round(e1,2), '后段超额10%': round(e2,2),
    })

sdf = pd.DataFrame(summary)
print(sdf.to_string(index=False))
print(f'\n全市场基准: 5日 {sig["buyh5"].mean():+.2f}% / 10日 {sig["buyh10"].mean():+.2f}%')

# ===== 最近交易日(10-23)候选信号预览 =====
last_date = sig['date'].max()
print(f'\n===== {last_date} 收盘满足 A合并 条件的候选 =====')
last = df[(df['date'] == pd.Timestamp(last_date))].copy()
mask_last = last['ma20_up5'] & last['dist_ma20'].between(-4,1) & (last['vol_ratio']<1.2)
cand = last[mask_last][['code','close','dist_ma20','vol_ratio']].sort_values('dist_ma20')
print(f'候选 {len(cand)} 只:')
print(cand.head(40).to_string(index=False))

# 保存
out = base + r'\output\ac_strategy_backtest.csv'
sdf.to_csv(out, index=False, encoding='utf-8-sig')
print(f'\n回测结果已保存: {out}')