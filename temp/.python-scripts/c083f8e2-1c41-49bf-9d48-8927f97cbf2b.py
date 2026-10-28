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
df['ma60_up5'] = df['ma60'] > df.groupby('code')['ma60'].shift(5)
df['ret10'] = df.groupby('code')['close'].pct_change(10) * 100

g = df.groupby('code')
df['open_nx'] = g['open'].shift(-1)
for h in [3, 5, 7, 10, 15, 20]:
    df[f'buyh{h}'] = (g['open'].shift(-(1+h)) / df['open_nx'] - 1) * 100

sig = df[(df['date'] >= '2026-07-01') & (df['date'] <= '2026-10-23')].dropna(subset=['buyh5', 'buyh10']).copy()
sig['date'] = sig['date'].dt.date
sig['month'] = sig['date'].astype(str).str[:7]

# 1) 全市场基准月度表现（判断市场环境）
print('===== 全市场基准(任意买入)月度 =====')
for m, sub in sig.groupby('month'):
    print(f'  {m}: n={len(sub)} 5日均值{sub["buyh5"].mean():+.2f}% 10日均值{sub["buyh10"].mean():+.2f}% 20日均值{sub["buyh20"].mean():+.2f}%')

# 2) 综合策略候选对比
def run(name, mask, hlist=[5,10,15]):
    t = sig[mask].dropna(subset=[f'buyh{h}' for h in hlist])
    n = len(t)
    if n < 50:
        print(f'\n{name}: n={n} 样本不足'); return
    print(f'\n{name}: n={n}')
    for h in hlist:
        m, w = t[f'buyh{h}'].mean(), (t[f'buyh{h}']>0).mean()*100
        bm = sig[f'buyh{h}'].mean()
        print(f'  持有{h}日: 均值 {m:+.2f}%  胜率 {w:.1f}%  超额vs基准 {m-bm:+.2f}%')
    # 前后段
    sub1, sub2 = t[t['date'] <= pd.Timestamp('2026-08-31').date()], t[t['date'] > pd.Timestamp('2026-08-31').date()]
    b1, b2 = sig[sig['date'] <= pd.Timestamp('2026-08-31').date()], sig[sig['date'] > pd.Timestamp('2026-08-31').date()]
    if len(sub1) >= 20 and len(sub2) >= 20:
        e1 = sub1['buyh10'].mean() - b1['buyh10'].mean()
        e2 = sub2['buyh10'].mean() - b2['buyh10'].mean()
        print(f'  分时段10日超额: 7-8月 {e1:+.2f}% / 9-10月 {e2:+.2f}%')
    return t

# 过滤器
low_price = sig['close'] >= 3
high_price = sig['close'] >= 5
amt = sig['amount']  # 成交额

# A1核心: 站上MA20 + MA20向上 + 回踩 ±3% + 缩量
a1 = (sig['close']>sig['ma20']) & sig['ma20_up5'] & sig['dist_ma20'].between(-3,1) & (sig['vol_ratio']<1.2)
# A4核心: 破MA20 1-4% + MA20向上 + 缩量
a4 = sig['ma20_up5'] & sig['dist_ma20'].between(-4,-1) & (sig['vol_ratio']<1.0)
# A1A4合并: 站上或微破MA20 4%内 + MA20向上 + 缩量
a_comb = sig['ma20_up5'] & sig['dist_ma20'].between(-4,1) & (sig['vol_ratio']<1.2)

# 强势基因过滤(近期曾涨5%+)增强A策略
g10max = sig.groupby('code')['pct'].transform(lambda x: x.rolling(10).max())
a_comb_strong = a_comb & (g10max >= 3)

run('A1 趋势回踩(基准)', a1)
run('A1 + 价>=5元', a1 & high_price)
run('A1 + 价>=5 + 成交额>=1亿', a1 & high_price & (amt >= 1e8))
run('A4 破MA20低吸(基准)', a4)
run('A4 + 价>=5 + 成交额>=1亿', a4 & high_price & (amt >= 1e8))
run('A合并(MA20向上±4%+缩量)', a_comb)
run('A合并 + 强势基因+价>=5+额>=1亿', a_comb_strong & high_price & (amt >= 1e8))
run('A合并 + MA60向上 + 价>=5 + 额>=1亿', a_comb & sig['ma60_up5'] & high_price & (amt >= 1e8))

# 每日信号数统计(最佳组合)
best = a_comb & sig['ma60_up5'] & high_price & (amt >= 1e8)
daily = sig[best].groupby('date').size()
print(f'\n[最佳组合] 每日信号: 均值{daily.mean():.1f} 中位{daily.median():.0f} 最大{daily.max()} 有信号天数{len(daily)}')