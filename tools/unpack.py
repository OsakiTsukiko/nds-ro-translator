"""Unpack the ROM from rom/ into work/ext with ndstool and print a quick inventory. Run once per game."""
import os, sys, subprocess, hashlib, shutil, collections
from common import *
rom = rom_path()
if os.path.exists(EXT) and '--force' not in sys.argv:
    sys.exit('work/ext already exists (pass --force to re-unpack; it is the pristine copy, never edit it)')
shutil.rmtree(EXT, ignore_errors=True); os.makedirs(EXT)
e = lambda x: os.path.join(EXT, x)
subprocess.check_call(['ndstool', '-x', rom, '-9', e('arm9.bin'), '-7', e('arm7.bin'), '-y9', e('y9.bin'), '-y7', e('y7.bin'),
                       '-d', e('data'), '-y', e('overlay'), '-t', e('banner.bin'), '-h', e('header.bin')], stdout=subprocess.DEVNULL)
h = open(rom, 'rb').read(0x200)
print('ROM     :', os.path.basename(rom))
print('title   :', h[0:12].decode('ascii', 'replace').strip('\0'), ' code:', h[12:16].decode('ascii', 'replace'))
print('sha1    :', hashlib.sha1(open(rom, 'rb').read()).hexdigest())
magic = collections.Counter(); ext = collections.Counter()
for d, _, fs in os.walk(e('data')):
    for f in fs:
        p = os.path.join(d, f); ext[os.path.splitext(f)[1].lower() or '(none)'] += 1
        b = open(p, 'rb').read(4)
        magic[b.decode('latin1') if all(32 <= x < 127 for x in b) else ('LZ10' if b[:1] == b'\x10' else b.hex())] += 1
print('extensions:', ', '.join('%s=%d' % kv for kv in ext.most_common(15)))
print('magics    :', ', '.join('%s=%d' % kv for kv in magic.most_common(15)))
print('next: find the text + fonts (guides/01_RECON_WITH_REA.md), set project.json, then python3 tools/dump.py')
