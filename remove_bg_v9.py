#!/usr/bin/env python3
"""Clean background removal with smart thresholding."""
import struct, zlib

INPUT = '/opt/data/profiles/designer/image_cache/img_54b0059054f1.png'
OUTPUT = '/workspace/slice_logo_nobg.png'

with open(INPUT, 'rb') as f:
    data = bytearray(f.read())

pos = 8
w = h = 0
idat = b''
while pos < len(data):
    length = struct.unpack('>I', data[pos:pos+4])[0]
    ctype = data[pos+4:pos+8].decode('ascii')
    cd = bytes(data[pos+8:pos+8+length])
    pos += 12 + length
    if ctype == 'IHDR':
        w, h = struct.unpack('>II', cd[:8])
    elif ctype == 'IDAT':
        idat += cd
    elif ctype == 'IEND':
        break

raw = zlib.decompress(idat)
print(f"Image: {w}x{h}")

out = bytearray(h * (1 + w * 4))
idx = 0
bg, fg = 0, 0

for y in range(h):
    out[idx] = 0
    idx += 1
    for x in range(w):
        ri = y * (1 + w * 3) + 1 + x * 3
        r, g, b = raw[ri], raw[ri+1], raw[ri+2]
        mx = max(r, g, b)
        
        # Keep: bright copper (mx >= 55) OR white glow center (all channels high)
        if mx >= 55:
            out[idx:idx+4] = struct.pack('BBBB', r, g, b, 255)
            fg += 1
        else:
            out[idx:idx+4] = struct.pack('BBBB', 0, 0, 0, 0)
            bg += 1
        idx += 4

total = w * h
print(f"BG removed: {bg} ({100*bg/total:.1f}%)")
print(f"Logo kept: {fg} ({100*fg/total:.1f}%)")

compressed = zlib.compress(bytes(out))

def chunk(ct, d):
    full = ct.encode() + d
    crc = struct.pack('>I', zlib.crc32(full) & 0xffffffff)
    return struct.pack('>I', len(d)) + full + crc

with open(OUTPUT, 'wb') as f:
    f.write(b'\x89PNG\r\n\x1a\n')
    f.write(chunk('IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)))
    f.write(chunk('IDAT', compressed))
    f.write(chunk('IEND', b''))
print(f"Written: {OUTPUT}")