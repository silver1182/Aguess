import sys, inspect
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
sys.path.insert(0, base + r'\temp')
import a_stock_data as a
# 找函数列表里包含 kline / daily / bar / quote 的
names = [n for n in dir(a) if any(k in n.lower() for k in ('kline','daily','bar','quote'))]
print([n for n in names if not n.startswith('_')])