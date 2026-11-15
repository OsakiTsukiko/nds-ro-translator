# 05 · Parallel translation agents

For large games (SoulSilver had ~41k translatable strings in 829 files), split the work and run several
translation agents. The coordinating agent:
1. Finishes recon, fonts and **the glossary and name tables first** (agents need fixed terminology).
2. `python3 tools/batches.py 250` → `docs/batches.json` (a list of batches; each item is `NAME` or `NAME:LO:HI`).
3. Starts at most ~6 agents at once, one batch each, with the prompt below (fill in the `<…>` parts).
4. After each agent: `python3 tools/check.py --missing <names>`, `python3 tools/qa.py -v`, read ~10 random strings
   per batch. Re-assign or fix bad batches. Update `docs/STATUS.md`.
5. When everything is done: the consistency pass (`00_WORKFLOW.md` phase 5).

---
## Prompt template

You translate <GAME> (Nintendo DS) text from English into natural, fluent Romanian for a fan translation.
Project root: <ABSOLUTE PATH>. `cd` there before every command.

1. Read `guides/04_TRANSLATION_STYLE.md` and `docs/GLOSSARY.md` fully. Whenever the English mentions a named item,
   skill, place or character, use exactly the Romanian name from the glossary or name tables
   (`grep -i "Potion" docs/*.tsv docs/GLOSSARY.md`).
2. Your assignments: <BATCH, e.g. ["field", "castle:0:250"]>. For each one:
   - `python3 tools/prep.py NAME` (or `python3 tools/prep.py NAME LO HI` for a range) lists the strings.
   - Translate **all** listed strings. Whole file → write `work/ro/NAME.json`. Range → write `work/ro/NAME@LO.json`
     so you don't collide with the agent holding the other half.
   - Write the JSON with a Python script kept in your own folder `<SCRATCH>/agent_<FIRST NAME>/` (other agents share
     the scratch dir, so don't reuse generic names): a dict `{key: "romanian"}` dumped with
     `json.dump(d, f, ensure_ascii=False, indent=1)`. For big files, do it in chunks (load, update, dump).
   - `python3 tools/check.py NAME` (whole files also with `--missing`). Fix **every** error and re-run until `errors: 0`.
     For "too wide" errors: re-break the line at a natural phrase boundary, or shorten the wording.
3. Only write files in `work/ro/` (and your scratch folder). Never edit `tools/`, `work/en/`, `docs/`, or other agents' files.
4. Quality: idiomatic Romanian a native localizer would write. Consistent terminology, correct diacritics with
   comma below (ș ț, not ş ţ), quotes „…”, keep personality and humour. Don't leave English sentences untranslated
   (names stay English per the glossary). Leave out debug, test or Japanese strings.
5. When finished, reply in ≤ 10 lines: files done, final `errors:` count, terms you were unsure about
   (so the glossary can be updated).
