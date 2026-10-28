# -*- coding: utf-8 -*-
"""输出最近N周 v9 选股明细: 代码/名称/评分/买入价/卖出价/周收益"""
import json, pandas as pd, numpy as np, urllib.request

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
with open(base + r'\temp\week_kline_long.json', 'r', encoding='utf-8') as f:
    cache = json.load(f)

all_bars = []
for code, bars in cache.items():
    for b in bars:
        b['code'] = code
        all_bars.append(b)
df = pd.DataFrame(all_bars)
df['date'] = pd.to_datetime(df['date'])
df = df[df['close'].notna()].sort_values(['code','date']).reset_index(drop=True)
g = df.groupby('code')
df['prev_close'] = g['close'].shift(1)
df['prev_vol'] = g['volume'].shift(1)
df['pct'] = df['close']/df['prev_close']-1
df['gap'] = df['open']/df['prev_close']-1
df['tail'] = df['close']/df['open']-1
df['vol_chg'] = df['volume']/df['prev_vol']
df['shrink_up'] = ((df['pct']>0)&(df['vol_chg']<1)).groupby(df['code']).transform(lambda x: x.rolling(10).mean())
df['amount_20d'] = g['volume'].transform(lambda x: x.rolling(20).mean())
df['max_up_20d'] = g['pct'].transform(lambda x: x.rolling(20).max())
df['expand_down'] = ((df['pct']<0)&(df['vol_chg']>1.2)).groupby(df['code']).transform(lambda x: x.rolling(10).mean())
df['tail_return'] = g['tail'].transform(lambda x: x.rolling(20).mean())
df['vol_chg_std'] = g['vol_chg'].transform(lambda x: x.rolling(20).std())
df['overnight_gap'] = g['gap'].transform(lambda x: x.rolling(20).mean())
df['yw'] = df['date'].dt.strftime('%Y-%U')
F = ['shrink_up','amount_20d','max_up_20d','expand_down','tail_return','vol_chg_std','overnight_gap']
sel_df = df[df[F].notna().all(axis=1)].copy()
week_list = df.groupby('yw')['date'].max().sort_values().index.tolist()
yw_to_next = {w: week_list[i+1] for i, w in enumerate(week_list[:-1])}
sel_df['buy_yw'] = sel_df['yw'].map(yw_to_next)
buy_info = df[['code','yw','open','close','low']].rename(columns={'open':'buy_open','close':'sell_close','low':'buy_low'})
sel = sel_df.merge(buy_info.rename(columns={'yw':'buy_yw'}), on=['code','buy_yw'], how='left')
sel = sel[['yw','buy_yw','code','buy_open','sell_close','buy_low']+F].dropna(subset=['buy_open']).copy()
for c in F:
    sel[c] = sel.groupby('yw')[c].transform(lambda s: (s.fillna(s.median()).rank(pct=True)-0.5)*2)
sel['score'] = (+sel['shrink_up']-sel['amount_20d']-sel['max_up_20d']+sel['expand_down']-sel['tail_return']-sel['vol_chg_std']-sel['overnight_gap'])/7
sel['ret0'] = sel['sell_close']/sel['buy_open']-1
sel['week_low_ret'] = sel['buy_low']/sel['buy_open']-1

# 最近12个信号周
recent_weeks = sorted(sel['yw'].unique())[-12:]
picks = sel[sel['yw'].isin(recent_weeks)].sort_values(['yw','score'], ascending=[True,False]).groupby('yw').head(5).reset_index(drop=True)

# 拉名称: 腾讯 qt.gtimg.cn
def fetch_names(codes):
    out = {}
    for i in range(0, len(codes), 60):
        chunk = codes[i:i+60]
        qs = ','.join(('sh' if c.startswith('6') else 'sz') + c for c in chunk)
        url = f'http://qt.gtimg.cn/q={qs}'
        try:
            req = urllib.request.Request(url, headers={'Referer':'http://stock.gtimg.cn/'})
            data = urllib.request.urlopen(req, timeout=10).read().decode('gbk', errors='ignore')
            for line in data.split(';'):
                if '~' not in line: continue
                p = line.split('~')
                if len(p) > 2:
                    out[p[2]] = p[1]
        except Exception as e:
            print('name fetch err', e)
    return out

names = fetch_names(picks['code'].unique().tolist())
picks['name'] = picks['code'].map(names)
picks['ret'] = picks['ret0'] - 0.0025  # 单边成本0.25%近似

# 周标签: 信号周->买入周(下一周)日期
yw_date = dict(zip(df['yw'], df['date'].dt.strftime('%Y-%m-%d')))
picks['sig_end'] = picks['yw'].map(yw_date)

pd.set_option('display.width', 200)
for yw in recent_weeks:
    sub = picks[picks['yw']==yw]
    if len(sub)==0: continue
    print(f"\n=== 信号周 {yw} (截至 {yw_date.get(yw,'')}) ===")
    print(sub[['code','name','score','buy_open','sell_close','week_low_ret','ret']].to_string(index=False))
