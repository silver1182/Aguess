import json
r = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\indicator_report.json'
with open(r, encoding='utf-8') as f:
    rep = json.load(f)
# 摘要信息
for k, v in rep.items():
    print(k, '| 收', v['最新收盘'], '| 5日', v['近5日%'], '| 20日', v['近20日%'], '| RSI', v['RSI14'], '| MACD', v['MACD'], '| KDJ', v['KDJ'], '| MA20上', v['站上MA20'])