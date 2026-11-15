# 08 · Release

1. `python3 tools/check.py --missing` → `errors: 0`; `python3 tools/qa.py` → 0 / 0.
2. `python3 tools/build.py --check` → `out/<output_name>.nds` and `out/<output_name>.bps`.
   The BPS is created against the ROM in `rom/` and verified by re-applying it (`tools/lib/bps.py`).
3. Smoke-test the **patched** ROM: apply the `.bps` to a fresh copy of the original with any BPS patcher (Flips,
   Rom Patcher JS, or `python3 -c "import sys;sys.path.insert(0,'tools/lib');import bps;..."`) and compare it to `out/*.nds`.
4. Release notes (`out/README.txt`):
   - game, region, game code, **SHA-1 of the source ROM** (from `unpack.py`)
   - what is translated (dialogue, menus, items, …) and what is not (baked graphics, title logo, credits, …)
   - console language requirement (e.g. Zelda: text only in `data/English`, unless `copy_to_langs` was used)
   - known issues
5. Distribute **only the `.bps`** and the notes. Never the ROM.
6. Archive the project state: commit `work/ro/`, `docs/`, `project.json` and any tool changes to git
   (`work/ext`, `work/build`, `out/`, ROMs are ignored). Mark the version in `docs/STATUS.md`.
