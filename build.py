#!/usr/bin/env python3
"""desktop-altar: turn altar.config.json into a desktop altar.

  python3 build.py altar.config.json --out out/
  python3 build.py altar.config.json --out out/ --motif cyberpunk --size 1440x900
  python3 build.py altar.config.json --out out/ --style path/to/style.json

Writes into the out folder:
  altar.html     the living altar (candles flicker, the moon and the daily line stay true), one self-contained file
  index.html     the same page, for apps that ask for a folder
  altar.png      a still wallpaper at your screen size (needs Chrome or Chromium)
  altar.widget/  the same page wrapped for Uebersicht on a Mac

Plain Python, standard library only. The config, style and motif logic follow the sibling kit desktop-core.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "scripts"))
import altar_moon  # noqa: E402
import altar_page  # noqa: E402

OBJECTS_DIR = HERE / "objects"
STYLE_EXAMPLE = HERE / "examples" / "style.rocha-coded.json"
HER_ALTAR = HERE / "examples" / "altar.rocha-coded.json"
OBJECT_TYPES = ("candle", "pillar-candle", "tealight", "crystal-point", "crystal-cluster", "seashell", "pearl",
                "crescent-moon", "full-moon", "rose", "dried-flowers", "incense", "photo-frame", "intention-card",
                "tarot-back", "cauldron", "bell", "feather")
MOTIFS = ("analog", "cyberpunk", "y2k-blog")
DEFAULT_MOTIF = "analog"
MOTIF_ALIASES = {"guest-check": "analog", "front-page": "analog", "magazine-scrawl": "analog",
                 "pink-paper": "analog", "rotary": "analog", "leopard": "analog", "neutral": "analog",
                 "retro-tv": "cyberpunk", "sticker-collage": "y2k-blog", "y2k": "y2k-blog", "blog": "y2k-blog"}
# Every object is drawn ONLY in these role colours, so a style.json re-tones the whole drawer.
TONES = {"#50163C": "plum", "#682047": "wine", "#3B1230": "ink", "#FFF7F4": "paper", "#FFE3F1": "paper_pink",
         "#E9B949": "gold", "#FE9DCA": "accent", "#C2246E": "marker"}
COLOUR = re.compile(r"^#[0-9A-Fa-f]{6}$")
FONT_NAME = re.compile(r"^[A-Za-z0-9 ]{1,40}$")
IMAGE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]{0,79}\.(png|jpe?g|webp)$", re.I)
SIZE = re.compile(r"^\s*(\d{3,4})\s*[xX]\s*(\d{3,4})\s*$")
MAX_OBJECTS, PER_SHELF, MAX_SHELVES, MAX_IMAGE_BYTES = 16, 6, 3, 5 * 1024 * 1024
PLACEHOLDER = "YOUR WORDS HERE"


# ---------- config ----------

def resolve_alias(motif: object) -> str | None:
    raw = str(motif or "").strip().lower()
    raw = MOTIF_ALIASES.get(raw, raw)
    return raw if raw in MOTIFS else None


def parse_size(val: object) -> tuple[int, int] | None:
    m = SIZE.match(str(val or ""))
    if not m:
        return None
    w, h = int(m.group(1)), int(m.group(2))
    return (w, h) if 640 <= w <= 7680 and 480 <= h <= 4320 else None


def validate_config(cfg: object) -> list[str]:
    """Return a list of kind, plain-English problems. An empty list means the altar is ready to build."""
    if not isinstance(cfg, dict):
        return ["The config should be one { ... } block. Start from altar.example.json in this folder."]
    errs: list[str] = []

    def text(key: str, val: object, cap: int) -> None:
        if val in (None, ""):
            return
        if not isinstance(val, str):
            errs.append(f'"{key}" should be words in quotes.')
        elif len(val) > cap:
            errs.append(f'"{key}" is {len(val)} characters. Keep it under {cap} so it fits on the altar.')

    text("name", cfg.get("name"), 60)
    text("intention", cfg.get("intention"), 140)
    if cfg.get("motif") not in (None, "") and not resolve_alias(cfg.get("motif")):
        errs.append(f'"motif" should be analog, cyberpunk or y2k-blog. Got: {cfg.get("motif")}')
    if cfg.get("screen") not in (None, "") and not parse_size(cfg.get("screen")):
        errs.append('"screen" should look like "2560x1600" (width x height of your screen).')
    for key in ("moon", "candle_flicker"):
        if key in cfg and not isinstance(cfg[key], bool):
            errs.append(f'"{key}" should be true or false, with no quotes.')
    if cfg.get("hemisphere") not in (None, "", "north", "south"):
        errs.append('"hemisphere" should be "north" or "south".')
    lines = cfg.get("daily_line", [])
    if lines not in (None, ""):
        if not isinstance(lines, list):
            errs.append('"daily_line" should be a list in [ ], one line per entry.')
        else:
            if len(lines) > 31:
                errs.append(f'"daily_line" has {len(lines)} lines. Keep it to 31, one for each day of a month.')
            for i, ln in enumerate(lines):
                if not isinstance(ln, str) or not ln.strip():
                    errs.append(f"daily_line[{i}] should be a line of words in quotes.")
                elif len(ln) > 120:
                    errs.append(f"daily_line[{i}] is {len(ln)} characters. Keep it under 120.")
    objs = cfg.get("objects", [])
    if objs in (None, ""):
        objs = []
    if not isinstance(objs, list):
        errs.append('"objects" should be a list in [ ], like [{"type": "candle"}].')
        return errs
    if len(objs) > MAX_OBJECTS:
        errs.append(f'"objects" has {len(objs)} things. The altar holds {MAX_OBJECTS}, so pick your favourites.')
    per_shelf: dict[int, int] = {}
    for i, o in enumerate(objs):
        if not isinstance(o, dict):
            errs.append(f'objects[{i}] should be a block like {{"type": "candle"}}.')
            continue
        img = o.get("image")
        if img not in (None, ""):
            if not isinstance(img, str) or ".." in img or not IMAGE_NAME.match(img):
                errs.append(f"objects[{i}].image should be a file name in objects/mine, like \"nana.png\" "
                            "(png, jpg or webp, no folders).")
        elif o.get("type") not in OBJECT_TYPES:
            errs.append(f'objects[{i}].type "{o.get("type")}" is not in the drawer. Pick one of: '
                        + ", ".join(OBJECT_TYPES) + '. Or add your own picture with "image".')
        text(f"objects[{i}].label", o.get("label"), 24)
        shelf = o.get("shelf")
        if shelf not in (None, ""):
            if not (isinstance(shelf, int) and not isinstance(shelf, bool) and 1 <= shelf <= MAX_SHELVES):
                errs.append(f"objects[{i}].shelf should be 1, 2 or 3 (1 is the top shelf).")
            else:
                per_shelf[shelf] = per_shelf.get(shelf, 0) + 1
    for shelf, n in sorted(per_shelf.items()):
        if n > PER_SHELF:
            errs.append(f"Shelf {shelf} has {n} things. A shelf holds {PER_SHELF}. Move some to another shelf.")
    return errs


def load_config(path: Path) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"I could not find {path}. Copy altar.example.json to altar.config.json, "
                         "or open arrange.html and press save.")
    except OSError as exc:
        raise SystemExit(f"Could not open {path}. Check the file name and try again. ({exc.strerror})")
    except ValueError as exc:
        raise SystemExit(f"{path} is not valid JSON yet. Look near line {getattr(exc, 'lineno', '?')}: "
                         "a missing comma or quote is the usual reason.")


# ---------- style.json (shared Rocha Coded schema, same rules as desktop-core) ----------

def find_style(explicit: Path | None = None, cwd: Path | None = None, home: Path | None = None) -> Path:
    """./style.json, then ~/.rocha-coded/style.json, then the bundled example."""
    if explicit:
        return Path(explicit)
    for cand in ((cwd or Path.cwd()) / "style.json", (home or Path.home()) / ".rocha-coded" / "style.json"):
        if cand.is_file():
            return cand
    return STYLE_EXAMPLE


def inherit_style(user: dict) -> dict:
    """A user's style borrows ONLY missing palette and font entries from the bundled example.
    Lines, owner, handle, name, references and notes never fall back to Rocha's."""
    try:
        example = json.loads(STYLE_EXAMPLE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        example = {}
    merged = dict(user)
    for key in ("palette", "fonts"):
        mine = user.get(key) if isinstance(user.get(key), dict) else {}
        base = example.get(key) if isinstance(example.get(key), dict) else {}
        merged[key] = {**base, **{k: v for k, v in mine.items() if str(v or "").strip()}}
    return merged


def load_style(path: Path | None = None) -> tuple[dict, bool]:
    """Return (style, is_bundled_example)."""
    path = Path(path or STYLE_EXAMPLE)
    bundled = path.resolve() == STYLE_EXAMPLE.resolve()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"Could not read style file {path} ({exc}). Using the bundled example look.", file=sys.stderr)
        data, bundled = json.loads(STYLE_EXAMPLE.read_text(encoding="utf-8")), True
    data = data if isinstance(data, dict) else {}
    return (data if bundled else inherit_style(data)), bundled


def page_style(style: dict) -> dict:
    """Only what the altar uses, with every colour and font name checked. Bad values borrow the example's."""
    base = json.loads(STYLE_EXAMPLE.read_text(encoding="utf-8"))
    pal = style.get("palette") if isinstance(style.get("palette"), dict) else {}
    fonts = style.get("fonts") if isinstance(style.get("fonts"), dict) else {}
    lines = style.get("lines") if isinstance(style.get("lines"), dict) else {}
    good_pal = {k: v.strip().upper() for k, v in pal.items() if isinstance(v, str) and COLOUR.match(v.strip())}
    good_fonts = {k: v.strip() for k, v in fonts.items() if isinstance(v, str) and FONT_NAME.match(v.strip())}
    return {"palette": {**{k: v.upper() for k, v in base["palette"].items()}, **good_pal},
            "fonts": {**base["fonts"], **good_fonts},
            "stamp": str(lines.get("stamp") or "").strip()[:16]}


def resolve_motif(cli: str | None, cfg: dict, style: dict, style_is_example: bool) -> str:
    """--motif, then the config's motif, then her own style.json motif, then analog."""
    for cand in (cli, cfg.get("motif"), None if style_is_example else style.get("motif")):
        m = resolve_alias(cand)
        if m:
            return m
    return DEFAULT_MOTIF


# ---------- objects ----------

def retone(svg: str, palette: dict) -> str:
    """Swap every role colour for the matching style.json colour, in one pass."""
    def swap(m: re.Match) -> str:
        role = TONES.get(m.group(0).upper())
        return palette.get(role, m.group(0)) if role else m.group(0)
    return re.sub(r"#[0-9A-Fa-f]{6}\b", swap, svg)


def object_svg(kind: str, palette: dict) -> str:
    svg = (OBJECTS_DIR / f"{kind}.svg").read_text(encoding="utf-8")
    svg = re.sub(r'\s(width|height)="\d+"', "", svg, count=2)
    return retone(svg.replace("<svg ", '<svg class="art" ', 1), palette).strip()


def find_image(name: str, config_dir: Path) -> Path | None:
    for base in (config_dir / "objects" / "mine", OBJECTS_DIR / "mine"):
        cand = (base / name).resolve()
        if cand.parent == base.resolve() and cand.is_file():
            return cand
    return None


def image_uri(path: Path) -> str:
    data = path.read_bytes()
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError(f"{path.name} is {len(data) // 1024} KB. Keep pictures under 5 MB.")
    kind = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}[path.suffix.lower().lstrip(".")]
    return f"data:image/{kind};base64," + base64.b64encode(data).decode("ascii")


def place(objs: list[dict]) -> list[list[dict]]:
    """Objects with a shelf go there, in order. The rest share the shelves evenly, from the top.
    Up to five things sit on one shelf, up to ten on two, the rest on three."""
    explicit = [o["shelf"] for o in objs if isinstance(o.get("shelf"), int)]
    natural = 1 if len(objs) <= 5 else 2 if len(objs) <= 10 else 3
    count = min(MAX_SHELVES, max([natural, *explicit]))
    goal = [len(objs) // count + (1 if i < len(objs) % count else 0) for i in range(count)]
    shelves: list[list[dict]] = [[] for _ in range(count)]
    for o in objs:
        if isinstance(o.get("shelf"), int):
            shelves[o["shelf"] - 1].append(o)
    for o in objs:
        if not isinstance(o.get("shelf"), int):
            target = next((s for s, g in zip(shelves, goal) if len(s) < min(g, PER_SHELF)), None)
            if target is None:
                target = next((s for s in shelves if len(s) < PER_SHELF), shelves[-1])
            target.append(o)
    return [s for s in shelves if s] or [[]]


# ---------- assemble ----------

def is_her_altar(cfg: dict) -> bool:
    """Her stamp shows with the bundled look only when her whole example altar is in use."""
    try:
        return cfg == json.loads(HER_ALTAR.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False


def daily_index(day: dt.date, count: int) -> int:
    """Same sum as the live page: the date's ordinal, wrapped round the list."""
    return day.toordinal() % count if count else 0


def altar_data(cfg: dict, style: dict, style_is_example: bool, motif: str, size: tuple[int, int],
               config_dir: Path, now: dt.datetime | None = None) -> dict:
    now = now or dt.datetime.now(dt.timezone.utc)
    ps = page_style(style)
    items = []
    for o in cfg.get("objects") or []:
        label = str(o.get("label") or "").strip()
        if o.get("image"):
            found = find_image(o["image"], config_dir)
            if not found:
                raise ValueError(f'I could not find objects/mine/{o["image"]}. Put the picture in the objects/mine '
                                 "folder next to your altar.config.json and build again.")
            items.append({"img": image_uri(found), "label": label, "kind": "mine", "shelf": o.get("shelf")})
        else:
            items.append({"svg": object_svg(o["type"], ps["palette"]), "label": label, "kind": o["type"],
                          "shelf": o.get("shelf")})
    lines = [str(x).strip() for x in (cfg.get("daily_line") or []) if str(x).strip()]
    local_day = now.astimezone().date()
    south = cfg.get("hemisphere") == "south"
    moon = None
    if cfg.get("moon", True):
        age = altar_moon.moon_age(now)
        moon = {"age": age, "name": altar_moon.phase_name(age), "path": altar_moon.moon_path(age, 50, 50, 44, south),
                "south": south, "new_moons": altar_moon.upcoming_new_moons(now, 30)}
    return {
        "name": str(cfg.get("name") or "").strip(),
        "intention": str(cfg.get("intention") or "").strip() or PLACEHOLDER,
        "shelves": place(items),
        "daily": lines,
        "daily_now": lines[daily_index(local_day, len(lines))] if lines else "",
        "moon": moon,
        "flicker": cfg.get("candle_flicker", True) is not False,
        "motif": motif,
        "size": size,
        "palette": ps["palette"],
        "fonts": ps["fonts"],
        "stamp": ps["stamp"] if (not style_is_example or is_her_altar(cfg)) else "",
        "today": local_day.strftime("%d %b %Y").upper(),
        "example": style_is_example,
    }


WIDGET = """// desktop-altar for Uebersicht (MIT). Shows altar.html from this folder across your desktop.
export const refreshFrequency = false;
export const className = `top: 0; left: 0; width: 100vw; height: 100vh; z-index: -1;`;
export const render = () => (
  <iframe src="altar.widget/altar.html" title="my altar"
    style={{border: 0, width: "100vw", height: "100vh", display: "block"}} />
);
"""


def build(cfg: dict, out: Path, motif: str | None = None, style_path: Path | None = None,
          size: str | None = None, config_dir: Path | None = None, png: bool = True,
          now: dt.datetime | None = None) -> dict:
    errs = validate_config(cfg)
    if size and not parse_size(size):
        errs.append('--size should look like 2560x1600.')
    if errs:
        raise ValueError("\n".join(errs))
    style, is_example = load_style(find_style(style_path))
    dims = parse_size(size) or parse_size(cfg.get("screen")) or (2560, 1600)
    chosen = resolve_motif(motif, cfg, style, is_example)
    data = altar_data(cfg, style, is_example, chosen, dims, Path(config_dir or Path.cwd()), now)
    html = altar_page.render_page(data)
    out.mkdir(parents=True, exist_ok=True)
    page = out / "altar.html"
    page.write_text(html, encoding="utf-8")
    (out / "index.html").write_text(html, encoding="utf-8")
    widget = out / "altar.widget"
    widget.mkdir(exist_ok=True)
    (widget / "altar.html").write_text(html, encoding="utf-8")
    (widget / "index.jsx").write_text(WIDGET, encoding="utf-8")
    result = {"html": page, "png": None, "motif": chosen, "size": dims, "message": ""}
    if png:
        import render
        ok, msg = render.screenshot(page.as_uri() + "?still=1", out / "altar.png", *dims)
        result["png"] = out / "altar.png" if ok else None
        result["message"] = msg
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build your desktop altar: a wallpaper picture and a living page.")
    ap.add_argument("config", nargs="?", default="altar.config.json", help="your altar.config.json")
    ap.add_argument("--out", default="out", help="folder to write (default: out/)")
    ap.add_argument("--motif", choices=MOTIFS, help="analog, cyberpunk or y2k-blog")
    ap.add_argument("--size", help="your screen, like 2560x1600 (default: the config's screen)")
    ap.add_argument("--style", type=Path, help="a style.json somewhere else")
    ap.add_argument("--no-png", action="store_true", help="skip the wallpaper picture")
    ap.add_argument("--moon-today", action="store_true", help="print tonight's moon phase and stop")
    a = ap.parse_args(argv)
    if a.moon_today:
        age = altar_moon.moon_age(dt.datetime.now(dt.timezone.utc))
        print(f"Tonight's moon: {altar_moon.phase_name(age)} ({round(altar_moon.illumination(age) * 100)}% lit).")
        return 0
    cfg_path = Path(a.config)
    cfg = load_config(cfg_path)
    try:
        res = build(cfg, Path(a.out), a.motif, a.style, a.size, cfg_path.resolve().parent, not a.no_png)
    except ValueError as exc:
        print("A few things to fix in your altar first:", file=sys.stderr)
        for line in str(exc).splitlines():
            print(f"  - {line}", file=sys.stderr)
        return 1
    print(f"READY. Your altar is in {res['html'].parent}/ ({res['motif']}, {res['size'][0]}x{res['size'][1]}).")
    if res["png"]:
        print(f"Wallpaper: {res['png']}  (set it as your desktop picture)")
    elif not a.no_png:
        print(res["message"])
    print(f"Living altar: {res['html']}  (show it with Plash, Lively or Uebersicht)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
