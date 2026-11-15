"""Locate a phrase you saw on screen inside work/ext: plain files, LZ10-compressed files and NARC members,
in ASCII/UTF-8, UTF-16LE and Shift-JIS. First recon step for an unknown game.
usage: find_text.py "Continue" ["Save"] ...        (use short phrases without punctuation; try several)"""
import os, sys
from common import *
import nds

ENCS = [('utf-8', 'utf-8'), ('utf-16le', 'utf-16le'), ('sjis', 'shift_jis')]


def blobs(path):
    d = open(path, 'rb').read(); yield '', d
    if d[:1] == b'\x10' and len(d) > 4:
        try: d2 = nds.lz10_decompress(d); yield ' [LZ10]', d2; d = d2
        except Exception: pass
    if d[:4] == b'NARC':
        try:
            p = nds.narc_parse(d)
            for i, f in enumerate(p['files']):
                nm = p['names'][i] if i < len(p['names']) else str(i)
                yield ' [NARC #%d %s]' % (i, nm), f
                if f[:1] == b'\x10':
                    try: yield ' [NARC #%d %s LZ10]' % (i, nm), nds.lz10_decompress(f)
                    except Exception: pass
        except Exception: pass


phr = sys.argv[1:] or sys.exit(__doc__)
hits = 0
for root, _, fs in os.walk(EXT):
    for f in fs:
        p = os.path.join(root, f); rel = os.path.relpath(p, EXT)
        for tag, b in blobs(p):
            for ph in phr:
                for en, codec in ENCS:
                    try: needle = ph.encode(codec)
                    except Exception: continue
                    o = b.find(needle)
                    if o >= 0:
                        hits += 1; print('%-55s %-9s @0x%06x  %s' % (rel + tag, en, o, ph))
print(hits, 'hits. No hits => text is compressed/encrypted/custom-encoded: see guides/01_RECON_WITH_REA.md step 3')
