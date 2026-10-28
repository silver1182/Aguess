import json, os
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
# 找缓存与脚本
for root, dirs, files in os.walk(base):
    for f in files:
        if f in ('kline_day_long.json','mkt_state_verify.py') or 'mkt' in f.lower() or 'state' in f.lower():
            print(os.path.join(root, f))
