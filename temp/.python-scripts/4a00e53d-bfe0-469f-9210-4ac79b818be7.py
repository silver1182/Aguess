import json
p = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\backtest_signals_v2_result.json'
d = json.load(open(p, encoding='utf-8'))
print('===== M1 结果 =====')
print('res:', d['M1']['res'])
print('dist mid:', {k: v for k, v in d['M1']['dist']['mid'].items() if k != 'by_ym'})
print('M1中熊分月:')
for k, v in d['M1']['dist']['mid'].get('by_ym', {}).items():
    print(' ', k, v)
print('===== S1 结果 =====')
print('res:', d['S1']['res'])
print('dist shallow:', {k: v for k, v in d['S1']['dist']['shallow'].items() if k != 'by_ym'})
print('S1浅熊分月:')
for k, v in d['S1']['dist']['shallow'].get('by_ym', {}).items():
    print(' ', k, v)
