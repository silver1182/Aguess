import sys, time
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
sys.path.insert(0, base + r'\temp')
import a_stock_data as a

# 等待 60s 后测试
time.sleep(60)
try:
    k = a.tencent_kline('600000', period='day', count=5)
    print('恢复, 行数:', 0 if k is None else len(k))
except Exception as e:
    print('仍限流:', str(e)[:100])