"""Moon phase maths for desktop-altar. Pure Python, no network, no dependencies.

Ported from the sibling Rocha Coded kit analog-bag (core/moon.py, MIT, Copyright (c) 2026
Rochelle Livingstone / Thriving Era Studio). Only the moon part is kept here; the seasons part stays there.
Phases use Jean Meeus, Astronomical Algorithms (2nd ed.), chapter 49, with the periodic and planetary
correction terms, then subtract Delta T to get UT. Accuracy is a few minutes.

Added for the altar: phase_name(), upcoming_new_moons() (so the live page can keep the moon true for
months without the internet) and moon_path() (the lit part of the moon as one SVG path).
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

J2000 = 2451545.0
SYNODIC = 29.530588861
PHASE_NAMES = ("new moon", "first quarter", "full moon", "last quarter")


def _sin(deg: float) -> float:
    return math.sin(math.radians(deg))


def _cos(deg: float) -> float:
    return math.cos(math.radians(deg))


def jd_to_datetime(jd: float) -> datetime:
    """Julian Day to an aware UTC datetime."""
    return datetime(2000, 1, 1, 12, tzinfo=timezone.utc) + timedelta(days=jd - J2000)


def datetime_to_jd(dt: datetime) -> float:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = dt - datetime(2000, 1, 1, 12, tzinfo=timezone.utc)
    return J2000 + delta.total_seconds() / 86400.0


def delta_t_seconds(year: float) -> float:
    """Delta T (TT minus UT). NASA polynomial for 2005 to 2050, held flat outside it."""
    t = min(max(year, 2005.0), 2050.0) - 2000.0
    return 62.92 + 0.32217 * t + 0.005589 * t * t


def _phase_jde(k: float) -> float:
    """Meeus 49.1 plus corrections. k is an integer for new moon, +.25 first quarter,
    +.5 full, +.75 last quarter. Returns JDE (Dynamical Time)."""
    t = k / 1236.85
    jde = (2451550.09766 + SYNODIC * k + 0.00015437 * t**2
           - 0.000000150 * t**3 + 0.00000000073 * t**4)
    e = 1 - 0.002516 * t - 0.0000074 * t**2
    m = 2.5534 + 29.10535670 * k - 0.0000014 * t**2 - 0.00000011 * t**3
    mp = (201.5643 + 385.81693528 * k + 0.0107582 * t**2
          + 0.00001238 * t**3 - 0.000000058 * t**4)
    f = (160.7108 + 390.67050284 * k - 0.0016118 * t**2
         - 0.00000227 * t**3 + 0.000000011 * t**4)
    om = 124.7746 - 1.56375588 * k + 0.0020672 * t**2 + 0.00000215 * t**3
    frac = round((k - math.floor(k)) * 4) % 4

    if frac in (0, 2):
        new = frac == 0
        c = ((-0.40720 if new else -0.40614) * _sin(mp)
             + (0.17241 if new else 0.17302) * e * _sin(m)
             + (0.01608 if new else 0.01614) * _sin(2 * mp)
             + (0.01039 if new else 0.01043) * _sin(2 * f)
             + (0.00739 if new else 0.00734) * e * _sin(mp - m)
             - (0.00514 if new else 0.00515) * e * _sin(mp + m)
             + (0.00208 if new else 0.00209) * e * e * _sin(2 * m)
             - 0.00111 * _sin(mp - 2 * f)
             - 0.00057 * _sin(mp + 2 * f)
             + 0.00056 * e * _sin(2 * mp + m)
             - 0.00042 * _sin(3 * mp)
             + 0.00042 * e * _sin(m + 2 * f)
             + 0.00038 * e * _sin(m - 2 * f)
             - 0.00024 * e * _sin(2 * mp - m)
             - 0.00017 * _sin(om)
             - 0.00007 * _sin(mp + 2 * m)
             + 0.00004 * _sin(2 * mp - 2 * f)
             + 0.00004 * _sin(3 * m)
             + 0.00003 * _sin(mp + m - 2 * f)
             + 0.00003 * _sin(2 * mp + 2 * f)
             - 0.00003 * _sin(mp + m + 2 * f)
             + 0.00003 * _sin(mp - m + 2 * f)
             - 0.00002 * _sin(mp - m - 2 * f)
             - 0.00002 * _sin(3 * mp + m)
             + 0.00002 * _sin(4 * mp))
    else:
        c = (-0.62801 * _sin(mp)
             + 0.17172 * e * _sin(m)
             - 0.01183 * e * _sin(mp + m)
             + 0.00862 * _sin(2 * mp)
             + 0.00804 * _sin(2 * f)
             + 0.00454 * e * _sin(mp - m)
             + 0.00204 * e * e * _sin(2 * m)
             - 0.00180 * _sin(mp - 2 * f)
             - 0.00070 * _sin(mp + 2 * f)
             - 0.00040 * _sin(3 * mp)
             - 0.00034 * e * _sin(2 * mp - m)
             + 0.00032 * e * _sin(m + 2 * f)
             + 0.00032 * e * _sin(m - 2 * f)
             - 0.00028 * e * e * _sin(mp + 2 * m)
             + 0.00027 * e * _sin(2 * mp + m)
             - 0.00017 * _sin(om)
             - 0.00005 * _sin(mp - m - 2 * f)
             + 0.00004 * _sin(2 * mp + 2 * f)
             - 0.00004 * _sin(mp + m + 2 * f)
             + 0.00004 * _sin(mp - 2 * m)
             + 0.00003 * _sin(mp + m - 2 * f)
             + 0.00003 * _sin(3 * m)
             + 0.00002 * _sin(2 * mp - 2 * f)
             + 0.00002 * _sin(mp - m + 2 * f)
             - 0.00002 * _sin(3 * mp + m))
        w = (0.00306 - 0.00038 * e * _cos(m) + 0.00026 * _cos(mp)
             - 0.00002 * _cos(mp - m) + 0.00002 * _cos(mp + m) + 0.00002 * _cos(2 * f))
        c += w if frac == 1 else -w

    planetary = (
        (0.000325, 299.77 + 0.107408 * k - 0.009173 * t**2),
        (0.000165, 251.88 + 0.016321 * k), (0.000164, 251.83 + 26.651886 * k),
        (0.000126, 349.42 + 36.412478 * k), (0.000110, 84.66 + 18.206239 * k),
        (0.000062, 141.74 + 53.303771 * k), (0.000060, 207.14 + 2.453732 * k),
        (0.000056, 154.84 + 7.306860 * k), (0.000047, 34.52 + 27.261239 * k),
        (0.000042, 207.19 + 0.121824 * k), (0.000040, 291.34 + 1.844379 * k),
        (0.000037, 161.72 + 24.198154 * k), (0.000035, 239.56 + 25.513099 * k),
        (0.000023, 331.55 + 3.592518 * k),
    )
    return jde + c + sum(a * _sin(arg) for a, arg in planetary)


def _jde_to_ut(jde: float) -> datetime:
    dt = jd_to_datetime(jde)
    return dt - timedelta(seconds=delta_t_seconds(dt.year + dt.timetuple().tm_yday / 365.25))


def phases_between(start: datetime, end: datetime) -> list[tuple[str, datetime]]:
    """Every principal phase with start <= time < end, as (name, UTC datetime)."""
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    years = start.year + (start.timetuple().tm_yday - 1) / 365.25 - 2000
    k = math.floor(years * 12.3685) - 1
    out: list[tuple[str, datetime]] = []
    while True:
        for q in range(4):
            when = _jde_to_ut(_phase_jde(k + q / 4))
            if when >= end:
                return out
            if when >= start:
                out.append((PHASE_NAMES[q], when))
        k += 1


def new_moon_jd(k: int) -> float:
    return datetime_to_jd(_jde_to_ut(_phase_jde(float(k))))


def moon_age(when: datetime) -> float:
    """Fraction of the lunation since the last new moon: 0 new, 0.5 full, toward 1 dark."""
    jd = datetime_to_jd(when)
    k = math.floor((jd - 2451550.09766) / SYNODIC)
    while new_moon_jd(k) > jd:
        k -= 1
    while new_moon_jd(k + 1) <= jd:
        k += 1
    nm, nxt = new_moon_jd(k), new_moon_jd(k + 1)
    return (jd - nm) / (nxt - nm)


def illumination(age: float) -> float:
    return (1 - math.cos(2 * math.pi * age)) / 2


PHASE8 = ("new moon", "waxing crescent", "first quarter", "waxing gibbous",
          "full moon", "waning gibbous", "last quarter", "waning crescent")


def phase_name(age: float) -> str:
    """One of eight names for a lunation fraction (0 new, 0.5 full)."""
    return PHASE8[int(math.floor(age * 8 + 0.5)) % 8]


def upcoming_new_moons(when: datetime, count: int = 30) -> list[int]:
    """The new moon before `when` and the next `count`, as Unix milliseconds (UTC)."""
    jd = datetime_to_jd(when)
    k = math.floor((jd - 2451550.09766) / SYNODIC)
    while new_moon_jd(k) > jd:
        k -= 1
    out = []
    for i in range(count + 1):
        dt = jd_to_datetime(new_moon_jd(k + i))
        out.append(int(dt.timestamp() * 1000))
    return out


def moon_path(age: float, cx: float, cy: float, r: float, south: bool = False) -> str:
    """The lit part of the moon as an SVG path. Waxing is lit on the right in the north.
    The terminator is a half-ellipse whose width follows cos(2 pi age)."""
    k = math.cos(2 * math.pi * age)
    rx = abs(k) * r
    waxing = age < 0.5
    right = waxing != south
    first = 1 if right else 0
    back = (0 if k > 0 else 1) if right else (1 if k > 0 else 0)
    top, bot = f"{cx:.2f} {cy - r:.2f}", f"{cx:.2f} {cy + r:.2f}"
    return (f"M{top} A{r:.2f} {r:.2f} 0 0 {first} {bot} "
            f"A{rx:.2f} {r:.2f} 0 0 {back} {top} Z")
