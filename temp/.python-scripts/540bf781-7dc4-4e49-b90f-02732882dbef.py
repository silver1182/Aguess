import requests, base64, hashlib, json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}

def fetch(page, type_, sort):
    url = f'https://gbcdn.dfcfw.com/rank/popularityList.js?type={type_}&sort={sort}&page={page}&m=28'
    r = requests.get(url, headers=UA, timeout=10)
    payload = r.text.split("'", 1)[1].rsplit("'", 1)[0]
    raw = base64.b64decode(payload)
    key = hashlib.md5(b'getUtilsFromFile').hexdigest().encode()
    iv  = b'getClassFromFile'[:16]
    plain = unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(raw), AES.block_size).decode('utf-8')
    return json.loads(plain)

d = fetch(1, 0, 0)
# history 结构
print('history 条数:', len(d[0]['history']))
print('history 前3:', d[0]['history'][:3])
print('history 末3:', d[0]['history'][-3:])
# 测试 sort 参数
for s in [1, 2]:
    try:
        dd = fetch(1, 0, s)
        print(f'sort={s} 返回 {len(dd)} 条, 首条:', {k: dd[0][k] for k in ('code','rankNumber','ironsFans','newFans')})
    except Exception as e:
        print(f'sort={s} 失败:', e)
