import json, sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
r = json.load(open(r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\backtest_signals_result.json', encoding='utf-8'))
print('情绪分层 (中熊/浅熊 × 亢奋/冷淡):')
for s in r['sentiment_layers']:
    if s['N'] > 0:
        print(f"{s['tag']:<30} {s['depth']} {s['sent']} N={s['N']:>4} 胜率={s['win_rate']:>5.1f}% mean={s['mean_r1']:>6.3f} net={s['mean_r1_net']:>6.3f} med={s['median_r1']:>6.3f} 最差={s['worst_day']:>6.3f} {'PASS' if s.get('pass') else ''}")
