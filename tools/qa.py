"""Find strings in ro/ that still look English, and Romanian text written with cedillas (ş ţ instead of ș ț).
usage: qa.py [-v]"""
import sys, re
from common import *
EN_WORDS = set("the you your and is was have has with what this that for will can not don't it's i'm you're please would like here there just".split())
sus = ced = 0
for n in en_names():
    for k, v in load_ro(n).items():
        t = CODE_ANY.sub(' ', v).replace('\\n', ' ').replace('\\r', ' ').replace('\\f', ' ')
        w = [x.lower().replace('’', "'") for x in re.findall(r"[A-Za-zăâîșțĂÂÎȘȚ’']+", t)]
        if len(w) >= 3 and sum(x in EN_WORDS for x in w) >= 2:
            sus += 1
            if '-v' in sys.argv: print('EN?  %s:%s %s' % (n, k, v[:100].replace('\n', '\\n')))
        if re.search('[şţŞŢ]', v):
            ced += 1
            if '-v' in sys.argv: print('CED  %s:%s %s' % (n, k, v[:100].replace('\n', '\\n')))
print('suspicious English strings:', sus, ' cedilla diacritics:', ced)
