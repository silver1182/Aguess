import importlib.util, warnings, time
import pandas as pd, numpy as np
warnings.filterwarnings('ignore')
spec = importlib.util.spec_from_file_location("a_stock_data", r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
ths = m.ths_hot_reason()
cands = ths[~ths['名称'].str.contains('ST', na=False)].copy()
extra = pd.DataFrame({'代码':['300031','688111','003006','601857'], '名称':['宝通科技','金山办公','百亚股份','中国石油']})
merged = pd.concat([cands[['代码','名称']], extra]).drop_duplicates('代码').reset_index(drop=True)

def indicators(df):
    c = df['close'].astype(float); v = df['volume'].astype(float)
    df = df.copy()
    for n in (5,10,20,60):
        df[f'ma{n}'] = c.rolling(n).mean()
    # RSI14
    diff = c.diff()
    up = diff.clip(lower=0).rolling(14).mean(); dn = (-diff.clip(upper=0)).rolling(14).mean()
    df['rsi14'] = 100 - 100/(1+up/dn.replace(0,np.nan))
    # MACD
    ema12 = c.ewm(span=12, adjust=False).mean(); ema26 = c.ewm(span=26, adjust=False).mean()
    df['dif'] = ema12-ema26; df['dea'] = df['dif'].ewm(span=9, adjust=False).mean(); df['macd'] = (df['dif']-df['dea'])*2
    # KDJ
    low9 = df['low'].rolling(9).min(); high9 = df['high'].rolling(9).max()
    rsv = (c-low9)/(high9-low9).replace(0,np.nan)*100
    df['k'] = rsv.ewm(com=2, adjust=False).mean(); df['d'] = df['k'].ewm(com=2, adjust=False).mean(); df['j'] = 3*df['k']-2*df['d']
    df['chg5'] = c.pct_change(5)*100; df['chg10'] = c.pct_change(10)*100; df['chg20'] = c.pct_change(20)*100
    df['dist_high20'] = (c/df['high'].rolling(20).max()-1)*100
    df['chg_today'] = c.pct_change()*100
    df['ma20_slope'] = df['ma20'].pct_change(5)*100
    return df

results = []
for i, row in merged.iterrows():
    try:
        k = m.tencent_kline(row['代码'], period='day', count=80)
        if k is None or len(k)<25:
            continue
        d = indicators(k)
        last = d.iloc[-1]; prev = d.iloc[-2]
        results.append({
            '代码': row['代码'], '名称': row['名称'],
            'close': round(last['close'],2),
            'chg_today': round(last['chg_today'],2),
            'chg5': round(last['chg5'],2), 'chg10': round(last['chg10'],2), 'chg20': round(last['chg20'],2),
            'rsi': round(last['rsi14'],1),
            'k': round(last['k'],1), 'd': round(last['d'],1), 'j': round(last['j'],1),
            'kdj_gold': 1 if (last['k']>last['d'] and prev['k']<=prev['d']) else 0,
            'macd_pos': 1 if last['macd']>0 else 0,
            'dif_dea': round(last['dif']-last['dea'],3),
            'ma_bull': 1 if (last['ma5']>last['ma10']>last['ma20']) else 0,
            'price_above_ma20': 1 if last['close']>last['ma20'] else 0,
            'dist_high20': round(last['dist_high20'],1),
            'ma20_slope': round(last['ma20_slope'],2),
            'body_pct': round((last['close']-last['open'])/last['open']*100,2),
            'prev_chg': round(prev['chg_today'],2),
        })
        time.sleep(0.05)
    except Exception as e:
        print('ERR', row['代码'], e)
out = pd.DataFrame(results)
out.to_csv(r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\cand_metrics.csv', index=False, encoding='utf-8-sig')
print('成功拉取:', len(out))
print(out[['代码','名称','close','chg_today','chg5','rsi','kdj_gold','macd_pos','ma_bull','dist_high20','ma20_slope','body_pct','prev_chg']].to_string())