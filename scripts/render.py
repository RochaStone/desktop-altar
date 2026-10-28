"""Headless Chrome tools for desktop-altar: screenshots, a true-size overflow check, and an arrange.html run.

Copied from the sibling kit desktop-core (scripts/render.py, MIT) and adapted for the altar.

Chrome on macOS will not shrink a headless window under 500px, so phone widths are measured inside an
iframe of the exact width. The page reports its own scrollWidth from inside that frame.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path


def find_chrome() -> str | None:
    env = os.environ.get("CHROME_PATH")
    if env and Path(env).exists():
        return env
    for cmd in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "microsoft-edge"):
        p = shutil.which(cmd)
        if p:
            return p
    for p in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Chromium.app/Contents/MacOS/Chromium",
              "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
              r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"):
        if Path(p).exists():
            return p
    return None


NO_CHROME = ("Chrome or Chromium is missing on this computer, so the wallpaper picture is skipped this time. "
             "Your altar.html is ready and opens in any browser. Install Chrome, or set CHROME_PATH, then build again.")


def png_size(path: Path) -> tuple[int, int]:
    head = Path(path).read_bytes()[:24]
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    return struct.unpack(">II", head[16:24])


def _run(args: list[str], width: int, height: int, budget: int = 6000) -> subprocess.CompletedProcess | None:
    chrome = find_chrome()
    if not chrome:
        return None
    with tempfile.TemporaryDirectory() as profile:
        cmd = [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
               "--no-default-browser-check", "--allow-file-access-from-files", f"--user-data-dir={profile}",
               f"--window-size={width},{height}", "--force-device-scale-factor=1",
               f"--virtual-time-budget={budget}", *args]
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            cmd.insert(1, "--no-sandbox")
        try:
            return subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return None


def screenshot(url: str, png: Path, width: int, height: int) -> tuple[bool, str]:
    res = _run([f"--screenshot={png}", url], width, height)
    if res is None:
        return False, NO_CHROME
    if not Path(png).exists():
        return False, "Chrome ran but wrote no picture."
    w, h = png_size(png)
    return True, f"{png} ({w}x{h})"


HARNESS = """<!doctype html><html><body style="margin:0"><iframe id="f" src="{src}" style="width:{w}px;height:{h}px;border:0"></iframe>
<pre id="r">pending</pre><script>
document.getElementById("f").onload = function () {{
  var fr = this;
  setTimeout(function () {{
    var out = document.getElementById("r");
    try {{
      var d = fr.contentDocument, de = d.documentElement, vis = function (sel) {{
        var n = d.querySelector(sel); return !!n && getComputedStyle(n).display !== "none"; }};
      out.textContent = JSON.stringify({{iw: fr.contentWindow.innerWidth, ih: fr.contentWindow.innerHeight,
        sw: de.scrollWidth, sh: de.scrollHeight, cls: de.className, text: d.body.innerText.slice(0, 4000),
        objs: d.querySelectorAll(".obj").length, flames: d.querySelectorAll(".flame").length,
        bar: vis(".bar"), prompt: vis(".prompt"), tape: vis(".tape"), counter: vis(".counter"),
        moon: (d.querySelector(".moon-lit") || {{getAttribute: function () {{ return ""; }}}}).getAttribute("d"),
        frameBottom: d.querySelector(".frame").getBoundingClientRect().bottom,
        frameRight: d.querySelector(".frame").getBoundingClientRect().right}});
    }} catch (e) {{ out.textContent = JSON.stringify({{error: e.message}}); }}
  }}, 1500);
}};
</script></body></html>"""

ARRANGE = """<!doctype html><html><body style="margin:0"><iframe id="f" src="{src}" style="width:1280px;height:1100px;border:0"></iframe>
<pre id="r">pending</pre><script>
document.getElementById("f").onload = function () {{
  var fr = this, w = fr.contentWindow, d = fr.contentDocument, out = document.getElementById("r");
  try {{
    var blob = null;
    w.URL.createObjectURL = function (b) {{ blob = b; return "about:blank"; }};
    w.HTMLAnchorElement.prototype.click = function () {{}};
    var drawer = d.querySelectorAll("#drawer button");
    {clicks}
    d.getElementById("name").value = {name};
    d.getElementById("intention").value = {intention};
    d.getElementById("daily").value = {daily};
    d.getElementById("motif").value = {motif};
    d.getElementById("save").click();
    if (!blob) {{ out.textContent = JSON.stringify({{error: d.getElementById("note").textContent}}); return; }}
    blob.text().then(function (t) {{ out.textContent = t; }});
  }} catch (e) {{ out.textContent = JSON.stringify({{error: e.message}}); }}
}};
</script></body></html>"""


def measure(page: Path, width: int, height: int = 900, query: str = "") -> dict:
    """Load the page inside an iframe exactly `width` wide and return what it reports about itself."""
    page = Path(page).resolve()
    with tempfile.TemporaryDirectory() as tmp:
        harness = Path(tmp) / "harness.html"
        harness.write_text(HARNESS.format(src=page.as_uri() + query, w=width, h=height), encoding="utf-8")
        res = _run(["--dump-dom", harness.as_uri()], max(width, 800), height + 200, budget=8000)
    if res is None:
        return {"error": NO_CHROME}
    m = re.search(r'<pre id="r">(.*?)</pre>', res.stdout, re.S)
    if not m:
        return {"error": "Chrome gave no report."}
    raw = m.group(1).replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&amp;", "&")
    try:
        return json.loads(raw)
    except ValueError:
        return {"error": "report was " + raw[:80]}


def run_arrange(page: Path, picks: list[int], name: str, intention: str, daily: list[str], motif: str,
                shot: Path | None = None) -> dict:
    """Open arrange.html, click drawer objects, fill the form, press save, and return the JSON it would download."""
    page = Path(page).resolve()
    clicks = "".join(f"drawer[{i}].click();" for i in picks)
    js = json.dumps
    with tempfile.TemporaryDirectory() as tmp:
        harness = Path(tmp) / "arrange-harness.html"
        harness.write_text(ARRANGE.format(src=page.as_uri(), clicks=clicks, name=js(name), intention=js(intention),
                                          daily=js("\n".join(daily)), motif=js(motif)), encoding="utf-8")
        if shot is not None:
            ok, msg = screenshot(harness.as_uri(), Path(shot), 1280, 1100)
            if not ok:
                return {"error": msg}
        res = _run(["--dump-dom", harness.as_uri()], 1400, 1300, budget=8000)
    if res is None:
        return {"error": NO_CHROME}
    m = re.search(r'<pre id="r">(.*?)</pre>', res.stdout, re.S)
    if not m:
        return {"error": "Chrome gave no report."}
    raw = m.group(1).replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&amp;", "&")
    try:
        return json.loads(raw)
    except ValueError:
        return {"error": "report was " + raw[:80]}


CLICK = """<!doctype html><html><body style="margin:0"><iframe id="f" src="{src}" style="width:1280px;height:800px;border:0"></iframe>
<pre id="r">pending</pre><script>
var loads = 0, rep = {{}};
document.getElementById("f").onload = function () {{
  var fr = this, d = fr.contentDocument, out = document.getElementById("r");
  loads += 1;
  try {{
    var first = function () {{ return d.querySelector(".lightable"); }};
    if (loads === 1) {{
      rep.count = d.querySelectorAll(".lightable").length;
      rep.litAtStart = !first().classList.contains("out");
      first().click();
      rep.outAfterClick = first().classList.contains("out");
      rep.pressed = first().getAttribute("aria-pressed");
      rep.stored = fr.contentWindow.localStorage.length > 0;
      fr.contentWindow.location.reload();
    }} else {{
      rep.rememberedAfterReload = first().classList.contains("out");
      first().dispatchEvent(new KeyboardEvent("keydown", {{key: "Enter", bubbles: true}}));
      rep.litAgainByKeyboard = !first().classList.contains("out");
      fr.contentWindow.localStorage.clear();
      out.textContent = JSON.stringify(rep);
    }}
  }} catch (e) {{ out.textContent = JSON.stringify({{error: e.message}}); }}
}};
</script></body></html>"""


def run_clicks(page: Path) -> dict:
    """Click the first candle in altar.html, reload, and report whether the altar remembered."""
    page = Path(page).resolve()
    with tempfile.TemporaryDirectory() as tmp:
        harness = Path(tmp) / "click-harness.html"
        harness.write_text(CLICK.format(src=page.as_uri()), encoding="utf-8")
        res = _run(["--dump-dom", harness.as_uri()], 1400, 1000, budget=8000)
    if res is None:
        return {"error": NO_CHROME}
    m = re.search(r'<pre id="r">(.*?)</pre>', res.stdout, re.S)
    if not m:
        return {"error": "Chrome gave no report."}
    raw = m.group(1).replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&amp;", "&")
    try:
        return json.loads(raw)
    except ValueError:
        return {"error": "report was " + raw[:80]}
