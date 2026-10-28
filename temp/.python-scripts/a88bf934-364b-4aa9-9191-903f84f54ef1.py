import requests, base64, hashlib, json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}

def fetch_page(page):
    url = f'https://gbcdn.dfcfw.com/rank/popularityList.js?type=0&sort=0&page={page}&m=28'
    r = requests.get(url, headers=UA, timeout=10)
    payload = r.text.split("'", 1)[1].rsplit("'", 1)[0]
    raw = base64.b64decode(payload)
    key = hashlib.md5(b'getUtilsFromFile').hexdigest().encode()
    iv  = b'getClassFromFile'[:16]
    plain = unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(raw), AES.block_size).decode('utf-8')
    return json.loads(plain)

d1 = fetch_page(1)
d2 = fetch_page(2)
print('page1 条数:', len(d1), ' page2 条数:', len(d2))
print('字段:', list(d1[0].keys()))
print('前5条:')
for x in d1[:5]:
    print({k: x[k] for k in ('code','rankNumber','ironsFans','newFans','exactTime')})
print('page1 code 列表:', [x['code'] for x in d1][:30])
