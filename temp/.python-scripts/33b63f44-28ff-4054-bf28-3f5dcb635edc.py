import requests, json
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}

def probe(name, fn):
    try:
        r = fn()
        print(f'[OK] {name}: {str(r)[:200]}')
    except Exception as e:
        print(f'[FAIL] {name}: {e}')

# 1. 东财股吧热帖榜(网页版API)
def t1():
    r = requests.get('https://gbapi.eastmoney.com/search/api/quote/rank', params={'code': 'all'}, headers=UA, timeout=8)
    return r.status_code, r.text[:200]
probe('东财gbapi rank', t1)

# 2. 东财股吧热门帖子(网页)
def t2():
    r = requests.get('https://guba.eastmoney.com/rank/', headers=UA, timeout=8)
    return r.status_code, r.text[:150]
probe('东财股吧rank页', t2)

# 3. 新浪股吧热帖榜
def t3():
    r = requests.get('https://vip.stock.finance.sina.com.cn/corp/go.php/vCB_BullGubaRank/stockid/600000.phtml', headers=UA, timeout=8)
    return r.status_code, r.text[:150]
probe('新浪个股股吧rank', t3)

# 4. 腾讯自选股热帖/讨论
def t4():
    r = requests.get('https://proxy.finance.qq.com/ifzqgtimg/appstock/news/info/notice', params={'symbol': '600000', 'type': '2'}, headers=UA, timeout=8)
    return r.status_code, r.text[:150]
probe('腾讯讨论帖', t4)
