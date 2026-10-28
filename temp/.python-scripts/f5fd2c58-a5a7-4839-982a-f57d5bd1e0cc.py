import os
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
for root, dirs, files in os.walk(base):
    for f in files:
        if f.endswith('.py') and any(k in f.lower() for k in ('fetch','ths','batch','update')):
            print(os.path.join(root, f))
