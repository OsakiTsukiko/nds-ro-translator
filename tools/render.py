"""Preview Romanian text boxes with the real (patched) game font. NFTR fonts only (bmg adapter).
usage: render.py OUT.png NAME:KEY [NAME:KEY ...]   [FONT=work/fonts/x.nftr env to pick another font]"""
import sys, os, re
from common import *
import nftr
from PIL import Image
c = cfg()
fp = os.environ.get('FONT') or os.path.join(FONTS, os.path.basename(c.get('bmg', {}).get('measure_font') or sorted(os.listdir(FONTS))[0]))
VARS = tuple(c.get('bmg', {}).get('var_code_prefixes', ['{fe']))
F = nftr.Font(fp); BL = c['layout']['box_lines']; W = c['layout']['max_width'] + 8
pal = [(0, 0, 0, 0)] + [(max(0, 200 - i * 40),) * 3 + (255,) for i in range(1, 1 << F.bpp)]
def box(lines, scale=3):
    lh = F.h + 2; img = Image.new('RGBA', (W, BL * lh + 8), (245, 240, 220, 255)); y = 4
    for l in lines[:BL]:
        x = 4
        for tok in re.findall(r'\{[0-9a-fA-F,]+\}|.', l):
            if tok.startswith('{'):
                if not any(tok.startswith(p) for p in VARS): continue
                tok = 'Nume'   # name/number insert placeholder
            for ch in tok:
                g = F.map.get(ord(ch))
                if g is None: continue
                bm = F.bitmap(g); lw, gw, adv = F.widths[g]
                for r in range(F.h):
                    for cc in range(F.w):
                        if bm[r][cc] and 0 <= x + lw + cc < W: img.putpixel((x + lw + cc, y + r), pal[bm[r][cc]])
                x += adv
        y += lh
    return img.resize((img.width * scale, img.height * scale), Image.NEAREST)
imgs = []
for spec in sys.argv[2:]:
    n, k = spec.rsplit(':', 1); ro = load_ro(n)
    t = (ro[k] if k in ro else load_en(n)[k]).replace('\\n', '\n')
    if k not in ro: print(spec, 'not translated yet: rendering English')
    ls = t.split('\n')
    for p in range(0, len(ls), BL): imgs.append(box(ls[p:p + BL]))
H = sum(i.height + 6 for i in imgs); canvas = Image.new('RGBA', (max(i.width for i in imgs), H), (60, 60, 60, 255)); y = 0
for i in imgs: canvas.paste(i, (0, y)); y += i.height + 6
canvas.save(sys.argv[1]); print('wrote', sys.argv[1], len(imgs), 'boxes')
