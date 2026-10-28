import sys, requests, json
base = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847'
sys.path.insert(0, base + r'\temp')
import a_stock_data as a

# 带 start_time 尝试
url = 'https://finance.pae.baidu.com/selfselect/getstockquotation'
params = {'all':'1','isIndex':'false','isBk':'false','isBlock':'false','isFutures':'false','isStock':'true','newFormat':'1','group':'quotation_kline_ab','finClientType':'pc','code':'000001','start_time':'2026-07-01','ktype':'1'}
headers = {'User-Agent':'Mozilla/5.0','Accept':'application/vnd.finance-web.v1+json','Origin':'https://gushitong.baidu.com','Referer':'https://gushitong.baidu.com/'}
r = requests.get(url, params=params, headers=headers, timeout=10)
d = r.json()
result = d.get('Result', {})
md = result.get('newMarketData', {})
print('keys:', md.get('keys'))
rows = md.get('marketData','').split(';')
print('行数:', len(rows), rows[:2], rows[-2:])