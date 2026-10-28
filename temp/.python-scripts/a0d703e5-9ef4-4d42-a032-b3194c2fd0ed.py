import json
with open(r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\limitup_pools.json','r',encoding='utf-8') as f:
    data = json.load(f)
dates = data['dates']; pools = data['pools']

# 收集所有股票（主板 60/00 开头，排除ST）
codes = set()
for d in dates:
    for r in pools[d]:
        c = str(r['code'])
        if c.startswith(('60','00')) and 'ST' not in r['name']:
            codes.add(c)
print('主板涨停股去重:', len(codes))
# 保存到文件供下一步使用
with open(r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\backtest_codes.json','w',encoding='utf-8') as f:
    json.dump(sorted(codes), f, ensure_ascii=False)
print('样例:', sorted(codes)[:10])