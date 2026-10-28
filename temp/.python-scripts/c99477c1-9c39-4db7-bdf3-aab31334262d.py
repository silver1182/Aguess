import json
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
data = json.load(open(base + r'\temp\limitup_pools_ext.json', encoding='utf-8'))
pools = data['pools']
# 全代码池（主板 60/00 开头）
all_codes = set()
main_codes = set()
for d, lst in pools.items():
    for r in lst:
        code = str(r['code']).zfill(6)
        all_codes.add(code)
        if code.startswith(('60','00')):
            main_codes.add(code)
print('全部代码:', len(all_codes), '主板代码:', len(main_codes))
# 存主板池
json.dump(sorted(main_codes), open(base + r'\temp\backtest_codes_ext.json','w'))
# 统计每天主板涨停数
cnt = {d: sum(1 for r in lst if str(r['code']).zfill(6).startswith(('60','00'))) for d, lst in pools.items()}
print('主板涨停记录总数:', sum(cnt.values()))
print('日均:', sum(cnt.values())/len(cnt))