import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from g4 import narc_read
from PIL import Image
def glyph_px(f, idx, msb=False):
    hs, wo, n = struct.unpack_from('<III', f, 0)
    g = f[hs + 64*idx: hs + 64*idx + 64]
    px = [[0]*16 for _ in range(16)]
    for t in range(4):
        tx, ty = (t % 2)*8, (t//2)*8
        for b in range(16):
            byte = g[t*16+b]
            for k in range(4):
                v = (byte >> (6-2*k)) & 3 if msb else (byte >> (2*k)) & 3
                p = b*4 + k
                px[ty + p//8][tx + 7 - p%8] = v
    return px
def sheet(f, codes, path, msb=False):
    pal = [(255,255,255),(0,0,0),(160,160,160),(255,0,0)]
    im = Image.new('RGB', (len(codes)*18, 18), (0,128,255))
    for i, c in enumerate(codes):
        px = glyph_px(f, c-1, msb)
        for y in range(16):
            for x in range(16):
                im.putpixel((i*18+x+1, y+1), pal[px[y][x]])
    im.resize((im.width*4, im.height*4), Image.NEAREST).save(path)
if __name__ == '__main__':
    # usage: g4font.py <font narc> <out dir>  -> contact sheets of the Romanian-relevant glyphs per font
    fs,_ = narc_read(open(sys.argv[1],'rb').read())
    codes = [0x145,0x146,0x158,0x162,0x182,0x174,0x194,0x1A1,0x1A2,0x181,0x18D,0x12B]
    for fi in range(len(fs)):
        try: sheet(fs[fi], codes, os.path.join(sys.argv[2], 'font%d.png' % fi))
        except Exception as ex: print('font', fi, 'skipped:', ex)

def glyph_bytes(px):
    g = bytearray(64)
    for t in range(4):
        tx, ty = (t % 2)*8, (t//2)*8
        for b in range(16):
            byte = 0
            for k in range(4):
                p = b*4 + k
                byte |= (px[ty + p//8][tx + 7 - p%8] & 3) << (2*k)
            g[t*16+b] = byte
    return bytes(g)

def set_glyph(f, code, px, width):
    hs, wo, n = struct.unpack_from('<III', f, 0)
    f[hs + 64*(code-1): hs + 64*code] = glyph_bytes(px)
    f[wo + code - 1] = width

SYM = {' ':0, '.':1, '#':2, '+':3}
# breve templates per font: (lower_rows_start, upper_rows_start, rows)
BREVE = {
    0: ["+.#+.#", "+#..##", "++##++"],
    1: ["+.#+.#", "+#..##", "++##++"],
    10: [".#+.#", "#..##", "+##++"],
    2: ["  +  + ", " +#.+#.", "  +#.. "],
    4: [" ######", " #.##.#", " ##..##"],
}

def find_rows_diff(a, b):
    return [y for y in range(16) if a[y] != b[y]]

def patch_font(f, fi):
    f = bytearray(f)
    hs, wo, n = struct.unpack_from('<III', f, 0)
    W = lambda c: f[wo + c - 1]
    G = lambda c: [row[:] for row in glyph_px(f, c - 1)]
    # --- ă / Ă : replace tilde rows of ã / Ã with breve
    for tilde_code, base_code in ((0x182, 0x145), (0x162, 0x12B)):
        g, base = G(tilde_code), G(base_code)
        # tilde rows = top rows that have content before base body starts (first 3 non-empty rows)
        rows = [y for y in range(16) if any(g[y][x] for x in range(16))][:3]
        tpl = BREVE[fi]
        for r, y in zip(tpl, rows):
            for x in range(16):
                g[y][x] = SYM[r[x]] if x < len(r) else 0
        set_glyph(f, tilde_code, g, W(tilde_code))
    # --- ţ / Ţ : base t/T + cedilla taken from ş - s
    s, sc = G(0x157), G(0x1A2)
    ced = {(y, x): sc[y][x] for y in range(16) for x in range(16) if sc[y][x] != s[y][x]}
    ced_text_x = [x for (y, x), v in ced.items() if v == 1]
    cx = sum(ced_text_x) / len(ced_text_x)
    for tgt, base_code in ((0x194, 0x158), (0x174, 0x13E)):
        g = G(base_code)
        # centre of the base glyph's lowest text row
        ys = [y for y in range(16) if any(v == 1 for v in g[y])]
        bottom = ys[-1]
        bx = [x for x in range(16) if g[bottom][x] == 1]
        # for 't' use stem: column with most text pixels
        cols = [sum(1 for y in range(16) if g[y][x] == 1) for x in range(16)]
        stem = cols.index(max(cols))
        dx = round(stem - cx + 0.5)
        sbottom = max(y for y in range(16) if any(v == 1 for v in s[y]))
        dy = bottom - sbottom
        for (y, x), v in ced.items():
            ny, nx = y + dy, x + dx
            if 0 <= ny < 16 and 0 <= nx < 16 and (g[ny][nx] != 1 or v == 1):
                if v == 0 and g[ny][nx] != 0:
                    continue
                g[ny][nx] = v
        set_glyph(f, tgt, g, max(W(base_code), W(tgt)))
    return bytes(f)
