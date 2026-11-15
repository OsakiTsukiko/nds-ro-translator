# Status

> Update at the end of every session: phase, what was done, what is next, open questions.

## ROM
| field | value |
|---|---|
| title / game code | |
| region | |
| SHA-1 | |
| format adapter | |

## Phase checklist
- [ ] 0 Setup: ROM unpacked
- [ ] 1 Recon: text + fonts identified, `dump.py` round-trips (0 warnings)
- [ ] 2 Fonts: diacritics verified in-game (screenshot)
- [ ] 3 Glossary + name tables
- [ ] 4 Translation: `status.py` 100%, `check.py --missing` 0 errors, `qa.py` clean
- [ ] 5 Consistency pass
- [ ] 6 Build + in-game test checklist
- [ ] 7 Graphics (optional / skipped)
- [ ] 8 Release: `.bps` + notes

## Progress
(paste `python3 tools/status.py | tail -1` here)

## Log
- YYYY-MM-DD: …
- 2026-11-16: Read project instructions and workflow. No project task specified; phase checklist unchanged. Next step: clarify the requested work.
- 2026-11-16: Added Codex repository instructions, launch/resume and REA MCP setup documentation, and client-neutral REA discovery guidance. Checked MCP command syntax against the installed Codex CLI and reviewed documentation links and whitespace. Translation phases are unchanged; next step is ROM setup for a chosen game. REA connectivity and in-game behavior were not tested for this documentation change.

## Open questions / known issues
-
