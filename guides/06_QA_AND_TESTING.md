# 06 · QA and testing

## Static checks (every change)
```
python3 tools/check.py NAME            # one file
python3 tools/check.py --missing       # everything, including untranslated strings
python3 tools/qa.py -v                 # leftover English, cedilla ş/ţ
python3 tools/status.py --todo         # unfinished files
```
What `check` catches: missing or changed control codes, characters with no glyph, lines wider than the box
(pixel-measured with the patched font), too many lines per box or page, page breaks added where they can't be,
trailing break mismatches, and timed codes moved to another page (bmg).

What it **cannot** catch: meaning errors, wrong gender or number agreement, text that fits the width but overflows a
differently sized window (signs, shop descriptions, battle boxes), and text drawn by code with its own limits.
Those need screenshots.

## Previews without the emulator (NFTR fonts)
`python3 tools/render.py /tmp/p.png field:1 field:2` draws the boxes with the real patched font
(`{name}` inserts shown as "Nume"). Open the PNG with the Read tool and look at it.

## Emulator screenshots (headless)
`tools/emu.py` drives the DeSmuME libretro core and saves PNGs (top screen above bottom, 2× scale):
```
python3 tools/emu.py out/<name>.nds test/boot.txt out/shots/boot
```
Script commands (one per line, `#` comments):
`wait N` (frames, 60 = 1 s) · `press A|B|X|Y|L|R|START|SELECT|UP|DOWN|LEFT|RIGHT[+…] [frames]` · `mash BTN COUNT` ·
`touch X Y [frames]` (bottom screen, 0–255 × 0–191) · `shot NAME` · `save PATH` / `load PATH` (savestates).

Tips:
- Build a savestate at an interesting point once (`save out/st_shop.state`), then run short scripts from it
  (`load out/st_shop.state` → `press A` → `shot shop1`). This is much faster than replaying from boot.
- To test a specific string, temporarily edit a ro string that appears early (e.g. the first NPC) to the text under test
  in a scratch copy, then build to a different output name. Never leave test text in `work/ro/`.
- Look at each screenshot: clipped last letters, a glyph missing (gap), ă showing as a, text running into a box border,
  English leftovers, and the bottom-screen UI.
- A `.sav` next to the ROM / `.dsv` in `tools/` holds the in-game save, if the game needs one to reach later areas.

## In-game test checklist
- [ ] Title screen, file select, new game, name entry (does the keyboard need ă ș ț? usually not, so leave it)
- [ ] First 10 minutes of dialogue: paging, choices (Da/Nu), name inserts
- [ ] Pause menu, inventory, item descriptions (often a narrower window)
- [ ] Shop: item names + prices + confirmation
- [ ] Battle / combat messages (inserts + plurals)
- [ ] Map and location names
- [ ] Save / load messages
- [ ] A timed cutscene (bmg `{000f}` text)
- [ ] Credits (often a separate font, e.g. `*_endL/_endS`)
- [ ] Baked graphics still in English (list them in STATUS; see `07_GRAPHICS.md`)
