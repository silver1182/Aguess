# -*- coding: utf-8 -*-
import sys, json, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
TEMP = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp'
sys.path.insert(0, TEMP)
import daily_pick as dp
import pandas as pd

# 伪造 mkt_df (120日)
idx = [100 + i*0.3 for i in range(120)]
dates = pd.date_range('2026-06-01', periods=120).strftime('%Y-%m-%d').tolist()
mkt_df = pd.DataFrame({'date': dates, 'idx': idx, 'ma20': [x-2 for x in idx]})
mkt_res = {'state':'熊','depth':'深熊','dev':-5.0,'ret5':-2.0,'ret20':-10.0,'verdict':'深熊+20日急跌: A2高胜率舒适区, 可精选介入','sentiment_score':3,'sentiment_label':'恐慌'}
sent = {'limit_up':{'count':80},'limit_down':{'count':2},'broken':{'count':30},'broken_rate':27.3,'lianban':{'max':4,'count_2plus':6}}
cands = [
 {'code':'600123','name':'测试股A','date':'2026-10-28','close':8.5,'pct':0.2,'prev2_pct':10.01,'vol_ratio':0.45,'ma5':8.2,'vol5':2000000},
 {'code':'000456','name':'测试股B','date':'2026-10-28','close':19.8,'pct':-1.5,'prev2_pct':9.98,'vol_ratio':0.3,'ma5':19.5,'vol5':1500000},
]
# 买入模式 (watch_only=False)
p1 = TEMP + r'\test_buy.html'
dp.build_html(mkt_df, mkt_res, sent, cands, False, '深熊舒适区可精选介入', '2026-10-28', p1, coverage=1649)
# 观察模式 (watch_only=True)
p2 = TEMP + r'\test_watch.html'
dp.build_html(mkt_df, mkt_res, sent, cands, True, '门控测试', '2026-10-28', p2, coverage=1649)
h1 = open(p1, encoding='utf-8').read()
h2 = open(p2, encoding='utf-8').read()
print('买入模式: 含"买入清单":', '买入清单' in h1, '| 含"可精选介入":', '可精选介入' in h1, '| 表格行数:', h1.count('<tr><td>'))
print('  含深熊标注94.7%:', '94.7%' in h1, '| 含r1 +1.88%:', 'r1 +1.88%' in h1)
print('观察模式: 含"市况门控":', '市况门控' in h2, '| 含"观察名单":', '观察名单' in h2, '| 表格行数:', h2.count('<tr><td>'))
print('两种模式表格数据一致:', h1.count('<tr><td>') == h2.count('<tr><td>'))
