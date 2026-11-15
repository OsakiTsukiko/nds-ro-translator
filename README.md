# DS → Romanian translation template (REA + AI)

A starting point for translating Nintendo DS games into Romanian with an AI agent (Claude Code + REA MCP).

## Quick start
1. Copy this folder: `cp -r nds-ro-translator my-game-ro && cd my-game-ro`
2. Put your own legally dumped ROM into `rom/` (exactly one `.nds`).
3. Open Claude Code in the folder and say: *"Read CLAUDE.md and start the translation."*
   The agent follows `guides/00_WORKFLOW.md`:
   recon with REA → configure `project.json` → dump → fonts → translate → check → build → test → release.

Manual commands (from the project root):
```
python3 tools/unpack.py            # rom/*.nds -> work/ext (+ inventory)
python3 tools/dump.py              # English text -> work/en/*.json
python3 tools/status.py            # progress
python3 tools/prep.py NAME         # strings still to translate in one file
python3 tools/check.py NAME        # validate a translation (must say errors: 0)
python3 tools/build.py             # -> out/<output_name>.nds + .bps
python3 tools/emu.py out/X.nds test/boot.txt out/shots/boot   # headless screenshots
```

## Requirements
- Python 3.9+ with Pillow (`pip install pillow`)
- `ndstool` (devkitPro) on PATH
- For screenshot tests: a desmume libretro core (`/usr/lib/libretro/desmume_libretro.so` or `LIBRETRO_CORE=...`)
- REA MCP server connected to Claude Code (for recon of unknown formats)

## Supported out of the box
| format | games it was proven on | text | fonts |
|---|---|---|---|
| `bmg` | Zelda PH, Zelda ST (EAD titles using MESGbmg1) | UTF-16 BMG | NFTR (raw or LZ10) |
| `g4`  | Pokémon SoulSilver (HG/SS; D/P/Pt with other paths) | encrypted Gen IV msg NARC | Gen IV font NARC |
| `custom` | anything else: write a codec with REA's help | — | — |

Distribute only the `.bps` patch, never the ROM.
