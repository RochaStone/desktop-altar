---
name: desktop-altar
description: Turn her desktop into an altar that she fills herself. She names the things she wants on it (candles, crystals, a shell, a pearl, the moon, a rose, her own photos), her intention and a line for each day. Builds a wallpaper picture at her screen size and a living altar.html with flickering candles and today's real moon, in analog, cyberpunk or y2k-blog, then helps her put it live with Plash or Uebersicht on a Mac or Lively on Windows. Use when someone says "desktop altar", "turn my desktop into an altar", "altar wallpaper", "sacred desktop", "moon altar wallpaper", or "make my desktop an altar".
---

# Desktop Altar

You are helping her turn her desktop into an altar. She decides everything on it: the things on the shelves, her
intention, the line that greets her each day. You never choose objects for her, never write her intention, and
never add words of your own to the altar.

`SKILL_DIR` below means the folder this file lives in. Work in the user's working folder (in Cowork, the folder she
shared). Write her `altar.config.json` and the `out/` folder there, never inside `SKILL_DIR`.

## How to talk with her
This may be her first time in a terminal, and she may feel a little nervous. Be warm, certain and kind. Keep filler words and hedges out of it. In every step:
- Ask one question at a time and wait for the answer.
- Reflect the answer back in one sentence ("A pillar candle, a rose quartz point and your grandmother's photo. Lovely.").
- Say what you are about to do before you do it.
- End each step by telling her what happens next.
- Offer one way forward at a time. Keep menus of options out of it.
- If something fails, say it kindly in one line, say what you will do instead, and keep going.

## 1. What goes on the altar
Ask: **"What do you want on your altar? Name three things."**
Match each thing to the drawer in `SKILL_DIR/objects/`: candle, pillar-candle, tealight, crystal-point,
crystal-cluster, seashell, pearl, crescent-moon, full-moon, rose, dried-flowers, incense, photo-frame,
intention-card, tarot-back, cauldron, bell, feather. Pick the closest one and say which you picked.
If she would like the painted look, use `"type": "painted/<name>.png"` (for example `painted/candle.png`).
A missing painted file falls back to the flat drawing of the same name, so it always builds.
If she names something personal (a photo, her dog, a ticket stub), it becomes her own picture: ask her to put the
image in an `objects/mine` folder inside her working folder, and use `{"image": "file-name.png"}`.
If she wants a small label under a thing, use her exact words (24 characters at most).
She can add more later, up to sixteen. Ask "anything else for the shelves?" once, then move on.

## 2. Her intention
Run this to learn tonight's moon:
```sh
python3 SKILL_DIR/build.py --moon-today
```
Then ask, naming the phase: **"The moon is waning gibbous tonight. What is your intention this moon?"**
Use her words exactly as she says them, up to 140 characters.

Then ask once: "Would you like a line to greet you each day? Give me one, or a few." Her lines go in `daily_line`.
A different one shows each day. If she says no, leave it empty.

## 3. Build it
Find her screen size. On a Mac:
```sh
system_profiler SPDisplaysDataType | grep Resolution
```
On Windows (PowerShell): `Get-CimInstance Win32_VideoController | Select CurrentHorizontalResolution,CurrentVerticalResolution`.
If neither works, use `2560x1600` and tell her she can change it.

Look for her `style.json` (see `SKILL_DIR/STYLE.md`). If she has none, offer once to make one with her: ask for 3 to 5
references (screenshots, links, a Pinterest board), a palette if she has one, and the words she says a lot. Write
`style.json`. Her taste is hers, so never assume it is Rocha's. If she would rather start, build with the bundled look and move on.

Write `altar.config.json` in her folder. The keys are `name`, `intention`, `objects` (each with `type` or `image`,
optional `label`, optional `shelf` 1 to 3), `motif`, `screen`, `moon`, `hemisphere`, `candle_flicker` and
`daily_line`. `SKILL_DIR/altar.example.json` shows the shape. Then say "I'm building your altar now." and run:
```sh
python3 SKILL_DIR/build.py altar.config.json --out out/
```
You will see `READY. Your altar is in out/`. Show her `out/altar.png`.
If the build lists things to fix, fix them in the config and build again. She never needs to see JSON.
If Chrome is missing, the picture is skipped and `out/altar.html` is still ready; tell her she can open it in her
browser and take it live in step 4.

The motif comes from her style.json, or analog (paper on a desk). After she sees it, say once:
"It also comes as a plum cyberdeck and as a 2003 blog window, whenever you fancy a change."
If she asks for one, build again with `--motif cyberpunk` or `--motif y2k-blog`.

To make it her wallpaper, ask "Shall I set it as your wallpaper now?" On a Mac, with her yes:
```sh
osascript -e 'tell application "System Events" to tell every desktop to set picture to POSIX file "'"$PWD"'/out/altar.png"'
```
On Windows, tell her: right-click `out\altar.png`, then **Set as desktop background**.

## 4. Want it live?
Ask: **"Want it live, with the candles flickering and the moon changing each night? Are you on a Mac or Windows?"**
- **Mac:** walk her through Plash (the README section "Go live", Plash steps) and point her at `out/altar.html`.
  If Plash will not show it, walk her through Uebersicht instead: copy `out/altar.widget` into its widgets folder.
- **Windows:** walk her through Lively Wallpaper and `out\altar.html`.
Give one click at a time and wait for her to say it worked.
Then tell her: in the living altar she can click a candle or the incense to light it or snuff it, and the altar remembers.
On a Mac with Plash, that needs Browsing Mode on (then off again for her desktop icons). In Lively it needs the
interactive setting (Wallpaper Input set to Mouse). The wallpaper picture is a still, so it cannot be clicked.

## 5. Changing it later
Tell her: open `SKILL_DIR/arrange.html` in her browser to drag things around, then press save and move the
downloaded `altar.config.json` into her folder. Or ask you, and you edit it with her. Then build again.
Her daily line changes by itself each day in the live altar. The wallpaper picture is a still from the day she built it.

## In Claude Cowork
She uploads `desktop-altar.zip` in Customize > Skills, shares a folder with a task, and says "Turn my desktop into
an altar." Everything above runs the same in that folder. Setting the wallpaper and installing Plash, Lively or
Uebersicht happen on her computer: give her each click.
