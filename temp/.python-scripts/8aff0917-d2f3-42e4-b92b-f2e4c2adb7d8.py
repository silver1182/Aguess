import requests, base64, json, re
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
r = requests.get('https://gbcdn.dfcfw.com/rank/popularityList.js?type=0&sort=0&page=1&m=28', headers=UA, timeout=10)
txt = r.text
payload = txt.split("'", 1)[1].rsplit("'", 1)[0]
print('payload len:', len(payload))
# 尝试 base64 解码
try:
    dec = base64.b64decode(payload)
    print('b64 decode OK, len', len(dec))
    print(dec[:500])
except Exception as e:
    print('b64 fail:', e)
    # 可能是 URL-safe 或需补位
    try:
        dec = base64.b64decode(payload + '=' * (-len(payload) % 4))
        print('padded b64 OK, len', len(dec))
        print(dec[:500])
    except Exception as e2:
        print('padded fail:', e2)
