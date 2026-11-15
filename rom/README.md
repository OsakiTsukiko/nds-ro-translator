# rom/: put the original ROM here

- Place **exactly one** original, untouched `.nds` file in this folder (your own dump).
  For several ROMs, set `"rom": "rom/<file>.nds"` in `project.json`.
- Prefer the **European (EUR) multi-language** release when one exists: it usually carries English *and*
  accented Latin glyphs (â î ç ã ş …) in the fonts, which makes Romanian much easier (see guides/03_FONTS.md).
- Nothing in the toolchain writes here. The ROM is read by `tools/unpack.py` (→ `work/ext/`) and by
  `tools/build.py` (as the BPS patch source).
- `.nds`, `.sav` and `.dsv` files are git-ignored. Never commit or distribute ROMs; release only the `.bps` patch.
- Record the ROM's title, game code and SHA-1 (printed by `unpack.py`) in `docs/STATUS.md`, since the BPS
  patch only applies to that exact dump.
