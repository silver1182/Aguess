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
buyable0 = df[~df['is_yizi']].copy()

def bt(sub, label):
    if len(sub) < 10: return None
    o = sub['ret_open']; c = sub['ret_close']
    daily = sub.groupby('date')['ret_open'].mean()
    nav = (1 + daily/100).prod() - 1
    return {'规则': label, '样本': len(sub), '开盘卖均值%': round(o.mean(),2), '胜率%': round((o>0).mean()*100,1),
            '复利%': round(nav*100,1), '正收益日': f"{(daily>0).sum()}/{len(daily)}", '最大单笔%': round(o.min(),1)}

B1 = buyable0['break_times']==1
B12 = buyable0['break_times'].between(1,2)
E = buyable0['seal_min']<=120
E60 = buyable0['seal_min']<=60
L2 = buyable0['lb']>=2
SR5 = buyable0['seal_rate']<0.5
SR6 = buyable0['seal_rate']<0.6
AG = buyable0['is_again']==1

results = []
results.append(bt(buyable0[B1], '炸板1次(基准)'))
results.append(bt(buyable0[B1 & E], '炸板1+早盘'))
results.append(bt(buyable0[B1 & E & L2], '炸板1+早盘+连板2+'))
results.append(bt(buyable0[B1 & L2], '炸板1+连板2+'))
results.append(bt(buyable0[B1 & AG], '炸板1+回封'))
results.append(bt(buyable0[B1 & SR5], '炸板1+封单率<0.5'))
results.append(bt(buyable0[B12 & E & L2], '炸板1-2+早盘+连板2+'))
results.append(bt(buyable0[SR5], '封单率<0.5(基准)'))
results.append(bt(buyable0[SR5 & E], '封单率<0.5+早盘'))
results.append(bt(buyable0[SR5 & L2], '封单率<0.5+连板2+'))
results.append(bt(buyable0[SR5 & E & L2], '封单率<0.5+早盘+连板2+'))
results.append(bt(buyable0[SR6], '封单率<0.6'))
results.append(bt(buyable0[SR6 & B1 & L2], '封单率<0.6+炸板1+连板2+'))

res = pd.DataFrame([r for r in results if r])
pd.set_option('display.max_rows', None); pd.set_option('display.width', 250)
print(res.to_string(index=False))
res.to_csv(base + r'\temp\strategy_tradable_matrix2.csv', index=False)