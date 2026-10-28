import re
p = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py'
with open(p, encoding='utf-8') as f:
    src = f.read()
# 列出所有函数定义
funcs = re.findall(r'^def (\w+)\((.*?)\):', src, re.M)
for name, sig in funcs:
    print(f'{name}({sig[:80]})')
print('总函数数:', len(funcs))
