from thsdk import THS
import time
with THS() as ths:
    print('ths ok')
    try:
        resp = ths.get_kline('USZA000002', start_date='2024-01-01', end_date='2024-01-20', frequency='daily')
        print(type(resp))
        print(resp)
    except Exception as e:
        import traceback; traceback.print_exc()
