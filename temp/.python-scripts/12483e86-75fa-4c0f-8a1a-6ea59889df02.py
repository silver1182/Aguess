import pandas as pd

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

# 综合可成交策略：炸板1-2次(非一字) + 早盘封板(<=120min) + 连板2+
mask = (~df['is_yizi']) & (df['break_times'].between(1,2)) & (df['seal_min']<=120) & (df['lb']>=2)
sel = df[mask].copy()
print('样本数:', len(sel))
print('最近20个样本:')
cols = ['date','code','name','high_days','board_type','break_times','first_time','seal_min','seal_rate','is_again','ret_open','ret_close']
print(sel[cols].sort_values('date').tail(20).to_string(index=False))