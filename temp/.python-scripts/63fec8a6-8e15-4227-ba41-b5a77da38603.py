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

def bt(sub, label):
    if len(sub) < 10: return None
    o = sub['ret_open']; c = sub['ret_close']
    daily = sub.groupby('date')['ret_open'].mean()
    nav = (1 + daily/100).prod() - 1
    return {'规则': label, '样本': len(sub), '开盘卖均值%': round(o.mean(),2), '开盘卖胜率%': round((o>0).mean()*100,1),
            '收盘卖均值%': round(c.mean(),2), '收盘卖胜率%': round((c>0).mean()*100,1),
            '开盘复利%': round(nav*100,1), '正收益日': f"{(daily>0).sum()}/{len(daily)}", '最大单笔%': round(o.min(),1)}

results = []
B = buyable['break_times']==0
E = buyable['seal_min']<=120
# 核心组合细分：连板高度
for lv in [2,3,4]:
    results.append(bt(buyable[B & E & (buyable['lb']==lv)], f'炸板0+早盘+{lv}板'))
results.append(bt(buyable[B & E & (buyable['lb']==2)], '炸板0+早盘+2板(精确)'))
results.append(bt(buyable[B & E & (buyable['lb']>=2) & (buyable['lb']<=3)], '炸板0+早盘+2~3板'))
# 连板2+ 加 RSI 过滤
results.append(bt(buyable[B & E & (buyable['lb']>=2) & (buyable['rsi']<70)], '炸板0+早盘+连板2+RSI<70'))
results.append(bt(buyable[B & E & (buyable['lb']>=2) & (buyable['rsi']<60)], '炸板0+早盘+连板2+RSI<60'))
results.append(bt(buyable[B & E & (buyable['lb']>=2) & (buyable['rsi']>70)], '炸板0+早盘+连板2+RSI>70'))
# 封单率叠加
results.append(bt(buyable[B & E & (buyable['lb']>=2) & (buyable['seal_rate']>=0.7)], '炸板0+早盘+连板2+封单0.7'))
# 早盘更早细分（连板2+）
results.append(bt(buyable[B & (buyable['seal_min']<=60) & (buyable['lb']>=2)], '炸板0+60分+连板2+'))
results.append(bt(buyable[B & (buyable['seal_min']<=90) & (buyable['lb']>=2)], '炸板0+90分+连板2+'))
# 卖出策略对比：连板2+组合收盘卖 vs 开盘卖
sub = buyable[B & E & (buyable['lb']>=2)]
c_daily = sub.groupby('date')['ret_close'].mean()
c_nav = (1+c_daily/100).prod()-1
print('连板2+收盘卖复利:', round(c_nav*100,1), '胜率:', round((sub['ret_close']>0).mean()*100,1))
# 样本数少，检查每日分布
print('每日样本中位数:', sub.groupby('date').size().median())

res = pd.DataFrame([r for r in results if r])
res.to_csv(base + r'\temp\strategy_long_matrix2.csv', index=False)
pd.set_option('display.max_rows', None); pd.set_option('display.width', 250)
print(res.to_string(index=False))