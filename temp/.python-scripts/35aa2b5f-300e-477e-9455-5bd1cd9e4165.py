import requests, json, time
s = requests.Session(); s.trust_env = False
headers = {'User-Agent':'Mozilla/5.0','Referer':'https://quote.eastmoney.com/'}

def depth(code):
    secid = ('1.' if code.startswith('6') else '0.') + code
    url = 'https://push2.eastmoney.com/api/qt/stock/get'
    # f31买一量 f32卖一量 f19买一价 f20卖一价 f17开盘 f15最高 f16最低 f18现价 f43
    params = {'secid': secid, 'ut':'fa5fd1943c7b386f172d6893dbfba10b',
              'fields':'f43,f44,f45,f46,f47,f48,f60,f31,f32,f19,f20,f15,f16,f17,f18,f40,f41'}
    r = s.get(url, params=params, headers=headers, timeout=8)
    return r.json().get('data') or {}

for code, name in [('603138','海量数据'), ('603337','杰克科技')]:
    d = depth(code)
    print(f'--- {code} {name} ---')
    print(json.dumps({k:d.get(k) for k in ['f43','f60','f31','f32','f19','f20','f40','f41']}, ensure_ascii=False))
    time.sleep(0.3)