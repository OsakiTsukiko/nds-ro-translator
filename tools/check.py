"""Validate ro/ against en/: control codes, glyph coverage, pixel width, line/page counts, missing strings.
usage: check.py [NAME ...] [--missing] [--quiet]     (no names = every file that has a ro/ translation)
Exit code 1 if any error. Must end with `errors: 0` before a batch counts as done."""
import sys
from common import *
A = adapter()
args = [x for x in sys.argv[1:] if not x.startswith('--')]; fl = set(x for x in sys.argv[1:] if x.startswith('--'))
names = args or sorted(set(n for n in en_names() if ro_parts(n)))
tot = 0
for name in names:
    jerr = []; ro = load_ro(name, jerr)
    for p, m in jerr: print(p, m); tot += 1
    en = load_en(name)
    if '--missing' in fl:
        miss = [k for k, v in en.items() if translatable(v) and k not in ro]
        if miss: print('%s MISSING %d: %s%s' % (name, len(miss), miss[:25], ' ...' if len(miss) > 25 else '')); tot += len(miss)
    errs = A.check(name, en, ro)
    for k, m in errs:
        if '--quiet' not in fl: print('%s:%s %s' % (name, k, m))
    tot += len(errs)
print('errors:', tot)
sys.exit(1 if tot else 0)
