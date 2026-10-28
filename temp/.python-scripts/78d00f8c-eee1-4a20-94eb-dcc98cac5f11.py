import re
p = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py'
src = open(p, encoding='utf-8').read()
m = re.search(r'def cls_telegraph.*?\n(?:    .*\n)+?    return', src)
print(m.group(0))
