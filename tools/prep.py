"""Print the strings of one file that need translation:  key<TAB>english (JSON-escaped, one per line).
usage: prep.py NAME [LO HI]      (LO/HI = integer key range, HI exclusive)
       prep.py NAME --todo       only keys not yet present in ro/"""
import sys, json
from common import *
a = sys.argv[1:]; name = a[0]; lo, hi = 0, 10**9
nums = [x for x in a[1:] if x.lstrip('-').isdigit()]
if len(nums) == 2: lo, hi = int(nums[0]), int(nums[1])
done = load_ro(name) if '--todo' in a else {}
for k, v in load_en(name).items():
    if lo <= int(k) < hi and translatable(v) and k not in done:
        print('%s\t%s' % (k, json.dumps(v, ensure_ascii=False)[1:-1]))
