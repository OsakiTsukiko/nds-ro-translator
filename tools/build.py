"""Build the Romanian ROM:  work/ext -> work/build (+ translations, fonts, graphics) -> out/<output_name>.nds + .bps
usage: build.py [--no-bps] [--check]   (--check: refuse to build while check.py reports errors)"""
import os, sys, shutil, subprocess
from common import *
import bps
c = cfg(); A = adapter(c)
if '--check' in sys.argv and subprocess.call([sys.executable, os.path.join(TOOLS, 'check.py'), '--quiet']):
    sys.exit('check.py reports errors; fix them or build without --check')
shutil.rmtree(BUILD, ignore_errors=True); shutil.copytree(EXT, BUILD, symlinks=True)
A.apply(c, BUILD)
os.makedirs(OUT, exist_ok=True)
rom = os.path.join(OUT, c['output_name'] + '.nds'); b = lambda x: os.path.join(BUILD, x)
subprocess.check_call(['ndstool', '-c', rom, '-9', b('arm9.bin'), '-7', b('arm7.bin'), '-y9', b('y9.bin'), '-y7', b('y7.bin'),
                       '-d', b('data'), '-y', b('overlay'), '-t', b('banner.bin'), '-h', b('header.bin')], stdout=subprocess.DEVNULL)
print('wrote', rom)
if '--no-bps' not in sys.argv:
    src = open(rom_path(c), 'rb').read(); tgt = open(rom, 'rb').read()
    p = bps.create(src, tgt); assert bps.apply(src, p) == tgt
    open(rom[:-4] + '.bps', 'wb').write(p); print('wrote', rom[:-4] + '.bps', len(p), 'bytes (verified)')
