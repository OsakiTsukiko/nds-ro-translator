"""Adapter skeleton for a text format the template does not know yet.

Copy this file to adapters/<fmt>_adapter.py, set "format": "<fmt>" in project.json and fill in the
functions. Work out the format with REA first (guides/01_RECON_WITH_REA.md, guides/02_TEXT_FORMATS.md)
and record what you learn in docs/NOTES.md.

Contract (the generic tools call exactly these):
  dump(c)                  read work/ext, write work/en/<name>.json = {"0": text, "1": text, ...}
                           (save extra lookup data as work/en/_*.json; names starting with "_" are ignored)
  check(name, en, ro)      -> [(key, message), ...] for codes / glyphs / width / line-count problems
  reflow(name)             optional auto re-wrap of ro/<name>*.json; return list of changed paths
  apply(c, build_dir)      write translated containers + patched fonts into build_dir (a copy of work/ext)

Rules that kept the previous projects safe:
  * dump must ROUND-TRIP: encode(decode(x)) == x for every string, and rebuilding an untouched file must be
    byte-identical. Print a warning per file when it is not, and fix the codec before translating.
  * Represent control codes as {hex} or {CMD,args} tokens that survive JSON and that check() can compare.
  * Never write into work/ext.
"""
import os, re
from common import *

CODE = re.compile(r'\{[^}]*\}')


def dump(c=None):
    raise NotImplementedError('write the decoder for this game (see guides/02_TEXT_FORMATS.md)')


def width(line):
    """Pixel width of one line. Replace with real font metrics (font width table) as soon as you have them."""
    return len(CODE.sub('', line)) * 6


def check(name, en, ro):
    c = cfg(); errs = []
    for k, r in ro.items():
        if k not in en: errs.append((k, 'key not in English file')); continue
        e = en[k]
        if sorted(CODE.findall(e)) != sorted(CODE.findall(r)): errs.append((k, 'codes differ'))
        lim = max([c['layout']['max_width']] + [width(l) for l in e.split('\n')])
        for l in r.split('\n'):
            if width(l) > lim: errs.append((k, 'too wide %d>%d: %s' % (width(l), lim, l)))
    return errs


def reflow(name):
    print('custom: no reflow implemented'); return []


def apply(c, build_dir):
    raise NotImplementedError('write the encoder / container rebuild for this game')
