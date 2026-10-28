import sys, pandas as pd
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
sys.path.insert(0, base + r'\temp')
import a_stock_data as a

pool = a.ths_limit_up_pool('20261026')
df = pd.DataFrame(pool)

# 解析连板高度
def parse_lb(s):
    s = str(s)
    if s == '首板': return 1
    # 如 '2天2板' -> 2, '12天8板' -> 8, '4天2板' -> 2
    import re
    m = re.search(r'(\d+)板$', s)
    return int(m.group(1)) if m else 1
df['lb'] = df['high_days'].apply(parse_lb)

# 封板时间分钟(从09:30起)
def seal_min(s):
    try:
        h, mi, _ = map(int, str(s).split(':'))
        return h*60+mi-570
    except Exception:
        return None
df['seal_min'] = df['first_time'].apply(seal_min)

m1 = df['code'].astype(str).str.startswith(('60','00'))           # 主板
m2 = ~df['board_type'].astype(str).str.contains('一字', na=False)  # 非一字
m3 = df['break_times'] == 0                                       # 炸板0
m4 = df['seal_min'] <= 120                                        # 早盘封板(11:30前)
m5 = df['lb'] >= 2                                                # 连板2+

print('=== 各过滤层级 ===')
print('主板:', m1.sum(), '| 非一字:', m2.sum(), '| 炸板0:', m3.sum(), '| 早盘:', m4.sum(), '| 连板2+:', m5.sum())

cand = df[m1 & m2 & m3 & m4 & m5]
print('\n=== 新策略候选 ===')
print(cand[['code','name','price','pct','high_days','break_times','first_time','seal_rate','reason']].to_string(index=False))

# 备选：放宽早盘到90分钟(10:00前)
cand2 = df[m1 & m2 & m3 & (df['seal_min']<=90) & m5]
print('\n=== 60分钟内封板版本(90min) ===')
print(cand2[['code','name','price','pct','high_days','break_times','first_time','seal_rate','reason']].to_string(index=False))