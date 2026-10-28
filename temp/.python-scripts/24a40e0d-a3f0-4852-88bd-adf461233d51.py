import sys, json, pandas as pd
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
sys.path.insert(0, base + r'\temp')
import a_stock_data as a

pool = a.ths_limit_up_pool('20261026')
df = pd.DataFrame(pool)
print('字段:', list(df.columns))
print(df.to_string())