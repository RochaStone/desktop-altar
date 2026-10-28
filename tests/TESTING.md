# Testing

Everything below was run on 28 Oct 2026, on macOS with Python 3.12.8 and Google Chrome installed.

## 1. Tests
```sh
python3 -m unittest discover -s tests -v
```
Result: **33 tests, all OK** (about 45 seconds, most of it headless Chrome). They cover:
- **Config validation:** both bundled altars pass; an object missing from the drawer, `moon` or `candle_flicker` as words instead of true/false, `daily_line` as one string, a bad screen size and an unknown motif are each reported in plain words; picture names with folders or `..` are refused so a picture can only come from `objects/mine`; more than 16 objects, 7 on one shelf, shelf 4 and a 141-character intention are refused; shelves fill evenly (5 on one shelf, 5 and 5, then 6, 5 and 5).
- **Objects:** the 18 files in `objects/` match the drawer in `build.py` and the drawer in `arrange.html`; every object uses only the eight role colours and has no gradients, filters, embedded images, scripts or ids; re-toning with a made-up palette leaves none of the original colours behind; re-toning swaps colours in one pass (plum and wine can trade places).
- **Style and the inheritance rule:** the fallback order (./style.json, then ~/.rocha-coded/style.json, then the bundled example); a user style borrows only missing palette and font entries; an altar built with a user style carries none of Rocha's lines (I AM SO LUCKY, EVERYTHING WORKS OUT FOR ME, WHAT IF YOUR FOUNDER WORLD WORKS OUT?, whimsy lore, LORE); the blank example with the bundled look shows YOUR WORDS HERE and no stamp; her LORE stamp appears only on her whole example altar; a user's own stamp word appears; bad colours and font names are dropped; motif order is `--motif`, the config, her own style.json, then analog.
- **Moon maths:** the ported Meeus method lands within six minutes of NASA's tables for the new moon of 8 April 2024 18:21 UTC and the full moon of 13 January 2025 22:27 UTC; the drawn shape is a full disc at full moon and nothing at new moon; south of the equator mirrors it; the live page gets 31 new moons, the first one before now; the daily line uses the same date sum as the page.
- **Build output:** `out/` holds `altar.html`, `index.html` and `altar.widget/` (`altar.html` and `index.jsx`); the page has no external script and reaches only fonts.googleapis.com and fonts.gstatic.com; neither page uses `innerHTML`, `console.log` or `text-shadow`; an intention of `</script><script>alert(1)</script>` stays text; a picture in `objects/mine` is inlined as a data URI, and a missing one stops the build kindly; the CLI prints "A few things to fix"; the PNG comes back at exactly 1440x900.
- **Headless render, all three motifs, at 2560x1600 and 1440x900:** her altar, then a full altar (16 objects, every one labelled, a 112-character intention). Each page reports its motif, has no sideways scroll, keeps the whole altar inside the screen on both axes, shows every object and the moon, and keeps its signature (analog: the washi tape; cyberpunk: the prompt line; y2k-blog: the visitor counter).
- **Light and snuff, and the painted drawer:** `painted/<name>.png` and `mine/<name>.png` validate, while `..`, folders, capitals and non-PNG painted names are refused; with an empty painted folder her example altar falls back to the 11 flat drawings; a painted PNG next to the config is used, its neighbour without a file falls back, and a painted name with no drawing of the same name stops the build kindly; her altar has three click targets (two candles and the incense). In headless Chrome a candle starts lit, a click snuffs it (`aria-pressed` false, saved to localStorage), the snuff survives a reload, and Enter lights it again.
- **arrange.html:** the page opens in headless Chrome, three drawer objects are clicked onto the shelf, the form is filled and save is pressed; the JSON it would download passes `validate_config` and holds exactly those objects, the motif and the daily lines.

## 2. Looked at by eye
The README images, the three motifs at 1600x1000 and 1440x900, the blank example and the 16-object altar were rendered and checked by eye.
Two real bugs were caught that way and fixed: the candle glow sat above the flames in cyberpunk, and the blank example picked up Rocha's LORE stamp from the bundled style.
Two more were caught by the tests: an empty shelf counted as "no shelf" when spreading objects, and shelves filled six, six, four instead of six, five, five.

## 3. What was not verified
- Plash, Lively Wallpaper and Übersicht were not installed on the test machine. The steps in the README follow their own websites and readmes (Plash: "Show a remote or local website"; Lively: "drag'n'drop media or webpages"). The Übersicht widget follows its documented widget format and was not run.
- Clicking through Plash Browsing Mode, Lively's interactive setting or Übersicht was not tried, for the same reason. The click itself is tested in Chrome.
- The painted set itself does not exist yet, so painted cutouts were tested with a 1-pixel PNG. Her example falls back to the drawings until the set lands.
- The live moon and daily line update while the page stays open; that script runs in a browser, and only its still mode (used for the PNG) is covered by the render tests.
- Windows: `build.py` uses only the standard library and finds Chrome in its usual Windows folders, and was run on macOS only.
