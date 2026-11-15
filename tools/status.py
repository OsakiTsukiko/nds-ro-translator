"""Progress per file: translated / translatable strings. usage: status.py [--todo]  (--todo: only unfinished files)"""
import sys
from common import *
T = D = 0
for n in en_names():
    en = load_en(n); ro = load_ro(n)
    need = [k for k, v in en.items() if translatable(v)]; done = sum(1 for k in need if k in ro)
    T += len(need); D += done
    if need and ('--todo' not in sys.argv or done < len(need)): print('%-24s %5d/%-5d %s' % (n, done, len(need), 'ok' if done == len(need) else ''))
print('TOTAL %d/%d (%.1f%%)' % (D, T, 100.0 * D / max(T, 1)))
