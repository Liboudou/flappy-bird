#!/usr/bin/env python3
"""Remove dark background from PNG image, keep copper/metallic logo with alpha."""

import struct
import zlib
import sys

def read_png(path):
    """Read PNG file, return (width, height, raw_pixels_as_rgba, color_type, bit_depth)."""
    with open(path, 'rb') as f:
        data = f.read()
    
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    
    chunks = {}
    pos = 8
    idat_data = b''
    iend = False
    
    while pos < len(data):
        length = struct.unpack('>I', data[pos:pos+4])[0]
        chunk_type = data[pos+4:pos+8].decode('ascii', errors='replace')
        chunk_data = data[pos+8:pos+8+length]
        crc = data[pos+8+length:pos+12+length]
        
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
    
    # Convert to RGBA
    pixels = []
    for y in range(height):
        filter_byte = raw[y * (1 + width * 3)]
        row_start = y * (1 + width * 3) + 1
        for x in range(width):
            px = row_start + x * 3
            if px + 3 <= len(raw):
                r, g, b = raw[px], raw[px+1], raw[px+2]
                pixels.append((r, g, b))
    
    return width, height, pixels

def write_png_rgba(path, width, height, pixels_rgba):
    """Write RGBA pixels (list of (r,g,b,a) tuples) to PNG."""
    # Build raw data with filter byte 0 (None) per row
    raw_data = b''
    for y in range(height):
        raw_data += b'\x00'  # filter byte
        for x in range(width):
            r, g, b, a = pixels_rgba[y * width + x]
            raw_data += struct.pack('BBBB', r, g, b, a)
    
    compressed = zlib.compress(raw_data)
    
    def make_chunk(chunk_type, data):
        chunk = chunk_type.encode('ascii') + data
        crc = struct.pack('>I', zlib.crc32(chunk) & 0xffffffff)
        return struct.pack('>I', len(data)) + chunk + crc
    
    signature = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)  # 8-bit RGBA
    idat = compressed
    
    with open(path, 'wb') as f:
        f.write(signature)
        f.write(make_chunk('IHDR', ihdr))
        f.write(make_chunk('IDAT', idat))
        f.write(make_chunk('IEND', b''))

def is_dark(r, g, b, threshold=40):
    """Check if pixel is dark (background)."""
    return r < threshold and g < threshold and b < threshold

def is_bokeh(r, g, b, brightness_threshold=100):
    """Check if pixel is a bokeh light spot."""
    # Bokeh lights are warmer/amber and brighter
    avg = (r + g + b) / 3
    return avg > brightness_threshold and avg < 200

def main():
    width, height, pixels = read_png('/workspace/slice_meta_01_icon.png')
    print(f"Image: {width}x{height}, {len(pixels)} pixels")
    
    # Analyze the image to find background color
    # Count color occurrences
    from collections import Counter
    cnt = Counter(pixels)
    most_common = cnt.most_common(20)
    print("Most common colors:")
    for color, count in most_common[:10]:
        print(f"  RGB({color[0]:3d},{color[1]:3d},{color[2]:3d}) : {count} px")
    
    # The background should be the most common dark color
    # Let's find the dominant dark color
    dark_colors = [(c, n) for c, n in most_common if is_dark(c[0], c[1], c[2], 60)]
    if dark_colors:
        bg_color = dark_colors[0][0]
        print(f"Dominant background color: RGB{bg_color}")
    else:
        bg_color = (0, 0, 0)
        print("No dominant dark color found, using pure black")
    
    # Create RGBA output
    rgba = []
    removed = 0
    kept = 0
    
    for r, g, b in pixels:
        brightness = (r + g + b) / 3
        
        # Background detection: very dark pixels
        if r < 50 and g < 50 and b < 50:
            # Check if it's near the dominant bg color
            rgba.append((r, g, b, 0))  # transparent
            removed += 1
        else:
            rgba.append((r, g, b, 255))  # opaque
            kept += 1
    
    print(f"Kept: {kept}, Removed (transparent): {removed}")
    
    write_png_rgba('/workspace/slice_meta_01_nobg.png', width, height, rgba)
    print("Written to /workspace/slice_meta_01_nobg.png")

if __name__ == '__main__':
    main()