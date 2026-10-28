import importlib.util, warnings
warnings.filterwarnings('ignore')
spec = importlib.util.spec_from_file_location("a_stock_data", r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\a_stock_data.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

print('===== 7. dragon_tiger_board 个股龙虎榜(歌尔股份) =====')
try:
    r = m.dragon_tiger_board('002241', '2026-10-23')
    if isinstance(r, dict):
        for k, v in r.items():
            if isinstance(v, list): print(f'{k}: {v[:2]}')
            else: print(f'{k}: {v}')
    else:
        print('type:', type(r), 'repr:', repr(r)[:400])
except Exception as e:
    print('ERR:', repr(e)[:200])

print('\n===== 8. ths_hot_reason 同花顺强势股题材归因 =====')
try:
    r = m.ths_hot_reason()
    if isinstance(r, list):
        for x in r[:5]: print(x)
    else:
        print('type:', type(r), 'repr:', repr(r)[:300])
except Exception as e:
    print('ERR:', repr(e)[:200])

print('\n===== 9. cls_telegraph 财联社电报 =====')
try:
    r = m.cls_telegraph()
    if isinstance(r, list):
        for x in r[:3]: print(x)
    else:
        print('type:', type(r), 'repr:', repr(r)[:300])
except Exception as e:
    print('ERR:', repr(e)[:200])