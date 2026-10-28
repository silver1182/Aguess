import importlib.util, warnings, time
warnings.filterwarnings('ignore')
spec = importlib.util.spec_from_file_location("a_stock_data", r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

print('===== 1b. tencent_quote 返回结构 =====')
try:
    q = m.tencent_quote(["600519", "sh000001"])
    print('type:', type(q))
    if hasattr(q, 'columns'):
        print('columns:', list(q.columns))
        print(q.to_string())
    elif isinstance(q, list):
        print('len:', len(q))
        print('first:', q[0] if q else None)
    else:
        print(q)
except Exception as e:
    print('ERR:', repr(e)[:300])

print('\n===== 3. industry_comparison 东财行业涨跌排名 =====')
try:
    r = m.industry_comparison()
    if hasattr(r, 'head'):
        print(r.head(5).to_string())
    elif isinstance(r, list):
        for x in r[:5]: print(x)
except Exception as e:
    print('ERR:', repr(e)[:200])

print('\n===== 4. eastmoney_fund_flow_minute 东财个股资金流(茅台) =====')
try:
    r = m.eastmoney_fund_flow_minute("600519")
    if hasattr(r, 'head'):
        print(r.tail(3).to_string())
    elif isinstance(r, list):
        for x in r[-3:]: print(x)
    else:
        print(str(r)[:300])
except Exception as e:
    print('ERR:', repr(e)[:200])