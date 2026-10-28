from thsdk import api
import time
api.auth()
t0 = time.time()
df = api.get_price('USHA600519', start_date='2024-01-01', end_date='2026-10-26')
dt = time.time() - t0
print(f'茅台两年: {len(df)}根, 耗时{dt:.2f}s')
# 测一只小盘
t0 = time.time()
df2 = api.get_price('USZA002656', start_date='2024-01-01', end_date='2026-10-26')
dt2 = time.time() - t0
print(f'002656: {len(df2)}根, 耗时{dt2:.2f}s')
