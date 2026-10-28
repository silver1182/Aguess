import sys, json
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
sys.path.insert(0, base + r'\temp')
import a_stock_data as a
d = a.baidu_kline_with_ma('000001')
print('keys:', d['keys'])
rows = d['rows']
print('行数:', len(rows))
print('前2行:', rows[:2])
print('后2行:', rows[-2:])