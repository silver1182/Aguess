import pandas as pd, numpy as np
warnings = __import__('warnings'); warnings.filterwarnings('ignore')
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp'
df = pd.read_csv(base+r'\backtest_raw.csv')

# 策略定义（对齐选股逻辑）：
# 涨停封板类：当日涨停主板，排除RSI>75高位连板（原过滤）
# 超跌反转类：涨停 + 近5日跌幅>5%（跌透拉回）或 RSI<40 低位
df['is_zt'] = df['pct']>=9.5
df['is_oversold'] = (df['chg5'] < -5) | (df['rsi'] < 40)
df['is_high'] = df['rsi'] > 75

# 三类：A 全部涨停(无过滤) / B 涨停-过滤高位 / C 超跌反转
grpA = df[df['is_zt']]
grpB = df[df['is_zt'] & ~df['is_high']]
grpC = df[df['is_zt'] & df['is_oversold']]

def stat(g, label):
    n = len(g)
    if n==0: print(f'{label}: 0'); return
    ro = g['ret_open']; rc = g['ret_close']
    print(f"{label}: n={n} | 开盘卖: avg={ro.mean():.2f}% med={ro.median():.2f}% 胜率={(ro>0).mean()*100:.1f}% 最大亏={(ro.min()):.1f}% | 收盘卖: avg={rc.mean():.2f}% 胜率={(rc>0).mean()*100:.1f}%")
stat(grpA,'A 全部涨停')
stat(grpB,'B 涨停-排高位(RSI>75)')
stat(grpC,'C 超跌反转(跌5%/RSI<40)')

# 两者合并 = 实际推荐池
grpD = df[df['is_zt'] & (~df['is_high'] | df['is_oversold'])]
stat(grpD,'D 策略合并(推荐池)')

# 日均推荐数量
print('\n日均推荐数: A=%.1f B=%.1f C=%.1f D=%.1f' % (
    grpA.groupby('date').size().mean(), grpB.groupby('date').size().mean(),
    grpC.groupby('date').size().mean(), grpD.groupby('date').size().mean()))

# 逐日胜率稳定性
print('\n逐日(推荐池D)胜率:')
per = grpD.groupby('date').apply(lambda g: pd.Series({'n':len(g),'avg':g['ret_open'].mean(),'win':(g['ret_open']>0).mean()*100}))
print(per.round(1).to_string())