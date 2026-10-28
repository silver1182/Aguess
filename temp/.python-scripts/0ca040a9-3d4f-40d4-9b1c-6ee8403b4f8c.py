import pandas as pd, numpy as np
warnings = __import__('warnings'); warnings.filterwarnings('ignore')
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp'
df = pd.read_csv(base+r'\backtest_raw.csv')
df['is_zt'] = df['pct']>=9.5
df['is_oversold'] = (df['chg5'] < -5) | (df['rsi'] < 40)
df['is_high'] = df['rsi'] > 75

# 每日推荐池内按"封板强度"模拟首选3只：涨停封板类按 pct 高+封板时间，简化按 pct 排序取前3
grpB = df[df['is_zt'] & ~df['is_high']].copy()
grpC = df[df['is_zt'] & df['is_oversold']].copy()

# 封板类每日取前3（按 pct 降序）
top3 = grpB.sort_values(['date','pct'], ascending=[True,False]).groupby('date').head(3)
def stat(g, label, cost=0.15):
    n=len(g); ro=g['ret_open']-cost
    print(f"{label}: n={n} | 净收益(开盘卖): avg={ro.mean():.2f}% med={ro.median():.2f}% 胜率={(ro>0).mean()*100:.1f}%")
stat(top3,'封板类每日前3')
stat(grpC,'超跌反转全部')

# 实际选股逻辑完整模拟：推荐池=封板(排高位)+超跌，等权每天全买
D = df[df['is_zt'] & (~df['is_high'] | df['is_oversold'])]
ro = D['ret_open']-0.15
print(f"\n完整策略池(22日, 共{len(D)}次信号):")
print(f"  单次平均净收益 {ro.mean():.2f}%, 中位 {ro.median():.2f}%, 胜率 {(ro>0).mean()*100:.1f}%")
# 按日等权组合（每日期望收益），算累计
daily = D.groupby('date').apply(lambda g: (g['ret_open']-0.15).mean())
print(f"  按日等权: 日均净收益 {daily.mean():.2f}%, 正收益天数 {(daily>0).mean()*100:.1f}% ({(daily>0).sum()}/{len(daily)})")
print(f"  按日等权累计(复利): {((1+daily/100).prod()-1)*100:.1f}%")
# 简单年化参考(22日) 
print(f"  22日年化折算约: {((1+daily.mean()/100)**(252/22)-1)*100:.1f}%")

# 超跌反转明细
print('\n超跌反转类明细:')
print(grpC.sort_values('date')[['date','name','pct','chg5','rsi','ret_open']].round(2).to_string(index=False))