#!/usr/bin/env python3
"""Validate shipped inputs without claiming a boot test."""
from pathlib import Path
import json, re, struct, xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[1]
config=root/'config'
for p in config.rglob('*.json'):
    json.loads(p.read_text())
for p in root.rglob('*.svg'):
    ET.parse(p)
png=config/'includes.chroot/usr/share/wallpapers/Nova/contents/images/1920x1080.png'
data=png.read_bytes()
assert data[:8] == b'\x89PNG\r\n\x1a\n'
assert struct.unpack('>II',data[16:24]) == (1920,1080)
packages=(config/'package-lists/nova.list.chroot').read_text().splitlines()
packages=[x for x in packages if x and not x.startswith('#')]
assert len(packages)==len(set(packages))
assert all(re.fullmatch(r'[a-z0-9][a-z0-9+.-]*',x) for x in packages)
assert {'linux-image-amd64','kde-plasma-desktop','fcitx5-mozc','firefox-esr'} <= set(packages)
assert 'calamares' not in packages
assert (root/'auto/config').stat().st_mode & 0o111
print(f'PASS: {len(packages)} package names, JSON, SVG, wallpaper, live configuration')

# Exercise the boot-menu hook in live-build's documented binary working directory.
import subprocess
import tempfile
with tempfile.TemporaryDirectory() as tmp:
    binary=Path(tmp)
    (binary/'boot/grub').mkdir(parents=True)
    (binary/'isolinux').mkdir()
    (binary/'boot/grub/config.cfg').write_text('set default=0\n')
    (binary/'isolinux/isolinux.cfg').write_text('default vesamenu.c32\ntimeout 0\n')
    subprocess.run([str(config/'hooks/live/0200-nova-boot-menu.hook.binary')],cwd=binary,check=True)
    assert 'set timeout=5' in (binary/'boot/grub/config.cfg').read_text()
    assert 'timeout 50' in (binary/'isolinux/isolinux.cfg').read_text()
print('PASS: GRUB and Syslinux automatic live boot')
