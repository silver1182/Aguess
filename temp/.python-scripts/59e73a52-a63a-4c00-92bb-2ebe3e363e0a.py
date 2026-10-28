import importlib.util, json
spec = importlib.util.spec_from_file_location('ms', r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\mkt_sentiment.py')
ms = importlib.util.module_from_spec(spec); spec.loader.exec_module(ms)
r = ms.main()
print('\n=== JSON关键字段 ===')
print('score:', r['sentiment_score'], r['sentiment_label'])
print('guba_max_score:', r['guba_max_score'], 'guba_limit_up_cnt:', r['guba_limit_up_cnt'], 'guba_up_cnt:', r['guba_up_cnt'])
