"""Minimal headless libretro frontend (desmume core) for screenshot testing. Needs Pillow + a desmume libretro core.
usage: emu.py ROM SCRIPT OUTPREFIX
SCRIPT: lines "wait N" | "press BTN [frames]" | "shot NAME" | "touch X Y [frames]" | "save PATH" | "load PATH"
example: python3 tools/emu.py out/Game.nds test/boot.txt out/shots/boot   (mash BTN COUNT also works)
"""
import ctypes as C, sys, os
from PIL import Image

CORE = os.environ.get('LIBRETRO_CORE', '/usr/lib/libretro/desmume_libretro.so')
lib = C.CDLL(CORE)

ENV_CB = C.CFUNCTYPE(C.c_bool, C.c_uint, C.c_void_p)
VIDEO_CB = C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
AUDIO_CB = C.CFUNCTYPE(None, C.c_int16, C.c_int16)
AUDIOB_CB = C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
POLL_CB = C.CFUNCTYPE(None)
STATE_CB = C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)

class GameInfo(C.Structure):
    _fields_ = [('path', C.c_char_p), ('data', C.c_void_p), ('size', C.c_size_t), ('meta', C.c_char_p)]
class Variable(C.Structure):
    _fields_ = [('key', C.c_char_p), ('value', C.c_char_p)]

SYSDIR = C.c_char_p(os.path.dirname(os.path.abspath(__file__)).encode())
fmt = [1]
USER = C.c_char_p(b'Player')
LOG_T = C.CFUNCTYPE(None, C.c_int, C.c_char_p)
@LOG_T
def LOGCB(level, msg):
    if os.environ.get('EMUDBG'): print('log', level, msg)
frame = {'img': None}
buttons = set()
touch = {'on': False, 'x': 0, 'y': 0}
VARS = {b'desmume_screens_layout': b'top/bottom', b'desmume_pointer_type': b'touch',
        b'desmume_cpu_mode': b'interpreter'}
_keep = []

@ENV_CB
def env(cmd, data):
    cmd &= 0xFFFF
    if os.environ.get("EMUDBG"): print("env", cmd, flush=True)
    if cmd == 10:  # SET_PIXEL_FORMAT
        fmt[0] = C.cast(data, C.POINTER(C.c_int))[0]; return True
    if cmd in (9, 31):  # SYSTEM_DIRECTORY / SAVE_DIRECTORY
        C.cast(data, C.POINTER(C.c_char_p))[0] = SYSDIR; return True
    if cmd == 15:  # GET_VARIABLE
        v = C.cast(data, C.POINTER(Variable))[0]
        if v.key in VARS:
            s = C.c_char_p(VARS[v.key]); _keep.append(s)
            C.cast(data, C.POINTER(Variable))[0].value = s; return True
        return False
    if cmd == 27:  # GET_LOG_INTERFACE
        C.cast(data, C.POINTER(C.c_void_p))[0] = C.cast(LOGCB, C.c_void_p).value; return True
    if cmd == 38:  # GET_USERNAME
        C.cast(data, C.POINTER(C.c_char_p))[0] = USER; return True
    if cmd == 39:  # GET_LANGUAGE
        C.cast(data, C.POINTER(C.c_uint))[0] = 0; return True
    if cmd == 3:  # GET_CAN_DUPE
        C.cast(data, C.POINTER(C.c_bool))[0] = True; return True
    return False

@VIDEO_CB
def video(data, w, h, pitch):
    if not data: return
    buf = C.string_at(data, pitch * h)
    if fmt[0] == 1:
        frame['img'] = Image.frombuffer('RGBA', (w, h), buf, 'raw', 'BGRA', pitch, 1).convert('RGB')
    else:
        frame['img'] = Image.frombuffer('RGB', (w, h), buf, 'raw', 'BGR;16', pitch, 1)

@AUDIO_CB
def audio(l, r): pass
@AUDIOB_CB
def audiob(d, n): return n
@POLL_CB
def poll(): pass

BTN = {'B': 0, 'Y': 1, 'SELECT': 2, 'START': 3, 'UP': 4, 'DOWN': 5, 'LEFT': 6, 'RIGHT': 7, 'A': 8, 'X': 9, 'L': 10, 'R': 11}
@STATE_CB
def state(port, device, index, id_):
    if port != 0: return 0
    if device == 1:
        return 1 if id_ in buttons else 0
    if device == 6:  # POINTER
        if id_ == 0: return int(touch['x'] / 256 * 65535 - 32768)
        if id_ == 1: return int((touch['y'] + 192) / 384 * 65535 - 32768)
        if id_ == 2: return 1 if touch['on'] else 0
    return 0

lib.retro_set_environment(env)
lib.retro_set_video_refresh(video)
lib.retro_set_audio_sample(audio)
lib.retro_set_audio_sample_batch(audiob)
lib.retro_set_input_poll(poll)
lib.retro_set_input_state(state)
lib.retro_init()

def run(rom, script, prefix):
    gi = GameInfo(rom.encode(), None, 0, None)
    assert lib.retro_load_game(C.byref(gi)), 'load failed'
    lib.retro_serialize_size.restype = C.c_size_t
    for line in open(script):
        p = line.split('#')[0].split()
        if not p: continue
        op = p[0]
        if op == 'wait':
            for _ in range(int(p[1])): lib.retro_run()
        elif op == 'press':
            n = int(p[2]) if len(p) > 2 else 6
            for b in p[1].split('+'): buttons.add(BTN[b])
            for _ in range(n): lib.retro_run()
            buttons.clear()
            for _ in range(6): lib.retro_run()
        elif op == 'mash':  # mash BTN COUNT
            for _ in range(int(p[2])):
                buttons.add(BTN[p[1]])
                for _ in range(4): lib.retro_run()
                buttons.clear()
                for _ in range(12): lib.retro_run()
        elif op == 'touch':
            touch.update(on=True, x=int(p[1]), y=int(p[2]))
            for _ in range(int(p[3]) if len(p) > 3 else 6): lib.retro_run()
            touch['on'] = False
            for _ in range(6): lib.retro_run()
        elif op == 'shot':
            frame['img'].resize((frame['img'].width*2, frame['img'].height*2), Image.NEAREST).save('%s_%s.png' % (prefix, p[1]))
        elif op == 'save':
            n = lib.retro_serialize_size(); b = C.create_string_buffer(n)
            assert lib.retro_serialize(b, C.c_size_t(n)); open(p[1], 'wb').write(b.raw)
        elif op == 'load':
            d = open(p[1], 'rb').read(); b = C.create_string_buffer(d, len(d))
            assert lib.retro_unserialize(b, C.c_size_t(len(d)))

if __name__ == '__main__':
    os.makedirs(os.path.dirname(os.path.abspath(sys.argv[3])), exist_ok=True)
    run(*sys.argv[1:4])
