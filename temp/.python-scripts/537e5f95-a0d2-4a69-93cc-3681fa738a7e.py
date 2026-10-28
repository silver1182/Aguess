import requests, base64, hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
url = 'https://gbcdn.dfcfw.com/rank/popularityList.js?type=0&sort=0&page=1&m=28'
r = requests.get(url, headers=UA, timeout=10)
payload = r.text.split("'", 1)[1].rsplit("'", 1)[0]
raw = base64.b64decode(payload)

key = hashlib.md5(b'getUtilsFromFile').hexdigest().encode()  # 32 bytes
iv  = b'getClassFromFile'[:16]  # 16 bytes

cipher = AES.new(key, AES.MODE_CBC, iv)
plain = unpad(cipher.decrypt(raw), AES.block_size).decode('utf-8')
print('解密成功, len:', len(plain))
print(plain[:1200])
