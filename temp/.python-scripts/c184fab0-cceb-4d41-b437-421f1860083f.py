import re
p = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py'
with open(p, encoding='utf-8') as f:
    src = f.read()
funcs = re.findall(r'^def (\w+)\(', src, re.M)
print('函数总数:', len(funcs))
print(funcs[:80])
# 找文档说明
doc = re.search(r'"""\n(.*?)"""', src, re.S)
if doc:
    print('---文档开头---')
    print(doc.group(1)[:800])
