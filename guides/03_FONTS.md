# 03 · Fonts and Romanian diacritics

Romanian needs **ă Ă â Â î Î ș Ș ț Ț** and the low-9 quote **„**. DS fonts (EUR) usually have â Â î Î ç ã ş ”,
but not ă ș ț „. Pick a strategy per font, then verify with `render.py` and an emulator screenshot.

## Strategy A: add new glyphs (NFTR fonts, `bmg` adapter, automatic)
`tools/lib/glyphs.py` (`patch()`), run by `build.py` for every `bmg.font_globs` font:
- **ă/Ă** = a/A + breve built from the circumflex rows of â/Â (the hat's outer pixels become a cup)
- **ș/ț/Ș/Ț** = base letter + comma under the stem, with the depth taken from ç
- **ş ţ Ş Ţ** (cedilla code points) = aliases of the comma glyphs, so text pasted with cedillas still renders
- **„** = ” moved down to the baseline of `,`
- Glyphs go into the last (type-2) CMAP. If a **type-1 CMAP's range already covers one of the new code points**
  (Spirit Tracks: 0x20–0x153 covers ă/Ă), they are folded into that table too (`fold_cmap`), because the game stops at
  the first CMAP whose range contains the character. Without this, ă shows as blank even though the glyph exists.
- LZ10-compressed fonts (Spirit Tracks) are decompressed, patched and recompressed automatically.
- Uncompressed patched copies go to `work/fonts/` (used by `check.py` widths and `render.py`).
- 3bpp fonts get hand-placed breve pixels tuned for Spirit Tracks: **check them visually on a new game.**

If `patch()` fails for a font (missing â, ç or ”), add glyphs by hand with `lib/nftr.py`:
`f = nftr.Font(bytes); f.add('ă', bitmap_rows, width_triplet); f.save(path)`. A bitmap is `f.h` rows of
`f.w` pixel values (0 = transparent, up to `2**bpp-1`). Copy a similar glyph with `f.bitmap(f.map[ord('a')])`
and edit it. `f.show('ă')` prints it as ASCII art.

## Strategy B: redraw unused accented slots (custom charset, `g4` adapter)
When the charset is a fixed table (Gen IV), you can't add code points. Instead, map Romanian letters onto
accented letters Romanian never uses and redraw those glyphs:
`ă→ã`, `Ă→Ã`, `ș→ş`, `Ș→Ş`, `ț→ţ`, `Ț→Ţ` (`RO_EXTRA` in `g4_adapter.py`). `lib/g4font.py patch_font()` replaces the
tilde with a breve (per-font templates in `BREVE`) and builds ţ/Ţ from t/T + the ş cedilla.
- The result shows a **cedilla** shape for ș/ț on Gen IV (glyph reuse). That was accepted for SoulSilver; draw a
  comma instead if you want it exact.
- New font NARC? Run `python3 tools/lib/g4font.py work/ext/<font narc> /tmp/sheets` to dump contact sheets per font,
  then adjust `g4.font_indices` and the `BREVE` templates.
- „ isn't in the Gen IV charset: use `"` (mapped to 0x1B5) or plain „ only if the charmap has it.

## Strategy C: other cases
- **Shift-JIS / Japanese-only font:** you must add Latin glyphs and maybe change the width logic. Find the
  glyph-lookup function with REA, since it often has a hard-coded range table.
- **Fixed-width font:** widths are constant, and `check` should count characters instead of pixels.
- **Tile-based text (no font):** the graphics route (`07_GRAPHICS.md`).

## Verify
1. `python3 tools/render.py /tmp/p.png NAME:KEY` with a string that contains `ăâîșțĂÂÎȘȚ„”`.
2. Build and take an emulator screenshot of the same line in-game (`06_QA_AND_TESTING.md`).
3. `check.py` reports `no glyph in font: …` for any character the measured font lacks.
