import re
p = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py'
src = open(p, encoding='utf-8').read()
# 找到cls_telegraph函数完整定义
start = src.find('def cls_telegraph')
end = src.find('\ndef ', start + 10)
print(src[start:end])
