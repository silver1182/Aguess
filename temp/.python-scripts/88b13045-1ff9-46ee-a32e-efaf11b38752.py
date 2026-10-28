import json, sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
r = json.load(open(r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\final_strategy_result.json', encoding='utf-8'))
for s in r['strategies']:
    if s['depth'] in ('中熊', '浅熊') and s['N'] > 0:
        print(f"\n=== {s['tag']} @ {s['depth']} N={s['N']} 股票数={s['dist'].get('n_distinct_stock')} ===")
        print('月份分布:', s['dist'].get('months'))
        print('Top股票:', s['dist'].get('top_stock'))
