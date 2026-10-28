import pandas as pd, numpy as np

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
df = pd.read_csv(base + r'\temp\backtest_long.csv')
df['lb'] = df['high_days'].apply(lambda s: 1 if s=='首板' else (int(str(s).split('天')[1].replace('板','')) if '天' in str(s) else 1))
def seal_min(s):
    try:
        h, mi, _ = map(int, str(s).split(':'))
        return h*60+mi-570
    except Exception:
        return None
df['seal_min'] = df['first_time'].apply(seal_min)
df['is_yizi'] = df['board_type'].astype(str).str.contains('一字', na=False)
buyable = df[~df['is_yizi']].copy()

best = buyable[(buyable['break_times']==0)&(buyable['seal_min']<=120)&(buyable['lb']>=2)].copy()
best = best.sort_values('date')
best['code'] = best['code'].astype(int).astype(str).str.zfill(6)
best['label'] = best['code'] + ' ' + best['name'] + ' ' + best['reason'].astype(str).str[:12]
out = best[['date','code','name','pct','lb','first_time','seal_rate','ret_open','ret_close','label']]
out.to_csv(base + r'\output\策略信号明细_炸板0早盘连板2.csv', index=False, encoding='utf-8-sig')
print('明细:', len(out), '条')
print(out.head(8).to_string(index=False))
print('...')
print(out.tail(8).to_string(index=False))