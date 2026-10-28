import requests, base64, json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'}
url = 'https://gbcdn.dfcfw.com/rank/popularityList.js?type=0&sort=0&page=1&m=28'
r = requests.get(url, headers=UA, timeout=10)
payload = r.text.split("'", 1)[1].rsplit("'", 1)[0]

key = b'wijrKSCUiQuGbrwsgyEMyIx7Uogmfe85'   # 32字节 AES-256
iv  = b'ho6KJIIz9WV7nozZl5fVnG7MtDUcSUB1'[:16]  # 取前16字节

raw = base64.b64decode(payload)
cipher = AES.new(key, AES.MODE_CBC, iv)
plain = unpad(cipher.decrypt(raw), AES.block_size).decode('utf-8')
print('解密成功, len:', len(plain))
print(plain[:800])
