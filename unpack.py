import struct, sys, os, json
from PIL import Image
src, out = sys.argv[1], sys.argv[2]
d = open(src, 'rb').read()
assert d[:6] == b'HMDIAL'
first = d.find(b'BM')
# offset table: run of u32 ending at first image, first entry == 0
offs = []
p = first - 4
while p >= 0:
    v = struct.unpack_from('<I', d, p)[0]
    offs.insert(0, v)
    if v == 0: break
    p -= 4
tbl = p
print('offset table at', tbl, 'resources', len(offs))
os.makedirs(out, exist_ok=True)
info = []
for i, o in enumerate(offs):
    a = first + o
    sig, w, h, rowb, bpp, ncol, transp = struct.unpack_from('<4sHHHHHH', d, a)
    q = a + 16
    pal = []
    for c in range(ncol):
        r, g, b, _ = d[q:q+4]; pal.append((r, g, b)); q += 4
    img = Image.new('RGBA', (w, h))
    px = img.load()
    for y in range(h):
        row = d[q + y*rowb: q + (y+1)*rowb]
        for x in range(w):
            if bpp in (1, 2, 4, 8):
                bit = x * bpp
                byte = row[bit // 8]
                idx = (byte >> (8 - bpp - (bit % 8))) & ((1 << bpp) - 1)
                r, g, b = pal[idx] if idx < len(pal) else (255, 0, 255)
                a_ = 0 if (transp and idx == 0) else 255
            elif bpp == 16:
                v = row[2*x] | row[2*x+1] << 8
                r, g, b, a_ = ((v >> 11) & 31) * 255 // 31, ((v >> 5) & 63) * 255 // 63, (v & 31) * 255 // 31, 255
            elif bpp == 24:
                b, g, r = row[3*x:3*x+3]; a_ = 255
            else:
                r = g = b = 0; a_ = 255
            px[x, y] = (r, g, b, a_)
    img.save(os.path.join(out, f'{i}.png'))
    info.append(dict(index=i, width=w, height=h, bpp=bpp, colors=ncol, transparent=bool(transp)))
json.dump(info, open(os.path.join(out, '_images.json'), 'w'), indent=1)
open(os.path.join(out, '_parameters.bin'), 'wb').write(d[32:tbl])
print(info[:3], '...')
