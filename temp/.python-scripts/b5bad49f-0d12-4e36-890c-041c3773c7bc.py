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
            '收盘卖均值%': round(c.mean(),2), '收盘胜率%': round((c>0).mean()*100,1),
            '复利%': round(nav*100,1), '正收益日': f"{(daily>0).sum()}/{len(daily)}", '最大单笔%': round(o.min(),1)}

B = buyable0['break_times']>=1
E = buyable0['seal_min']<=120
L2 = buyable0['lb']>=2
L1 = buyable0['lb']==1
AG = buyable0['is_again']==1
SR = buyable0['seal_rate']<0.5

results = []
results.append(bt(buyable0, '基准:排除一字(含封死)'))
results.append(bt(buyable0[B], '真实可成交:炸板>=1'))
results.append(bt(buyable0[buyable0['break_times']==1], '炸板1次'))
results.append(bt(buyable0[B & E], '炸板>=1+早盘封板'))
results.append(bt(buyable0[B & E & L2], '炸板>=1+早盘+连板2+'))
results.append(bt(buyable0[B & L2], '炸板>=1+连板2+'))
results.append(bt(buyable0[B & L1], '炸板>=1+首板'))
results.append(bt(buyable0[B & AG], '炸板>=1+回封(有上车点)'))
results.append(bt(buyable0[B & E & L2 & AG], '炸板>=1+早盘+连板2+回封'))
results.append(bt(buyable0[SR], '封单率<0.5(易成交)'))
results.append(bt(buyable0[SR & L2], '封单率<0.5+连板2+'))

res = pd.DataFrame([r for r in results if r])
pd.set_option('display.max_rows', None); pd.set_option('display.width', 250)
print(res.to_string(index=False))
res.to_csv(base + r'\temp\strategy_tradable_matrix.csv', index=False)