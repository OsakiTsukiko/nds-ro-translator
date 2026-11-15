import struct, re

def parse(path):
    d = open(path,'rb').read()
    assert d[:8] == b'MESGbmg1'
    nsec = struct.unpack_from('<I', d, 0xC)[0]
    enc = d[0x10]
    off = 0x20
    secs = {}
    order = []
    for _ in range(nsec):
        magic = d[off:off+4].decode(); size = struct.unpack_from('<I', d, off+4)[0]
        secs[magic] = d[off:off+size]; order.append(magic); off += size
    inf = secs['INF1']
    n, esz = struct.unpack_from('<HH', inf, 8)
    inf_extra = inf[12:16]
    entries = []
    for i in range(n):
        e = inf[16+i*esz:16+(i+1)*esz]
        entries.append((struct.unpack_from('<I', e, 0)[0], e[4:]))
    dat = secs['DAT1'][8:]
    msgs = []
    for o, attr in entries:
        msgs.append(decode(dat, o))
    fullsize=struct.unpack_from('<I',d,8)[0]>=len(d)
    return dict(fullsize=fullsize,header=d[:0x20], order=order, secs=secs, esz=esz, inf_extra=inf_extra,
                attrs=[a for _, a in entries], msgs=msgs, offsets=[o for o,_ in entries])

def decode(dat, o):
    out = []
    while True:
        c = struct.unpack_from('<H', dat, o)[0]
        if c == 0: break
        if c == 0x1A:
            ln = dat[o+2]
            out.append('{' + dat[o+3:o+ln].hex() + '}')
            o += ln; continue
        ch = chr(c)
        if ch in '{}': ch = '\\' + ch
        out.append(ch); o += 2
    return ''.join(out)

def encode(s):
    b = bytearray(); i = 0
    while i < len(s):
        ch = s[i]
        if ch == '\\' and i+1 < len(s) and s[i+1] in '{}':
            b += struct.pack('<H', ord(s[i+1])); i += 2; continue
        if ch == '{':
            j = s.index('}', i); h = bytes.fromhex(s[i+1:j])
            b += struct.pack('<H', 0x1A) + bytes([len(h)+3]) + h; i = j+1; continue
        b += struct.pack('<H', ord(ch)); i += 1
    return bytes(b) + b'\0\0'

def build(p, msgs):
    dat = bytearray(b'\0\0')  # original starts with empty string at offset 0
    offs = []; cache = {}
    for i,m in enumerate(msgs):
        if p.get('offsets') and p['offsets'][i]==0 and m=='':
            offs.append(0); continue
        enc = encode(m)
        offs.append(len(dat)); dat += enc
    while (len(dat)+8) % 32: dat += b'\0'
    datsec = b'DAT1' + struct.pack('<I', len(dat)+8) + dat
    inf = bytearray(b'INF1' + b'\0'*4 + struct.pack('<HH', len(msgs), p['esz']) + p['inf_extra'])
    for o, a in zip(offs, p['attrs']):
        inf += struct.pack('<I', o) + a
    while len(inf) % 32: inf += b'\0'
    struct.pack_into('<I', inf, 4, len(inf))
    secs = dict(p['secs']); secs['INF1'] = bytes(inf); secs['DAT1'] = datsec
    body = b''.join(secs[k] for k in p['order'])
    hdr = bytearray(p['header']); total=0x20+len(body)
    if p.get('fullsize'): struct.pack_into('<I', hdr, 8, (total+31)//32*32)
    else: struct.pack_into('<I', hdr, 8, 0x20 + len(secs['INF1']) + len(secs['DAT1']))
    return bytes(hdr) + body
