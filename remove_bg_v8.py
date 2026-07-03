#!/usr/bin/env python3
"""Remove dark background - more aggressive threshold."""
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

# Analyze background color more carefully
# Sample corners to determine background color
from collections import Counter
corner_colors = Counter()
for y in range(50):
    for x in range(50):
        ri = y * (1 + w * 3) + 1 + x * 3
        r, g, b = raw[ri], raw[ri+1], raw[ri+2]
        corner_colors[(r//8*8, g//8*8, b//8*8)] += 1

print('Corner color distribution (quantized):')
for c, n in corner_colors.most_common(5):
    print(f'  RGB({c[0]:3d},{c[1]:3d},{c[2]:3d}) : {n}')

# The background is warm dark brown. Let me find a good threshold.
# Copper logo has R > 60 typically, background is all < 50 in all channels
# I'll use max(r,g,b) < 60 as background
# Also catch green/blue bokeh specks

out = bytearray(h * (1 + w * 4))
idx = 0
bg, fg = 0, 0

for y in range(h):
    out[idx] = 0
    idx += 1
    for x in range(w):
        ri = y * (1 + w * 3) + 1 + x * 3
        r, g, b = raw[ri], raw[ri+1], raw[ri+2]
        
        # Background detection
        is_bg = False
        
        # Pure dark / near-black
        if r < 60 and g < 40 and b < 35:
            is_bg = True
        
        # Green/blue cold bokeh specks  
        if r < 30 and (g > 80 or b > 80):
            is_bg = True
        
        # Very dim blue
        if b > r * 1.5 and r < 40 and b < 80:
            is_bg = True
            
        # Orange/amber bokeh that's in the background (dimmer orange)
        if r > 60 and g > 30 and b < 30 and r < 120:
            is_bg = True
        
        if is_bg:
            out[idx:idx+4] = struct.pack('BBBB', 0, 0, 0, 0)
            bg += 1
        else:
            out[idx:idx+4] = struct.pack('BBBB', r, g, b, 255)
            fg += 1
        idx += 4

total = w * h
print(f"\nBG removed: {bg} ({100*bg/total:.1f}%)")
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