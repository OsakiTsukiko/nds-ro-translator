"""Shared paths, config and JSON helpers for every tool. Import with `from common import *`."""
import os, sys, json, glob, re, importlib

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, os.path.join(TOOLS, 'lib'))
sys.path.insert(0, os.path.join(TOOLS, 'adapters'))

ROMDIR = os.path.join(ROOT, 'rom')
WORK = os.path.join(ROOT, 'work')
EXT = os.path.join(WORK, 'ext')        # pristine unpacked ROM (never edit)
EN = os.path.join(WORK, 'en')          # English dump (never edit by hand)
RO = os.path.join(WORK, 'ro')          # Romanian translations (the real work product)
FONTS = os.path.join(WORK, 'fonts')    # patched, uncompressed fonts (for measuring/previews)
BUILD = os.path.join(WORK, 'build')    # staging tree (generated)
OUT = os.path.join(ROOT, 'out')
DOCS = os.path.join(ROOT, 'docs')


def cfg():
    return json.load(open(os.path.join(ROOT, 'project.json'), encoding='utf-8'))


def rom_path(c=None):
    c = c or cfg()
    if c.get('rom'):
        p = c['rom'] if os.path.isabs(c['rom']) else os.path.join(ROOT, c['rom'])
        if os.path.exists(p): return p
        sys.exit('project.json "rom" not found: %s' % p)
    roms = sorted(glob.glob(os.path.join(ROMDIR, '*.nds')))
    if not roms: sys.exit('No ROM: put the original .nds into rom/ (see rom/README.md)')
    if len(roms) > 1: sys.exit('Several ROMs in rom/, set "rom" in project.json: %s' % roms)
    return roms[0]


def adapter(c=None):
    c = c or cfg()
    return importlib.import_module(c['format'] + '_adapter')


def load(p):
    return json.load(open(p, encoding='utf-8'))


def save(p, d, indent=1):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=indent)
        f.write('\n')


def en_names():
    return sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(EN, '*.json')) if not os.path.basename(p).startswith('_'))


def load_en(name):
    return load(os.path.join(EN, name + '.json'))


def ro_parts(name):
    """ro/<name>.json plus split parts ro/<name>@<anything>.json (used when a file is shared between agents)."""
    p = [os.path.join(RO, name + '.json')] + sorted(glob.glob(os.path.join(RO, glob.escape(name) + '@*.json')))
    return [x for x in p if os.path.exists(x)]


def load_ro(name, errors=None):
    d = {}
    for p in ro_parts(name):
        try:
            d.update(load(p))
        except Exception as ex:
            if errors is None: raise
            errors.append((p, 'JSON ERROR %s' % ex))
    return d


CODE_ANY = re.compile(r'\{[^}]*\}')


def translatable(text):
    """True if a string contains real letters once control codes / break escapes are removed."""
    s = CODE_ANY.sub('', text).replace('\\n', '').replace('\\r', '').replace('\\f', '')
    return bool(re.search(r'[A-Za-zé]', s))
