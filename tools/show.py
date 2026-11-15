"""Show English (and Romanian if present) side by side.  usage: show.py NAME [LO HI]"""
import sys, json
from common import *
n = sys.argv[1]; lo = int(sys.argv[2]) if len(sys.argv) > 2 else 0; hi = int(sys.argv[3]) if len(sys.argv) > 3 else 10**9
en = load_en(n); ro = load_ro(n)
for k, v in en.items():
    if lo <= int(k) < hi and translatable(v):
        print('#%s EN %s' % (k, json.dumps(v, ensure_ascii=False)))
        if k in ro: print('#%s RO %s' % (k, json.dumps(ro[k], ensure_ascii=False)))
