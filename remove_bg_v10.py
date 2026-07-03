#!/usr/bin/env python3
"""Gentle background removal: keep ALL copper, remove only true BG."""
import struct, zlib

INPUT = '/opt/data/profiles/designer/image_cache/img_9b6b610f0024.png'
OUTPUT = '/workspace/slice_logo_clean.png'

with open(INPUT, 'rb') as f:
    data = bytearray(f.read())

pos = 8
w = h = 0
idat = b''
while pos < len(data):
    l = struct.unpack('>I', data[pos:pos+4])[0]
    ctype = data[pos+4:pos+8].decode('ascii')
    cd = bytes(data[pos+8:pos+8+l])
    pos += 12 + l
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
        
        # KEEP if any of these conditions met:
        keep = False
        
        # 1. White/glow center areas
        if mx > 180:
            keep = True
        # 2. True copper (warm, red-dominant, medium-high brightness)
        elif r > 80 and g > 30 and r > b and (r - b) > 15 and mx > 50:
            keep = True
        # 3. Brighter copper/highlights
        elif mx > 70 and r > g and g > b:
            keep = True
        # 4. Medium-bright warm pixels
        elif mx > 55 and r > b * 1.3 and g > b * 1.2:
            keep = True
        # 5. Catch copper edges (darker but still warm)
        elif r > 45 and b < 30 and g > 15 and r > g * 1.1:
            keep = True
        # 6. Bright ambient glow around logo (near-white warm)
        elif mx > 100 and r > 80 and g > 60:
            keep = True
        
        if keep:
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