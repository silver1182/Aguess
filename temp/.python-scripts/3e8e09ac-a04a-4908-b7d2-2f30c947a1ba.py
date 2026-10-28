import sys, requests, json
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
sys.path.insert(0, base + r'\temp')
import a_stock_data as a

# 腾讯实时盘口
for code, name in [('603138','海量数据'), ('603337','杰克科技')]:
    try:
        r = a.tencent_quote(code)
        print(f'--- {code} {name} ---')
        print(r)
    except Exception as e:
        print(code, 'EXC', e)
        break