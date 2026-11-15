"""NARC + Gen IV (HGSS) message archive codec."""
import struct, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
CHARMAP = os.environ.get('G4_CHARMAP', os.path.join(HERE, 'charmap_hgss.txt'))

# ---------------------------------------------------------------- NARC
def narc_read(data):
    assert data[:4] == b'NARC'
    off = struct.unpack_from('<H', data, 12)[0]
    assert data[off:off+4] == b'BTAF'
    btaf_size, n = struct.unpack_from('<IH', data, off+4)
    fat = [struct.unpack_from('<II', data, off+12+8*i) for i in range(n)]
    off += btaf_size
    assert data[off:off+4] == b'BTNF'
    btnf = data[off:off+struct.unpack_from('<I', data, off+4)[0]]
    off += len(btnf)
    assert data[off:off+4] == b'GMIF'
    base = off + 8
    return [data[base+s:base+e] for s, e in fat], btnf

def narc_write(files, btnf):
    fimg = b''
    fat = []
    for f in files:
        s = len(fimg)
        fimg += f
        fat.append((s, len(fimg)))
        fimg += b'\xff' * ((-len(fimg)) % 4)
    btaf = b'BTAF' + struct.pack('<IHH', 12 + 8*len(files), len(files), 0) + b''.join(struct.pack('<II', *x) for x in fat)
    gmif = b'GMIF' + struct.pack('<I', 8 + len(fimg)) + fimg
    body = btaf + btnf + gmif
    return b'NARC' + struct.pack('<HHIHH', 0xFFFE, 0x0100, 16 + len(body), 16, 3) + body

# ---------------------------------------------------------------- charmap
def load_charmap():
    c2s, s2c = {}, {}
    cmds = {}
    for line in open(CHARMAP, encoding='utf-8'):
        line = line.rstrip('\r\n')
        if '//' in line and not line.startswith('01B1'):
            line = line[:line.index('//')]
        line = line.lstrip(' \t')
        if not line or '=' not in line:
            continue
        k, v = line.split('=', 1)
        code = int(k, 16)
        if v.startswith('{') and len(v) > 1:
            cmds[code] = v[1:-1]
            continue
        if code in (0xE000, 0x25BC, 0x25BD):
            continue
        c2s[code] = v
        if v not in s2c:
            s2c[v] = code
    return c2s, s2c, cmds

C2S, S2C, CMDS = load_charmap()
# characters that need special escaping in our text form
SPECIAL = {0xE000: '\\n', 0x25BC: '\\r', 0x25BD: '\\f'}
S2C['['] = None  # sanity: we never use raw brackets for chars

# ---------------------------------------------------------------- message files
def _dec_alloc(key, i):
    k = (765 * i * key) & 0xFFFF
    return k | (k << 16)

def msg_read_raw(data):
    count, key = struct.unpack_from('<HH', data, 0)
    out = []
    for i in range(count):
        o, l = struct.unpack_from('<II', data, 4 + 8*i)
        ak = _dec_alloc(key, i + 1)
        o ^= ak; l ^= ak
        k = (596947 * (i + 1)) & 0xFFFF
        s = []
        for j in range(l):
            c = struct.unpack_from('<H', data, o + 2*j)[0] ^ k
            k = (k + 18749) & 0xFFFF
            s.append(c)
        out.append(s)
    return key, out

def msg_write_raw(key, msgs):
    count = len(msgs)
    hdr = struct.pack('<HH', count, key)
    table = b''
    body = b''
    pos = 4 + 8*count
    for i, s in enumerate(msgs):
        ak = _dec_alloc(key, i + 1)
        table += struct.pack('<II', (pos + len(body)) ^ ak, len(s) ^ ak)
        k = (596947 * (i + 1)) & 0xFFFF
        for c in s:
            body += struct.pack('<H', c ^ k)
            k = (k + 18749) & 0xFFFF
    return hdr + table + body

def _decomp9(s):
    out = []
    bit = 0
    idx = 1
    while idx < len(s):
        c = (s[idx] >> bit) & 0x1FF
        bit += 9
        if bit >= 15:
            idx += 1
            bit -= 15
            if bit and idx < len(s):
                c |= (s[idx] << (9 - bit)) & 0x1FF
        if c == 0x1FF:
            break
        out.append(c)
    return out

def decode(s):
    """u16 list -> readable text. Terminator 0xFFFF stripped."""
    if s and s[-1] == 0xFFFF:
        s = s[:-1]
    if s and s[0] == 0xF100:
        return '{COMP}' + decode(_decomp9(s))
    r = []
    j = 0
    while j < len(s):
        c = s[j]
        if c == 0xFFFE:
            cmd = s[j+1]; n = s[j+2]
            args = s[j+3:j+3+n]
            r.append('{%04X%s}' % (cmd, ''.join(',%d' % a for a in args)))
            j += 3 + n
            continue
        if c in SPECIAL:
            r.append(SPECIAL[c])
        elif c in C2S:
            ch = C2S[c]
            if ch in ('{', '}', '\\'):
                ch = '\\' + ch
            r.append(ch)
        else:
            r.append('{X%04X}' % c)
        j += 1
    return ''.join(r)

TOK = re.compile(r'\\n|\\r|\\f|\\\{|\\\}|\\\\|\{COMP\}|\{X[0-9A-F]{4}\}|\{[0-9A-F]{4}(?:,\d+)*\}|.', re.S)

def norm(t):
    return t.replace('\n', '\\n').replace('\r', '\\r').replace('\x0c', '\\f')

def encode(t, extra=None):
    """readable text -> u16 list incl. 0xFFFF terminator"""
    t = norm(t)
    if t.startswith('{COMP}'):
        # we store uncompressed; game handles both
        t = t[6:]
    out = []
    for m in TOK.finditer(t):
        x = m.group(0)
        if x == '\\n' or x == '\n': out.append(0xE000)
        elif x == '\\r': out.append(0x25BC)
        elif x == '\\f': out.append(0x25BD)
        elif x in ('\\{', '\\}', '\\\\'): out.append(S2C[x[1]])
        elif x.startswith('{X'): out.append(int(x[2:6], 16))
        elif x.startswith('{') and len(x) > 1:
            parts = x[1:-1].split(',')
            args = [int(a) for a in parts[1:]]
            out += [0xFFFE, int(parts[0], 16), len(args)] + args
        else:
            if extra and x in extra:
                out.append(extra[x])
            elif x in S2C and S2C[x] is not None:
                out.append(S2C[x])
            else:
                raise ValueError('unencodable char %r in %r' % (x, t))
    out.append(0xFFFF)
    return out
