# -*- coding: utf-8 -*-
"""短线特征信号全样本扫描: 2024-01 ~ 2026-10 主板1649只两年日K
对每类特征信号统计次日/3日/5日可成交收益(信号日收盘买入, 持有N日收盘卖)"""
import json, math
import pandas as pd
import numpy as np

temp = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp'
with open(temp + r'\kline_day_long.json', encoding='utf-8') as f:
    data = json.load(f)

COST = 0.0015  # 双边成本: 万2.5*2 + 印花税千1
# 涨跌停限制(主板10%)
LIMIT = 9.8

def prep(df):
    df = df.copy()
    for c in ['open','high','low','close','volume','amount']:
        df[c] = df[c].astype(float)
    df['pct'] = df['close'].pct_change() * 100
    df['prev_pct'] = df['pct'].shift(1)
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma10'] = df['close'].rolling(10).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['vol5'] = df['volume'].rolling(5).mean()
    df['vol20'] = df['volume'].rolling(20).mean()
    df['ret10'] = df['close'].pct_change(10) * 100
    df['ret5'] = df['close'].pct_change(5) * 100
    df['high20'] = df['high'].rolling(20).max().shift(1)
    df['low20'] = df['low'].rolling(20).min().shift(1)
    df['low10'] = df['low'].rolling(10).min().shift(1)
    body = (df['close'] - df['open']).abs()
    rng = (df['high'] - df['low']).replace(0, np.nan)
    df['lower_shadow'] = (df[['open','close']].min(axis=1) - df['low']) / rng
    df['upper_shadow'] = (df['high'] - df[['open','close']].max(axis=1)) / rng
    df['body_ratio'] = body / rng
    # 量比: 当日量/5日均量
    df['vol_ratio'] = df['volume'] / df['vol5']
    df['vol_min20'] = df['volume'].rolling(20).min().shift(1)
    df['prev_vol'] = df['volume'].shift(1)
    df['prev_low'] = df['low'].shift(1)
    df['prev_high'] = df['high'].shift(1)
    df['prev_close'] = df['close'].shift(1)
    df['prev_vol_ratio'] = df['vol_ratio'].shift(1)
    return df

# 特征定义(返回布尔Series)
def feat_breakout(df):
    """放量突破20日新高: 收盘创20日新高(不含今日) + 量比>=1.8 + 涨幅2~7%且未涨停"""
    return (df['close'] > df['high20']) & (df['vol_ratio'] >= 1.8) & (df['pct'] >= 2) & (df['pct'] <= 7) & (df['pct'] < LIMIT)

def feat_pullback_zt(df):
    """涨停次日缩量回踩不破5日线: 昨日涨停 + 今日缩量(量比<=0.8) + 今日跌幅-4~0 + 收盘>ma5"""
    zt = df['prev_pct'] >= LIMIT
    return zt & (df['vol_ratio'] <= 0.8) & (df['pct'] >= -4) & (df['pct'] < 0) & (df['close'] > df['ma5'])

def feat_long_shadow(df):
    """长下影反转: 前3日连跌 + 今日下影>=0.5 + 收阳/平 + 跌幅收窄"""
    down3 = (df['prev_pct'] < 0) & (df['pct'].shift(2) < 0) & (df['pct'].shift(3) < 0)
    return down3 & (df['lower_shadow'] >= 0.5) & (df['close'] >= df['open']) & (df['pct'] > -1)

def feat_vol_expand(df):
    """缩量调整后首日放量阳线: 前5日中至少4日收跌且量能萎缩 + 今日放量(vol_ratio>=1.5)收阳涨1~6%"""
    prev5_down = (df['prev_pct'] < 0).rolling(5).sum().shift(1) >= 4
    prev5_vol_low = df['vol5'].shift(1) < df['vol20'].shift(1)
    return prev5_down & prev5_vol_low & (df['vol_ratio'] >= 1.5) & (df['pct'] >= 1) & (df['pct'] <= 6) & (df['close'] > df['open'])

def feat_ma_squeeze(df):
    """均线粘合突破: MA5/10/20三线间距<=2% + 今日放量(vol_ratio>=1.5)涨>=3%"""
    ma_max = df[['ma5','ma10','ma20']].max(axis=1)
    ma_min = df[['ma5','ma10','ma20']].min(axis=1)
    squeeze = (ma_max - ma_min) / ma_min * 100 <= 2
    return squeeze & (df['vol_ratio'] >= 1.5) & (df['pct'] >= 3) & (df['pct'] < LIMIT)

def feat_pullback_ma10(df):
    """强势股回踩10日线: 前10日累计涨幅>=12% + 今日回踩10日线±2%内 + 收阳"""
    strong = df['ret10'] >= 12
    touch = ((df['low'] <= df['ma10'] * 1.02) & (df['close'] >= df['ma10'] * 0.98))
    return strong & touch & (df['close'] > df['open']) & (df['pct'] > 0)

def feat_ground_vol(df):
    """地量企稳后放量阳: 今日量为20日最低(地量) + 次日放量收阳涨>=2%"""
    # 需要跨日, 这里用信号=地量日, 收益从地量日收盘起算也可
    ground = df['volume'] <= df['vol_min20']
    return ground & (df['pct'] > -1)

def feat_n_shape(df):
    """N字突破: 前日涨>=5% + 昨日缩量小阴/十字 + 今日放量收阳"""
    prev_big = df['prev_pct'].shift(1) >= 5
    prev_shrink = (df['prev_vol_ratio'] <= 0.7) & (df['prev_pct'] >= -3) & (df['prev_pct'] <= 1)
    return prev_big & prev_shrink & (df['vol_ratio'] >= 1.3) & (df['close'] > df['open']) & (df['pct'] >= 1) & (df['pct'] < LIMIT)

def feat_new_high_vol(df):
    """温和放量创新高(启动初期): 收盘创60日新高 + 量比1~2.5 + 涨幅1.5~5%"""
    df['high60'] = df['high'].rolling(60).max().shift(1)
    return (df['close'] > df['high60']) & (df['vol_ratio'] >= 1) & (df['vol_ratio'] <= 2.5) & (df['pct'] >= 1.5) & (df['pct'] <= 5) & (df['pct'] < LIMIT)

FEATS = {
    'F1放量突破20日新高': feat_breakout,
    'F2涨停次日缩量回踩': feat_pullback_zt,
    'F3长下影反转(前3连跌)': feat_long_shadow,
    'F4缩量调整后放量阳': feat_vol_expand,
    'F5均线粘合放量突破': feat_ma_squeeze,
    'F6强势股回踩10日线': feat_pullback_ma10,
    'F7地量企稳': feat_ground_vol,
    'F8 N字突破': feat_n_shape,
    'F9温和放量创60日新高': feat_new_high_vol,
}

def stats_for(sig, df, name):
    """sig为布尔Series, 信号日收盘买入"""
    idx = df.index[sig]
    if len(idx) == 0:
        return None
    rows = []
    for n in (1, 3, 5):
        rets = []
        for i in idx:
            j = i + n
            if j < len(df):
                r = (df['close'].iloc[j] / df['close'].iloc[i] - 1) * 100 - COST * 100
                rets.append(r)
        if rets:
            arr = np.array(rets)
            rows.append({'horizon': f'r{n}', 'n': len(arr), 'mean': arr.mean(), 'med': np.median(arr),
                         'win': (arr > 0).mean() * 100, 'std': arr.std()})
    return name, rows

all_feat_stats = {}
random_ret = []

for code, bars in data.items():
    df = prep(pd.DataFrame(bars))
    if len(df) < 70:
        continue
    df.reset_index(drop=True, inplace=True)
    for name, fn in FEATS.items():
        try:
            sig = fn(df).fillna(False)
        except Exception:
            continue
        st = stats_for(sig, df, name)
        if st:
            if name not in all_feat_stats:
                all_feat_stats[name] = []
            all_feat_stats[name].append(st[1])
    # 随机对照: 每只取20个随机交易日收盘买次日卖
    n = len(df)
    if n > 25:
        rng = np.random.default_rng(42)
        picks = rng.choice(range(n - 1), min(20, n - 1), replace=False)
        for i in picks:
            r = (df['close'].iloc[i+1] / df['close'].iloc[i] - 1) * 100 - COST * 100
            random_ret.append(r)

print('=' * 70)
print(f'全样本特征扫描 | 股票池{len(data)}只 | 2024-01~2026-10 | 信号日收盘买入持有N日')
print('=' * 70)
for name, per_list in all_feat_stats.items():
    # 聚合: 取各股信号次数加权
    agg = {}
    for pl in per_list:
        for row in pl:
            h = row['horizon']
            if h not in agg:
                agg[h] = []
            agg[h].append(row)
    print(f'\n【{name}】')
    for h, rows in agg.items():
        # 合并所有股票该horizon的收益(需要原始arr, 简化用均值再聚: 加权平均)
        n = sum(r['n'] for r in rows)
        w = np.average([r['mean'] for r in rows], weights=[r['n'] for r in rows])
        wr = np.average([r['win'] for r in rows], weights=[r['n'] for r in rows])
        print(f'  {h}: 信号数{n:5d} 加权均值{w:+.2f}% 胜率{wr:.1f}%')

rr = np.array(random_ret)
print(f'\n随机对照(收盘买次日卖): n={len(rr)} 均值{rr.mean():+.2f}% 胜率{(rr>0).mean()*100:.1f}%')
