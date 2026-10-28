import json
with open(r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\limitup_pools.json','r',encoding='utf-8') as f:
    data = json.load(f)
dates = data['dates']; pools = data['pools']
# 看一个样本的所有字段
for d in dates[:3]:
    for r in pools[d][:5]:
        print(d, r)
    print('---')