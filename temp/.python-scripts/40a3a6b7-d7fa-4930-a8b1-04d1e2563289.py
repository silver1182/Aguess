import subprocess, sys, time
# 长时间采集任务, 用子进程后台运行并分段查看
script = r'C:\Users\Administrator\AppData\Roaming\Tencent\Marvis\User\oAN1i2TE0PyCl2LM6QKe2P1pkrkw\workspace\conv_56dfbc72a6e94fb9984daad052543847\temp\iter6_fetch_dragon.py'
p = subprocess.Popen([sys.executable, script], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
# 先跑45秒看进度
time.sleep(45)
try:
    p.kill()
except Exception:
    pass
out = p.stdout.read() if p.stdout else ''
print(out[-1500:])
