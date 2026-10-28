import requests, json, time
s = requests.Session(); s.trust_env = False
headers = {'User-Agent':'Mozilla/5.0','Referer':'https://quote.eastmoney.com/'}

# 东财实时快照：f31=f买一量, f32=f卖一量, f19=f最新价, f17=f开盘, f16=f最高, f18=f最低, f15=f最高价
# 用 qt/ulist 接口拿买卖盘
def snap(code):
    secid = ('1.' if code.startswith('6') else '0.') + code
    url = 'https://push2.eastmoney.com/api/qt/stock/get'
    params = {'secid': secid, 'ut':'fa5fd1943c7b386f172d6893dbfba10b',
              'fields':'f43,f44,f45,f46,f47,f48,f19,f17,f16,f18,f15,f31,f32,f33,f34,f35,f36,f37,f38,f39,f40,f57,f58,f60'}
    r = s.get(url, params=params, headers=headers, timeout=8)
    return r.json().get('data') or {}

for code, name in [('603138','海量数据'), ('603337','杰克科技')]:
    d = snap(code)
    print(f'--- {code} {name} ---')
    print('最新价f43(×100):', d.get('f43'), '| 涨停价f40:', d.get('f40'), '| 昨收f60:', d.get('f60'))
    print('买一价f19:', d.get('f19'), '买一量f31:', d.get('f31'))
    print('卖一价f20:', d.get('f20') if 'f20' in d else None, '卖一量f32:', d.get('f32'))
    # 委比等
    print('涨幅f170:', d.get('f170'))
    time.sleep(0.3)