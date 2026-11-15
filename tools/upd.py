"""Merge a JSON object from stdin into ro/<NAME>.json (or ro/<NAME>@<PART>.json).  usage: upd.py NAME[@PART] < chunk.json"""
import sys, json
from common import *
p = os.path.join(RO, sys.argv[1] + '.json')
d = load(p) if os.path.exists(p) else {}
d.update(json.load(sys.stdin))
save(p, dict(sorted(d.items(), key=lambda kv: int(kv[0]) if kv[0].isdigit() else 0)))
print(sys.argv[1], len(d), 'strings')
