"""Tests for desktop-altar. Run: python3 -m unittest discover -s tests -v

The headless-Chrome tests skip, with a message, when Chrome is not installed.
"""
from __future__ import annotations

import copy
import datetime as dt
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import altar_moon  # noqa: E402
import build  # noqa: E402
import render  # noqa: E402

HER = json.loads((ROOT / "examples" / "altar.rocha-coded.json").read_text(encoding="utf-8"))
BLANK = json.loads((ROOT / "altar.example.json").read_text(encoding="utf-8"))
HER_LINES = ("I AM SO LUCKY", "EVERYTHING WORKS OUT FOR ME", "WHAT IF YOUR FOUNDER WORLD WORKS OUT?",
             "whimsy lore", "LORE")
CHROME = render.find_chrome()
NOW = dt.datetime(2026, 10, 28, 12, 0, tzinfo=dt.timezone.utc)
UTC = dt.timezone.utc


def user_style(tmp: Path, **extra) -> Path:
    data = {"name": "Mine", "palette": {"hero": "#123456", "gold": "#ABCDEF", "accent": "#00AA55"}, "motif": "",
            "lines": {}}
    data.update(extra)
    path = tmp / "style.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def mine_cfg() -> dict:
    return {"name": "Juniper", "intention": "soft and steady", "daily_line": ["morning light"],
            "objects": [{"type": "candle"}, {"type": "pearl", "label": "calm"}]}


class ConfigValidation(unittest.TestCase):
    def test_examples_are_valid(self):
        self.assertEqual(build.validate_config(HER), [])
        self.assertEqual(build.validate_config(BLANK), [])

    def test_unknown_object_and_bad_types(self):
        cfg = copy.deepcopy(HER)
        cfg["objects"][0]["type"] = "unicorn"
        cfg["moon"] = "yes"
        cfg["candle_flicker"] = 1
        cfg["daily_line"] = "one line"
        cfg["screen"] = "big"
        cfg["motif"] = "vaporwave"
        errs = "\n".join(build.validate_config(cfg))
        for needle in ('objects[0].type "unicorn"', '"moon" should be', '"candle_flicker" should be',
                       '"daily_line" should be a list', '"screen" should look like', '"motif" should be'):
            self.assertIn(needle, errs)

    def test_image_names_stay_in_objects_mine(self):
        for bad in ("../secret.png", "a/b.png", "/etc/x.png", "nana.svg", "nana"):
            errs = build.validate_config({"objects": [{"image": bad}]})
            self.assertTrue(any("objects[0].image" in e for e in errs), bad)
        self.assertEqual(build.validate_config({"objects": [{"image": "nana.png"}]}), [])

    def test_limits(self):
        many = {"objects": [{"type": "candle"}] * 17}
        self.assertTrue(any("holds 16" in e for e in build.validate_config(many)))
        crowded = {"objects": [{"type": "bell", "shelf": 2}] * 7}
        self.assertTrue(any("Shelf 2 has 7" in e for e in build.validate_config(crowded)))
        self.assertTrue(build.validate_config({"objects": [{"type": "bell", "shelf": 4}]}))
        self.assertTrue(build.validate_config({"intention": "x" * 141}))
        self.assertEqual(len(build.validate_config(["nope"])), 1)

    def test_placement(self):
        five = [{"kind": str(i)} for i in range(5)]
        self.assertEqual([len(s) for s in build.place(five)], [5])
        self.assertEqual([len(s) for s in build.place(five * 2)], [5, 5])
        self.assertEqual([len(s) for s in build.place(five * 3 + [{}])], [6, 5, 5])
        pinned = [{"shelf": 2}, {}, {}]
        self.assertEqual([len(s) for s in build.place(pinned)], [2, 1])

    def test_sizes(self):
        self.assertEqual(build.parse_size("2560x1600"), (2560, 1600))
        self.assertEqual(build.parse_size(" 1440 X 900 "), (1440, 900))
        self.assertIsNone(build.parse_size("100x100"))


class Objects(unittest.TestCase):
    def test_drawer_matches_files_and_arrange_page(self):
        files = sorted(p.stem for p in (ROOT / "objects").glob("*.svg"))
        self.assertEqual(files, sorted(build.OBJECT_TYPES))
        self.assertTrue(12 <= len(files) <= 18)
        page = (ROOT / "arrange.html").read_text(encoding="utf-8")
        listed = re.findall(r'"([a-z-]+)"', re.search(r"var OBJECTS = \[(.*?)\];", page, re.S).group(1))
        self.assertEqual(listed, list(build.OBJECT_TYPES))

    def test_objects_use_only_role_colours_and_stay_flat(self):
        for kind in build.OBJECT_TYPES:
            svg = (ROOT / "objects" / f"{kind}.svg").read_text(encoding="utf-8")
            colours = {c.upper() for c in re.findall(r"#[0-9A-Fa-f]{6}\b", svg)}
            self.assertTrue(colours <= set(build.TONES), f"{kind} uses {colours - set(build.TONES)}")
            self.assertNotRegex(svg, r"(?i)gradient|<filter|<image|<script|\bid=")

    def test_retone_follows_style(self):
        pal = {"plum": "#111111", "wine": "#222222", "ink": "#333333", "paper": "#444444", "paper_pink": "#555555",
               "gold": "#666666", "accent": "#777777", "marker": "#888888"}
        for kind in build.OBJECT_TYPES:
            out = build.object_svg(kind, pal)
            left = {c.upper() for c in re.findall(r"#[0-9A-Fa-f]{6}\b", out)}
            self.assertTrue(left <= set(pal.values()), f"{kind} kept {left - set(pal.values())}")
            self.assertTrue(left, kind)

    def test_retone_is_one_pass(self):
        swapped = build.retone('<a fill="#50163C"/><b fill="#682047"/>', {"plum": "#682047", "wine": "#50163C"})
        self.assertEqual(swapped, '<a fill="#682047"/><b fill="#50163C"/>')


class StyleAndInheritance(unittest.TestCase):
    def test_fallback_order(self):
        with tempfile.TemporaryDirectory() as cwd, tempfile.TemporaryDirectory() as home:
            cwd, home = Path(cwd), Path(home)
            self.assertEqual(build.find_style(cwd=cwd, home=home), build.STYLE_EXAMPLE)
            (home / ".rocha-coded").mkdir()
            (home / ".rocha-coded" / "style.json").write_text("{}")
            self.assertEqual(build.find_style(cwd=cwd, home=home), home / ".rocha-coded" / "style.json")
            (cwd / "style.json").write_text("{}")
            self.assertEqual(build.find_style(cwd=cwd, home=home), cwd / "style.json")

    def test_user_style_borrows_palette_never_lines(self):
        merged = build.inherit_style({"palette": {"hero": "#123456"}, "lines": {}})
        self.assertEqual(merged["palette"]["hero"], "#123456")
        self.assertEqual(merged["palette"]["gold"], "#E9B949")
        self.assertEqual(merged["lines"], {})
        self.assertNotIn("owner", merged)
        self.assertNotIn("notes", merged)

    def test_user_altar_never_shows_her_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            res = build.build(mine_cfg(), tmp / "out", None, user_style(tmp), png=False, now=NOW)
            html = res["html"].read_text(encoding="utf-8")
            for line in HER_LINES:
                self.assertNotIn(line, html)
            self.assertIn("--hero:#123456", html)
            self.assertIn("--gold:#ABCDEF", html)
            self.assertIn("--paper:#FFF7F4", html)

    def test_her_stamp_only_with_her_whole_example(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            blank = build.build(BLANK, tmp / "a", None, build.STYLE_EXAMPLE, png=False, now=NOW)
            self.assertIn('<span class="stamp"></span>', blank["html"].read_text(encoding="utf-8"))
            self.assertIn("YOUR WORDS HERE", blank["html"].read_text(encoding="utf-8"))
            hers = build.build(HER, tmp / "b", None, build.STYLE_EXAMPLE, png=False, now=NOW)
            self.assertIn('<span class="stamp">LORE</span>', hers["html"].read_text(encoding="utf-8"))
            own = build.build(mine_cfg(), tmp / "c", None, user_style(tmp, lines={"stamp": "HUSH"}), png=False, now=NOW)
            self.assertIn('<span class="stamp">HUSH</span>', own["html"].read_text(encoding="utf-8"))

    def test_bad_colours_and_fonts_are_dropped(self):
        ps = build.page_style({"palette": {"hero": "red;}</style>", "gold": "#abcdef"},
                               "fonts": {"masthead": "x'}</style>"}})
        self.assertEqual(ps["palette"]["hero"], "#50163C")
        self.assertEqual(ps["palette"]["gold"], "#ABCDEF")
        self.assertEqual(ps["fonts"]["masthead"], "Fraunces")

    def test_motif_order(self):
        self.assertEqual(build.resolve_motif("cyberpunk", {"motif": "analog"}, {}, True), "cyberpunk")
        self.assertEqual(build.resolve_motif(None, {"motif": "blog"}, {}, True), "y2k-blog")
        self.assertEqual(build.resolve_motif(None, {}, {"motif": "retro-tv"}, False), "cyberpunk")
        self.assertEqual(build.resolve_motif(None, {}, {"motif": "cyberpunk"}, True), "analog")


class Moon(unittest.TestCase):
    def near(self, name: str, when: dt.datetime, minutes: int = 6):
        found = altar_moon.phases_between(when - dt.timedelta(days=2), when + dt.timedelta(days=2))
        hits = [t for n, t in found if n == name]
        self.assertTrue(hits, f"no {name} near {when}")
        self.assertLess(abs((hits[0] - when).total_seconds()), minutes * 60, f"{name}: {hits[0]} vs {when}")

    def test_known_dates(self):
        # NASA phase tables: the total eclipse new moon of 8 April 2024, and the full moon of 13 January 2025.
        self.near("new moon", dt.datetime(2024, 4, 8, 18, 21, tzinfo=UTC))
        self.near("full moon", dt.datetime(2025, 1, 13, 22, 27, tzinfo=UTC))
        self.assertLess(altar_moon.moon_age(dt.datetime(2024, 4, 8, 18, 30, tzinfo=UTC)), 0.01)
        self.assertEqual(altar_moon.phase_name(altar_moon.moon_age(dt.datetime(2025, 1, 13, 22, 27, tzinfo=UTC))),
                         "full moon")

    def sweeps(self, path: str) -> tuple[str, str, str]:
        arcs = re.findall(r"A([\d.]+) 44.00 0 0 (\d)", path)
        return arcs[1][0], arcs[0][1], arcs[1][1]

    def test_shape(self):
        # Full: two half circles that sweep the same way, so the whole disc is lit.
        rx, first, back = self.sweeps(altar_moon.moon_path(0.5, 50, 50, 44))
        self.assertEqual((rx, first == back), ("44.00", True))
        # New: the second arc retraces the first, so nothing is lit.
        rx, first, back = self.sweeps(altar_moon.moon_path(0.0, 50, 50, 44))
        self.assertEqual((rx, first == back), ("44.00", False))
        self.assertIn("A0.00 44.00", altar_moon.moon_path(0.25, 50, 50, 44))
        self.assertNotEqual(altar_moon.moon_path(0.1, 50, 50, 44), altar_moon.moon_path(0.1, 50, 50, 44, south=True))

    def test_new_moons_for_the_live_page(self):
        nm = altar_moon.upcoming_new_moons(NOW, 30)
        self.assertEqual(len(nm), 31)
        self.assertLessEqual(nm[0], NOW.timestamp() * 1000)
        self.assertGreater(nm[1], NOW.timestamp() * 1000)

    def test_daily_line_matches_the_page_sum(self):
        self.assertEqual(dt.date(1970, 1, 1).toordinal(), 719163)
        self.assertEqual(build.daily_index(dt.date(2026, 10, 28), 3), dt.date(2026, 10, 28).toordinal() % 3)


class BuildOutput(unittest.TestCase):
    def test_outputs_and_self_contained(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            build.build(HER, out, None, build.STYLE_EXAMPLE, png=False, config_dir=ROOT, now=NOW)
            for name in ("altar.html", "index.html", "altar.widget/altar.html", "altar.widget/index.jsx"):
                self.assertTrue((out / name).is_file(), name)
            html = (out / "altar.html").read_text(encoding="utf-8")
            self.assertNotRegex(html, r"<script[^>]+src=")
            self.assertEqual(set(re.findall(r'(?:href|src)="(https?://[^/"]+)', html)),
                             {"https://fonts.googleapis.com", "https://fonts.gstatic.com"})
            self.assertEqual(html.count('class="obj '), 11)
            for page in (html, (ROOT / "arrange.html").read_text(encoding="utf-8")):
                self.assertNotIn("innerHTML", page)
                self.assertNotIn("console.log", page)
                self.assertNotIn("text-shadow", page)

    def test_words_cannot_break_out(self):
        cfg = mine_cfg()
        cfg["intention"] = "</script><script>alert(1)</script>"
        cfg["daily_line"] = ["</script><b>x</b>"]
        with tempfile.TemporaryDirectory() as tmp:
            res = build.build(cfg, Path(tmp) / "o", None, build.STYLE_EXAMPLE, png=False, now=NOW)
            html = res["html"].read_text(encoding="utf-8")
            self.assertNotIn("<script>alert(1)", html)
            self.assertNotIn("</script><b>", html)

    def test_own_picture_is_inlined(self):
        png = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15"
               b"\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa7\x35\x81\x84\x00\x00\x00\x00IEND\xaeB`\x82")
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "objects" / "mine").mkdir(parents=True)
            (tmp / "objects" / "mine" / "nana.png").write_bytes(png)
            cfg = {"objects": [{"image": "nana.png", "label": "nana"}]}
            res = build.build(cfg, tmp / "o", None, build.STYLE_EXAMPLE, png=False, config_dir=tmp, now=NOW)
            self.assertIn('src="data:image/png;base64,', res["html"].read_text(encoding="utf-8"))
            with self.assertRaises(ValueError):
                build.build({"objects": [{"image": "gone.png"}]}, tmp / "p", None, build.STYLE_EXAMPLE,
                            png=False, config_dir=tmp, now=NOW)

    def test_cli_reports_problems_kindly(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "altar.config.json"
            bad.write_text(json.dumps({"objects": [{"type": "unicorn"}]}), encoding="utf-8")
            import io
            from contextlib import redirect_stderr
            err = io.StringIO()
            with redirect_stderr(err):
                code = build.main([str(bad), "--out", str(Path(tmp) / "o"), "--no-png"])
            self.assertEqual(code, 1)
            self.assertIn("A few things to fix", err.getvalue())

    @unittest.skipUnless(CHROME, "Chrome not installed: skipping the PNG test")
    def test_png_at_screen_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            res = build.build(HER, Path(tmp) / "o", "analog", build.STYLE_EXAMPLE, "1440x900", ROOT, True, NOW)
            self.assertIsNotNone(res["png"], res["message"])
            self.assertEqual(render.png_size(res["png"]), (1440, 900))


@unittest.skipUnless(CHROME, "Chrome not installed: skipping the headless render tests")
class Render(unittest.TestCase):
    SIGNS = {"analog": "tape", "cyberpunk": "prompt", "y2k-blog": "counter"}

    def check(self, cfg: dict, w: int, h: int):
        with tempfile.TemporaryDirectory() as tmp:
            for motif in build.MOTIFS:
                page = build.build(cfg, Path(tmp) / motif, motif, build.STYLE_EXAMPLE, f"{w}x{h}", ROOT, False, NOW)["html"]
                rep = render.measure(page, w, h, "?still=1")
                self.assertNotIn("error", rep, rep)
                where = f"{motif} at {w}x{h}"
                self.assertIn(f"m-{motif}", rep["cls"], where)
                self.assertLessEqual(rep["sw"], rep["iw"], f"sideways scroll in {where}")
                self.assertLessEqual(rep["frameRight"], rep["iw"] + 0.5, f"altar cut off at the side in {where}")
                self.assertLessEqual(rep["frameBottom"], rep["ih"] + 0.5, f"altar cut off at the bottom in {where}")
                self.assertTrue(rep[self.SIGNS[motif]], f"{motif} lost its signature")
                self.assertEqual(rep["objs"], len(cfg["objects"]), where)
                self.assertTrue(rep["moon"].startswith("M50.00 6.00"), where)

    def test_her_altar_at_both_sizes(self):
        self.check(HER, 2560, 1600)
        self.check(HER, 1440, 900)

    def test_a_full_altar_still_fits(self):
        cfg = copy.deepcopy(HER)
        cfg["objects"] = [{"type": t, "label": "a little label"} for t in build.OBJECT_TYPES[:16]]
        cfg["intention"] = "My intention is long today and it keeps going on and on because I have a lot to say " \
                           "about this moon and this one"
        self.check(cfg, 1440, 900)
        self.check(cfg, 2560, 1600)

    def test_arrange_page_saves_a_valid_altar(self):
        picks = [build.OBJECT_TYPES.index(t) for t in ("candle", "rose", "bell")]
        cfg = render.run_arrange(ROOT / "arrange.html", picks, "my altar", "steady", ["one", "two"], "cyberpunk")
        self.assertNotIn("error", cfg, cfg)
        self.assertEqual(build.validate_config(cfg), [])
        self.assertEqual([o["type"] for o in cfg["objects"]], ["candle", "rose", "bell"])
        self.assertEqual(cfg["motif"], "cyberpunk")
        self.assertEqual(cfg["daily_line"], ["one", "two"])


if __name__ == "__main__":
    unittest.main()
