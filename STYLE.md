# style.json

One file holds your look. Every Rocha Coded tool reads the same file, so you make it once.

## Where it goes
The tool looks in this order and uses the first one it finds:
1. `style.json` in the folder you are working in (your Cowork folder, or wherever you run Claude Code)
2. `~/.rocha-coded/style.json`, to use one look across every project
3. `examples/style.rocha-coded.json`, the bundled example (Rocha's look)

Start from `style.example.json`: copy it to `style.json` and fill it in. Or ask Claude to make one with you.

Your words live somewhere else. Your altar's name, intention, objects and daily lines live in `altar.config.json`.
`style.json` is colour, type and motif.

## The keys
| Key | What to put there | Used by this tool |
|---|---|---|
| `name`, `owner`, `handle`, `site` | your brand, your name, your handle, your site | no (your altar takes its name from `altar.config.json`) |
| `palette.hero` | your ground colour, the deep one, as a hex code like `#50163C` | the room behind the altar |
| `palette.plum` | a deep shade | the y2k title bar, the cyberdeck desk, the deep parts of objects |
| `palette.wine` | a second deep colour | shelves, the cyberdeck bezel, the dark side of the moon |
| `palette.accent` | your one bright accent | washi tape, flames, crystals, the blinking cursor |
| `palette.paper` | a light paper colour | cream shelves, candles, pearls, the lit side of the moon |
| `palette.paper_pink` | a second paper colour | the analog sheet, the y2k wallpaper, shells |
| `palette.ink` | your line colour | outlines on every object, text |
| `palette.marker` | the colour of a pen mark | the date stamp, your stamp word, the daily line on paper |
| `palette.gold` | a highlight colour | candle dishes, the bell, tarot line art, screws, pixel stars |
| `palette.cool` | one cool accent | no |
| `fonts.masthead` | a big display font from Google Fonts | your intention, the stamp |
| `fonts.label` | a font for labels | the altar name, the cyberpunk intention |
| `fonts.body` | a reading font | small text |
| `fonts.scrawl` | a handwriting or marker font | the daily line in analog |
| `fonts.script` | a signature script font | loaded, kept for other tools |
| `fonts.mono` | a typewriter font | the moon, the date, labels on paper, the terminal |
| `motif` | `analog`, `cyberpunk` or `y2k-blog` (older names like `guest-check` or `retro-tv` still work) | yes, when `altar.config.json` has no motif of its own |
| `lines.stamp` | one short word of yours | a stamp beside the moon in analog |
| `lines.*` (the rest) | more of your own lines | kept for other tools |
| `references`, `notes` | 3 to 5 images or links, and your look in a sentence | Claude reads these when it makes your style with you |

## How the objects take your colours
Every object in the drawer is drawn in eight role colours: plum, wine, ink, paper, paper_pink, gold, accent and marker.
When you build, each role becomes your colour from `palette`, so the candle, the shell and the moon all wear your look.
In the cyberpunk motif the lines turn light, so the objects read as line art on a dark screen.

## Which motif wins
`--motif` on the command line, then `motif` in `altar.config.json`, then `motif` in your own `style.json`, then `analog`.

## Good to know
- Colours must be hex codes (`#RRGGBB`). Anything else is skipped and the bundled colour is used for that slot.
- Fonts are Google Fonts names, letters, numbers and spaces only. Offline, the page uses a similar font already on the computer.
- Any colour or font you leave empty borrows the bundled example's, so the altar always looks finished.
- Your words stay yours. Leave `lines.stamp` empty and there is no stamp. Rocha's LORE stamp appears only on her own example altar.
