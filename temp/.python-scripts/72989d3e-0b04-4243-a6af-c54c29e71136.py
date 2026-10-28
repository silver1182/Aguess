import pandas as pd, numpy as np

base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
df = pd.read_csv(base + r'\temp\backtest_enriched.csv')

# 解析连板数：'首板'=1, '2天2板'=2, '6天4板'=4, '3天2板'=2(实际高度2)
def parse_days(s):
    if s == '首板': return 1
    try:
        # 形式如 "3天2板" -> 2板
        return int(s.split('天')[1].replace('板',''))
    except Exception:
        return 1
df['lb'] = df['high_days'].apply(parse_days)

# 封板时间分类
def seal_period(m):
    if m is None: return '未知'
    if m <= 120: return '早盘(11:30前)'
    if m <= 240: return '午盘(11:30-14:00)'
    return '尾盘(14:00后)'
df['seal_period'] = df['seal_min'].apply(seal_period)

# 一字板标记
df['is_yizi'] = df['board_type'].astype(str).str.contains('一字', na=False)
print('一字板数量:', df['is_yizi'].sum(), '/', len(df))

# 统一回测：过滤子集 -> 统计
def bt(sub, label):
    if len(sub) < 10:
        return None
    o = sub['ret_open']; c = sub['ret_close']
    # 日等权复利（按日分组）
    daily = sub.groupby('date')['ret_open'].mean()
    nav = (1 + daily/100).prod() - 1
    pos_days = (daily > 0).sum()
    return {
        '规则': label, '样本': len(sub),
        '开盘卖均值%': round(o.mean(),2), '开盘卖胜率%': round((o>0).mean()*100,1),
        '收盘卖均值%': round(c.mean(),2), '收盘卖胜率%': round((c>0).mean()*100,1),
        '开盘复利%': round(nav*100,1), '正收益日': f"{pos_days}/{len(daily)}",
        '最大单笔%': round(o.min(),1),
    }

results = []
# 基准
results.append(bt(df, '基准:全部涨停'))
results.append(bt(df[~df['is_yizi']], '排除一字板'))

# 连板高度
for k, v in [(1,'首板'), (2,'2板及以上'), (3,'3板及以上'), (2,'2板'), (3,'3板'), (4,'4板及以上')]:
    results.append(bt(df[df['lb']==k], f'连板高度={v}'))

# 封板类型
for t in ['换手板','一字板','回封板']:
    results.append(bt(df[df['board_type']==t], f'封板类型={t}'))

# 封单率
for thr in [0.5, 0.7, 0.8, 0.9]:
    results.append(bt(df[df['seal_rate']>=thr], f'封单率>={thr}'))

# 炸板次数
for n in [0, 1, 2]:
    results.append(bt(df[df['break_times']<=n], f'炸板次数<={n}'))

# 封板时间
for p in ['早盘(11:30前)','午盘(11:30-14:00)','尾盘(14:00后)']:
    results.append(bt(df[df['seal_period']==p], f'封板时间:{p}'))

# RSI
for lo, hi, lab in [(60, None,'RSI>60'), (70, None,'RSI>70'), (None, 75,'RSI<75'), (None, 70,'RSI<70'), (None, 60,'RSI<60'), (30, 75,'RSI 30-75'), (40, 80,'RSI 40-80')]:
    m = (df['rsi']>lo) if lo else pd.Series(True, index=df.index)
    if hi: m &= (df['rsi']<hi)
    results.append(bt(df[m], lab))

# 超跌反转类
results.append(bt(df[(df['rsi']<40)|(df['chg5']<-5)], '超跌反转(RSI<40或近5日跌>5%)'))
results.append(bt(df[(df['rsi']<40)&(df['chg5']<-5)], '超跌反转(双条件)'))
results.append(bt(df[df['chg2']<0], '近2日跌(短期回调)'))

res = pd.DataFrame([r for r in results if r])
res.to_csv(base + r'\temp\strategy_matrix_1.csv', index=False)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 250)
print(res.to_string(index=False))