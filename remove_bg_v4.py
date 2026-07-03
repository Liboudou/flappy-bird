#!/usr/bin/env python3
"""Fast background removal - handles multiple IDAT chunks."""

import struct
import zlib

def process():
    with open('/workspace/slice_meta_01_icon.png', 'rb') as f:
        data = bytearray(f.read())
    
    pos = 8
    width = height = 0
    idat_compressed = b''
    
    while pos < len(data):
        length = struct.unpack('>I', data[pos:pos+4])[0]
        ctype = data[pos+4:pos+8].decode('ascii')
        cdata = bytes(data[pos+8:pos+8+length])
        pos += 12 + length
        if ctype == 'IHDR':
            width = struct.unpack('>II', cdata[:8])[0]
            height = struct.unpack('>II', cdata[:8])[1]
        elif ctype == 'IDAT':
            idat_compressed += cdata
        elif ctype == 'IEND':
            break
    
    print(f"{width}x{height}, compressed size: {len(idat_compressed)}")
    raw = zlib.decompress(idat_compressed)
    print(f"Raw size: {len(raw)}")
    
    # Process - using memoryview for speed
    w = width
    h = height
    out = bytearray(h * (1 + w * 4))
    
    idx = 0
    for y in range(h):
        out[idx] = 0  # filter byte
        idx += 1
        row_start = y * (1 + w * 3) + 1
        for x in range(w):
            px = row_start + x * 3
            r = raw[px]
            g = raw[px+1]
            b = raw[px+2]
            
            avg = (r + g + b) / 3
            is_logo = False
            
            # White/glow
            if r > 200 and g > 200 and b > 200:
                is_logo = True
            # Copper tones: warm, red-dominated
            elif r > 80 and g > 30 and r > b and (r - b) > 20 and avg > 40:
                is_logo = True
            # Bright metallic highlights
            elif avg > 100 and r > g and r > 50:
                is_logo = True
            # Copper with reflections
            elif r > 60 and g > 30 and avg > 35 and (r + g) > (b + 30):
                is_logo = True
            # Dark copper edges
            elif r > 40 and g > 20 and b > 10 and r > g * 1.2 and avg > 25:
                is_logo = True
            
            if is_logo:
                out[idx:idx+4] = struct.pack('BBBB', r, g, b, 255)
            else:
                out[idx:idx+4] = struct.pack('BBBB', r, g, b, 0)
            idx += 4
    
    compressed = zlib.compress(bytes(out))
    
    def chunk(ct, d):
        full = ct.encode() + d
        crc = struct.pack('>I', zlib.crc32(full) & 0xffffffff)
        return struct.pack('>I', len(d)) + full + crc
    
    with open('/workspace/slice_meta_01_nobg.png', 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        f.write(chunk('IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)))
        f.write(chunk('IDAT', compressed))
        f.write(chunk('IEND', b''))
    
    print(f"Done! Output: /workspace/slice_meta_01_nobg.png")

if __name__ == '__main__':
    process()