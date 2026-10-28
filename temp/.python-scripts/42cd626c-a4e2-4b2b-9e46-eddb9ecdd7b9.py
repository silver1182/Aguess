import json
p = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\backtest_signals_v2_result.json'
d = json.load(open(p, encoding='utf-8'))
sl = d['sentiment_layers']
print('== 情绪分层 通过项(N>=30 & win>=55 & net>0) ==')
for r in sl:
    if r.get('N', 0) >= 30 and r.get('pass'):
        print(f"{r['tag'][:30]:<32} {r['depth']} {r['sent']} N={r['N']:>4} win={r['win_rate']:>5.1f} mean={r['mean_r1']:>6.3f} net={r['mean_r1_net']:>6.3f}")
print('\n== 上一轮两条通过信号在扩展样本中的情绪分层明细 ==')
for r in sl:
    if r['tag'] in ('超跌B1 r20<=-15 volr<=0.8 pct>0', '超跌B2 r20<=-15 volr<=0.8 pct[-2,2]'):
        print(r)
print('\n== 超跌B3/B4 在中熊/浅熊情绪分层 ==')
for r in sl:
    if r['tag'] in ('超跌B3 r20<=-20 volr<=0.7 pct[-2,2]', '超跌B4 r20<=-15 volr<=0.6 pct[-2,2]'):
        print(f"{r['tag'][:30]:<32} {r['depth']} {r['sent']} N={r['N']:>4} win={r['win_rate']:>5.1f} net={r['mean_r1_net']:>6.3f}")
