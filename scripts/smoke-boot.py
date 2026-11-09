#!/usr/bin/env python3
"""Boot the actual ISO with OVMF/TCG, log in, and require a running Plasma shell.
No writable hard disk, host device, network, or installer is attached.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument('--iso', type=Path, default=ROOT/'dist/nova-os-0.1-amd64.iso')
p.add_argument('--timeout', type=int, default=1000)
a = p.parse_args()
if not a.iso.is_file():
    p.error(f'ISO not found: {a.iso}')
out = ROOT/'dist'
out.mkdir(exist_ok=True)
code = Path(os.environ.get('OVMF_CODE', '/usr/share/OVMF/OVMF_CODE_4M.fd'))
var = Path(os.environ.get('OVMF_VARS', '/usr/share/OVMF/OVMF_VARS_4M.fd'))
# Construct the marker at run time: terminal echo of the command cannot pass the test.
probe = ("ready=1; systemctl is-active --quiet sddm || ready=0; "
         "pgrep -u nova -x plasmashell >/dev/null || ready=0; "
         "pgrep -u nova -x fcitx5 >/dev/null || ready=0; "
         "test -r /usr/share/wallpapers/Nova/contents/images/1920x1080.png || ready=0; "
         "if [ \"$ready\" = 1 ]; then "
         "busctl --user --timeout=10 call org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell "
         "evaluateScript s 'print(panels().length)' | grep -Eq '^s \"[1-9][0-9]*' || ready=0; fi; "
         "if [ \"$ready\" = 1 ]; then printf '\\n%s%s\\n' NOVA_ DESKTOP_READY; "
         "else printf '\\n%s%s\\n' NOVA_ DESKTOP_WAIT; "
         "systemctl is-active sddm; pgrep -a -u nova -f 'plasmashell|kwin_wayland|fcitx5'; "
         "sudo journalctl -b -u sddm --no-pager -n 12; "
         "journalctl --user -b --no-pager -n 20; fi\n")
passed = False
phase = 'starting QEMU'
with tempfile.TemporaryDirectory(prefix='nova-boot-') as d:
    d = Path(d)
    shutil.copy(var, d/'vars.fd')
    command = ['qemu-system-x86_64', '-machine', 'q35,accel=tcg', '-cpu', 'max',
               '-m', '4096', '-smp', '2', '-display', 'none', '-vga', os.environ.get('NOVA_QEMU_VGA', 'std'),
               '-drive', f'if=pflash,format=raw,readonly=on,file={code}',
               '-drive', f'if=pflash,format=raw,file={d}/vars.fd',
               '-cdrom', str(a.iso.resolve()), '-boot', 'd', '-nic', 'none',
               '-serial', f'unix:{d}/serial,server=on,wait=off',
               '-qmp', f'unix:{d}/qmp,server=on,wait=off']
    with (out/'qemu-stderr.log').open('wb') as errors, (out/'qemu-serial.log').open('wb') as log:
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=errors)
        serial = None
        qmp = None
        try:
            start = time.monotonic()
            while not (d/'serial').exists():
                if process.poll() is not None:
                    raise RuntimeError('QEMU exited; see qemu-stderr.log')
                if time.monotonic()-start > 30:
                    raise TimeoutError('QEMU serial socket startup timeout')
                time.sleep(.1)
            serial = socket.socket(socket.AF_UNIX)
            serial.connect(str(d/'serial'))
            serial.settimeout(1)
            phase = 'waiting for live user login'
            buffer = b''
            sent_login = False
            sent_password = False
            next_probe = float('inf')
            authenticated = False
            attempts = 0
            while time.monotonic()-start < a.timeout:
                if process.poll() is not None:
                    raise RuntimeError('Guest exited unexpectedly')
                try:
                    data = serial.recv(65536)
                except socket.timeout:
                    data = b''
                if data:
                    log.write(data)
                    log.flush()
                    buffer = (buffer+data)[-65536:]
                # Match translated prompts and ignore interleaved kernel/status messages.
                plain = re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]', b'', buffer).decode('utf-8', errors='replace')
                if not authenticated and re.search(r'(?im)(?:^|[\r\n])[^\r\n]{0,80}(?:login|ログイン):\s*', plain):
                    attempts += 1
                    if attempts > 3:
                        raise RuntimeError('Live login failed after three attempts')
                    serial.sendall(b'nova\n')
                    sent_login = True
                    sent_password = False
                    buffer = b''
                    phase = 'waiting for live password prompt'
                elif sent_login and not sent_password and re.search(r'(?i)(?:password|パスワード):\s*', plain):
                    serial.sendall(b'live\n')
                    sent_password = True
                    buffer = b''
                    phase = 'waiting for authenticated live shell'
                elif not authenticated and re.search(r'nova@[^\r\n]*[#$]', plain):
                    authenticated = True
                    next_probe = time.monotonic()+10
                    buffer = b''
                    phase = 'live shell authenticated'
                if time.monotonic() >= next_probe:
                    serial.sendall(probe.encode())
                    phase = 'checking SDDM, Plasma shell, Fcitx5 and Nova wallpaper'
                    next_probe = time.monotonic()+20
                if re.search(rb'\r?\nNOVA_DESKTOP_READY\r?\n', buffer):
                    passed = True
                    phase = 'live desktop D-Bus response, panel, processes and wallpaper verified'
                    time.sleep(10)
                    break
            # Save a guest framebuffer for visual review on both success and timeout.
            qmp = socket.socket(socket.AF_UNIX)
            qmp.settimeout(10)
            qmp.connect(str(d/'qmp'))
            f = qmp.makefile('rwb', buffering=0)
            f.readline()
            for request in [{'execute': 'qmp_capabilities'},
                            {'execute': 'screendump', 'arguments': {'filename': str(out/'qemu-desktop.ppm')}}]:
                f.write((json.dumps(request)+'\n').encode())
                while True:
                    response = json.loads(f.readline())
                    if 'return' in response or 'error' in response:
                        if 'error' in response:
                            raise RuntimeError(str(response))
                        break
        except Exception as error:
            phase = f'{phase}: {error}'
            passed = False
        finally:
            if serial:
                serial.close()
            if qmp:
                qmp.close()
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            result = {'passed': passed, 'phase': phase, 'firmware': 'OVMF UEFI',
                      'accelerator': 'TCG', 'vga': os.environ.get('NOVA_QEMU_VGA', 'std'), 'iso': a.iso.name,
                      'limitations': ['Secure Boot not tested', 'Japanese text entry requires manual verification',
                                      'Physical hardware and proprietary NVIDIA drivers not tested']}
            (out/'boot-result.json').write_text(json.dumps(result, indent=2)+'\n')
            print(json.dumps(result, indent=2))
raise SystemExit(0 if passed else 1)
