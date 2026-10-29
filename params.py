import sys, json, struct
d = open(sys.argv[1], 'rb').read()
NAMES = {2:'Background',3:'Time',4:'Activity',5:'Date',6:'Weather',7:'StepsProgress',8:'Status',9:'Battery',10:'AnalogDialFace'}
def varint(b, i):
    r = s = 0
    while True:
        c = b[i]; i += 1; r |= (c & 0x7f) << s; s += 7
        if not c & 0x80: break
    if r >= 1 << 63: r -= 1 << 64
    return r, i
def parse(b):
    out, i = [], 0
    while i < len(b):
        k, i = varint(b, i); f, t = k >> 3, k & 7
        if t == 0:
            v, i = varint(b, i)
        elif t == 2:
            n, i = varint(b, i); raw = b[i:i+n]; i += n
            try: v = parse(raw)
            except Exception: v = raw.hex()
        else: raise ValueError
        out.append((f, v))
    return out
def tojson(items):
    o = {}
    for f, v in items:
        v = tojson(v) if isinstance(v, list) else v
        key = str(f)
        if key in o:
            if not isinstance(o[key], list) or not (o[key] and isinstance(o[key][0], (dict,int)) and getattr(o, '_l', None)):
                pass
            o.setdefault('_' + key, [o.pop(key)]) if not isinstance(o.get(key), list) or True else None
            o['_' + key].append(v) if '_' + key in o else None
        else:
            o[key] = v
    return o
base = 40
tbl_len = struct.unpack_from('<I', d, 36)[0]
table = parse(d[base:base+tbl_len])
start = base + tbl_len
res = {}
for f, v in table:
    if f == 1: res['_header'] = {'parametersSize': dict(v)[1], 'imagesCount': dict(v)[2]}; continue
    o, n = dict(v).get(1, 0), dict(v)[2]
    res[NAMES.get(f, f'Field{f}')] = tojson(parse(d[start+o:start+o+n]))
json.dump(res, open(sys.argv[2], 'w'), indent=2)
print(json.dumps(res, indent=1)[:2500])
