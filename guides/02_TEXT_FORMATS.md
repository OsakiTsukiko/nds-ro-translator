# 02 · Text formats and adapters

All tools work on one normalized form: `work/en/<name>.json` and `work/ro/<name>.json` are
`{"0": "text", "1": "text", ...}` (string keys = message index). An **adapter** (`tools/adapters/<format>_adapter.py`)
converts between the game's containers and this form, and knows how to check and rebuild.

## Contract of an adapter
| function | called by | must do |
|---|---|---|
| `dump(c)` | `dump.py` | write `work/en/*.json`; warn per file that does not round-trip |
| `check(name, en, ro)` | `check.py`, `fix.py` | return `[(key, msg)]`: codes, glyphs, width, lines/pages |
| `reflow(name)` | `fix.py` | optional auto-wrap |
| `apply(c, build_dir)` | `build.py` | write rebuilt containers + patched fonts into `build_dir` |

Split ro files: `ro/<name>@<part>.json` are merged with `ro/<name>.json`. Use them when several agents share one big file.

## `bmg`: Nintendo EAD BMG (Zelda PH / ST)
- Header `MESGbmg1`, sections `INF1` (offsets + attributes), `DAT1` (UTF-16LE strings), sometimes `MID1`/`FLW1`
  (kept as-is). Codec: `tools/lib/bmg.py`, byte-identical round-trip on both Zelda games.
- Control code = `0x001A`, length byte, payload → written as `{hexpayload}` (e.g. `{000100}`). Literal braces = `\{` `\}`.
- A newline is a real `\n`. Boxes are `layout.box_lines` lines, and more lines continue on the next page.
- Zelda codes seen: `{000000}Da{000100}Nu` choice list; `{000b..}` pause; `{000a..}` speed; `{000f..}` timed page
  advance (cutscenes: keep on the same page, which `check` enforces); `{fe0000}` player name; `{fe0c/fe0d/fe0e..}`
  numbers; `{ff0000xx}` colour (ignored when comparing); `{0401 00 NN 00 …}` **plural word**: three UTF-16LE forms
  (zero / one / many) separated by NUL. Re-encode the forms in Romanian (puncte/punct, rupii/rupie, ori/dată). Only the
  first 11 hex chars are compared (`bmg.compare_prefix`).
- Config: `message_globs`, `extra_files` (e.g. `data/staff.bmg`), `copy_to_langs` (write RO text into the
  French/German/... folders too, so the console language doesn't matter), `font_globs`, `measure_font`.

## `g4`: Pokémon Gen IV message NARC (SoulSilver)
- One NARC (`data/a/0/2/7` in HG/SS) with ~830 message files, each encrypted with a per-file key
  (codec `tools/lib/g4.py`, charset `tools/lib/charmap_hgss.txt`). D/P/Pt use the same codec. Find their
  NARC paths with `find_text.py` (no hits, since it's encrypted) or REA, then record them.
- Text form: `\n` new line, `\r` wait then scroll, `\f` wait then clear (2-char escapes). Commands `{0100,N,0}` with decimal
  args. `{COMP}` prefix = originally 9-bit compressed (stored back uncompressed, which the game accepts).
- Common commands: `{0100,N,0}` species, `{0101,N,0}` nickname, `{0103,N,0}` player/trainer, `{0106}` move,
  `{0107}` ability, `{0108}` item, `{0102}` type, `{0132..0136}` numbers, `{FF00,X}` colour, `{0200,0}` yes/no follows,
  `{0201,N}` pause, `{0203,X}` cursor x, `{0205}` centre, `{0206}` right-align.
- Boxes show 2 lines. You may add `\r`/`\f` to strings that already have them, but never to menus or descriptions.
  A trailing `\r` must match the English one.
- Name tables (items, moves, abilities, …) have tight limits: list their file numbers in `g4.namelists`, with optional
  per-file pixel limits `namemax` and character limits `namelen`. `inline_files` = text shown inline in menus.
  `allow_wide` = `"file:index"` exceptions verified in-game.
- Romanian letters are mapped onto unused accented slots (ă→ã 0x182, Ă→Ã 0x162, ș→ş 0x1A2, Ș→Ş 0x1A1,
  ț→ţ 0x194, Ț→Ţ 0x174) whose glyphs are redrawn. See `03_FONTS.md`.

## A new format (`custom`)
1. Reverse it with REA (`01_RECON_WITH_REA.md`). Write the spec into `docs/NOTES.md` first.
2. `cp tools/adapters/custom_adapter.py tools/adapters/<fmt>_adapter.py`, set `"format": "<fmt>"`.
3. Codec in `tools/lib/<fmt>.py`: `parse(bytes) -> (container, [str])` and `build(container, [str]) -> bytes`.
   - Represent every non-text unit as a `{...}` token, so nothing is lost and `check` can compare codes.
   - Unknown charset bytes → `{Xnnnn}` tokens (like Gen IV) instead of crashing.
   - **Round-trip test across every file before translating anything.** If the game uses fixed-size slots or
     offsets inside `arm9.bin`/overlays, note it: longer Romanian text may need pointer repointing or a bigger file.
4. Typical traps: strings referenced by absolute offsets from code (search arm9 for the offset values), length
   limits in fixed tables, text inside compressed overlays (`y9.bin` flags; decompress with BLZ / `ndstool`),
   Shift-JIS fonts with no Latin accents, and duplicate text in several languages (patch the one the game loads).
