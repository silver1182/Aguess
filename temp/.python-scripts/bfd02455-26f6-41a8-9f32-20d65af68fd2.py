import sys
sys.path.insert(0, r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp')
try:
    import thsdk
    print('thsdk版本:', getattr(thsdk, '__version__', 'unknown'))
    from thsdk import get_price, auth
    print('auth:', auth())
    df = get_price('000002', start_date='2024-01-01', end_date='2024-01-20', freq='1d')
    print(type(df))
    print(df.head() if hasattr(df, 'head') else df)
except Exception as e:
    import traceback; traceback.print_exc()
