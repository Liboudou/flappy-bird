#!/usr/bin/env python3
"""Smart background removal: keep copper dither + glow, remove dark and bokeh."""
import struct, zlib

def process():
    with open('/workspace/slice_meta_01_icon.png', 'rb') as f:
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
            mn = min(r, g, b)
            
            keep = False
            
            # 1. Very dark pixels = background
            if mx < 30:
                keep = False
            # 2. Pure white / glow (all channels high)
            elif mx > 200 and mn > 150:
                keep = True
            # 3. Copper = red-dominant dither pattern
            elif r > g and r > b and r > 40:
                keep = True
            # 4. Warm copper (r ~= g but r > b significantly)
            elif r > b * 1.3 and g > b * 1.2 and mn > 20:
                keep = True
            # 5. Any pixel where the max channel is bright enough and not green/blue dominant
            elif mx > 80:
                # Green-dominant = bokeh
                if g > r * 1.3 and g > b * 1.3:
                    keep = False
                # Blue-dominant = bokeh
                elif b > r * 1.3 and b > g * 1.3:
                    keep = False
                else:
                    keep = True
            else:
                keep = False
            
            if keep:
                out[idx:idx+4] = struct.pack('BBBB', r, g, b, 255)
                fg += 1
            else:
                out[idx:idx+4] = struct.pack('BBBB', 0, 0, 0, 0)
                bg += 1
            idx += 4
    
    total = w * h
    print(f"Removed (transparent): {bg} ({100*bg/total:.1f}%)")
    print(f"Kept (opaque): {fg} ({100*fg/total:.1f}%)")
    
    compressed = zlib.compress(bytes(out))
    
    def chunk(ct, d):
        full = ct.encode() + d
        crc = struct.pack('>I', zlib.crc32(full) & 0xffffffff)
        return struct.pack('>I', len(d)) + full + crc
    
    with open('/workspace/slice_meta_01_nobg.png', 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        f.write(chunk('IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)))
        f.write(chunk('IDAT', compressed))
        f.write(chunk('IEND', b''))
    print(f"Done!")

process()