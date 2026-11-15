# 00 · Workflow

Every phase ends with a concrete check. Don't start the next phase until the current one passes.
Write progress into `docs/STATUS.md` as you go.

## Phase 0 · Setup
- Exactly one `.nds` in `rom/`. `python3 tools/unpack.py` prints the title, game code, SHA-1 and an inventory of
  file extensions and magics. Copy that into `docs/STATUS.md`.
- **Done when:** `work/ext/` exists with `arm9.bin`, `data/` and so on.

## Phase 1 · Recon: where is the text, what format, which fonts? (`01_RECON_WITH_REA.md`)
- Use the inventory plus REA to find the message containers and the font files.
- Decide the adapter: `bmg`, `g4`, or a new one copied from `tools/adapters/custom_adapter.py`.
- Fill `project.json` (format, paths, `layout.box_lines`, `layout.max_width`).
- **Done when:** `python3 tools/dump.py` reports **0 round-trip warnings** and `work/en/` looks like readable English.

## Phase 2 · Fonts (`03_FONTS.md`)
- Make sure ă Ă ș Ș ț Ț „ render. `bmg` adds them to NFTR fonts automatically. `g4` redraws unused accented
  slots. Custom formats need their own work.
- **Done when:** a test build shows correct diacritics in-game (an emulator screenshot of a translated line).
  Do this **before** mass translation: if the font can't be fixed, the style rules change.

## Phase 3 · Glossary (`04_TRANSLATION_STYLE.md`)
- Skim `work/en/` (menus, items, places, system messages). Fill `docs/GLOSSARY.md` with game terms, names that
  stay English, and the item/move/place tables. Translate the **name tables first** (items, skills, places):
  dialogue refers to them.
- **Done when:** the glossary covers every recurring term and the name tables pass `check.py`.

## Phase 4 · Translate
- Small game (< ~3k strings): translate file by file yourself:
  `prep.py NAME` → write `work/ro/NAME.json` → `check.py NAME` → fix → repeat.
- Large game: `python3 tools/batches.py 250` → `docs/batches.json`, then run parallel agents with the prompt in
  `05_AGENT_TASK.md` (one batch per agent, at most ~6 at a time). Review their output with `check.py`, `qa.py -v`
  and spot reads.
- `python3 tools/status.py` shows progress.
- **Done when:** `status.py` shows 100%, `check.py --missing` prints `errors: 0`, and `qa.py` shows 0 English and 0 cedillas.

## Phase 5 · Consistency pass
- Grep `work/ro/` for every glossary term and for the English originals of name-table entries, and fix drift
  (e.g. one agent wrote "Rucsac", another "Geantă"). After renaming in a name table, re-run `check.py` on every
  file that mentions it, since longer names can overflow boxes.
- **Done when:** the glossary terms are used uniformly.

## Phase 6 · Build and test (`06_QA_AND_TESTING.md`)
- `python3 tools/build.py --check` → `out/<output_name>.nds` + `.bps`.
- Screenshot tests with `tools/emu.py` (boot, menus, first dialogue, a shop, a battle, the save screen).
- Look for clipped text, missing glyphs (blank squares or gaps), wrong box paging, untranslated baked graphics.
- **Done when:** a human (or you) has played the opening ~30 minutes plus the menus without text bugs.

## Phase 7 · Graphics, optional (`07_GRAPHICS.md`)
- Titles, menu buttons and HUD labels baked into images.

## Phase 8 · Release (`08_RELEASE.md`)
- A `.bps` patch against the documented ROM SHA-1, plus a README listing what is and isn't translated.

## Tool reference
| tool | purpose |
|---|---|
| `unpack.py [--force]` | ROM → `work/ext` + inventory |
| `dump.py` | `work/ext` → `work/en/*.json` (via adapter) |
| `status.py [--todo]` | translated/translatable per file |
| `prep.py NAME [LO HI] [--todo]` | list strings to translate: `key<TAB>english` |
| `show.py NAME [LO HI]` | English and Romanian side by side |
| `upd.py NAME[@PART] < chunk.json` | merge a JSON chunk into a ro file |
| `check.py [NAME..] [--missing] [--quiet]` | validate; exit 1 on errors |
| `fix.py NAME..` | auto re-wrap long lines (bmg), then check |
| `qa.py [-v]` | leftover English, cedilla ş/ţ |
| `batches.py [N]` | split remaining work → `docs/batches.json` |
| `build.py [--check] [--no-bps]` | build ROM + verified BPS |
| `render.py OUT.png NAME:KEY..` | preview text boxes with the game font (NFTR) |
| `emu.py ROM SCRIPT PREFIX` | headless DeSmuME screenshots |
| `lib/g4font.py NARC OUTDIR` | contact sheet of Gen IV font glyphs |
| `gfx/cellsheet.py OUTDIR ARC..` · `gfx/gfxbuild.py [preview.png]` | baked graphics |
