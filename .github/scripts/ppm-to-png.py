#!/usr/bin/env python3
"""Convert QEMU P6 screenshots to PNG using only the standard library."""
from pathlib import Path
import struct
import sys
import zlib

source, target = map(Path, sys.argv[1:])
with source.open('rb') as f:
    assert f.readline().strip() == b'P6', 'Expected QEMU P6 screenshot'
    line = f.readline()
    while line.startswith(b'#'):
        line = f.readline()
    width, height = map(int, line.split())
    assert 0 < width * height <= 20_000_000
    assert f.readline().strip() == b'255'
    data = f.read(width * height * 3 + 1)
    assert len(data) == width * height * 3

def chunk(kind, payload):
    return (struct.pack('>I', len(payload)) + kind + payload
            + struct.pack('>I', zlib.crc32(kind + payload) & 0xffffffff))
rows = b''.join(b'\0' + data[y*width*3:(y+1)*width*3] for y in range(height))
target.write_bytes(b'\x89PNG\r\n\x1a\n'
    + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
    + chunk(b'IDAT', zlib.compress(rows, 6)) + chunk(b'IEND', b''))
