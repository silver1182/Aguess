import requests, json, re
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
# 东财股吧人气榜: type=0 A股, sort=0 人气, page=1
for url in [
    'https://gbcdn.dfcfw.com/rank/popularityList.js?type=0&sort=0&page=1&m=28',
    'https://gbcdn.dfcfw.com/rank/popularityList.js?type=0&sort=1&page=1&m=28',
]:
    try:
        r = requests.get(url, headers=UA, timeout=10)
        print(url[:80], '->', r.status_code, 'len', len(r.text))
        print(r.text[:400])
        print('====')
    except Exception as e:
        print('FAIL', e)
