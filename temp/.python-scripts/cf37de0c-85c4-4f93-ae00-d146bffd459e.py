import json, time
from thsdk import api
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
with open(base + r'\temp\kline_day_long.json', encoding='utf-8') as f:
    data = json.load(f)
codes = list(data.keys())

api.auth()
def ths_code(code):
    return ('USHA' if code.startswith('6') else 'USZA') + code

# 测前50只, 拉10-27~10-28
t0 = time.time()
ok = 0
for code in codes[:50]:
    try:
        df = api.get_price(ths_code(code), start_date='2026-10-27', end_date='2026-10-28')
        if df is not None and len(df):
            ok += 1
    except Exception as e:
        pass
    time.sleep(0.02)
print(f'50只耗时 {time.time()-t0:.1f}s, 成功{ok}')
