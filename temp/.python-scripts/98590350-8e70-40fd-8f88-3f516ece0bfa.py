import pandas as pd
df = pd.read_csv(r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\cand_metrics.csv')
df['代码'] = df['代码'].astype(str).str.zfill(6)
main = df[df['代码'].str.match(r'^(60|00)\d{4}$')].copy()
print('主板候选数:', len(main))
z = main[(main['body_pct']>=0) & (main['chg_today']>=9.5)].sort_values('rsi')
print('\n== 涨停候选(主板) =='); print(z[['代码','名称','close','chg_today','rsi','dist_high20']].to_string())
t = main[(main['price_above_ma20']==1)&(main['ma20_slope']>0)&(main['chg_today']>=0)&(main['chg_today']<9.5)]
print('\n== 趋势候选(主板) =='); print(t[['代码','名称','close','chg_today','rsi','dist_high20']].to_string())
d = main[(main['chg5']<0)&(main['chg_today']>0)&(main['body_pct']>0)]
print('\n== 超跌反弹(主板) =='); print(d[['代码','名称','close','chg_today','chg5','rsi']].to_string())