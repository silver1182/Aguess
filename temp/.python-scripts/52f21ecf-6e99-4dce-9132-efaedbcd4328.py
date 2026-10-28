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
df['ma20_up'] = df['ma20'] > df.groupby('code')['ma20'].shift(5)
df['ma60_up'] = df['ma60'] > df.groupby('code')['ma60'].shift(5)
df['ret10'] = df.groupby('code')['close'].pct_change(10) * 100
df['ret20'] = df.groupby('code')['close'].pct_change(20) * 100
df['hh20'] = df.groupby('code')['close'].transform(lambda x: x.rolling(20).max())

# 次日开盘买入价(下一交易日开盘) / 次日开盘卖出价
g = df.groupby('code')
df['open_nx'] = g['open'].shift(-1)   # t+1开盘（买入价）
df['close_nx'] = g['close'].shift(-1)
# 持有N日：在t+1开盘买入，t+1+N日开盘卖出 -> 收益 = open[t+1+N]/open[t+1] - 1
for h in [3, 5, 10, 20]:
    df[f'buyh{h}'] = (g['open'].shift(-(1+h)) / df['open_nx'] - 1) * 100

# 信号在t收盘确定，只在有次日开盘数据的行上评估
sig = df[(df['date'] >= '2026-07-01') & (df['date'] <= '2026-10-23')].dropna(subset=['buyh5', 'buyh10']).copy()
sig['date'] = sig['date'].dt.date

# 基准：全样本任意买入持有
print('=== 全市场基准(任意日买入) ===')
for h in [3, 5, 10, 20]:
    print(f'持有{h}日: 均值 {sig[f"buyh{h}"].mean():.2f}%  胜率 {(sig[f"buyh{h}"]>0).mean()*100:.1f}%')

def run(name, mask, hlist=[5,10,20], min_trades=50):
    t = sig[mask].dropna(subset=[f'buyh{h}' for h in hlist])
    if len(t) < min_trades:
        print(f'\n=== {name} === 信号数 {len(t)} (不足{min_trades},跳过)')
        return None
    print(f'\n=== {name} === 信号数:{len(t)} 股票:{t["code"].nunique()}')
    for h in hlist:
        m, w = t[f'buyh{h}'].mean(), (t[f'buyh{h}']>0).mean()*100
        bm = sig[f'buyh{h}'].mean()
        print(f'  持有{h}日: 均值 {m:.2f}%  胜率 {w:.1f}%  超额vs基准 {m-bm:+.2f}%')
    return t

# ============ A策略变体 ============
# A1: 站上MA20+MA20向上+回踩MA20(0~-3%,可略破) + 缩量回调(vol<1.2)
run('A1 趋势回踩MA20(站上+向上+回踩+缩量)',
    (sig['close']>sig['ma20']) & sig['ma20_up'] & sig['dist_ma20'].between(-3,1) & (sig['vol_ratio']<1.2))

# A2: 站上MA60+MA60向上+回踩MA20附近 + 缩量
run('A2 长趋势回踩MA20(MA60向上)',
    (sig['close']>sig['ma60']) & sig['ma60_up'] & (sig['close']>sig['ma20']) & sig['dist_ma20'].between(-2,2) & (sig['vol_ratio']<1.2))

# A3: 突破20日新高买入(close突破hh20前值)
run('A3 突破20日新高',
    sig['close'] > sig.groupby('code')['close'].shift(1).transform(lambda x: x.rolling(20).max()))

# A4: 回踩MA20更深(破MA20 1-4%)且MA20向上——真正的"回调低吸"
run('A4 破MA20回调低吸(MA20向上)',
    sig['ma20_up'] & sig['dist_ma20'].between(-4,-1) & (sig['vol_ratio']<1.0))

# ============ C策略变体 ============
# C1: 近期强势(ret10>10%) + 回调到MA10(0~-4%) + 回调缩量
run('C1 强势股回调MA10(10日涨>10%+缩量)',
    (sig['ret10']>10) & sig['dist_ma10'].between(-4,0) & (sig['vol_ratio']<1.0))

# C2: 有涨停基因(近20日单日涨幅>=7%) + 回调到MA10附近
g20 = sig.groupby('code')['pct'].transform(lambda x: x.rolling(20).max())
run('C2 大涨基因回调MA10(近20日有涨7%+)',
    (g20>=7) & sig['dist_ma10'].between(-3,1) & (sig['vol_ratio']<1.2))

# C3: 强势股回踩MA20(10日涨>10% + dist_ma20在-5~0) —— 深度回调
run('C3 强势股深度回调MA20',
    (sig['ret10']>10) & sig['dist_ma20'].between(-5,0) & (sig['vol_ratio']<1.0))

# C4: 涨停后回调(近10日曾涨停) + 回调到MA5/MA10附近
g10 = sig.groupby('code')['pct'].transform(lambda x: x.rolling(10).max())
run('C4 涨停后回调MA5/MA10(近10日涨停+)',
    (g10>=9.5) & ((sig['dist_ma5'].between(-3,1)) | (sig['dist_ma10'].between(-3,1))) & (sig['vol_ratio']<1.2))