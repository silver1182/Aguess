import json, os
import pandas as pd, numpy as np
warnings = __import__('warnings'); warnings.filterwarnings('ignore')

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp'
with open(base+r'\limitup_pools.json','r',encoding='utf-8') as f:
    data = json.load(f)
dates = data['dates']; pools = data['pools']
kdir = base + r'\bk_kline'

# 读取所有K线到dict
kl = {}
for fn in os.listdir(kdir):
    if fn.endswith('.csv'):
        c = fn[:-4]
        df = pd.read_csv(os.path.join(kdir, fn))
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        kl[c] = df.set_index('date')

# 指标计算
def ind(df, idx):
    row = df.loc[idx]
    c = df['close'].astype(float)
    pos = df.index.get_loc(idx)
    if pos < 14: return None
    closes = c.iloc[:pos+1]
    diff = closes.diff()
    up = diff.clip(lower=0).rolling(14).mean().iloc[-1]; dn = (-diff.clip(upper=0)).rolling(14).mean().iloc[-1]
    rsi = 100 - 100/(1+up/dn) if dn>0 else 100
    chg5 = (row['close']/c.iloc[pos-5]-1)*100 if pos>=5 else None
    chg2 = (row['close']/c.iloc[pos-2]-1)*100 if pos>=2 else None
    return {'rsi':rsi, 'chg5':chg5, 'chg2':chg2}

results = []
for i, d in enumerate(dates):
    if i == len(dates)-1: break  # 最后一天无法验证次日
    nxt = dates[i+1]
    for r in pools[d]:
        c = str(r['code'])
        if not (c.startswith(('60','00')) and 'ST' not in r['name']): continue
        if c not in kl or d not in kl[c].index or nxt not in kl[c].index: continue
        m = ind(kl[c], d)
        if m is None: continue
        buy = kl[c].loc[d,'close']
        sell_open = kl[c].loc[nxt,'open']
        sell_close = kl[c].loc[nxt,'close']
        results.append({
            'date': d, 'code': c, 'name': r['name'],
            'pct': r['pct'], 'rsi': m['rsi'], 'chg5': m['chg5'], 'chg2': m['chg2'],
            'ret_open': (sell_open/buy-1)*100, 'ret_close': (sell_close/buy-1)*100,
            'board_type': r.get('board_type',''), 'high_days': r.get('high_days',''),
        })
df = pd.DataFrame(results)
print('总样本(涨停次日收益):', len(df))
df.to_csv(base+r'\backtest_raw.csv', index=False, encoding='utf-8-sig')
print(df.groupby('date').size().head(10).to_string())