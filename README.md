# DS → Romanian translation template (REA + AI)

A starting point for translating Nintendo DS games into Romanian with an AI agent (Codex or Claude Code + REA MCP).

## Quick start
1. Copy this folder: `cp -r nds-ro-translator my-game-ro && cd my-game-ro`
2. Put your own legally dumped ROM into `rom/` (exactly one `.nds`).
3. Open Codex or Claude Code in the folder and say: *"Read CLAUDE.md and start the translation."*
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
- Codex or Claude Code, with a REA MCP server connected for recon of unknown formats

## Using Codex

Launch Codex CLI from the project root:

```sh
codex "Read CLAUDE.md and start the translation."
```

Codex reads the root [`AGENTS.md`](AGENTS.md), which directs it to the shared instructions in
[`CLAUDE.md`](CLAUDE.md). Both clients follow the same phase guides and use the same Python tools.
To resume a project, ask Codex to read `docs/STATUS.md` and continue the current phase.

Configure REA in Codex separately from Claude Code. For a local stdio server, substitute the executable
and arguments from your REA installation:

```sh
codex mcp add rea -- /absolute/path/to/rea-server <server-arguments>
```

For a REA installation that exposes a Streamable HTTP MCP endpoint, use its actual URL instead:

```sh
codex mcp add rea --url <REA_MCP_URL>
```

Choose the command matching your installation, then run `codex mcp list` to check registration and start a
new Codex session. Ask the agent to confirm REA tools are available before starting recon. Server commands,
arguments and endpoints depend on your REA installation; the examples above contain placeholders.
The Python tools can run without REA once the game's format is understood and configured.

For project-only MCP settings, use `.codex/config.toml` in a trusted project. Keep machine-specific paths
and credentials in your local configuration; this template does not prescribe a server installation or model.
See the official OpenAI documentation for [repository instructions](https://developers.openai.com/codex/guides/agents-md)
and [MCP configuration](https://developers.openai.com/codex/mcp).

## Supported out of the box
| format | games it was proven on | text | fonts |
|---|---|---|---|
| `bmg` | Zelda PH, Zelda ST (EAD titles using MESGbmg1) | UTF-16 BMG | NFTR (raw or LZ10) |
| `g4`  | Pokémon SoulSilver (HG/SS; D/P/Pt with other paths) | encrypted Gen IV msg NARC | Gen IV font NARC |
| `custom` | anything else: write a codec with REA's help | — | — |

Distribute only the `.bps` patch, never the ROM.
