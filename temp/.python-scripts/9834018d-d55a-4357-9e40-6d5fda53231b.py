import pandas as pd
df = pd.read_csv(r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\cand_metrics.csv')
# 尾盘策略：涨停封板(涨幅>=9.5%且body>0)、或站上MA20且资金主线
sel = df[(df['body_pct']>=0) & (df['chg_today']>=9.5)]
sel2 = df[(df['price_above_ma20']==1) & (df['ma20_slope']>0) & (df['chg_today']>=0) & (df['chg_today']<9.5)]
print('涨停候选:', len(sel)); print(sel[['代码','名称','close','chg_today','rsi','dist_high20']].to_string())
print('\n趋势候选:', len(sel2)); print(sel2[['代码','名称','close','chg_today','rsi','dist_high20','ma20_slope']].to_string())