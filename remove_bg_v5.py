#!/usr/bin/env python3
"""Remove background with better copper dithering handling."""
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
    total = h * w
    
    # Step 1: Classify every pixel
    # We'll build a heatmap: how "far" each pixel is from pure black
    # and whether it looks like copper vs bokeh/background
    
    def is_background(r, g, b):
        """Return True if pixel is background (black, dark, or bokeh)."""
        avg = (r + g + b) / 3
        
        # Pure black or very dark
        if avg < 20:
            return True
        
        # Bokeh lights: very saturated colors that aren't warm
        # Check saturation (max - min)
        mx = max(r, g, b)
        mn = min(r, g, b)
        sat = mx - mn
        
        # High saturation colors that aren't red-dominant = bokeh
        if sat > 150 and avg > 30:
            # Green-dominant bokeh (like pure green, cyan)
            if g > r * 1.5 and g > b * 1.5:
                return True
            # Blue-dominant bokeh (like pure blue)
            if b > r * 1.5 and b > g * 1.5:
                return True
            # Magenta bokeh  
            if r > 100 and b > 100 and g < 50:
                return True
        
        # Amber/gold bokeh lights - warm but very bright and saturated
        # These are the circular bokeh spots
        if avg > 60 and sat > 80:
            # Yellow-ish bokeh (r≈g > b)
            if abs(r - g) < 20 and r > b * 1.5 and b < 100:
                return True
            # Orange bokeh
            if r > g * 1.3 and g > b and b < 60 and r > 150:
                return True
        
        return False
    
    # Count stats
    bg_count = 0
    fg_count = 0
    
    # Build output
    out = bytearray(h * (1 + w * 4))
    idx = 0
    for y in range(h):
        out[idx] = 0
        idx += 1
        for x in range(w):
            ri = y * (1 + w * 3) + 1 + x * 3
            r, g, b = raw[ri], raw[ri+1], raw[ri+2]
            
            if is_background(r, g, b):
                out[idx:idx+4] = struct.pack('BBBB', 0, 0, 0, 0)
                bg_count += 1
            else:
                out[idx:idx+4] = struct.pack('BBBB', r, g, b, 255)
                fg_count += 1
            idx += 4
    
    print(f"Background (transparent): {bg_count} ({100*bg_count/total:.1f}%)")
    print(f"Foreground (opaque): {fg_count} ({100*fg_count/total:.1f}%)")
    
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
    print(f"Written: /workspace/slice_meta_01_nobg.png ({len(compressed)} bytes compressed)")

if __name__ == '__main__':
    process()