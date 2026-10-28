import json
DATA = r"C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\kline_day_long.json"
with open(DATA, 'r', encoding='utf-8') as f:
    raw = json.load(f)
if isinstance(raw, dict):
    first = next(iter(raw.values()))[0]
else:
    first = raw[0]
print(list(first.keys()))
print(first)