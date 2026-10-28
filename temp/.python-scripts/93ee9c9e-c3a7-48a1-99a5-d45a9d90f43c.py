import json
p = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\kline_day_long.json'
with open(p, encoding='utf-8') as f:
    d = json.load(f)
print(type(d))
if isinstance(d, dict):
    keys = list(d.keys())[:5]
    print('codes:', len(d), '示例:', keys)
    import sys
    sample = d[keys[0]]
    print('sample type:', type(sample))
    if isinstance(sample, list):
        print('len:', len(sample), 'last:', sample[-1])
        print('first:', sample[0])
