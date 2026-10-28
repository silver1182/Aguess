import sys, inspect
sys.path.insert(0, r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp')
from thsdk import get_price
print('签名:', inspect.signature(get_price))
import thsdk
# 看下get_price源码doc
print(get_price.__doc__[:800] if get_price.__doc__ else 'no doc')
