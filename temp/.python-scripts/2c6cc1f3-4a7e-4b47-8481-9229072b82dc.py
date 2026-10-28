import pandas as pd, numpy as np

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
df = pd.read_csv(base + r'\temp\backtest_enriched.csv')
df['lb'] = df['high_days'].apply(lambda s: 1 if s=='首板' else (int(str(s).split('天')[1].replace('板','')) if '天' in str(s) else 1))
def seal_period(m):
    if pd.isna(m): return '未知'
    return '早盘(11:30前)' if m<=120 else ('午盘(11:30-14:00)' if m<=240 else '尾盘(14:00后)')
df['seal_period'] = df['seal_min'].apply(seal_period)
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
# 炸板0为核心，叠加不同维度
B = buyable['break_times']==0
results.append(bt(buyable[B & (buyable['seal_period']=='早盘(11:30前)')], '炸板0+早盘(核心)'))
# 早盘细分：封板时间更早更优?
for m in [60, 90, 120]:
    results.append(bt(buyable[B & (buyable['seal_min']<=m)], f'炸板0+{m}分钟前封板'))
# 封单率细分叠加
for thr in [0.5,0.6,0.7,0.8,0.9]:
    results.append(bt(buyable[B & (buyable['seal_period']=='早盘(11:30前)') & (buyable['seal_rate']>=thr)], f'炸板0+早盘+封单>={thr}'))
# RSI细分叠加
for hi in [60,65,70,75,None]:
    m = buyable[B & (buyable['seal_period']=='早盘(11:30前)')]
    if hi: m = m[m['rsi']<hi]
    results.append(bt(m, f'炸板0+早盘+RSI<{hi if hi else "无限制"}'))
# 首板/连板细分
results.append(bt(buyable[B & (buyable['seal_period']=='早盘(11:30前)') & (buyable['lb']==1)], '炸板0+早盘+首板'))
results.append(bt(buyable[B & (buyable['seal_period']=='早盘(11:30前)') & (buyable['lb']>=2)], '炸板0+早盘+连板2+'))
# is_again 回封/首次封板
results.append(bt(buyable[B & (buyable['seal_period']=='早盘(11:30前)') & (buyable['is_again']==0)], '炸板0+早盘+首封(非回封)'))
results.append(bt(buyable[B & (buyable['seal_period']=='早盘(11:30前)') & (buyable['is_again']==1)], '炸板0+早盘+回封'))

res = pd.DataFrame([r for r in results if r])
res.to_csv(base + r'\temp\strategy_matrix_3.csv', index=False)
pd.set_option('display.max_rows', None); pd.set_option('display.width', 250)
print(res.to_string(index=False))