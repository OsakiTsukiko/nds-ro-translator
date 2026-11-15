"""Split untranslated work into batches for parallel translation agents -> docs/batches.json
usage: batches.py [STRINGS_PER_BATCH=250]
Each batch is a list of assignments: "NAME" (whole file) or "NAME:LO:HI" (key range; agent writes ro/NAME@LO.json)."""
import sys
from common import *
size = int(sys.argv[1]) if len(sys.argv) > 1 else 250
batches = []; cur = []; n = 0
for name in en_names():
    en = load_en(name); ro = load_ro(name)
    keys = [int(k) for k, v in en.items() if translatable(v) and k not in ro]
    if not keys: continue
    if len(keys) <= size:
        if n + len(keys) > size and cur: batches.append(cur); cur = []; n = 0
        cur.append(name); n += len(keys); continue
    for i in range(0, len(keys), size):        # big file: split into key ranges
        part = keys[i:i + size]; lo, hi = part[0], part[-1] + 1
        if cur: batches.append(cur); cur = []; n = 0
        batches.append(['%s:%d:%d' % (name, lo, hi)])
if cur: batches.append(cur)
save(os.path.join(DOCS, 'batches.json'), batches, indent=None)
print(len(batches), 'batches written to docs/batches.json')
