"""Adapter: Nintendo EAD BMG messages (MESGbmg1, UTF-16) + NFTR fonts.
Proven on Zelda: Phantom Hourglass (EU) and Zelda: Spirit Tracks (EU).

Text form in en/ro JSON:  real newline = new line in the box, `{hex}` = raw control code bytes,
`\\{` / `\\}` = literal braces. Boxes hold layout.box_lines lines; extra lines flow onto the next page.
"""
import os, re, glob, json, shutil, collections
from common import *
import bmg, nds, glyphs, nftr

CODE = re.compile(r'\{[0-9a-f]+\}')


def _c(c=None):
    c = c or cfg(); b = c['bmg']; return c, b


def files(c=None):
    """name -> path relative to work/ext. Basename is the key; collisions get the parent dir prefixed."""
    c, b = _c(c)
    paths = []
    for g in b['message_globs']:
        paths += sorted(os.path.relpath(p, EXT) for p in glob.glob(os.path.join(EXT, g)))
    paths += b.get('extra_files', [])
    out = {}
    for p in paths:
        n = os.path.splitext(os.path.basename(p))[0]
        if n in out: n = os.path.basename(os.path.dirname(p)) + '__' + n
        out[n] = p
    return out


def dump(c=None):
    c, b = _c(c)
    fm = files(c); bad = 0; total = 0
    for name, rel in fm.items():
        p = bmg.parse(os.path.join(EXT, rel))
        if bmg.build(p, p['msgs']) != open(os.path.join(EXT, rel), 'rb').read():
            print('WARNING round-trip differs:', rel, '(check bmg.py against this file before translating it)'); bad += 1
        save(os.path.join(EN, name + '.json'), {str(i): m for i, m in enumerate(p['msgs'])})
        total += len(p['msgs'])
    save(os.path.join(EN, '_files.json'), fm)
    print('dumped %d files, %d messages, %d round-trip warnings' % (len(fm), total, bad))


# ------------------------------------------------------------------ fonts
def _font_files(c):
    c, b = _c(c); out = []
    for g in b.get('font_globs', []):
        out += sorted(os.path.relpath(p, EXT) for p in glob.glob(os.path.join(EXT, g)))
    return out


def patch_fonts(c=None, build_dir=None):
    """Add ă Ă ș Ș ț Ț (+ cedilla aliases, „) to every font. Writes uncompressed copies to work/fonts/,
    and the game-format copy (LZ10 again if the original was) into build_dir."""
    c, b = _c(c); os.makedirs(FONTS, exist_ok=True)
    for rel in _font_files(c):
        raw = open(os.path.join(EXT, rel), 'rb').read()
        comp = raw[:1] == b'\x10'
        plain = nds.lz10_decompress(raw) if comp else raw
        try:
            f = glyphs.patch(plain)
        except Exception as ex:
            print('FONT %s not patched (%s): add glyphs by hand, see guides/03_FONTS.md' % (rel, ex)); continue
        data = f.save()
        open(os.path.join(FONTS, os.path.basename(rel)), 'wb').write(data)
        if build_dir:
            open(os.path.join(build_dir, rel), 'wb').write(nds.lz10_compress(data) if comp else data)


_M = {}
def _font():
    if 'f' in _M: return _M['f']
    c, b = _c()
    name = os.path.basename(b.get('measure_font') or (_font_files(c) or [''])[0])
    p = os.path.join(FONTS, name)
    if not name: _M['f'] = None; return None
    if not os.path.exists(p): patch_fonts(c)
    _M['f'] = nftr.Font(p) if os.path.exists(p) else None
    return _M['f']


def cw(ch):
    f = _font()
    if f is None: return 8
    g = f.map.get(ord(ch))
    return None if g is None else f.widths[g][2]


def linew(line):
    c, b = _c(); w = 0
    for tok in re.findall(r'\{[0-9a-f]+\}|\\[{}]|.', line):
        if tok.startswith('{'):
            if any(tok.startswith(p) for p in b['var_code_prefixes']): w += c['layout']['var_width']
            continue
        if tok.startswith('\\'): tok = tok[1]
        x = cw(tok); w += x if x is not None else 10
    return w


# ------------------------------------------------------------------ checks
def _limit(en):
    c, b = _c()
    vp = tuple(b['var_code_prefixes'])
    widest = max([linew(l) for e in en.values() for l in e.split('\n') if not any(p in l for p in vp)] + [0])
    return min(c['layout']['max_width'], widest) + 2


def _codes(s):
    c, b = _c(); out = collections.Counter()
    for x in CODE.findall(s):
        if any(x.startswith(p) for p in b['ignore_codes']): continue
        for p, n in b['compare_prefix'].items():
            if x.startswith(p): x = x[:n]
        out[x] += 1
    return out


def _timed_pages(s):
    c, b = _c(); bl = c['layout']['box_lines']; out = []
    for i, l in enumerate(s.split('\n')):
        for p in b.get('timed_page_codes', []):
            out += [i // bl] * l.count(p)
    return out


def check(name, en, ro):
    """-> list of (key, message). Missing keys are reported by check.py, not here."""
    errs = []; lim = _limit(en)
    for k, r in ro.items():
        if k not in en: errs.append((k, 'key not in English file')); continue
        e = en[k]
        if _codes(e) != _codes(r):
            errs.append((k, 'codes differ: en %s ro %s' % (sorted(CODE.findall(e)), sorted(CODE.findall(r)))))
        elim = max(lim, max([linew(x) for x in e.split('\n')] + [0]))
        for l in r.split('\n'):
            if linew(l) > elim: errs.append((k, 'too wide %dpx > %dpx: %s' % (linew(l), elim, l)))
        bad = set(ch for ch in CODE.sub('', r) if ch not in '\n\\' and cw(ch) is None)
        if bad: errs.append((k, 'no glyph in font: %s' % ''.join(sorted(bad))))
        if _timed_pages(e) != _timed_pages(r): errs.append((k, 'timed page code moved to another page %s -> %s' % (_timed_pages(e), _timed_pages(r))))
    return errs


# ------------------------------------------------------------------ reflow (tools/fix.py)
def _wrap(words, lim):
    lines = []; cur = ''
    for w in words:
        t = (cur + ' ' + w) if cur else w
        if linew(t) <= lim or not cur: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines


def reflow_msg(m, lim):
    """Re-wrap over-wide lines inside box_lines-line pages. -> (new, changed, still_bad)"""
    c, b = _c(); BL = c['layout']['box_lines']; choice = re.compile(b['choice_regex'])
    lines = m.split('\n')
    if all(linew(l) <= lim for l in lines): return m, False, False
    pages = [lines[p:p + BL] for p in range(0, len(lines), BL)]
    if any(t in m for t in b.get('timed_page_codes', [])):  # timed cutscene text: never move text across pages
        out = []; bad = False
        for page in pages:
            if all(linew(l) <= lim for l in page): out += page; continue
            nl = _wrap([w for l in page if l.strip() for w in l.strip().split(' ')], lim)
            if len(nl) <= len(page): out += nl + [''] * (len(page) - len(nl))
            else: out += page; bad = True
        return '\n'.join(out), True, bad
    out = []; carry = []
    for i, page in enumerate(pages):
        if any(choice.search(l) for l in page):
            if carry: out += _wrap(carry, lim); carry = []
            while len(out) % BL: out.append('')
            out += page; continue
        if not carry and all(linew(l) <= lim for l in page): out += page; continue
        words = carry + [w for l in page if l.strip() for w in l.strip().split(' ')]
        nl = _wrap(words, lim); last = i == len(pages) - 1
        if len(nl) <= len(page) or (last and len(nl) <= BL):
            out += nl + [''] * ((BL - len(nl)) if not last else max(0, len(page) - len(nl))); carry = []
        else:
            out += nl[:BL]; carry = ' '.join(nl[BL:]).split(' ')
    while carry:
        nl = _wrap(carry, lim); out += nl[:BL]; carry = ' '.join(nl[BL:]).split(' ') if len(nl) > BL else []
    while out and out[-1] == '': out.pop()
    return '\n'.join(out), True, any(linew(l) > lim for l in out)


def reflow(name):
    en = load_en(name); lim = _limit(en); changed = []
    for p in ro_parts(name):
        ro = load(p); dirty = False
        for k in ro:
            elim = max(lim, max(linew(x) for x in en[k].split('\n')))
            new, ch, bad = reflow_msg(ro[k], elim)
            if ch and new != ro[k]: ro[k] = new; dirty = True
            if bad: print(name, k, 'NEEDS MANUAL FIX:', json.dumps(ro[k], ensure_ascii=False))
        if dirty: save(p, ro); changed.append(p)
    return changed


# ------------------------------------------------------------------ build
def apply(c, build_dir):
    c, b = _c(c); fm = load(os.path.join(EN, '_files.json')); total = done = 0
    for name, rel in fm.items():
        en = load_en(name); ro = load_ro(name)
        total += len(en); done += sum(1 for k in en if k in ro)
        msgs = [ro.get(str(i), en[str(i)]) for i in range(len(en))]
        p = bmg.parse(os.path.join(EXT, rel)); data = bmg.build(p, msgs)
        targets = [rel] + [rel.replace('/English/', '/%s/' % L) for L in b.get('copy_to_langs', []) if '/English/' in rel]
        for t in targets:
            dst = os.path.join(build_dir, t)
            if os.path.exists(os.path.dirname(dst)): open(dst, 'wb').write(data)
    patch_fonts(c, build_dir)
    gfx = os.path.join(WORK, 'gfx_out')
    for g in glob.glob(os.path.join(gfx, '**', '*'), recursive=True):
        if os.path.isfile(g): shutil.copy(g, os.path.join(build_dir, 'data', os.path.relpath(g, gfx)))
    print('translated %d/%d messages' % (done, total))
