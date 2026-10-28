import pandas as pd, numpy as np

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
df = pd.read_csv(base + r'\temp\backtest_enriched.csv')
df['lb'] = df['high_days'].apply(lambda s: 1 if s=='首板' else (int(str(s).split('天')[1].replace('板','')) if '天' in str(s) else 1))
def seal_period(m):
    if pd.isna(m): return '未知'
    return '早盘(11:30前)' if m<=120 else ('午盘(11:30-14:00)' if m<=240 else '尾盘(14:00后)')
df['seal_period'] = df['seal_min'].apply(seal_period)
df['is_yizi'] = df['board_type'].astype(str).str.contains('一字', na=False)

# 可成交池：排除一字板
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
results.append(bt(buyable, '可成交池(排除一字板)'))

# 基础条件两两组合
combos = {
    '炸板0次': buyable['break_times']==0,
    '炸板<=1': buyable['break_times']<=1,
    '早盘封板': buyable['seal_period']=='早盘(11:30前)',
    '封单率>=0.7': buyable['seal_rate']>=0.7,
    '封单率>=0.9': buyable['seal_rate']>=0.9,
    'RSI<60': buyable['rsi']<60,
    'RSI<70': buyable['rsi']<70,
    '连板2+': buyable['lb']>=2,
    '连板2-3': buyable['lb'].isin([2,3]),
    '首板': buyable['lb']==1,
}
for k, m in combos.items():
    results.append(bt(buyable[m], k))

# 组合
results.append(bt(buyable[(buyable['break_times']==0)&(buyable['seal_period']=='早盘(11:30前)')], '炸板0+早盘封板'))
results.append(bt(buyable[(buyable['break_times']==0)&(buyable['rsi']<60)], '炸板0+RSI<60'))
results.append(bt(buyable[(buyable['break_times']==0)&(buyable['seal_rate']>=0.7)], '炸板0+封单>=0.7'))
results.append(bt(buyable[(buyable['break_times']==0)&(buyable['lb']>=2)], '炸板0+连板2+'))
results.append(bt(buyable[(buyable['break_times']==0)&(buyable['seal_period']=='早盘(11:30前)')&(buyable['rsi']<70)], '炸板0+早盘+RSI<70'))
results.append(bt(buyable[(buyable['break_times']==0)&(buyable['rsi']<60)&(buyable['lb']>=2)], '炸板0+RSI<60+连板2+'))
results.append(bt(buyable[(buyable['break_times']==0)&(buyable['seal_rate']>=0.7)&(buyable['rsi']<70)], '炸板0+封单0.7+RSI<70'))
results.append(bt(buyable[(buyable['seal_rate']>=0.9)&(buyable['break_times']==0)], '封单>=0.9+炸板0'))

res = pd.DataFrame([r for r in results if r])
res.to_csv(base + r'\temp\strategy_matrix_2.csv', index=False)
pd.set_option('display.max_rows', None); pd.set_option('display.width', 250)
print(res.to_string(index=False))