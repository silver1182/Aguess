import importlib.util, warnings, time, inspect, json
warnings.filterwarnings('ignore')
spec = importlib.util.spec_from_file_location("a_stock_data", r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

# 查看相关函数签名
for fn in ['industry_comparison','eastmoney_fund_flow_minute','board_fund_flow','ths_hot_reason','daily_dragon_tiger']:
    f = getattr(m, fn, None)
    print(fn, inspect.signature(f) if f else 'None')

# 板块资金流(可能不需要参数)
try:
    bf = m.board_fund_flow()
    if isinstance(bf, dict):
        print('\nboard_fund_flow keys:', list(bf.keys()))
        for k,v in bf.items():
            if isinstance(v, (pd.DataFrame, list, dict)):
                print(k, type(v), len(v))
    else:
        print('\nboard_fund_flow type:', type(bf))
        if hasattr(bf,'head'): print(bf.head(5).to_string())
except Exception as e:
    print('board ERR', repr(e)[:150])