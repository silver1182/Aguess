import pandas as pd
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
df = pd.read_csv(base + r'\temp\backtest_long.csv')
print('总数:', len(df), '有rsi:', df['rsi'].notna().sum(), '缺:', df['rsi'].isna().sum())
# 看缺 rsi 的日期分布
miss = df[df['rsi'].isna()]
print(miss['date'].value_counts().head(10))
print('最早日期样本:', df['date'].min(), '该日有rsi数:', df[df['date']=='2026-07-01']['rsi'].notna().sum())