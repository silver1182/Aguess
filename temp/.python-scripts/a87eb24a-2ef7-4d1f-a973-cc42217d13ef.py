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
df['month'] = df['date'].str[:7]
buyable = df[~df['is_yizi']].copy()

def bt(sub, label):
    if len(sub) < 10: return None
    o = sub['ret_open']
    daily = sub.groupby('date')['ret_open'].mean()
    nav = (1 + daily/100).prod() - 1
    return {'规则': label, '样本': len(sub), '开盘卖均值%': round(o.mean(),2), '胜率%': round((o>0).mean()*100,1),
            '复利%': round(nav*100,1), '正收益日': f"{(daily>0).sum()}/{len(daily)}"}

B = buyable['break_times']==0
combo_masks = {
    '炸板0+早盘': B & (buyable['seal_min']<=120),
    '炸板0+60分+连板2+': B & (buyable['seal_min']<=60) & (buyable['lb']>=2),
    '炸板0+早盘+2板': B & (buyable['seal_min']<=120) & (buyable['lb']==2),
}
# 按月验证每个组合
print('=== 按月稳健性验证 ===')
for name, mask in combo_masks.items():
    sub = buyable[mask]
    print(f'\n[{name}] 总样本 {len(sub)}')
    for m in ['2026-07','2026-08','2026-09','2026-10']:
        s = sub[sub['month']==m]
        if len(s) >= 10:
            r = bt(s, m)
            print(f'  {m}: 样本{r["样本"]} 均值{r["开盘卖均值%"]}% 胜率{r["胜率%"]}% 复利{r["复利%"]}% 正日{r["正收益日"]}')
        else:
            print(f'  {m}: 样本不足({len(s)})')