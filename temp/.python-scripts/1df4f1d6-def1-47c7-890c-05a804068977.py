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
    return {'规则': label, '样本': len(sub), '开盘卖均值%': round(o.mean(),2), '胜率%': round((o>0).mean()*100,1),
            '收盘卖均值%': round(c.mean(),2), '收盘胜率%': round((c>0).mean()*100,1),
            '复利%': round(nav*100,1), '正收益日': f"{(daily>0).sum()}/{len(daily)}", '最大单笔%': round(o.min(),1)}

results = []
# 超跌反转类（用户策略分支）
results.append(bt(buyable[buyable['rsi']<40], '超跌反转:RSI<40'))
results.append(bt(buyable[buyable['chg5']<-5], '超跌反转:近5日跌>5%'))
results.append(bt(buyable[(buyable['rsi']<40)|(buyable['chg5']<-5)], '超跌反转:RSI<40或5日跌5%'))
results.append(bt(buyable[(buyable['rsi']<40)|(buyable['chg5']<-5)] & (buyable['break_times']==0), '超跌反转+炸板0'))
results.append(bt(buyable[(buyable['rsi']<40)|(buyable['chg5']<-5)] & (buyable['break_times']==0) & (buyable['seal_min']<=120), '超跌反转+炸板0+早盘'))
# 涨停追强最终对比
results.append(bt(buyable[(buyable['break_times']==0)&(buyable['seal_min']<=120)&(buyable['lb']>=2)], '追强:炸板0+早盘+连板2+'))
results.append(bt(buyable[(buyable['break_times']==0)&(buyable['seal_min']<=60)&(buyable['lb']>=2)], '追强:炸板0+60分+连板2+'))
results.append(bt(buyable[(buyable['break_times']==0)&(buyable['seal_min']<=120)&(buyable['lb']==2)], '追强:炸板0+早盘+2板'))
# RSI 高位过滤在连板组合上
results.append(bt(buyable[(buyable['break_times']==0)&(buyable['seal_min']<=120)&(buyable['lb']>=2)&(buyable['rsi']<70)], '追强+RSI<70'))
results.append(bt(buyable[(buyable['break_times']==0)&(buyable['seal_min']<=120)&(buyable['lb']>=2)&(buyable['rsi']>70)], '追强+RSI>70'))
# 首板/多板对比
results.append(bt(buyable[(buyable['break_times']==0)&(buyable['seal_min']<=120)&(buyable['lb']==1)], '炸板0+早盘+首板'))
results.append(bt(buyable[(buyable['break_times']==0)&(buyable['seal_min']<=120)&(buyable['lb']>=3)], '炸板0+早盘+3板+'))

res = pd.DataFrame([r for r in results if r])
res.to_csv(base + r'\temp\strategy_long_matrix3.csv', index=False)
pd.set_option('display.max_rows', None); pd.set_option('display.width', 250)
print(res.to_string(index=False))