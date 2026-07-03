#!/usr/bin/env python3
"""Fast background removal - process raw bytearray for speed."""

import struct
import zlib
import sys

def process():
    with open('/workspace/slice_meta_01_icon.png', 'rb') as f:
        data = bytearray(f.read())
    
    # Parse PNG chunks
    pos = 8
    chunks = []
    width = height = 0
    while pos < len(data):
        length = struct.unpack('>I', data[pos:pos+4])[0]
        ctype = data[pos+4:pos+8].decode('ascii')
        cdata = data[pos+8:pos+8+length]
        pos += 12 + length
        if ctype == 'IHDR':
            width = struct.unpack('>II', cdata[:8])[0]
            height = struct.unpack('>II', cdata[:8])[1]
            print(f"{width}x{height}")
        elif ctype == 'IDAT':
            raw = zlib.decompress(bytes(cdata))
    
    print(f"Raw data size: {len(raw)}")
    
    # Process rows: convert RGB to RGBA
    out = bytearray()
    for y in range(height):
        out.append(0)  # filter byte
        row_start = y * (1 + width * 3) + 1
        for x in range(width):
            px = row_start + x * 3
            r, g, b = raw[px], raw[px+1], raw[px+2]
            
            # Copper logic
            avg = (r + g + b) / 3
            is_logo = False
            
            # White/glow
            if r > 200 and g > 200 and b > 200:
                is_logo = True
            # Copper tones
            elif r > 80 and g > 30 and r > b and (r - b) > 20 and r > 60 and avg > 40:
                is_logo = True
            # Highlights
            elif avg > 100 and r > g and r > 50:
                is_logo = True
            # Copper with reflections
            elif r > 60 and g > 30 and avg > 35 and (r + g) > (b + 30):
                is_logo = True
            # Darker copper edges
            elif r > 40 and g > 20 and b > 10 and r > g * 1.2 and avg > 25:
                is_logo = True
            
            if is_logo:
                out.extend([r, g, b, 255])
            else:
                out.extend([r, g, b, 0])
    
    print(f"Output data size: {len(out)}")
    compressed = zlib.compress(bytes(out))
    
    # Write new PNG
    def chunk(ct, d):
        full = ct.encode() + d
        crc = struct.pack('>I', zlib.crc32(full) & 0xffffffff)
        return struct.pack('>I', len(d)) + full + crc
    
    with open('/workspace/slice_meta_01_nobg.png', 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        f.write(chunk('IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)))
        f.write(chunk('IDAT', compressed))
        f.write(chunk('IEND', b''))
    
    print("Done!")

if __name__ == '__main__':
    process()