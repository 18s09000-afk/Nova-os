import tempfile,pathlib,shutil,subprocess,os,json
fake='''#!/usr/bin/env python3
import socket,sys,time,json,threading,os
args=sys.argv
if os.environ.get('FAKE_FAIL'):
 sys.exit(3)
def arg(k): return args[args.index(k)+1].split('unix:',1)[1].split(',')[0]
s=socket.socket(socket.AF_UNIX);s.bind(arg('-serial'));s.listen(1)
q=socket.socket(socket.AF_UNIX);q.bind(arg('-qmp'));q.listen(1)
def serial():
 c,_=s.accept();f=c.makefile('rwb',buffering=0)
 f.write(b'nova login: \\r\\nkernel: late message\\r\\n')
 assert f.readline()==b'nova\\n'
 f.write(('パスワード: ' if os.environ.get('FAKE_JA') else 'Password: ').encode())
 assert f.readline()==b'live\\n'
 f.write(b'nova@nova:~$ ')
 command=f.readline()
 assert command.endswith(b'fi\\n'),repr(command)
 assert b'NOVA_DESKTOP_READY' not in command
 f.write(command) # terminal echo must not be sufficient
 f.write(b'\\r\\nNOVA_DESKTOP_READY\\r\\n')
threading.Thread(target=serial,daemon=True).start()
c,_=q.accept();f=c.makefile('rwb',buffering=0);f.write(b'{"QMP":{}}\\n')
while True:
 line=f.readline()
 if not line:break
 request=json.loads(line)
 if request['execute']=='screendump':
  open(request['arguments']['filename'],'wb').write(b'P6\\n1 1\\n255\\n\\0\\0\\0')
 f.write(b'{"return":{}}\\n')
time.sleep(30)
'''
with tempfile.TemporaryDirectory() as tmp:
 p=pathlib.Path(tmp);(p/'scripts').mkdir();(p/'bin').mkdir();(p/'dist').mkdir()
 shutil.copy(pathlib.Path(__file__).resolve().parents[1]/'scripts/smoke-boot.py',p/'scripts/smoke-boot.py')
 (p/'bin/qemu-system-x86_64').write_text(fake);(p/'bin/qemu-system-x86_64').chmod(0o755)
 (p/'fixture.iso').touch()
 env=dict(os.environ,PATH=str(p/'bin')+':'+os.environ['PATH'])
 for fail, japanese in [(False, False), (False, True), (True, False)]:
  e=dict(env)
  if fail:e['FAKE_FAIL']='1'
  if japanese:e['FAKE_JA']='1'
  r=subprocess.run(['python3',str(p/'scripts/smoke-boot.py'),'--iso',str(p/'fixture.iso'),'--timeout','40'],env=e,capture_output=True,text=True,timeout=50)
  data=json.loads((p/'dist/boot-result.json').read_text())
  assert (r.returncode==0)==(not fail),(r.stdout,r.stderr)
  assert data['passed']==(not fail),data
  print('PASS: simulated QEMU protocol', 'early exit rejected' if fail else ('Japanese' if japanese else 'English')+' serial login, probe and QMP screenshot')
print('Protocol tests only; not a Nova ISO boot test.')
