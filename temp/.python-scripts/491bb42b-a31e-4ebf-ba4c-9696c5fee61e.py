import importlib.util, warnings
warnings.filterwarnings('ignore')
spec = importlib.util.spec_from_file_location("a_stock_data", r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
for d in ['20261023','20261022','20261021','20261020']:
    try:
        r = m.ths_limit_up_pool(d)
        print(d, '数量:', len(r))
        if r:
            print('  样例:', r[0])
            break
    except Exception as e:
        print(d, 'ERR', type(e).__name__, str(e)[:100])