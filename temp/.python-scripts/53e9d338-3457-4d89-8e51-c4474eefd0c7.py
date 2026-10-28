from thsdk import api
# 尝试认证（本地已有保存的token）
try:
    r = api.auth()
    print('auth结果:', r)
except Exception as e:
    print('auth err:', str(e)[:200])
import time
time.sleep(1)
try:
    df = api.get_price('USZA000002', start_date='2024-01-02', end_date='2024-01-20')
    print('get_price OK:', type(df), df.shape)
    print(df.head(2).to_string())
    print(df.columns.tolist())
except Exception as e:
    import traceback; traceback.print_exc()
