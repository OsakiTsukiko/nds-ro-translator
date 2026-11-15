"""Adapter: Pokémon Gen IV encrypted message NARC + Gen IV fonts.
Proven on Pokémon SoulSilver (EU). HeartGold is the same; Diamond/Pearl/Platinum use the same codec
but other NARC paths (verify with REA before trusting them).

Text form in en/ro JSON (as stored by the game codec):
  `\\n` new line, `\\r` wait+scroll, `\\f` wait+clear page  (written as the 2-char escapes; a real newline is accepted too)
  `{0100,N,0}` commands with decimal args, `{X1234}` unknown char code, `{COMP}` = originally compressed (stored uncompressed).
Romanian letters are not in the charset: they are mapped onto unused accented slots whose glyphs we redraw
(ă→ã, Ă→Ã, ș→ş, ț→ţ ...; see RO_EXTRA and lib/g4font.py).
"""
import os, re, json, shutil, struct
from common import *
from g4 import *
from g4font import patch_font

RO_EXTRA = {'ă': 0x182, 'Ă': 0x162, 'ţ': 0x194, 'Ţ': 0x174, 'ț': 0x194, 'Ț': 0x174,
            'ș': 0x1A2, 'Ș': 0x1A1, 'ş': 0x1A2, 'Ş': 0x1A1, "'": 0x1B3, '"': 0x1B5}


def _c(c=None):
    c = c or cfg(); return c, c['g4']


def dump(c=None):
    c, g = _c(c)
    files, _ = narc_read(open(os.path.join(EXT, g['message_narc']), 'rb').read())
    bad = total = 0
    for n, f in enumerate(files):
        key, msgs = msg_read_raw(f); texts = []
        for s in msgs:
            t = decode(s); texts.append(t); total += 1
            if not t.startswith('{COMP}') and encode(t) != s: bad += 1
        save(os.path.join(EN, '%04d.json' % n), {str(i): t for i, t in enumerate(texts)}, indent=0)
    print('dumped %d files, %d messages, %d bad round-trips' % (len(files), total, bad))


# ------------------------------------------------------------------ measuring
_F = {}
def _font():
    if 'f' not in _F:
        c, g = _c()
        fonts, _ = narc_read(open(os.path.join(EXT, g['font_narc']), 'rb').read())
        _F['f'] = fonts[g.get('measure_font_index', 0)]
        _F['wo'] = struct.unpack_from('<I', _F['f'], 4)[0]   # width table offset
    return _F['f'], _F['wo']


def width(line):
    F, wo = _font(); w = 0; vw = cfg()['layout']['var_width']
    for m in TOK.finditer(line):
        x = m.group(0)
        if x.startswith('{') and len(x) > 1:
            if x.startswith('{01') or x.startswith('{03') or x.startswith('{34'): w += vw   # name/number inserts
            continue
        code = RO_EXTRA.get(x) or S2C.get(x.lstrip('\\'))
        if code: w += F[wo + code - 1]
    return w


def _segs(t): return re.split(r'\\r|\\f', norm(t))
def _lines(t): return [l for s in _segs(t) for l in s.split('\\n')]
def _cmds(t): return sorted(re.findall(r'\{[0-9A-FX][0-9A-F]{3}[^}]*\}', t))


def check(name, en, ro):
    c, g = _c(); fid = int(name.split('@')[0]); errs = []
    enl = [en[str(i)] for i in range(len(en))]
    allow = set(g.get('allow_wide', [])); namemax = {int(k): v for k, v in g.get('namemax', {}).items()}
    namelen = {int(k): v for k, v in g.get('namelen', {}).items()}
    if fid in set(g.get('namelists', [])):   # item / move / ability name tables: tight width + length limits
        mw = max([width(m) for m in enl] + [0]); mc = max([len(m) for m in enl] + [0])
        for k, t in ro.items():
            if k not in en: errs.append((k, 'index out of range')); continue
            t = norm(t)
            try: encode(t, RO_EXTRA)
            except ValueError as ex: errs.append((k, 'ENC ' + str(ex))); continue
            if _cmds(t) != _cmds(en[k]): errs.append((k, 'CMD mismatch'))
            lim = max(mw + 6, namemax.get(fid, 0))
            if width(t) > lim: errs.append((k, 'WIDTH %d>%d (name list): %s' % (width(t), lim, t)))
            ml = max(mc + 2, 16, namelen.get(fid, 0))
            if len(t) > ml: errs.append((k, 'LENGTH %d>%d chars (name list): %s' % (len(t), ml, t)))
            if '\\n' in t and '\\n' not in en[k]: errs.append((k, 'newline not allowed'))
        return errs
    maxw = max([width(l) for m in enl for l in _lines(m) if l.strip()] + [0])
    for k, t in ro.items():
        if k not in en: errs.append((k, 'index out of range')); continue
        e = en[k]; t = norm(t)
        try: encode(t, RO_EXTRA)
        except ValueError as ex: errs.append((k, 'ENC ' + str(ex))); continue
        if _cmds(t) != _cmds(e): errs.append((k, 'CMD mismatch %s vs %s' % (_cmds(t), _cmds(e))))
        ew = max(width(l) for l in _lines(e))
        multi = '\\n' in e or '\\r' in e or '\\f' in e or len(e) > 30
        lim = max(maxw, ew) if multi else max(int(ew * 1.25), ew + 10)
        if not multi and ew <= 72: lim = max(lim, 56, ew + 16)
        if fid in set(g.get('inline_files', [])): lim = maxw + 12
        if '%d:%s' % (fid, k) in allow: lim = max(lim, 64, ew + 28)
        for l in _lines(t):
            if width(l) > lim: errs.append((k, 'WIDTH %d>%d: %s' % (width(l), lim, l)))
        el = max(len(s.split('\\n')) for s in _segs(e)); tl = max(len(s.split('\\n')) for s in _segs(t))
        has_box = '\\r' in e or '\\f' in e
        if has_box and tl > max(el, 2): errs.append((k, 'LINES per box %d>%d' % (tl, max(el, 2))))
        if not has_box:
            if '\\r' in t or '\\f' in t: errs.append((k, 'added \\r/\\f where English has none'))
            allowed = el if (el > 1 or len(e) < 20) else 2
            if tl > allowed: errs.append((k, 'LINES %d>%d' % (tl, allowed)))
        if e.endswith('\\r') != t.endswith('\\r'): errs.append((k, 'trailing \\r must match English'))
    return errs


def reflow(name):
    print('g4: no automatic reflow; re-break lines by hand at phrase boundaries (check.py shows widths).'); return []


# ------------------------------------------------------------------ build
def apply(c, build_dir):
    c, g = _c(c)
    files, btnf = narc_read(open(os.path.join(EXT, g['message_narc']), 'rb').read())
    n = 0; nfiles = 0
    for name in en_names():
        ro = load_ro(name)
        if not ro: continue
        fid = int(name); key, msgs = msg_read_raw(files[fid]); nfiles += 1
        for idx, text in ro.items():
            try: msgs[int(idx)] = encode(text, RO_EXTRA); n += 1
            except Exception as ex: print('SKIP %04d:%s %s' % (fid, idx, ex))
        files[fid] = msg_write_raw(key, msgs)
    open(os.path.join(build_dir, g['message_narc']), 'wb').write(narc_write(files, btnf))
    fonts, fb = narc_read(open(os.path.join(EXT, g['font_narc']), 'rb').read())
    for fi in g['font_indices']:
        fonts[fi] = patch_font(fonts[fi], fi)
    open(os.path.join(build_dir, g['font_narc']), 'wb').write(narc_write(fonts, fb))
    print('applied %d strings across %d files' % (n, nfiles))
