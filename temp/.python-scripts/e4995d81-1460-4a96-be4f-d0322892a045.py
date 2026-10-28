import pandas as pd

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
df = pd.read_csv(base + r'\temp\ztpool_20261026.csv')
print(df.columns.tolist())
print(df[['c','n','p','zdp','fbt','lbt','days','zttj','fund','zbc']].head(10).to_string(index=False))