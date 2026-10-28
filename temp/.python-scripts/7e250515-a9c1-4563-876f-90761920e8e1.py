import pandas as pd
p = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\backtest_raw.csv'
df = pd.read_csv(p)
print(df.shape)
print(df.columns.tolist())
print(df.head(3).to_string())
print(df.tail(2).to_string())