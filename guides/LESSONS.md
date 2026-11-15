# Lessons from previous projects

Problems that cost real time in Phantom Hourglass (PH), Spirit Tracks (ST) and SoulSilver (SS). Check here first.

## Text containers
- **BMG file-size field differs between games.** PH writes `0x20 + INF1 + DAT1`; ST stores the full file size rounded
  to 32. `bmg.py` detects which one the original uses (`fullsize`). Unknown BMG variants: check the round-trip warning.
- **BMG empty strings at offset 0.** Some messages point at offset 0 (the shared empty string). Rebuild keeps them at 0,
  otherwise the round-trip isn't byte-identical.
- **ST credits** are in `data/staff.bmg`, outside the Message folder (`bmg.extra_files`).
- **Zelda only reads `data/English`** when the console language is English. Use `copy_to_langs` to make the patch
  language-independent, or document the requirement.
- **Plural codes (`{0401…}`)** embed the word forms inside the code. Re-encode them in Romanian. The checker compares
  only the code header.
- **SS strings with `{COMP}`** are 9-bit compressed in the original. Writing them back uncompressed works.
- **SS big files** (e.g. 0728, 1400+ strings) were split between two agents → use `NAME@PART.json`.

## Fonts
- **Glyph added but not displayed (ST):** a type-1 CMAP covered 0x20–0x153 (including ă), so lookup stopped there and
  never reached the type-2 entries. Fixed by `glyphs.fold_cmap`.
- **ST fonts are LZ10-compressed**, PH fonts are not. The adapter handles both.
- **3bpp message font (ST):** the generic breve looked wrong, so it got hand-placed pixels. Always look at a render.
- **Gen IV has no free code points:** reuse ã/Ã/ş/Ş/ţ/Ţ slots and redraw them (cedilla look for ș/ț remains).
- Add the cedilla code points (ş ţ) as aliases anyway: translators and agents paste them by accident.

## Width and layout
- Measure in pixels with the real font, never in characters (Romanian letters are narrow, "m"/"w" are wide).
- Inserts (`{fe..}`, `{0101,..}`) count as `layout.var_width` px (~6 chars). Names are often longer than "Link".
- SS name tables (items, moves, abilities) are shown in narrow menus: cap them with `namemax` / `namelen`, and
  do a **final terminology pass** (SS `fixnames.py`) that renames in the table and propagates to dialogue only where
  the result still passes `check`.
- Abbreviations made to fit name tables leaked into dialogue ("Rouă Suf."). Grep for `\w+\.` abbreviations in
  dialogue at the end and expand them where there is room (SS `abbr.py` approach).
- Timed cutscene pages (Zelda `{000f}`) must keep each timed code on its page, or the text desyncs from the scene.

## Process
- Translate name tables and the glossary **before** dialogue. Renaming later means touching thousands of strings.
- Parallel agents: one batch per agent, each with its own scratch folder, writing only its own ro files.
  ≤ 6 at once is manageable to review.
- Agents sometimes leave English in long files or switch to cedillas: run `qa.py -v` after every batch.
- Keep `docs/NOTES.md` current. Format details were re-derived several times when they weren't written down.
- Build output can differ by a few bytes between ndstool runs (file ordering) while the content is identical.
  Compare ROMs by unpacking both and diffing trees, not with `cmp`.
