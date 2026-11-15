"""Auto re-wrap over-wide lines (adapter permitting), then re-check.  usage: fix.py NAME [NAME ...]"""
import sys, subprocess
from common import *
A = adapter()
for n in sys.argv[1:]: A.reflow(n)
subprocess.call([sys.executable, os.path.join(TOOLS, 'check.py')] + sys.argv[1:])
