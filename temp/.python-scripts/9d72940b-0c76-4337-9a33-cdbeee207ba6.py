import importlib.util, sys
spec = importlib.util.spec_from_file_location("a_stock_data", r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py')
m = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(m)
    fns = [n for n in dir(m) if not n.startswith('_') and callable(getattr(m, n))]
    print('模块加载成功，公开函数数:', len(fns))
    print(sorted(fns))
except Exception as e:
    import traceback
    traceback.print_exc()