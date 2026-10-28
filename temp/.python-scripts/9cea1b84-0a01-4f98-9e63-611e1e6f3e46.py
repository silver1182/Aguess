from thsdk import api
import json, time
api.auth()
# 上证指数两年日K
df = api.get_price('USHI000001', start_date='2024-01-01', end_date='2026-10-26')
print(len(df))
bars = [{'date': str(idx)[:10], 'close': float(r['close'])} for idx, r in df.iterrows()]
temp = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp'
with open(temp + r'\index_daily.json', 'w', encoding='utf-8') as f:
    json.dump(bars, f, ensure_ascii=False)
print('指数已保存', bars[0], bars[-1])
