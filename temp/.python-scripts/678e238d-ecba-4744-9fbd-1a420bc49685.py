import json
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
data = json.load(open(base + r'\temp\limitup_pools_ext.json', encoding='utf-8'))
dates = sorted(data['dates'])
print('日期数:', len(dates))
print('前5:', dates[:5])
print('后5:', dates[-5:])
# 检查两种格式
dash = [d for d in dates if '-' in d]
nodash = [d for d in dates if '-' not in d]
print('带连字符:', len(dash), '不带:', len(nodash))
# 重命名统一为 YYYY-MM-DD
pools = data['pools']
new_pools = {}
for d, v in pools.items():
    nd = d.replace('-', '')
    new_pools[nd] = v
dates2 = sorted(new_pools.keys())
print('统一后日期数:', len(dates2), '首尾:', dates2[0], dates2[-1])
json.dump({'dates': dates2, 'pools': new_pools}, open(base + r'\temp\limitup_pools_ext.json','w',encoding='utf-8'), ensure_ascii=False)
print('ok')