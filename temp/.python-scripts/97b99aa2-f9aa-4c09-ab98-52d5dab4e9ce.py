import re
p = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py'
src = open(p, encoding='utf-8').read()
# 提取 em_hot_rank / ths_hot_list / em_hot_concept 函数体
for fn in ['em_hot_rank', 'ths_hot_list', 'em_hot_concept']:
    m = re.search(rf'def {fn}\(.*?(?=\ndef |\Z)', src, re.S)
    if m:
        print('='*20, fn, '='*20)
        print(m.group(0)[:1500])
        print()
