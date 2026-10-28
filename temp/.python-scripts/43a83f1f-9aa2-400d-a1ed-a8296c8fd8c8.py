import importlib.util, warnings
warnings.filterwarnings('ignore')
spec = importlib.util.spec_from_file_location("a_stock_data", r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

print('===== 10. baostock_valuation_history 估值历史(茅台) =====')
try:
    r = m.baostock_valuation_history('600519', '2026-10-20', '2026-10-26')
    if hasattr(r, 'tail'):
        print(r.tail(3).to_string())
    else:
        print('type:', type(r), 'repr:', repr(r)[:300])
except Exception as e:
    print('ERR:', repr(e)[:200])

print('\n===== 11. hsgt_realtime 北向资金 =====')
try:
    r = m.hsgt_realtime()
    if isinstance(r, dict):
        for k, v in list(r.items())[:6]: print(f'{k}: {v}')
    else:
        print('type:', type(r), 'repr:', repr(r)[:300])
except Exception as e:
    print('ERR:', repr(e)[:200])

print('\n===== 12. margin_trading 融资融券(茅台) =====')
try:
    r = m.margin_trading('600519')
    if hasattr(r, 'head'):
        print(r.head(3).to_string())
    elif isinstance(r, list):
        for x in r[:2]: print(x)
    else:
        print('type:', type(r), 'repr:', repr(r)[:300])
except Exception as e:
    print('ERR:', repr(e)[:200])

print('\n===== 13. forward_pe/pe_digestion 估值工具 =====')
try:
    print('forward_pe:', m.forward_pe(1335.0, 65.0))
    print('pe_digestion:', m.pe_digestion(30.0, 0.2))
    print('calc_peg:', m.calc_peg(30.0, 0.2))
except Exception as e:
    print('ERR:', repr(e)[:200])