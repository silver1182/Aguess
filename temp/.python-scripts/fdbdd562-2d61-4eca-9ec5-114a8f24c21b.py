import pandas as pd

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
df = pd.read_csv(base + r'\temp\backtest_long.csv')
print('字段:', df.columns.tolist())
# 检查 seal_amount / seal_rate 的分布
if 'seal_amount' in df.columns:
    print(df['seal_amount'].describe())
if 'seal_rate' in df.columns:
    print(df['seal_rate'].describe())