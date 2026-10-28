import sys, json
sys.path.insert(0, r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp')
try:
    from thsdk import api
    api.auth()
    def ths_code(code):
        return ('USHA' if code.startswith('6') else 'USZA') + code
    for code in ['600519', '000001', '002438']:
        df = api.get_price(ths_code(code), start_date='2022-01-01', end_date='2023-12-31')
        if df is None:
            print(code, 'None')
        else:
            print(code, 'rows=', len(df), 'first=', str(df.index[0])[:10], 'last=', str(df.index[-1])[:10])
except Exception as e:
    import traceback
    traceback.print_exc()
