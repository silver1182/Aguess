import importlib.util, time
TEMP = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp'
spec = importlib.util.spec_from_file_location('asd', TEMP + r'\a_stock_data.py')
asd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asd)

# 测试不同 page_size
for ps in (30, 50, 80):
    try:
        rows = asd.cls_telegraph(page_size=ps)
        print(f'page_size={ps} -> {len(rows)} 条')
    except Exception as e:
        print(f'page_size={ps} err: {e}')
    time.sleep(1)
