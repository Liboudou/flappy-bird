#!/usr/bin/env python3
"""More precise background removal - remove dark bg AND bokeh lights."""

import struct
import zlib
import math
from collections import Counter

def read_png(path):
    with open(path, 'rb') as f:
        data = f.read()
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    pos = 8
    idat_data = b''
    width = height = bit_depth = color_type = 0
    while pos < len(data):
        length = struct.unpack('>I', data[pos:pos+4])[0]
        chunk_type = data[pos+4:pos+8].decode('ascii', errors='replace')
        chunk_data = data[pos+8:pos+8+length]
        if chunk_type == 'IHDR':
            width = struct.unpack('>I', chunk_data[0:4])[0]
            height = struct.unpack('>I', chunk_data[4:8])[0]
            bit_depth = chunk_data[8]
            color_type = chunk_data[9]
        elif chunk_type == 'IDAT':
            idat_data += chunk_data
        elif chunk_type == 'IEND':
            break
        pos += 12 + length
    
    raw = zlib.decompress(idat_data)
    pixels = []
    for y in range(height):
        row_start = y * (1 + width * 3) + 1
        for x in range(width):
            px = row_start + x * 3
            if px + 3 <= len(raw):
                pixels.append((raw[px], raw[px+1], raw[px+2]))
    return width, height, pixels

def write_png_rgba(path, width, height, pixels):
    raw_data = b''
    for y in range(height):
        raw_data += b'\x00'
        for x in range(width):
            r, g, b, a = pixels[y * width + x]
            raw_data += struct.pack('BBBB', min(255,r), min(255,g), min(255,b), min(255,a))
    compressed = zlib.compress(raw_data)
    
    def chunk(t, d):
        c = t.encode('ascii') + d
        crc = struct.pack('>I', zlib.crc32(c) & 0xffffffff)
        return struct.pack('>I', len(d)) + c + crc
    
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        f.write(chunk('IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)))
        f.write(chunk('IDAT', compressed))
        f.write(chunk('IEND', b''))

def main():
    width, height, pixels = read_png('/workspace/slice_meta_01_icon.png')
    print(f"Image: {width}x{height}")
    
    # Strategy: 
    # 1. Identify the copper/metal logo colors
    # 2. Everything else = transparent
    
    # Sample the logo color range by looking at non-dark pixels
    all_colors = Counter(pixels)
    
    # The logo is copper: warm brown/reddish tones with metallic sheen
    # Key characteristics of copper pixels:
    # - High red component (100-255)
    # - Medium green (50-180) 
    # - Low to medium blue (20-100)
    # - Or bright white/silver highlights
    
    def is_copper_or_logo(r, g, b):
        """Check if pixel belongs to the copper logo or its glow."""
        avg = (r + g + b) / 3
        
        # Pure white center dot and glow
        if r > 200 and g > 200 and b > 200:
            return True
        
        # Copper tones: warm, red-dominated
        # r > g > b typically for copper/bronze
        if r > 80 and g > 30 and r > b and (r - b) > 20:
            if r > 60 and avg > 40:
                return True
        
        # Metallic highlights (bright warm)
        if avg > 100 and r > g and r > 50:
            return True
        
        # Copper with some blue/purple reflections
        if r > 60 and g > 30 and avg > 35 and (r + g) > (b + 30):
            return True
            
        # Catch copper edges and darker copper areas
        if r > 40 and g > 20 and b > 10 and r > g * 1.2 and avg > 25:
            return True
            
        return False
    
    # Build output
    rgba = []
    logo_pixels = 0
    removed = 0
    
    for r, g, b in pixels:
        if is_copper_or_logo(r, g, b):
            rgba.append((r, g, b, 255))
            logo_pixels += 1
        else:
            rgba.append((r, g, b, 0))
            removed += 1
    
    print(f"Logo pixels (opaque): {logo_pixels} ({100*logo_pixels/len(pixels):.1f}%)")
    print(f"Removed (transparent): {removed} ({100*removed/len(pixels):.1f}%)")
    
    write_png_rgba('/workspace/slice_meta_01_nobg.png', width, height, rgba)
    print("Written to /workspace/slice_meta_01_nobg.png")

if __name__ == '__main__':
    main()