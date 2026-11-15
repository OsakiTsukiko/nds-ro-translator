# 07 · Text baked into graphics (optional)

Menu buttons, titles and HUD labels are often images, not text. Phantom Hourglass relabelled 45 menu cells
(pause menu, "Save and quit", …). Spirit Tracks left them in English. Decide per project and record it in STATUS.

## Formats involved
- `NCGR` (tiles, 4bpp/8bpp) + `NCLR` (palette) + `NCER` (cells = OAM sprite groups), often packed in an
  LZ10-compressed NARC. Readers in `tools/lib/nds.py` (`ncgr_parse`, `nclr_parse`, `ncer_parse`, `render_cell`).
- Backgrounds use `NSCR` (tile map). Not included: add a parser if needed.

## Tools (from Phantom Hourglass, in `tools/gfx/`)
1. Find the graphic: `python3 tools/gfx/cellsheet.py /tmp/sheets work/ext/data/English/Menu/UI_main/pauseM.bin`
   → a PNG per archive with each cell numbered. Open it with Read.
2. Describe the replacements in `docs/gfx_spec.json`: a list of `[archive, cell, "Romanian text", options]`, where
   `archive` is relative to `work/ext/data/<lang>/Menu/` without `.bin` (adapt `gfxbuild.py` for other layouts).
   Options for `relabel.smart2`: `margin [l,t,r,b]` (area to clear and redraw), `fill`/`outline` (palette indices),
   `bold`, `xref` (column used as background reference), `swap`, `fillrows`, `exclude`, `font` (an NFTR name in
   `work/fonts/`; the default is Zelda's `zeldaDS_15`).
3. `python3 tools/gfx/gfxbuild.py /tmp/preview.png` → writes `work/gfx_out/…` and a preview sheet.
   It prints `DOES NOT FIT` when the text is too long. Shorten it, or reduce margins and bold.
4. `build.py` (bmg adapter) copies `work/gfx_out/**` over `data/` automatically.

## Limits
- Text can only use the pixels inside the existing cell. You can't grow a button.
- Tiles shared between cells change in all of them. Check the whole sheet after building.
- Title logos are usually best left alone (or redrawn by hand in an image editor and re-encoded).
- Use REA (`search_strings` for the archive name in arm9/overlays) when you can't tell which file a screen loads.
