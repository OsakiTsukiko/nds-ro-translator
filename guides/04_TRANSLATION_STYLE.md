# 04 · Translation style (English → Romanian)

The bar: **natural, fluent Romanian, the way a professional localizer would write it for a Nintendo game.** Not word-for-word.
Consistency beats variety. The game-specific terms live in `docs/GLOSSARY.md`, which always wins over this file.

## Language
- Mandatory diacritics: **ă â î ș ț** / **Ă Â Î Ș Ț**, with **comma below** (U+0219/U+021B), never cedilla ş ţ.
  `qa.py` flags cedillas. Spelling: "â" inside words (cânt, România), "î" at the start and end (înapoi, a urî)
  and in compounds (neîntrerupt).
- Quotes: „text” (opening low „, closing high ”). Ellipsis stays `...` (or `…` if the font has it).
- Address: **tu** between kids, friends, rivals and most NPCs. **dumneavoastră** for staff (nurses, shopkeepers, receptionists,
  officials) when the English is polite. Royalty and formal characters may use formal forms consistently.
- Keep character voice: a rude rival stays rude, an old man rambles, a pirate sounds like a pirate. Adapt puns and jokes
  rather than translating them literally. Onomatopoeia and creature cries ("Pikaaa!") stay.
- Avoid gender agreement with variables. `{name}` may be a boy, a girl or a Pokémon: "{name} a leșinat!" is fine,
  "frumoasa {name}" is not. Rephrase to avoid adjectives on inserts.
- Plurals with number inserts: "1 rupie / 2 rupii / 20 de rupii". When the count is variable and there is no plural
  code, prefer forms that stay correct ("Rupii: {n}", "x{n}").
- UI verbs in menus: short imperative forms (Salvează, Continuă, Înapoi, Renunță, Da/Nu, Confirmă).
  Keep menu items within the English width: abbreviate with a period if needed (Apăr. Sp.) and list abbreviations in the glossary.

## What stays English
- Proper names of characters, creatures/species and most place names (decide once and record it in the glossary).
  Generic parts can be translated: "Route 29" → "Ruta 29", "Professor Elm" → "Profesorul Elm".
- Brand and console terms: Nintendo, DS, Wi-Fi, Nintendo WFC.
- Names the game shows as logos or graphics you won't redraw (stay consistent with them).

## Formatting rules (the checker enforces most)
- Control codes `{...}`: same codes, same count. You may move them to fit Romanian word order.
- Line breaks: Romanian is ~15–25% longer. Re-break at phrase boundaries, never mid-phrase. bmg: run `fix.py NAME` to auto-wrap,
  then fix whatever it reports as `NEEDS MANUAL FIX` by shortening.
- Don't add page breaks to menus, item descriptions or one-line UI strings. Dialogue may get extra pages where the format allows.
- Choice prompts (`{000000}Da{000100}Nu`, `{0200,0}`) must keep their structure and page.
- Timed cutscene text (`{000f..}` in Zelda) must keep each timed code on the same page.
- Leave out debug, test or Japanese-only strings (when unsure, check in-game whether they appear).
- Strings that look identical in several files (system messages) must be translated identically. Grep `work/ro/` before inventing.

## Writing files
- `python3 tools/prep.py NAME` prints `key<TAB>english` with JSON escapes. Copy escapes exactly
  (`\n` is a newline; Gen IV `\\r`/`\\f` in JSON are the 2-char codes `\r`/`\f`).
- Write JSON with a small Python script (`json.dump(d, f, ensure_ascii=False, indent=1)`) or `tools/upd.py NAME < chunk.json`.
  For big files, write in chunks of ~100 strings.
- Then `python3 tools/check.py NAME` until `errors: 0`.

## Common terms (generic, override in the glossary)
| EN | RO |
|---|---|
| Save / Load | Salvează / Încarcă |
| Continue / New Game | Continuă / Joc nou |
| Options / Settings | Opțiuni / Setări |
| Yes / No | Da / Nu |
| Back / Cancel / Quit | Înapoi / Anulează / Ieși |
| Item / Items | Obiect / Obiecte |
| Map | Hartă |
| Quest / Mission | Misiune |
| Level / Lv. | Nivel / Nv. |
| HP | PV (Puncte de Viață) |
| Attack / Defense / Speed | Atac / Apărare / Viteză |
| Shop / Buy / Sell | Magazin / Cumpără / Vinde |
| Treasure / Chest | Comoară / Cufăr |
| Key / Boss Key | Cheie / Cheia Șefului |
| Dungeon | Temniță (Zelda) / peșteră, după context |
| Heart Container / Piece of Heart | Recipient de Inimă / Fragment de Inimă |
| Rupee(s) | rupie / rupii |
| Got X! | Ai obținut X! |
| You can't do that now. | Nu poți face asta acum. |
| Saving... Don't turn off the power. | Se salvează... Nu opri consola. |
