from thsdk import get_price
import time
# 上证 6开头: USHA, 深证: USZA
df = get_price('USZA000002', start_date='2024-01-01', end_date='2024-01-20')
print(type(df), df.shape)
print(df.head(3).to_string())
print(df.columns.tolist())
