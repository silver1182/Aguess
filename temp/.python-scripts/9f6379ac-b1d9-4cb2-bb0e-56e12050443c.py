import importlib.util, warnings, time, json
import pandas as pd, numpy as np
warnings.filterwarnings('ignore')
spec = importlib.util.spec_from_file_location("a_stock_data", r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

xlsx = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\kline_data.xlsx'
xl = pd.ExcelFile(xlsx)

def calc_indicators(df):
    df = df.reset_index(drop=True)
    c = df['close']; v = df['volume']
    for n in (5,10,20,60):
        df[f'ma{n}'] = c.rolling(n).mean()
    # RSI14
    diff = c.diff()
    up = diff.clip(lower=0).rolling(14).mean()
    dn = (-diff.clip(upper=0)).rolling(14).mean()
    df['rsi14'] = 100 - 100/(1+up/dn.replace(0,np.nan))
    # MACD
    ema12 = c.ewm(span=12, adjust=False).mean()
    ema26 = c.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    df['macd'] = (dif-dea)*2; df['dif']=dif; df['dea']=dea
    # KDJ 9,3,3
    ln = df['low'].rolling(9).min(); hn = df['high'].rolling(9).max()
    rsv = (c-ln)/(hn-ln).replace(0,np.nan)*100
    df['k'] = rsv.ewm(alpha=1/3, adjust=False).mean()
    df['d'] = df['k'].ewm(alpha=1/3, adjust=False).mean()
    df['j'] = 3*df['k']-2*df['d']
    # 量能
    df['v_ma5'] = v.rolling(5).mean()
    return df

report = {}
for name in xl.sheet_names:
    df = pd.read_excel(xl, sheet_name=name)
    df = calc_indicators(df)
    tail = df.iloc[-1]
    prev = df.iloc[-2]
    pct_5 = (tail['close']/df['close'].iloc[-6]-1)*100
    pct_20 = (tail['close']/df['close'].iloc[-21]-1)*100
    above_ma20 = tail['close'] > tail['ma20']
    above_ma60 = tail['close'] > tail['ma60']
    ma_bull = tail['ma5'] > tail['ma10'] > tail['ma20']
    macd_bull = tail['dif'] > tail['dea']
    kdj_state = '金叉' if tail['k']>tail['d'] and prev['k']<=prev['d'] else ('死叉' if tail['k']<tail['d'] and prev['k']>=prev['d'] else ('多头' if tail['k']>tail['d'] else '空头'))
    vol_ratio = tail['volume']/tail['v_ma5'] if tail['v_ma5'] and not np.isnan(tail['v_ma5']) else np.nan
    report[name] = {
        '最新收盘': round(tail['close'],3), '近5日%': round(pct_5,2), '近20日%': round(pct_20,2),
        'MA5/10/20': [round(tail['ma5'],2), round(tail['ma10'],2), round(tail['ma20'],2)],
        '站上MA20': bool(above_ma20), '站上MA60': bool(above_ma60), '短均多头': bool(ma_bull),
        'MACD': '多头' if macd_bull else '空头', 'KDJ': kdj_state,
        'RSI14': round(tail['rsi14'],1), '量比(5日均)': round(vol_ratio,2) if not np.isnan(vol_ratio) else None,
        '日期': str(tail['date']),
    }

print(json.dumps(report, ensure_ascii=False, indent=1))

# 补充当日资金流/行业
try:
    ind = m.industry_comparison()
    if ind is not None:
        print('\n=== 行业/板块行情(前10) ===')
        print(ind.head(10).to_string())
except Exception as e:
    print('行业 ERR', repr(e)[:100])
time.sleep(0.5)
try:
    flow = m.eastmoney_fund_flow_minute('2026-10-26')
    if flow is not None:
        print('\n=== 当日大盘资金流(尾盘) ===')
        print(flow.tail(3).to_string())
except Exception as e:
    print('资金流 ERR', repr(e)[:100])

import os
with open(r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\indicator_report.json','w',encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
print('\nsaved indicator_report.json')