import importlib.util, warnings, inspect
warnings.filterwarnings('ignore')
spec = importlib.util.spec_from_file_location("a_stock_data", r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
for f in ['ths_limit_up_pool','index_constituents','limit_up_sentiment','daily_dragon_tiger','st_stock_list']:
    fn = getattr(m, f)
    try:
        print(f, inspect.signature(fn))
        print('   doc:', (fn.__doc__ or '')[:120].replace('\n',' '))
    except Exception as e:
        print(f, 'ERR', e)