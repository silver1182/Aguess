import importlib.util, warnings
warnings.filterwarnings('ignore')
spec = importlib.util.spec_from_file_location("a_stock_data", r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

print('===== 3b. industry_comparison 排查 =====')
try:
    r = m.industry_comparison()
    print('type:', type(r), 'len/empty:', len(r) if hasattr(r,'__len__') else 'N/A')
    print('repr:', repr(r)[:300])
except Exception as e:
    import traceback; traceback.print_exc()

print('\n===== 5. board_fund_flow 板块资金流(行业/今日) =====')
try:
    r = m.board_fund_flow('industry', 'today')
    if hasattr(r, 'head'):
        print(r.head(3).to_string())
    elif isinstance(r, list):
        for x in r[:3]: print(x)
    else:
        print('type:', type(r), 'repr:', repr(r)[:300])
except Exception as e:
    print('ERR:', repr(e)[:200])

print('\n===== 6. daily_dragon_tiger 全市场龙虎榜 =====')
try:
    r = m.daily_dragon_tiger('2026-10-23')
    if hasattr(r, 'head'):
        print(r.head(3).to_string())
    elif isinstance(r, list):
        for x in r[:3]: print(x)
    else:
        print('type:', type(r), 'repr:', repr(r)[:300])
except Exception as e:
    print('ERR:', repr(e)[:200])