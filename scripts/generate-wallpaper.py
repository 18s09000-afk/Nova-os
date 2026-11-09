#!/usr/bin/env python3
"""Dependency-free deterministic Nova Horizon artwork (CC0)."""
from pathlib import Path
import struct
import zlib
W,H=1920,1080
rows=[]
for y in range(H):
    row=bytearray([0])
    for x in range(W):
        glow=max(0,1-((x-W*.67)**2/(W*.55)**2+(y-H*.44)**2/(H*.8)**2))
        c=[int(7+5*glow),int(11+23*glow),int(23+35*glow)]
        # Cyan horizon, angular mountain outline, and perspective grid.
        ridge=int(H*.57+abs(x-W*.67)*.19)
        if abs(y-ridge)<2 or (y>H*.73 and (y%60==0 or abs((x-W/2)/max(1,y-H*.60)*160)%130<1)):
            c=[0,100,120]
        # Geometric N signature in the upper-left.
        if 160<=y<310 and (150<=x<172 or 254<=x<276 or abs(x-(172+(y-160)*.55))<12):
            c=[0,201,221]
        row.extend(c)
    rows.append(row)
def chunk(t,d):
    return struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d)&0xffffffff)
p=Path(__file__).resolve().parents[1]/'config/includes.chroot/usr/share/wallpapers/Nova/contents/images/1920x1080.png'
p.parent.mkdir(parents=True,exist_ok=True)
p.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',W,H,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(rows),9))+chunk(b'IEND',b''))
print(p)
