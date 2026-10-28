import re
p = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py'
with open(p, encoding='utf-8') as f:
    src = f.read()
# 找tencent_quote / tencent_kline 函数定义
for name in ['tencent_quote', 'tencent_kline', 'em_get', 'cls_telegraph']:
    m = re.search(rf'def {name}\(.*?\n(?:    .*\n)+?    return', src)
    print('='*20, name)
    if m:
        print(m.group(0)[:1200])
