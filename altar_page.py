"""Render the altar as one self-contained HTML page. One function, three motif skins.

The DOM is the same for analog, cyberpunk and y2k-blog. The motif class on <html> decides the structure you see
(a paper sheet on a desk, a cyberdeck screen, a 2003 window). The palette and fonts come from style.json.
The only thing the page loads from the internet is the Google Fonts stylesheet; offline it falls back to
fonts already on the computer. A small script keeps the moon and the daily line true while the page stays open.
"""
from __future__ import annotations

import json
import re
from html import escape
from urllib.parse import quote, quote_plus

AXES = {"Fraunces": ":opsz,wght@9..144,400;9..144,900", "Bricolage Grotesque": ":opsz,wght@12..96,400;12..96,800",
        "DM Mono": ":wght@400;500"}
PIXEL = "Silkscreen"
FLAME_Y = {"candle": 0.19, "pillar-candle": 0.28, "tealight": 0.68}
STAR = ["0001000", "0001000", "1111111", "0111110", "0110110", "1000001"]
# Dark screens swap the line colour so objects read as line art on the cyberdeck.
DARK_SWAP = {"ink": "paper", "plum": "wine"}


def _fonts_href(fonts: dict) -> str:
    names = list(dict.fromkeys([*fonts.values(), PIXEL]))
    fams = "&".join(f"family={quote_plus(n)}{AXES.get(n, '')}" for n in names)
    return f"https://fonts.googleapis.com/css2?{fams}&display=swap"


def _star_tile(gold: str) -> str:
    rects = "".join(f'<rect x="{12 + c}" y="{10 + r}" width="1" height="1"/>'
                    for r, row in enumerate(STAR) for c, v in enumerate(row) if v == "1")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" shape-rendering="crispEdges">'
           f'<g fill="{gold}" transform="scale(2)">{rects}</g></svg>')
    return "data:image/svg+xml," + quote(svg)


GRAIN = ("data:image/svg+xml," + quote(
    '<svg xmlns="http://www.w3.org/2000/svg" width="240" height="240"><filter id="n">'
    '<feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="3" stitchTiles="stitch"/>'
    '<feColorMatrix values="0 0 0 0 .2 0 0 0 0 .05 0 0 0 0 .15 0 0 0 .09 0"/></filter>'
    '<rect width="240" height="240" filter="url(#n)"/></svg>'))


def _swap_dark(svg: str, pal: dict) -> str:
    table = {pal[k].upper(): pal[v] for k, v in DARK_SWAP.items()}
    return re.sub(r"#[0-9A-Fa-f]{6}\b", lambda m: table.get(m.group(0).upper(), m.group(0)), svg)


def _figure(item: dict, i: int, dark: bool, pal: dict) -> str:
    label = escape(item.get("label") or "")
    cap = f'<figcaption>{label}</figcaption>' if label else ""
    kind = escape(item["kind"])
    lit = " lit" if item["kind"] in FLAME_Y else ""
    glow = f';--fy:{FLAME_Y[item["kind"]]}' if lit else ""
    if "img" in item:
        art = f'<span class="mine"><img src="{item["img"]}" alt="{label or "my own picture"}"></span>'
    else:
        art = _swap_dark(item["svg"], pal) if dark else item["svg"]
    return f'<figure class="obj k-{kind}{lit}" style="--i:{i}{glow}">{art}{cap}</figure>'


def _shelves(data: dict) -> str:
    dark = data["motif"] == "cyberpunk"
    out, i = [], 0
    for shelf in data["shelves"]:
        figs = []
        for item in shelf:
            figs.append(_figure(item, i, dark, data["palette"]))
            i += 1
        out.append(f'<div class="shelf"><div class="row">{"".join(figs)}</div><div class="plank"></div></div>')
    return f'<div class="shelves n{len(data["shelves"])}">{"".join(out)}</div>'


def _moon(data: dict) -> str:
    m = data["moon"]
    if not m:
        return ""
    return (f'<div class="moonbox"><svg class="moon" viewBox="0 0 100 100" role="img" aria-label="today\'s moon">'
            f'<circle cx="50" cy="50" r="44" class="moon-dark"/><path class="moon-lit" data-live="moon" d="{m["path"]}"/>'
            f'<circle cx="50" cy="50" r="44" class="moon-rim"/></svg>'
            f'<p class="phase" data-live="phase">{escape(m["name"])}</p></div>')


def _live(data: dict) -> str:
    m = data["moon"]
    payload = {"daily": data["daily"], "moon": bool(m), "south": bool(m and m["south"]),
               "newMoons": m["new_moons"] if m else []}
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


CSS = """
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:100%;height:100%;overflow:hidden}
:root{--u:min(1vw,1.6vh)}
body{background:var(--hero);color:var(--ink);font-family:var(--f-body),Georgia,serif;-webkit-font-smoothing:antialiased}
.stage{position:relative;width:100%;height:100%;display:flex;align-items:center;justify-content:center;padding:calc(var(--u)*3) 0 calc(var(--u)*6)}
.frame{position:relative;width:calc(var(--u)*86);max-width:100%;display:flex;flex-direction:column}
.bar,.prompt,.y2k,.tape,.datestamp,.stamp,.screws{display:none}
.body{display:grid;grid-template-columns:minmax(0,1fr) calc(var(--u)*20);gap:calc(var(--u)*2.4);padding:calc(var(--u)*2.4)}
.altar{display:flex;flex-direction:column;min-width:0}
.kicker{font-family:var(--f-label),sans-serif;font-weight:800;font-size:calc(var(--u)*1.15);letter-spacing:.02em}
.intention{font-family:var(--f-mast),Georgia,serif;font-weight:900;font-size:calc(var(--u)*2.7);line-height:1.04;margin:calc(var(--u)*.4) 0 calc(var(--u)*1.6);overflow-wrap:anywhere}
.shelves{display:flex;flex-direction:column;gap:calc(var(--u)*1.9)}
.row{display:flex;align-items:flex-end;justify-content:space-evenly;gap:calc(var(--u)*1);padding:0 calc(var(--u)*1.5)}
.obj{--h:calc(var(--u)*13);position:relative;height:var(--h);width:calc(var(--h)*.8333);display:flex;justify-content:center}
.n2 .obj{--h:calc(var(--u)*10.2)}.n3 .obj{--h:calc(var(--u)*7.4)}
.obj .art{width:100%;height:100%;display:block;overflow:visible}
.obj figcaption{position:absolute;top:calc(100% + var(--u)*.35);left:50%;transform:translateX(-50%);width:max-content;max-width:calc(var(--h)*.95);text-align:center;
 font-family:var(--f-label),sans-serif;font-weight:800;font-size:calc(var(--u)*.8);line-height:1;padding:calc(var(--u)*.2) calc(var(--u)*.5);z-index:2}
.mine{display:block;width:100%;height:92%;margin-top:auto;padding:calc(var(--u)*.35) calc(var(--u)*.35) calc(var(--u)*1.1);background:var(--paper);
 border:calc(var(--u)*.12) solid var(--ink);transform:rotate(-2deg)}
.mine img{width:100%;height:100%;object-fit:cover;display:block}
.plank{height:calc(var(--u)*1.7);border:calc(var(--u)*.16) solid var(--ink);border-radius:calc(var(--u)*.2)}
.cloth{margin-top:calc(var(--u)*1.9);min-height:calc(var(--u)*3.4);display:flex;align-items:center;justify-content:center;overflow:hidden;padding:0 calc(var(--u)*1)}
.daily{font-size:calc(var(--u)*1.5);text-align:center;white-space:nowrap}
.side{display:flex;flex-direction:column;gap:calc(var(--u)*1.2);min-width:0}
.moonbox{display:flex;flex-direction:column;align-items:center;gap:calc(var(--u)*.6)}
.moon{width:calc(var(--u)*11);height:calc(var(--u)*11)}
.moon-dark{fill:var(--wine)}.moon-lit{fill:var(--paper)}.moon-rim{fill:none;stroke:var(--gold);stroke-width:2}
.date{display:none}.m-cyberpunk .date{display:block}
.phase,.date,.y2k p{font-family:var(--f-mono),monospace;font-size:calc(var(--u)*.95);text-transform:lowercase;text-align:center}
.flame,.smoke{transform-box:view-box}
.flicker .flame{animation:flick 1.9s ease-in-out infinite alternate;animation-delay:calc(var(--i)*-.37s)}
.smoke{transform-origin:68px 42px;animation:drift 7s ease-in-out infinite}
@keyframes flick{0%{transform:scale(1,1) rotate(-2deg)}45%{transform:scale(.93,1.07) rotate(1.5deg)}100%{transform:scale(1.04,.95) rotate(-.5deg)}}
@keyframes drift{0%{opacity:.25;transform:translateY(3px)}50%{opacity:1}100%{opacity:.15;transform:translateY(-5px) skewX(8deg)}}
@keyframes slide{from{transform:translateX(60%)}to{transform:translateX(-60%)}}
@keyframes blink{50%{opacity:0}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
.still *{animation:none!important}

/* analog: a blush paper sheet on a desk, cream shelves, washi tape, a date stamp, soft light */
.m-analog body{background:var(--paper) url("GRAIN")}
.m-analog .stage::before{content:"";position:absolute;width:calc(var(--u)*120);height:calc(var(--u)*70);border-radius:50%;background:var(--paper_pink);opacity:.6;top:50%;left:50%;transform:translate(-50%,-55%);filter:blur(calc(var(--u)*7))}
.m-analog .frame{background:var(--paper_pink) url("GRAIN");transform:rotate(-.5deg);box-shadow:0 calc(var(--u)*.9) calc(var(--u)*2.6) rgba(40,10,30,.28)}
.m-analog .tape{display:block;position:absolute;width:calc(var(--u)*10);height:calc(var(--u)*2.4);background:var(--accent);opacity:.82;z-index:3}
.m-analog .t1{top:calc(var(--u)*-1);left:calc(var(--u)*-2.4);transform:rotate(-24deg)}
.m-analog .t2{top:calc(var(--u)*-1);right:calc(var(--u)*-2.4);transform:rotate(22deg)}
.m-analog .kicker{color:var(--wine);text-transform:lowercase}
.m-analog .intention{color:var(--ink)}
.m-analog .plank{background:var(--paper);box-shadow:0 calc(var(--u)*.35) 0 var(--ink)}
.m-analog figcaption{background:var(--paper);color:var(--ink);border:calc(var(--u)*.1) solid var(--ink);font-family:var(--f-mono),monospace;font-weight:500}
.m-analog .cloth{border-top:calc(var(--u)*.16) dashed var(--ink)}
.m-analog .daily{font-family:var(--f-scrawl),cursive;color:var(--marker);font-size:calc(var(--u)*1.8);transform:rotate(-1.5deg)}
.m-analog .side{background:var(--paper);border:calc(var(--u)*.14) solid var(--ink);padding:calc(var(--u)*1.4);transform:rotate(1.2deg);align-self:start}
.m-analog .datestamp{display:block;align-self:center;font-family:var(--f-mono),monospace;font-weight:500;color:var(--marker);border:calc(var(--u)*.16) solid var(--marker);
 padding:calc(var(--u)*.3) calc(var(--u)*.7);font-size:calc(var(--u)*1);transform:rotate(-6deg);letter-spacing:.08em}
.m-analog .stamp{display:block;align-self:center;font-family:var(--f-mast),serif;font-weight:900;color:var(--marker);border:calc(var(--u)*.22) double var(--marker);
 padding:calc(var(--u)*.2) calc(var(--u)*1);font-size:calc(var(--u)*2.4);letter-spacing:.14em;transform:rotate(7deg);opacity:.9}
.m-analog .stamp:empty{display:none}

/* cyberpunk: a plum cyberdeck, gold screws, a terminal prompt, candle glow, a whisper of scanlines */
.m-cyberpunk body{background:var(--plum)}
.m-cyberpunk .frame{background:var(--wine);border-radius:calc(var(--u)*1.4);padding:calc(var(--u)*1.6);box-shadow:0 calc(var(--u)*1) calc(var(--u)*3) rgba(0,0,0,.4)}
.m-cyberpunk .screws{display:block}
.m-cyberpunk .screws i{position:absolute;width:calc(var(--u)*.9);height:calc(var(--u)*.9);border-radius:50%;background:var(--gold);border:calc(var(--u)*.12) solid var(--ink)}
.m-cyberpunk .screws i:nth-child(1){top:calc(var(--u)*.4);left:calc(var(--u)*.4)}.m-cyberpunk .screws i:nth-child(2){top:calc(var(--u)*.4);right:calc(var(--u)*.4)}
.m-cyberpunk .screws i:nth-child(3){bottom:calc(var(--u)*.4);left:calc(var(--u)*.4)}.m-cyberpunk .screws i:nth-child(4){bottom:calc(var(--u)*.4);right:calc(var(--u)*.4)}
.m-cyberpunk .screen{position:relative;background:var(--ink);border-radius:calc(var(--u)*.6);overflow:hidden}
.m-cyberpunk .screen::after{content:"";position:absolute;inset:0;pointer-events:none;background:repeating-linear-gradient(0deg,rgba(255,247,244,.035) 0 1px,transparent 1px 4px)}
.m-cyberpunk .prompt{display:block;font-family:var(--f-mono),monospace;color:var(--accent);font-size:calc(var(--u)*1.05);padding:calc(var(--u)*1.2) calc(var(--u)*2.4) 0}
.m-cyberpunk .cursor{display:inline-block;width:.6em;height:1em;background:var(--accent);vertical-align:-.12em;margin-left:.3em;animation:blink 1.1s steps(1) infinite}
.m-cyberpunk .kicker{font-family:var(--pixel),monospace;font-weight:400;color:var(--gold);text-transform:lowercase}
.m-cyberpunk .intention{font-family:var(--f-label),sans-serif;font-weight:800;color:var(--paper);letter-spacing:-.01em}
.m-cyberpunk .plank{background:var(--plum);border-color:var(--accent);border-width:calc(var(--u)*.16) 0 0;border-radius:0}
.m-cyberpunk figcaption{font-family:var(--pixel),monospace;font-weight:400;color:var(--ink);background:var(--gold)}
.m-cyberpunk .lit::before{content:"";position:absolute;left:50%;top:calc(var(--h)*var(--fy));width:calc(var(--h)*.9);height:calc(var(--h)*.9);transform:translate(-50%,-50%);border-radius:50%;
 background:radial-gradient(circle,rgba(233,185,73,.34),rgba(233,185,73,0) 68%);pointer-events:none}
.m-cyberpunk .daily{font-family:var(--f-mono),monospace;color:var(--paper)}
.m-cyberpunk .daily::before{content:"> ";color:var(--accent)}
.m-cyberpunk .side{border-left:calc(var(--u)*.14) dashed var(--gold);padding-left:calc(var(--u)*2)}
.m-cyberpunk .phase,.m-cyberpunk .date{color:var(--paper)}
.m-cyberpunk .moon-dark{fill:var(--plum)}

/* y2k-blog: a cream 2003 window on tiled blush, plum title bar, gold buttons, sidebar, hit counter, marquee */
.m-y2k-blog body{background:var(--paper_pink) url("STARS")}
.m-y2k-blog .frame{background:var(--paper);border:calc(var(--u)*.2) solid var(--ink);box-shadow:calc(var(--u)*.8) calc(var(--u)*.8) 0 var(--ink)}
.m-y2k-blog .bar{display:flex;align-items:center;gap:calc(var(--u)*1);height:calc(var(--u)*2.6);padding:0 calc(var(--u)*1);color:var(--paper);
 background:var(--plum) repeating-linear-gradient(0deg,rgba(255,247,244,.12) 0 2px,transparent 2px 5px);border-bottom:calc(var(--u)*.2) solid var(--ink)}
.m-y2k-blog .btns{display:flex;gap:calc(var(--u)*.45)}
.m-y2k-blog .btns i{width:calc(var(--u)*1.1);height:calc(var(--u)*1.1);background:var(--gold);border:calc(var(--u)*.12) solid var(--ink)}
.m-y2k-blog .title{font-family:var(--pixel),monospace;font-size:calc(var(--u)*1.05);margin:0 auto;padding:0 calc(var(--u)*.8);background:var(--plum)}
.m-y2k-blog .kicker{font-family:var(--pixel),monospace;font-weight:400;color:var(--marker);text-transform:lowercase}
.m-y2k-blog .plank{background:var(--wine);box-shadow:inset 0 calc(var(--u)*.3) 0 var(--gold)}
.m-y2k-blog figcaption{font-family:var(--pixel),monospace;font-weight:400;background:var(--paper_pink);color:var(--ink);border:calc(var(--u)*.1) solid var(--ink)}
.m-y2k-blog .cloth{background:var(--paper_pink);border:calc(var(--u)*.14) solid var(--ink)}
.m-y2k-blog .daily{font-family:var(--f-label),sans-serif;font-weight:800;color:var(--wine);animation:slide 16s linear infinite}
.m-y2k-blog .side{background:var(--paper_pink);border:calc(var(--u)*.14) solid var(--ink);padding:calc(var(--u)*1.2)}
.m-y2k-blog .y2k{display:block}
.m-y2k-blog .y2k h2{font-family:var(--pixel),monospace;font-weight:400;font-size:calc(var(--u)*.95);background:var(--plum);color:var(--paper);padding:calc(var(--u)*.25) calc(var(--u)*.6);margin-bottom:calc(var(--u)*.4)}
.m-y2k-blog .y2k p{text-align:left;overflow-wrap:anywhere}
.m-y2k-blog .counter{border:calc(var(--u)*.12) solid var(--ink);background:var(--ink);color:var(--gold);padding:calc(var(--u)*.3) calc(var(--u)*.5);text-transform:none!important}
.m-y2k-blog .moonbox .phase{display:none}
"""


def render_page(data: dict) -> str:
    pal, fonts, motif = data["palette"], data["fonts"], data["motif"]
    tokens = ";".join(f"--{k}:{v}" for k, v in pal.items())
    font_vars = ";".join(f"--f-{'mast' if k == 'masthead' else k}:'{v}'" for k, v in fonts.items())
    css = (CSS.replace("GRAIN", GRAIN).replace("STARS", _star_tile(pal["gold"]))
           + f":root{{{tokens};{font_vars};--pixel:'{PIXEL}'}}")
    name = escape(data["name"])
    title = name or "my altar"
    mood = escape(data["moon"]["name"]) if data["moon"] else "lit"
    stamp = escape(data["stamp"]) if data["stamp"] else ""
    classes = f"m-{motif}" + (" flicker" if data["flicker"] else "")
    body = f"""<main class="stage">
<div class="frame">
<span class="tape t1"></span><span class="tape t2"></span><span class="screws"><i></i><i></i><i></i><i></i></span>
<div class="bar"><span class="btns"><i></i><i></i><i></i></span><span class="title">altar.exe</span></div>
<div class="screen">
<p class="prompt">altar:~$ light<span class="cursor"></span></p>
<div class="body">
<section class="altar">
<p class="kicker">{name}</p>
<h1 class="intention">{escape(data["intention"])}</h1>
{_shelves(data)}
<div class="cloth"><p class="daily" data-live="daily">{escape(data["daily_now"])}</p></div>
</section>
<aside class="side">
{_moon(data)}
<p class="date" data-live="date">{escape(data["today"])}</p>
<span class="datestamp" data-live="date">{escape(data["today"])}</span>
<span class="stamp">{stamp}</span>
<div class="y2k"><h2>about me</h2><p>{title}</p></div>
<div class="y2k"><h2>mood</h2><p>&#10023; <span data-live="phase">{mood}</span></p></div>
<div class="y2k"><p class="counter">you are visitor no. 000,777</p></div>
<div class="y2k"><p>last updated <span data-live="date">{escape(data["today"])}</span></p></div>
</aside>
</div>
</div>
</div>
</main>"""
    w, h = data["size"]
    return f"""<!doctype html>
<html lang="en" class="{classes}" data-size="{w}x{h}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{escape(_fonts_href(fonts))}">
<style>{css}</style>
<script>if (/[?&]still/.test(location.search)) document.documentElement.classList.add("still");</script>
</head>
<body>
{body}
<script type="application/json" id="altar-live">{_live(data)}</script>
<script>{LIVE_JS}</script>
</body>
</html>
"""


LIVE_JS = """
(function () {
  if (document.documentElement.classList.contains("still")) return;
  var data;
  try { data = JSON.parse(document.getElementById("altar-live").textContent); } catch (e) { return; }
  var MONTHS = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"];
  var NAMES = ["new moon","waxing crescent","first quarter","waxing gibbous","full moon","waning gibbous","last quarter","waning crescent"];
  var SYNODIC = 29.530588861 * 864e5;
  function each(key, fn) { Array.prototype.forEach.call(document.querySelectorAll('[data-live="' + key + '"]'), fn); }
  function ordinal(d) { return Math.floor((Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) - Date.UTC(1970, 0, 1)) / 864e5) + 719163; }
  function age(t) {
    var nm = data.newMoons;
    for (var i = nm.length - 2; i >= 0; i--) { if (nm[i] <= t && t < nm[i + 1]) return (t - nm[i]) / (nm[i + 1] - nm[i]); }
    var a = ((t - nm[nm.length - 1]) % SYNODIC) / SYNODIC;
    return a < 0 ? a + 1 : a;
  }
  function path(a) {
    var r = 44, k = Math.cos(2 * Math.PI * a), rx = Math.abs(k) * r, right = (a < 0.5) !== data.south;
    var first = right ? 1 : 0, back = right ? (k > 0 ? 0 : 1) : (k > 0 ? 1 : 0);
    return "M50.00 6.00 A44.00 44.00 0 0 " + first + " 50.00 94.00 A" + rx.toFixed(2) + " 44.00 0 0 " + back + " 50.00 6.00 Z";
  }
  function tick() {
    var now = new Date();
    var day = ("0" + now.getDate()).slice(-2) + " " + MONTHS[now.getMonth()] + " " + now.getFullYear();
    each("date", function (el) { el.textContent = day; });
    if (data.daily.length) {
      var line = data.daily[ordinal(now) % data.daily.length];
      each("daily", function (el) { el.textContent = line; });
    }
    if (data.moon && data.newMoons.length > 1) {
      var a = age(now.getTime());
      each("moon", function (el) { el.setAttribute("d", path(a)); });
      each("phase", function (el) { el.textContent = NAMES[Math.floor(a * 8 + 0.5) % 8]; });
    }
  }
  tick();
  setInterval(tick, 10 * 60 * 1000);
})();
"""
