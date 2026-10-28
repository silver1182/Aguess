import sys, json
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
sys.path.insert(0, base + r'\temp')
import a_stock_data as a

# 拉今日涨停池
try:
    pool = a.ths_limit_up_pool('20261026')
    print('今日涨停池:', len(pool) if pool is not None else None)
    if pool is not None:
        print(pool.head(5).to_string())
except Exception as e:
    print('EXC', e)