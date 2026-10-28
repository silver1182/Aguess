import sys
sys.path.insert(0, r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp')
from thsdk import get_price
df = get_price('000002', start_date='2024-01-01', end_date='2024-01-20')
print(type(df), df.shape)
print(df.head(3).to_string())
print(df.columns.tolist())
