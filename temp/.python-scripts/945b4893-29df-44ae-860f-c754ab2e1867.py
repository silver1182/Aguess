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

# 竞价买入模拟：次日开盘价买入（ret_open 相对涨停日收盘的涨幅）
# 排除一字板（竞价封死买不进）
# 卖出：次日收盘（收益 = ret_close - ret_open）
df['bid_ret'] = df['ret_close'] - df['ret_open']  # 竞价买入、当日收盘卖
df['hold_next_open'] = df['ret_open']  # 竞价买入成本（相对昨收）

def bt(sub, label):
    if len(sub) < 10: return None
    r = sub['bid_ret']
    daily = sub.groupby('date')['bid_ret'].mean()
    nav = (1 + daily/100).prod() - 1
    return {'模式': label, '样本': len(sub), '竞价买入收益均值%': round(r.mean(),2), '胜率%': round((r>0).mean()*100,1),
            '复利%': round(nav*100,1), '正收益日': f"{(daily>0).sum()}/{len(daily)}", '最大单笔%': round(r.min(),1),
            '平均高开%': round(sub['ret_open'].mean(),2)}

B1 = df['break_times'].between(1,2)
E = df['seal_min']<=120
L2 = df['lb']>=2
Z0 = df['break_times']==0
G5 = df['ret_open']<=5  # 竞价高开不超过5%，防止追太高
G3 = df['ret_open']<=3

results = []
results.append(bt(df[~df['is_yizi'] & Z0 & E & L2], '原规则:炸板0+早盘+连板2(竞价买)'))
results.append(bt(df[~df['is_yizi'] & B1 & E & L2], '炸板1-2+早盘+连板2(竞价买)'))
results.append(bt(df[~df['is_yizi'] & B1 & E & L2 & G5], '炸板1-2+早盘+连板2+高开<=5%(竞价买)'))
results.append(bt(df[~df['is_yizi'] & B1 & E & L2 & G3], '炸板1-2+早盘+连板2+高开<=3%(竞价买)'))
results.append(bt(df[~df['is_yizi'] & B1 & E & L2 & (df['ret_open']<=0)], '炸板1-2+早盘+连板2+平开低开(竞价买)'))

res = pd.DataFrame([r for r in results if r])
pd.set_option('display.max_rows', None); pd.set_option('display.width', 250)
print(res.to_string(index=False))