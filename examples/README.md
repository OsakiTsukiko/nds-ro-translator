# Example configurations

Working `project.json` settings from the finished projects. Copy the closest one over `project.json` and adjust.
The two Zelda ones and the SoulSilver one were re-validated against the original projects when this template was built.

| file | game | adapter |
|---|---|---|
| `zelda-phantom-hourglass.project.json` | Zelda PH (EUR) | bmg (uncompressed NFTR fonts, + `tools/gfx` menu relabels in the original project) |
| `zelda-spirit-tracks.project.json` | Zelda ST (EUR) | bmg (LZ10 fonts, `data/staff.bmg` credits) |
| `pokemon-soulsilver.project.json` | Pokémon SS (EUR) | g4 (name-table limits tuned in-game) |

HeartGold should work with the SoulSilver config (same paths). Diamond/Pearl/Platinum need other NARC paths
and font indices: confirm them first (guides/01_RECON_WITH_REA.md).
