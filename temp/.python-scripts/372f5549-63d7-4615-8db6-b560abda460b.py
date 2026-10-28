import sys, inspect
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
sys.path.insert(0, base + r'\temp')
import a_stock_data as a
# 看 tdx_daily_package 用法摘要
src = inspect.getsource(a.tdx_daily_package)
print(src[:1200])
print('===')
print(inspect.getsource(a.tencent_quote)[:600])