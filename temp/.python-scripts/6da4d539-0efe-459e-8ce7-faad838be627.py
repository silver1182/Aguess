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
df['ma20_up5'] = df['ma20'] > df.groupby('code')['ma20'].shift(5)
df['ma20_up10'] = df['ma20'] > df.groupby('code')['ma20'].shift(10)
df['ma20_up3'] = df['ma20'] > df.groupby('code')['ma20'].shift(3)

g = df.groupby('code')
df['open_nx'] = g['open'].shift(-1)
for h in [3, 5, 7, 10, 15, 20]:
    df[f'buyh{h}'] = (g['open'].shift(-(1+h)) / df['open_nx'] - 1) * 100

sig = df[(df['date'] >= '2026-07-01') & (df['date'] <= '2026-10-23')].dropna(subset=['buyh5', 'buyh10']).copy()
sig['date'] = sig['date'].dt.date

def grid(name, mask, hlist=[5,10]):
    t = sig[mask]
    n = len(t)
    if n < 30:
        print(f'{name}: n={n} 过少')
        return
    outs = []
    for h in hlist:
        m, w = t[f'buyh{h}'].mean(), (t[f'buyh{h}']>0).mean()*100
        bm = sig[f'buyh{h}'].mean()
        outs.append(f'{h}日 {m:+.2f}% 胜{w:.0f}% 超{bm:+.2f}%')
    # 分时段超额
    sub1 = t[t['date'] <= pd.Timestamp('2026-08-31').date()]
    sub2 = t[t['date'] > pd.Timestamp('2026-08-31').date()]
    extra = ''
    if len(sub1) >= 20 and len(sub2) >= 20:
        e1 = sub1['buyh10'].mean() - sig[sig['date'] <= pd.Timestamp('2026-08-31').date()]['buyh10'].mean()
        e2 = sub2['buyh10'].mean() - sig[sig['date'] > pd.Timestamp('2026-08-31').date()]['buyh10'].mean()
        extra = f'  | 前后段超额10日: {e1:+.2f}% / {e2:+.2f}%'
    print(f'{name}: n={n} | ' + ' | '.join(outs) + extra)

print('===== A4 参数网格(MA20向上变体 × 回调深度 × 缩量) =====')
for up_name, up in [('up3', sig['ma20_up3']), ('up5', sig['ma20_up5']), ('up10', sig['ma20_up10'])]:
    for depth in ['(-6,-2)', '(-5,-1)', '(-4,-1)', '(-3,0)']:
        lo, hi = map(int, depth.strip('()').split(','))
        for vr in ['<0.8', '<1.0', '<1.2']:
            vv = {'<0.8': 0.8, '<1.0': 1.0, '<1.2': 1.2}[vr]
            grid(f'A4 {up_name} 深度{depth} 量{vr}',
                 up & sig['dist_ma20'].between(lo, hi) & (sig['vol_ratio'] < vv))

# 每天信号数量（检查是否太多/太少）
print('\n===== 每日信号数(选一个代表性参数: up5, 深度-4~-1, 量<1.0) =====')
sel = sig[sig['ma20_up5'] & sig['dist_ma20'].between(-4,-1) & (sig['vol_ratio']<1.0)]
daily = sel.groupby('date').size()
print(f'每日信号: 均值{daily.mean():.1f} 中位{daily.median():.0f} 最大{daily.max()} 最小{daily.min()} 有信号天数{len(daily)}')

# 按日期分布看看9-10月情况
print('\n按月信号数与10日收益:')
sel['month'] = sel['date'].astype(str).str[:7]
for m, sub in sel.groupby('month'):
    print(f'  {m}: n={len(sub)} 10日均值{sub["buyh10"].mean():+.2f}% 胜率{(sub["buyh10"]>0).mean()*100:.0f}%')