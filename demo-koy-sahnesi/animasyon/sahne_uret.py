#!/usr/bin/env python3
"""Köy sahnesi: köylü kız (Elif) ve babası. index.html üretici (HyperFrames kompozisyonu).

Süreler ../timing.json'dan (sure_olc.py çıktısı, Audio Lock), altyazılar ../cumleler.txt'den gelir.
Ağız açıklığı ses dosyasının ses şiddeti zarfından (30 kare/sn) çıkar: hece sayarak değil, sesin
kendisinden. Çizimlerin hepsi koddur (SVG); görsel modeli kullanılmadı.

Kullanım (demo-koy-sahnesi/animasyon içinde):  python3 sahne_uret.py
"""
import json
import random
import wave
from array import array
from html import escape
from pathlib import Path

AYRI = Path(__file__).resolve().parent
KOK = AYRI.parent
TIMING = json.loads((KOK / "timing.json").read_text(encoding="utf-8"))
SATIRLAR = []
for ham in (KOK / "cumleler.txt").read_text(encoding="utf-8").splitlines():
    if ham.strip():
        ad, _, metin = ham.partition(":")
        SATIRLAR.append((ad.strip(), metin.strip()))
assert len(SATIRLAR) == len(TIMING["cumleler"]), "cümle sayısı ile ses sayısı aynı olmalı"
KONUSMACI = {"elif": ("e", "Elif"), "baba": ("b", "Baba")}

W, H = 1280, 720
HOR = 380  # ufuk çizgisi
NAVY = "#1d2b4a"
SKIN, SKIN2 = "#f0c49a", "#e0a574"


# ---------------------------------------------------------------- ses zarfı (ağız)
def zarf(yol: Path, fps: int = 30) -> list[int]:
    with wave.open(str(yol), "rb") as w:
        sr, kanal = w.getframerate(), w.getnchannels()
        ham = array("h")
        ham.frombytes(w.readframes(w.getnframes()))
    if kanal > 1:
        ham = ham[::kanal]
    adim = max(1, sr // fps)
    rms = []
    for i in range(0, len(ham), adim):
        blok = ham[i:i + adim]
        if blok:
            rms.append((sum(x * x for x in blok) / len(blok)) ** 0.5)
    p90 = sorted(rms)[int(len(rms) * 0.9)] or 1.0
    v = [min(1.0, r / p90) for r in rms]
    v = [0.0 if x < 0.14 else x for x in v]
    n = len(v)
    sm = [0.25 * v[max(0, i - 1)] + 0.5 * v[i] + 0.25 * v[min(n - 1, i + 1)] for i in range(n)]
    return [int(round(x * 20)) * 5 for x in sm]


# ---------------------------------------------------------------- küçük çizim yardımcıları
def uzuv(x1, y1, x2, y2, w, renk):
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{NAVY}" stroke-width="{w + 6}" stroke-linecap="round"/>'
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{renk}" stroke-width="{w}" stroke-linecap="round"/>')


def kol(p, taraf, sx, sy, ust, alt, kol_rengi, on_rengi, w):
    """Yerel pivotlar mutlak tuval koordinatında (svgOrigin). L = izleyicinin solu."""
    d = -1 if taraf == "L" else 1
    ex, ey = sx + d * 4, sy + ust
    wx, wy = ex + d * 3, ey + alt
    return (f'<g class="{p}-a{taraf}" data-ox="{sx:.1f}" data-oy="{sy:.1f}">'
            + uzuv(sx, sy, ex, ey, w, kol_rengi)
            + f'<g class="{p}-f{taraf}" data-ox="{ex:.1f}" data-oy="{ey:.1f}">'
            + uzuv(ex, ey, wx, wy, w - 3, on_rengi)
            + f'<circle cx="{wx:.1f}" cy="{wy + 3:.1f}" r="{w * 0.56:.1f}" fill="{SKIN}" stroke="{NAVY}" stroke-width="3.5"/>'
            + "</g></g>")


def yuz_ortak(p, fx, by, r, agiz_rx, my):
    """Gözler (kırpma grubu), gülümseme ve açık ağız (zarfla ölçeklenir)."""
    ex = r * 0.37
    ge = by + 3
    gozler = (
        f'<g class="{p}-goz" data-ox="{fx:.1f}" data-oy="{ge:.1f}">'
        f'<circle cx="{fx - ex:.1f}" cy="{ge:.1f}" r="{r * 0.105:.1f}" fill="{NAVY}"/>'
        f'<circle cx="{fx + ex:.1f}" cy="{ge:.1f}" r="{r * 0.105:.1f}" fill="{NAVY}"/>'
        f'<circle cx="{fx - ex + 1.2:.1f}" cy="{ge - 1.3:.1f}" r="1.2" fill="#ffffff"/>'
        f'<circle cx="{fx + ex + 1.2:.1f}" cy="{ge - 1.3:.1f}" r="1.2" fill="#ffffff"/></g>'
    )
    gulus = (f'<path class="{p}-gulus" d="M{fx - agiz_rx:.1f},{my:.1f} Q{fx:.1f},{my + 8:.1f} {fx + agiz_rx:.1f},{my:.1f}" '
             f'fill="none" stroke="{NAVY}" stroke-width="3.6" stroke-linecap="round"/>')
    agiz = (f'<ellipse class="{p}-agiz" cx="{fx:.1f}" cy="{my + 2:.1f}" rx="{agiz_rx:.1f}" ry="8" fill="#7a2230" '
            f'stroke="{NAVY}" stroke-width="2.6" opacity="0" data-ox="{fx:.1f}" data-oy="{my:.1f}"/>')
    return gozler + gulus + agiz


def baba_ciz(p, fx, fy):
    bacak, govde, r = 92, 104, 37
    kalca = fy - bacak
    omuz = kalca - govde
    by = omuz - r - 7
    PANTOL, SOS, GOMLEK, YELEK, KUSAK, KASKET = "#4d5b73", "#3a2a20", "#efe6d2", "#7a5236", "#b5322a", "#6b6f78"
    s = []
    for dx in (-13, 13):
        s.append(uzuv(fx + dx * 0.8, kalca, fx + dx * 1.15, fy - 10, 24, PANTOL))
        s.append(f'<ellipse cx="{fx + dx * 1.25 + (3 if dx > 0 else -3):.1f}" cy="{fy - 3}" rx="17" ry="9" fill="{SOS}" stroke="{NAVY}" stroke-width="3.5"/>')
    s.append(uzuv(fx, omuz - 12, fx, omuz + 2, 13, SKIN))
    s.append(f'<path d="M{fx - 26},{omuz} Q{fx},{omuz - 7} {fx + 26},{omuz} L{fx + 24},{kalca + 5} L{fx - 24},{kalca + 5} Z" '
             f'fill="{GOMLEK}" stroke="{NAVY}" stroke-width="4" stroke-linejoin="round"/>')
    s.append(f'<path d="M{fx - 25},{omuz + 2} L{fx - 7},{omuz + 4} L{fx - 5},{kalca - 6} L{fx - 23},{kalca - 6} Z" fill="{YELEK}" stroke="{NAVY}" stroke-width="3" stroke-linejoin="round"/>')
    s.append(f'<path d="M{fx + 25},{omuz + 2} L{fx + 7},{omuz + 4} L{fx + 5},{kalca - 6} L{fx + 23},{kalca - 6} Z" fill="{YELEK}" stroke="{NAVY}" stroke-width="3" stroke-linejoin="round"/>')
    s.append(f'<rect x="{fx - 25}" y="{kalca - 10}" width="50" height="13" rx="3" fill="{KUSAK}" stroke="{NAVY}" stroke-width="3"/>')
    for dy in (10, 34, 58):
        s.append(f'<circle cx="{fx}" cy="{omuz + dy}" r="2.4" fill="{NAVY}"/>')
    s.append(kol(p, "L", fx - 27, omuz + 8, 54, 50, GOMLEK, SKIN, 15))
    s.append(kol(p, "R", fx + 27, omuz + 8, 54, 50, GOMLEK, SKIN, 15))
    my = by + r * 0.42 + 11
    bas = [
        f'<circle cx="{fx - r * 0.97:.1f}" cy="{by + 5:.1f}" r="8" fill="{SKIN}" stroke="{NAVY}" stroke-width="3"/>',
        f'<circle cx="{fx + r * 0.97:.1f}" cy="{by + 5:.1f}" r="8" fill="{SKIN}" stroke="{NAVY}" stroke-width="3"/>',
        f'<circle cx="{fx}" cy="{by}" r="{r}" fill="{SKIN}" stroke="{NAVY}" stroke-width="4"/>',
        f'<line x1="{fx - r * 0.55:.1f}" y1="{by - 7}" x2="{fx - r * 0.17:.1f}" y2="{by - 10}" stroke="#4e4038" stroke-width="5.5" stroke-linecap="round"/>',
        f'<line x1="{fx + r * 0.55:.1f}" y1="{by - 7}" x2="{fx + r * 0.17:.1f}" y2="{by - 10}" stroke="#4e4038" stroke-width="5.5" stroke-linecap="round"/>',
        f'<ellipse cx="{fx}" cy="{by + r * 0.22:.1f}" rx="6.5" ry="7.5" fill="{SKIN2}" stroke="{NAVY}" stroke-width="2.6"/>',
        yuz_ortak(p, fx, by, r, 9, my),
    ]
    y0 = by + r * 0.42
    bas.append(f'<path d="M{fx - 25},{y0:.1f} Q{fx - 12},{y0 - 13:.1f} {fx},{y0 - 4:.1f} Q{fx + 12},{y0 - 13:.1f} {fx + 25},{y0:.1f} '
               f'Q{fx + 17},{y0 + 9:.1f} {fx},{y0 + 1:.1f} Q{fx - 17},{y0 + 9:.1f} {fx - 25},{y0:.1f} Z" fill="#5a493d" stroke="{NAVY}" stroke-width="2.6" stroke-linejoin="round"/>')
    bas.append(f'<ellipse cx="{fx}" cy="{by - 12}" rx="{r * 0.93:.1f}" ry="7.5" fill="#575b64" stroke="{NAVY}" stroke-width="3.2"/>')
    bas.append(f'<path d="M{fx - r - 2},{by - 12} A{r + 2},{r + 2} 0 0 1 {fx + r + 2},{by - 12} Z" fill="{KASKET}" stroke="{NAVY}" stroke-width="4" stroke-linejoin="round"/>')
    bas.append(f'<circle cx="{fx}" cy="{by - r - 7}" r="4" fill="#575b64" stroke="{NAVY}" stroke-width="2.6"/>')
    s.append(f'<g class="{p}-bas" data-ox="{fx}" data-oy="{omuz - 4}">' + "".join(bas) + "</g>")
    return f'<g class="{p}">' + "".join(s) + "</g>"


def kiz_ciz(p, fx, fy):
    bacak, govde, r = 58, 74, 33
    kalca = fy - bacak
    omuz = kalca - govde
    by = omuz - r - 6
    ELBISE, ONLUK, SAC, KURDELE, SOS = "#e8a33d", "#fff4e4", "#5a3a22", "#d6382f", "#7a4a2c"
    s = []
    for dx in (-10, 10):
        s.append(uzuv(fx + dx, kalca + 24, fx + dx * 1.1, fy - 7, 9, SKIN))
        s.append(f'<ellipse cx="{fx + dx * 1.2 + (2 if dx > 0 else -2):.1f}" cy="{fy - 3}" rx="12" ry="7" fill="{SOS}" stroke="{NAVY}" stroke-width="3.2"/>')
    s.append(uzuv(fx, omuz - 10, fx, omuz + 2, 11, SKIN))
    s.append(f'<path d="M{fx - 18},{omuz} Q{fx},{omuz - 6} {fx + 18},{omuz} L{fx + 38},{kalca + 28} Q{fx},{kalca + 36} {fx - 38},{kalca + 28} Z" '
             f'fill="{ELBISE}" stroke="{NAVY}" stroke-width="4" stroke-linejoin="round"/>')
    s.append(f'<path d="M{fx - 37},{kalca + 21} Q{fx},{kalca + 29} {fx + 37},{kalca + 21}" fill="none" stroke="{KURDELE}" stroke-width="5"/>')
    s.append(f'<path d="M{fx - 12},{omuz + 14} L{fx + 12},{omuz + 14} L{fx + 22},{kalca + 26} Q{fx},{kalca + 32} {fx - 22},{kalca + 26} Z" '
             f'fill="{ONLUK}" stroke="{NAVY}" stroke-width="3" stroke-linejoin="round"/>')
    s.append(f'<rect x="{fx - 17}" y="{kalca + 6}" width="14" height="13" rx="2" fill="#9ec9e8" stroke="{NAVY}" stroke-width="2.4" stroke-dasharray="4 2"/>')
    s.append(kol(p, "L", fx - 17, omuz + 7, 38, 36, ONLUK, SKIN, 11))
    s.append(kol(p, "R", fx + 17, omuz + 7, 38, 36, ONLUK, SKIN, 11))
    my = by + r * 0.5 + 6
    bas = [f'<circle cx="{fx}" cy="{by - 3}" r="{r + 3}" fill="{SAC}" stroke="{NAVY}" stroke-width="4"/>']
    for d, ad in ((-1, "L"), (1, "R")):
        ax, ay = fx + d * (r - 3), by + 8
        segs = []
        for i in range(4):
            segs.append(f'<ellipse cx="{ax + d * i * 2.6:.1f}" cy="{ay + i * 15:.1f}" rx="{9 - 0.9 * i:.1f}" ry="10" fill="{SAC}" stroke="{NAVY}" stroke-width="3"/>')
        bx, bY = ax + d * 10, ay + 62
        segs.append(f'<path d="M{bx:.1f},{bY} L{bx - 10:.1f},{bY - 8} L{bx - 10:.1f},{bY + 8} Z M{bx:.1f},{bY} L{bx + 10:.1f},{bY - 8} L{bx + 10:.1f},{bY + 8} Z" fill="{KURDELE}" stroke="{NAVY}" stroke-width="2.4" stroke-linejoin="round"/>')
        bas.append(f'<g class="{p}-ort{ad}" data-ox="{ax:.1f}" data-oy="{ay:.1f}">' + "".join(segs) + "</g>")
    bas.append(f'<circle cx="{fx}" cy="{by}" r="{r}" fill="{SKIN}" stroke="{NAVY}" stroke-width="4"/>')
    bas.append(
        f'<path d="M{fx - r + 1},{by - 5} A{r},{r} 0 0 1 {fx + r - 1},{by - 5} C{fx + r * 0.6:.1f},{by - r * 0.46:.1f} {fx + r * 0.2:.1f},{by - r * 0.58:.1f} {fx},{by - r * 0.26:.1f} '
        f'C{fx - r * 0.2:.1f},{by - r * 0.58:.1f} {fx - r * 0.6:.1f},{by - r * 0.46:.1f} {fx - r + 1},{by - 5} Z" fill="{SAC}" stroke="{NAVY}" stroke-width="3" stroke-linejoin="round"/>')
    bas.append(f'<path d="M{fx - r * 0.55:.1f},{by - 2} Q{fx - r * 0.35:.1f},{by - 6} {fx - r * 0.15:.1f},{by - 3}" fill="none" stroke="{SAC}" stroke-width="2.6" stroke-linecap="round"/>')
    bas.append(f'<path d="M{fx + r * 0.55:.1f},{by - 2} Q{fx + r * 0.35:.1f},{by - 6} {fx + r * 0.15:.1f},{by - 3}" fill="none" stroke="{SAC}" stroke-width="2.6" stroke-linecap="round"/>')
    bas.append(f'<circle cx="{fx - r * 0.56:.1f}" cy="{by + r * 0.3:.1f}" r="6.5" fill="#f2907a" opacity="0.55"/>')
    bas.append(f'<circle cx="{fx + r * 0.56:.1f}" cy="{by + r * 0.3:.1f}" r="6.5" fill="#f2907a" opacity="0.55"/>')
    bas.append(f'<path d="M{fx - 2.5},{by + r * 0.2:.1f} Q{fx},{by + r * 0.3:.1f} {fx + 2.5},{by + r * 0.2:.1f}" fill="none" stroke="{SKIN2}" stroke-width="2.6" stroke-linecap="round"/>')
    bas.append(yuz_ortak(p, fx, by, r, 7.5, my))
    s.append(f'<g class="{p}-bas" data-ox="{fx}" data-oy="{omuz - 4}">' + "".join(bas) + "</g>")
    return f'<g class="{p}">' + "".join(s) + "</g>"


# ---------------------------------------------------------------- arka plan
def bulut(x, y, olcek):
    return (f'<g class="bulut"><g transform="translate({x} {y}) scale({olcek})" fill="#fff6ea" opacity="0.9">'
            '<ellipse cx="0" cy="6" rx="64" ry="17"/><circle cx="-24" cy="-8" r="22"/>'
            '<circle cx="10" cy="-18" r="28"/><circle cx="42" cy="-4" r="19"/></g></g>')


def ev(x, yb, w, h):
    cx, cy = x + w * 0.7 + 8, yb - h - h * 0.5
    kiremit = "".join(f'<line x1="{x - 8 + i * 6}" y1="{yb - h - h * 0.14 * (i + 1) + 2}" x2="{x + w + 8 - i * 6}" y2="{yb - h - h * 0.14 * (i + 1) + 2}" stroke="#8c3a28" stroke-width="2"/>' for i in range(3))
    return (
        f'<rect x="{x + w * 0.7:.1f}" y="{yb - h - h * 0.5:.1f}" width="16" height="{h * 0.4:.1f}" fill="#cbbfa9" stroke="{NAVY}" stroke-width="3"/>'
        f'<rect x="{x}" y="{yb - h}" width="{w}" height="{h}" fill="#e6d6b8" stroke="{NAVY}" stroke-width="3.5"/>'
        f'<polygon points="{x - 14},{yb - h} {x + w / 2:.1f},{yb - h - h * 0.62:.1f} {x + w + 14},{yb - h}" fill="#b5503a" stroke="{NAVY}" stroke-width="3.5" stroke-linejoin="round"/>'
        + kiremit +
        f'<rect x="{x + w * 0.12:.1f}" y="{yb - h * 0.62:.1f}" width="{w * 0.18:.1f}" height="{h * 0.62:.1f}" fill="#8a5a3a" stroke="{NAVY}" stroke-width="3"/>'
        f'<rect x="{x + w * 0.5:.1f}" y="{yb - h * 0.7:.1f}" width="{w * 0.22:.1f}" height="{h * 0.32:.1f}" fill="#9ec9e8" stroke="{NAVY}" stroke-width="3"/>'
        f'<line x1="{x + w * 0.61:.1f}" y1="{yb - h * 0.7:.1f}" x2="{x + w * 0.61:.1f}" y2="{yb - h * 0.38:.1f}" stroke="{NAVY}" stroke-width="2.4"/>'
        f'<circle class="duman" cx="{cx:.1f}" cy="{cy:.1f}" r="9" fill="#f1ede6" opacity="0" data-ox="{cx:.1f}" data-oy="{cy:.1f}"/>'
        f'<circle class="duman" cx="{cx:.1f}" cy="{cy:.1f}" r="9" fill="#f1ede6" opacity="0" data-ox="{cx:.1f}" data-oy="{cy:.1f}"/>'
    )


def ceviz(x, yb):
    return (f'<g class="agac" data-ox="{x}" data-oy="{yb}">'
            f'<path d="M{x - 9},{yb} L{x - 6},{yb - 80} L{x + 6},{yb - 80} L{x + 9},{yb} Z" fill="#7a5236" stroke="{NAVY}" stroke-width="3.5"/>'
            f'<circle cx="{x - 44}" cy="{yb - 100}" r="40" fill="#8f9f4b" stroke="{NAVY}" stroke-width="3.5"/>'
            f'<circle cx="{x + 44}" cy="{yb - 104}" r="42" fill="#8f9f4b" stroke="{NAVY}" stroke-width="3.5"/>'
            f'<circle cx="{x}" cy="{yb - 136}" r="50" fill="#9db055" stroke="{NAVY}" stroke-width="3.5"/>'
            f'<circle cx="{x - 14}" cy="{yb - 150}" r="22" fill="#b3c46a" opacity="0.7"/></g>')


def kavak(x, yb, h):
    return (f'<g class="agac" data-ox="{x}" data-oy="{yb}">'
            f'<rect x="{x - 4}" y="{yb - 34}" width="8" height="34" fill="#7a5236" stroke="{NAVY}" stroke-width="2.6"/>'
            f'<ellipse cx="{x}" cy="{yb - 34 - h / 2:.0f}" rx="{h * 0.16:.0f}" ry="{h / 2:.0f}" fill="#8a9f55" stroke="{NAVY}" stroke-width="3.2"/>'
            f'<ellipse cx="{x - 4}" cy="{yb - 34 - h * 0.58:.0f}" rx="{h * 0.07:.0f}" ry="{h * 0.3:.0f}" fill="#a3b86a" opacity="0.7"/></g>')


def citler():
    s = []
    for x in range(520, 920, 40):
        s.append(f'<rect x="{x}" y="{HOR + 30}" width="7" height="36" fill="#8a5a3a" stroke="{NAVY}" stroke-width="2.4"/>')
    s.append(f'<rect x="518" y="{HOR + 38}" width="404" height="5" fill="#9a6a45" stroke="{NAVY}" stroke-width="2"/>')
    s.append(f'<rect x="518" y="{HOR + 52}" width="404" height="5" fill="#9a6a45" stroke="{NAVY}" stroke-width="2"/>')
    return "".join(s)


def kuyu(x, y):
    taslar = "".join(
        f'<rect x="{x - 54 + ((i % 2) * 14) + j * 28}" y="{y - 48 + i * 15}" width="24" height="12" rx="3" fill="{c}" stroke="{NAVY}" stroke-width="1.8"/>'
        for i, c in enumerate(("#c3beb0", "#b2ad9f", "#c3beb0")) for j in range(4)
    )
    return (
        f'<ellipse cx="{x}" cy="{y + 2}" rx="68" ry="14" fill="#6f6a5e" opacity="0.45"/>'
        f'<rect x="{x - 56}" y="{y - 52}" width="112" height="52" fill="#b5b0a2" stroke="{NAVY}" stroke-width="3.5"/>' + taslar +
        f'<ellipse cx="{x}" cy="{y - 52}" rx="56" ry="14" fill="#7c8088" stroke="{NAVY}" stroke-width="3"/>'
        f'<ellipse cx="{x}" cy="{y - 52}" rx="40" ry="9" fill="#1f2a3a"/>'
        f'<rect x="{x - 52}" y="{y - 132}" width="9" height="84" fill="#8a5a3a" stroke="{NAVY}" stroke-width="3"/>'
        f'<rect x="{x + 43}" y="{y - 132}" width="9" height="84" fill="#8a5a3a" stroke="{NAVY}" stroke-width="3"/>'
        f'<rect x="{x - 58}" y="{y - 140}" width="116" height="11" fill="#6e472b" stroke="{NAVY}" stroke-width="3"/>'
        f'<polygon points="{x - 74},{y - 138} {x},{y - 182} {x + 74},{y - 138}" fill="#b5503a" stroke="{NAVY}" stroke-width="3.5" stroke-linejoin="round"/>'
        f'<g class="kova" data-ox="{x}" data-oy="{y - 130}"><line x1="{x}" y1="{y - 130}" x2="{x}" y2="{y - 86}" stroke="#6b4a2e" stroke-width="3"/>'
        f'<path d="M{x - 15},{y - 86} L{x + 15},{y - 86} L{x + 12},{y - 58} L{x - 12},{y - 58} Z" fill="#8a5a3a" stroke="{NAVY}" stroke-width="3"/>'
        f'<line x1="{x - 14}" y1="{y - 76}" x2="{x + 14}" y2="{y - 76}" stroke="{NAVY}" stroke-width="2.4"/></g>'
    )


def tavuk(x, y):
    return (
        f'<g transform="translate({x} {y})"><g class="tavuk">'
        f'<g class="tavuk-bL" data-ox="-6" data-oy="8"><line x1="-6" y1="8" x2="-6" y2="22" stroke="#e08a2a" stroke-width="3" stroke-linecap="round"/></g>'
        f'<g class="tavuk-bR" data-ox="6" data-oy="8"><line x1="6" y1="8" x2="6" y2="22" stroke="#e08a2a" stroke-width="3" stroke-linecap="round"/></g>'
        f'<path d="M-18,-2 L-30,-14 L-26,2 Z" fill="#f2e6cf" stroke="{NAVY}" stroke-width="2.4" stroke-linejoin="round"/>'
        f'<ellipse cx="0" cy="0" rx="20" ry="14" fill="#f6efe0" stroke="{NAVY}" stroke-width="2.8"/>'
        f'<g class="tavuk-bas" data-ox="14" data-oy="-6"><circle cx="22" cy="-12" r="8" fill="#f6efe0" stroke="{NAVY}" stroke-width="2.6"/>'
        f'<circle cx="20" cy="-21" r="3.2" fill="#d6382f" stroke="{NAVY}" stroke-width="1.6"/><circle cx="25" cy="-20" r="3.2" fill="#d6382f" stroke="{NAVY}" stroke-width="1.6"/>'
        f'<path d="M29,-13 L37,-10 L29,-8 Z" fill="#f2a516" stroke="{NAVY}" stroke-width="1.6" stroke-linejoin="round"/>'
        f'<circle cx="24" cy="-14" r="1.5" fill="{NAVY}"/></g></g></g>'
    )


def kus(x, y, olcek=1.0):
    return (f'<g transform="translate({x} {y}) scale({olcek})"><g class="kus" data-ox="0" data-oy="0">'
            f'<path d="M-12,2 Q-6,-8 0,0 Q6,-8 12,2" fill="none" stroke="{NAVY}" stroke-width="2.8" stroke-linecap="round"/></g></g>')


def filiz(olcek=1.0, sinif="filiz"):
    return (
        f'<g class="{sinif}" data-ox="0" data-oy="0"><g transform="scale({olcek})">'
        f'<path d="M0,0 C0,-14 -2,-26 2,-40" fill="none" stroke="{NAVY}" stroke-width="9" stroke-linecap="round"/>'
        f'<path d="M0,0 C0,-14 -2,-26 2,-40" fill="none" stroke="#5aa845" stroke-width="5" stroke-linecap="round"/>'
        f'<path d="M1,-26 C-18,-36 -30,-28 -27,-18 C-16,-15 -7,-18 1,-26 Z" fill="#7ccb58" stroke="{NAVY}" stroke-width="3" stroke-linejoin="round"/>'
        f'<path d="M2,-38 C20,-52 34,-44 32,-32 C20,-28 9,-31 2,-38 Z" fill="#8fd966" stroke="{NAVY}" stroke-width="3" stroke-linejoin="round"/>'
        f'</g></g>'
    )


def yildiz(x, y, r):
    return (f'<g transform="translate({x} {y})"><g class="isil" data-ox="0" data-oy="0" opacity="0">'
            f'<path d="M0,{-r} L{r * 0.28:.1f},{-r * 0.28:.1f} L{r},0 L{r * 0.28:.1f},{r * 0.28:.1f} L0,{r} L{-r * 0.28:.1f},{r * 0.28:.1f} L{-r},0 L{-r * 0.28:.1f},{-r * 0.28:.1f} Z" '
            f'fill="#fff3a8" stroke="#f2c230" stroke-width="2" stroke-linejoin="round"/></g></g>')


def tarla():
    rnd = random.Random(11)
    s = [f'<clipPath id="tarla-kes"><rect x="-400" y="{HOR + 42}" width="2400" height="900"/></clipPath>', '<g clip-path="url(#tarla-kes)">']
    s.append(f'<rect x="-400" y="{HOR + 40}" width="2400" height="900" fill="#b08457"/>')
    xs = list(range(-1400, 2700, 130))
    for i in range(len(xs) - 1):
        if i % 2:
            s.append(f'<polygon points="640,{HOR + 10} {xs[i]},1000 {xs[i + 1]},1000" fill="#9d7249" opacity="0.8"/>')
    s.append(f'<rect x="-400" y="{HOR + 40}" width="2400" height="900" fill="url(#sis)"/>')
    # kuru sap kümeleri (perspektif: uzakta küçük)
    for _ in range(70):
        y = rnd.uniform(HOR + 70, 700)
        t = (y - HOR) / 320
        x = rnd.uniform(-150, 1450)
        h = 14 + 34 * t
        for k in (-1, 0, 1):
            s.append(f'<path d="M{x + k * 4 * t:.0f},{y:.0f} q{k * 5 * t:.0f},{-h * 0.5:.0f} {k * 9 * t:.0f},{-h:.0f}" fill="none" stroke="#d3b374" stroke-width="{1.6 + 1.6 * t:.1f}" stroke-linecap="round"/>')
    # çatlaklar
    for _ in range(9):
        x, y = rnd.uniform(150, 1100), rnd.uniform(560, 700)
        s.append(f'<polyline points="{x:.0f},{y:.0f} {x + 22:.0f},{y + 8:.0f} {x + 30:.0f},{y + 3:.0f} {x + 54:.0f},{y + 14:.0f}" fill="none" stroke="#7a5836" stroke-width="2.4" stroke-linecap="round" opacity="0.7"/>')
    s.append("</g>")
    return "".join(s)


def mini_filizler():
    out = []
    pozlar = [(300, 452), (390, 470), (470, 448), (560, 462), (700, 450), (790, 468), (880, 454), (960, 472), (1060, 458), (1150, 470)]
    for x, y in pozlar:
        t = (y - HOR) / 320
        out.append(f'<g transform="translate({x} {y})">{filiz(0.45 + 0.5 * t, "mini")}</g>')
    return "".join(out)


# ---------------------------------------------------------------- sahne
ELIF_X, ELIF_Y = 470, 575
BABA_X, BABA_Y = 745, 560
FILIZ_X, FILIZ_Y = 612, 588


def svg_sahne():
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <defs>
    <linearGradient id="gok" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#78b0e2"/><stop offset="0.55" stop-color="#f1d9b6"/><stop offset="1" stop-color="#fbe6c6"/>
    </linearGradient>
    <linearGradient id="cim" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#bdb468"/><stop offset="1" stop-color="#9c9556"/></linearGradient>
    <linearGradient id="sis" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f1d6ae" stop-opacity="0.55"/><stop offset="0.45" stop-color="#f1d6ae" stop-opacity="0"/></linearGradient>
    <radialGradient id="parlak"><stop offset="0" stop-color="#fff0c0" stop-opacity="0.95"/><stop offset="1" stop-color="#fff0c0" stop-opacity="0"/></radialGradient>
    <radialGradient id="vin" cx="0.5" cy="0.45" r="0.75"><stop offset="0.6" stop-color="#2a1608" stop-opacity="0"/><stop offset="1" stop-color="#2a1608" stop-opacity="0.38"/></radialGradient>
  </defs>
  <g class="kamera" data-ox="640" data-oy="400">
    <rect x="-500" y="-600" width="2300" height="{HOR + 640}" fill="url(#gok)"/>
    <g class="gunes" data-ox="1040" data-oy="346"><circle cx="1040" cy="346" r="150" fill="url(#parlak)"/><circle cx="1040" cy="346" r="42" fill="#fff0b8"/></g>
    {bulut(240, 110, 1.0)}{bulut(760, 70, 0.8)}{bulut(1180, 170, 0.7)}{bulut(-60, 190, 0.8)}{bulut(1480, 90, 0.9)}
    {kus(120, 190, 1.1)}{kus(190, 224, 0.9)}{kus(70, 240, 0.8)}
    <g class="l-uzak">
      <path d="M-500,{HOR} L-500,326 Q-300,286 -100,322 T220,316 T520,300 T820,322 T1120,304 T1420,330 T1800,312 L1800,{HOR} Z" fill="#a3bdb3" stroke="none"/>
    </g>
    <g class="l-orta">
      <path d="M-500,{HOR + 14} L-500,352 Q-260,326 0,354 T420,348 T780,360 T1160,346 T1500,362 T1800,350 L1800,{HOR + 14} Z" fill="#8fa97c"/>
      {ev(20, HOR + 24, 200, 90)}{ev(262, HOR + 18, 120, 62)}{ev(1160, HOR + 16, 130, 60)}{ev(1330, HOR + 12, 100, 52)}
      {kavak(430, HOR + 22, 150)}{kavak(1090, HOR + 18, 170)}{kavak(1450, HOR + 16, 130)}
    </g>
    <rect x="-500" y="{HOR + 10}" width="2300" height="64" fill="url(#cim)"/>
    {ceviz(96, HOR + 80)}
    {tarla()}
    {citler()}
    {mini_filizler()}
    {kuyu(1030, 500)}
    {tavuk(60, 482)}
    <g transform="translate({FILIZ_X} {FILIZ_Y})"><ellipse class="islak" cx="0" cy="3" rx="44" ry="10" fill="#6e4a2c" opacity="0" data-ox="0" data-oy="3"/></g>
    {kiz_ciz("e", ELIF_X, ELIF_Y)}
    {baba_ciz("b", BABA_X, BABA_Y)}
    <g transform="translate({FILIZ_X} {FILIZ_Y})">{filiz(1.45)}</g>
    {yildiz(FILIZ_X - 40, FILIZ_Y - 54, 15)}{yildiz(FILIZ_X + 42, FILIZ_Y - 68, 18)}{yildiz(FILIZ_X + 4, FILIZ_Y - 104, 13)}{yildiz(FILIZ_X - 62, FILIZ_Y - 22, 11)}{yildiz(FILIZ_X + 66, FILIZ_Y - 26, 11)}
  </g>
  <rect width="{W}" height="{H}" fill="url(#vin)"/>
</svg>"""


CSS = """
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { margin: 0; width: 1280px; height: 720px; overflow: hidden; background: #2a1608; }
      #root { position: relative; width: 1280px; height: 720px; overflow: hidden;
              font-family: system-ui, -apple-system, sans-serif; }
      .sahne { position: absolute; left: 0; top: 0; width: 1280px; height: 720px; overflow: hidden; }
      .sahne svg { position: absolute; left: 0; top: 0; }
      .altyazi { position: absolute; left: 70px; right: 70px; bottom: 32px; text-align: center; }
      .altyazi .ad { display: inline-block; margin-bottom: 8px; padding: 3px 16px 4px; border-radius: 12px;
                     font-size: 24px; font-weight: 800; color: #1d2b4a; letter-spacing: 0.6px; }
      .altyazi .ad-e { background: #f2a33a; }
      .altyazi .ad-b { background: #7fb2e0; }
      .altyazi .metin { display: block; }
      .altyazi .metin span { display: inline-block; max-width: 1140px; padding: 10px 28px 12px; border-radius: 18px;
                      background: rgba(30, 16, 6, 0.82); color: #ffffff; font-size: 42px; font-weight: 700;
                      line-height: 1.22; letter-spacing: 0.2px; }
"""

JS = r"""
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });
      document.querySelectorAll("[data-ox]").forEach(function (el) {
        gsap.set(el, { svgOrigin: el.dataset.ox + " " + el.dataset.oy });
      });
      gsap.set(".filiz, .mini", { scale: 0 });

      const SEG = __SEG__;
      const LIP = __LIP__;
      const CAM = __CAM__;
      const TOTAL = __TOTAL__;
      function Q(s) { return document.querySelector(s); }
      function QA(s) { return Array.prototype.slice.call(document.querySelectorAll(s)); }
      // [t0, t1] aralığını dolduran gidip-gelen döngü
      function git(el, from, to, per, ease, t0, t1) {
        const N = Math.max(1, Math.round((t1 - t0) / per));
        tl.fromTo(el, from, Object.assign({ duration: (t1 - t0) / N, ease: ease || "sine.inOut", repeat: N - 1, yoyo: true, immediateRender: false }, to), t0);
      }
      function kos(el, from, to, dur, ease, t0, adet) {
        tl.fromTo(el, from, Object.assign({ duration: dur, ease: ease || "none", repeat: adet - 1, immediateRender: false }, to), t0);
      }
      // uzuv açısı: her anahtar için önceki açıdan sonrakine (sıra zaman sırasıdır)
      const EL = {}, ANG = {};
      function mv(p, k, to, t, dur) {
        const s = "." + p + "-" + k;
        if (!EL[s]) { EL[s] = Q(s); ANG[s] = 0; }
        tl.fromTo(EL[s], { rotation: ANG[s] }, { rotation: to, duration: dur, ease: "power2.inOut", immediateRender: false }, t);
        ANG[s] = to;
      }
      function beat(p, k, a, b, t0, t1, per) {
        let t = t0, i = 0;
        while (t + per <= t1 + 1e-6) { mv(p, k, i % 2 === 0 ? a : b, t, per); t += per; i++; }
      }

      // ---- kamera: her segment kendi çekimi
      CAM.forEach(function (c) {
        tl.fromTo(Q(".kamera"), { scale: c.z0, x: c.x0, y: c.y0 }, { scale: c.z1, x: c.x1, y: c.y1, duration: c.D, ease: "sine.inOut", immediateRender: false }, c.S);
      });

      // ---- ağız: ses zarfından (30 kare/sn); konuşmayan karakter gülümser
      SEG.forEach(function (s, idx) {
        const ag = Q("." + s.p + "-agiz"), gu = Q("." + s.p + "-gulus"), bas = Q("." + s.p + "-bas");
        tl.set(gu, { opacity: 0 }, s.S);
        tl.set(ag, { opacity: 1 }, s.S);
        let prev = -1;
        LIP[idx].forEach(function (v, k) {
          if (v === prev) return;
          prev = v;
          tl.set(ag, { scaleY: 0.14 + 0.86 * v / 100, scaleX: 1 - 0.22 * v / 100 }, s.S + k / 30);
          tl.set(bas, { y: -2.2 * v / 100 }, s.S + k / 30);
        });
        tl.set(ag, { opacity: 0 }, s.S + s.D - 0.001);
        tl.set(gu, { opacity: 1 }, s.S + s.D - 0.001);
        tl.set(bas, { y: 0 }, s.S + s.D - 0.001);
      });

      // ---- göz kırpma
      const KIRP = { e: [1.1, 4.9, 9.3, 12.4], b: [0.5, 3.6, 6.4, 10.6] };
      Object.keys(KIRP).forEach(function (p) {
        KIRP[p].forEach(function (t) {
          tl.fromTo(Q("." + p + "-goz"), { scaleY: 1 }, { scaleY: 0.08, duration: 0.07, yoyo: true, repeat: 1, ease: "none", immediateRender: false }, t);
        });
      });

      // ---- sürekli arka plan hareketi
      QA(".bulut").forEach(function (b, i) { tl.fromTo(b, { x: 0 }, { x: 18 + i * 9, duration: TOTAL, ease: "none", immediateRender: false }, 0); });
      tl.fromTo(Q(".l-uzak"), { x: 0 }, { x: -10, duration: TOTAL, ease: "none", immediateRender: false }, 0);
      tl.fromTo(Q(".l-orta"), { x: 0 }, { x: -18, duration: TOTAL, ease: "none", immediateRender: false }, 0);
      QA(".duman").forEach(function (d, i) {
        kos(d, { y: 0, x: 0, scale: 0.5, opacity: 0.8 }, { y: -70, x: 26, scale: 1.8, opacity: 0 }, 2.6, "none", (i % 2) * 1.3 + Math.floor(i / 2) * 0.4, Math.ceil(TOTAL / 2.6) + 1);
      });
      QA(".agac").forEach(function (a, i) { git(a, { rotation: -0.9 }, { rotation: 0.9 }, 2.4 + i * 0.3, "sine.inOut", 0, TOTAL); });
      git(Q(".kova"), { rotation: -3 }, { rotation: 3 }, 1.8, "sine.inOut", 0, TOTAL);
      git(Q(".gunes"), { scale: 0.97 }, { scale: 1.04 }, 2.6, "sine.inOut", 0, TOTAL);
      tl.fromTo(Q(".tavuk"), { x: 0 }, { x: 250, duration: TOTAL, ease: "none", immediateRender: false }, 0);
      git(Q(".tavuk-bas"), { rotation: 0 }, { rotation: 30 }, 0.7, "sine.in", 0, TOTAL);
      git(Q(".tavuk-bL"), { rotation: -24 }, { rotation: 24 }, 0.35, "sine.inOut", 0, TOTAL);
      git(Q(".tavuk-bR"), { rotation: 24 }, { rotation: -24 }, 0.35, "sine.inOut", 0, TOTAL);
      QA(".kus").forEach(function (k, i) {
        tl.fromTo(k, { x: 0 }, { x: 760 + i * 60, duration: TOTAL, ease: "none", immediateRender: false }, 0);
        git(k, { scaleY: 1 }, { scaleY: 0.35 }, 0.22 + i * 0.03, "sine.inOut", 0, TOTAL);
      });
      git(Q(".e-ortL"), { rotation: -3 }, { rotation: 3 }, 1.4, "sine.inOut", 0, TOTAL);
      git(Q(".e-ortR"), { rotation: 3 }, { rotation: -3 }, 1.6, "sine.inOut", 0, TOTAL);

      // ---- jestler (S = segmentin başlangıcı)
      const S1 = SEG[0].S, S2 = SEG[1].S, S3 = SEG[2].S, S4 = SEG[3].S, S5 = SEG[4].S;

      // 1) Elif soruyor: tarlayı gösteriyor, baba dinliyor
      mv("e", "aR", -84, S1 + 0.12, 0.4); mv("e", "fR", -12, S1 + 0.12, 0.4);
      mv("e", "aL", 8, S1 + 0.2, 0.4);
      mv("e", "bas", -3, S1 + 0.1, 0.5);
      mv("b", "bas", 3, S1 + 0.4, 0.8);

      // 2) Baba: önce göğü, sonra toprağı gösteriyor
      mv("e", "aR", -10, S2, 0.4); mv("e", "fR", 0, S2, 0.4);
      mv("e", "bas", -4, S2, 0.5);
      mv("b", "bas", 4, S2 + 0.2, 0.5);
      mv("b", "aL", 150, S2 + 0.25, 0.55); mv("b", "fL", 15, S2 + 0.25, 0.55);
      mv("b", "bas", -4, S2 + 2.0, 0.6);
      mv("b", "aL", 50, S2 + 2.0, 0.6); mv("b", "fL", 50, S2 + 2.0, 0.6);
      mv("e", "bas", -1, S2 + 2.4, 0.4);
      mv("b", "aL", 36, S2 + 3.0, 0.7); mv("b", "fL", 30, S2 + 3.0, 0.7);
      mv("b", "bas", 2, S2 + 4.0, 0.4);
      mv("b", "aL", 8, S2 + 4.05, 0.43); mv("b", "fL", 0, S2 + 4.05, 0.43);

      // 3) Elif omuz silkiyor: "Biz ne yapacağız?"
      mv("e", "aL", 38, S3 + 0.12, 0.3); mv("e", "fL", 75, S3 + 0.12, 0.3);
      mv("e", "aR", -38, S3 + 0.12, 0.3); mv("e", "fR", -75, S3 + 0.12, 0.3);
      mv("e", "bas", 9, S3 + 0.1, 0.4);
      mv("b", "bas", 3, S3 + 0.3, 0.5);
      mv("e", "fL", 55, S3 + 1.0, 0.4); mv("e", "fR", -55, S3 + 1.0, 0.4);

      // 4) Baba kuyuyu gösteriyor
      mv("b", "aR", -100, S4 + 0.2, 0.5); mv("b", "fR", -6, S4 + 0.2, 0.5);
      mv("b", "bas", -5, S4 + 0.2, 0.5);
      mv("e", "aL", 8, S4 + 0.1, 0.4); mv("e", "fL", 0, S4 + 0.1, 0.4);
      mv("e", "aR", -8, S4 + 0.1, 0.4); mv("e", "fR", 0, S4 + 0.1, 0.4);
      mv("e", "bas", -6, S4 + 0.4, 0.5);
      beat("b", "fR", -4, -26, S4 + 1.0, S4 + 2.4, 0.35);
      mv("e", "bas", 0, S4 + 2.2, 0.5);
      mv("b", "aR", -12, S4 + 2.6, 0.4); mv("b", "fR", 0, S4 + 2.6, 0.4);
      mv("b", "bas", 3, S4 + 2.5, 0.5);

      // 5) Elif sevinçle zıplıyor, ilk filiz çıkıyor
      [0.12, 0.62, 1.12].forEach(function (d) {
        tl.fromTo(Q(".e"), { y: 0 }, { y: -24, duration: 0.2, ease: "power2.out", yoyo: true, repeat: 1, immediateRender: false }, S5 + d);
      });
      mv("e", "aL", 152, S5 + 0.1, 0.25); mv("e", "fL", 14, S5 + 0.1, 0.25);
      mv("e", "aR", -152, S5 + 0.1, 0.25); mv("e", "fR", -14, S5 + 0.1, 0.25);
      mv("e", "bas", 0, S5 + 0.1, 0.3);
      mv("b", "aR", -10, S5 + 0.1, 0.35); mv("b", "fR", 0, S5 + 0.1, 0.35);
      mv("b", "bas", 7, S5 + 0.1, 0.4);
      beat("e", "aL", 152, 128, S5 + 0.4, S5 + 1.6, 0.2);
      beat("e", "aR", -152, -128, S5 + 0.4, S5 + 1.6, 0.2);

      tl.fromTo(Q(".islak"), { opacity: 0, scaleX: 0.2 }, { opacity: 0.75, scaleX: 1, duration: 0.5, ease: "power2.out", immediateRender: false }, S5 + 0.05);
      tl.fromTo(Q(".filiz"), { scale: 0 }, { scale: 1, duration: 0.6, ease: "back.out(2.2)", immediateRender: false }, S5 + 0.25);
      QA(".isil").forEach(function (st, i) {
        tl.fromTo(st, { scale: 0, opacity: 1 }, { scale: 1.3, opacity: 0, duration: 0.7, ease: "power2.out", immediateRender: false }, S5 + 0.55 + i * 0.08);
      });
      QA(".mini").forEach(function (m, i) {
        tl.fromTo(m, { scale: 0 }, { scale: 1, duration: 0.5, ease: "back.out(2)", immediateRender: false }, S5 + 0.45 + i * 0.1);
      });

      window.__timelines["main"] = tl;
      tl.seek(0);
"""


def kamera(z, cx, cy):
    """Odak noktasını (cx,cy) ekranın (640,340) noktasına getiren x/y; kamera pivotu (640,400)."""
    return round(-z * (cx - 640), 1), round(-60 - z * (cy - 400), 1)


KARELER = [
    # (z0, odak0, z1, odak1)
    (1.00, (640, 440), 1.10, (570, 450)),
    (1.25, (735, 440), 1.35, (745, 440)),
    (1.35, (480, 500), 1.45, (478, 500)),
    (1.15, (780, 440), 1.15, (900, 450)),
    (1.15, (600, 480), 1.50, (612, 470)),
]


def main():
    segler, lip, cam, altyazilar = [], [], [], []
    for i, ((ad, metin), kayit) in enumerate(zip(SATIRLAR, TIMING["cumleler"])):
        p, etiket = KONUSMACI[ad]
        S, D = kayit["bas"], kayit["sure"]
        segler.append({"p": p, "S": S, "D": D})
        lip.append(zarf(KOK / "ses" / kayit["dosya"]))
        z0, f0, z1, f1 = KARELER[i]
        x0, y0 = kamera(z0, *f0)
        x1, y1 = kamera(z1, *f1)
        cam.append({"S": S, "D": D, "z0": z0, "x0": x0, "y0": y0, "z1": z1, "x1": x1, "y1": y1})
        altyazilar.append(
            f'<div id="alt{i + 1}" class="altyazi clip" data-start="{S}" data-duration="{D}" data-track-index="{i + 2}">'
            f'<span class="ad ad-{p}">{etiket}</span><div class="metin"><span>{escape(metin)}</span></div></div>')
    toplam = TIMING["toplam"]
    js = (JS.replace("__SEG__", json.dumps(segler)).replace("__LIP__", json.dumps(lip))
          .replace("__CAM__", json.dumps(cam)).replace("__TOTAL__", str(toplam)))
    html = f"""<!doctype html>
<html lang="tr">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>{CSS}    </style>
  </head>
  <body>
    <!-- Bu dosya sahne_uret.py ile üretilir; süreler ../timing.json'dan (ölçülmüş ses süreleri). -->
    <div id="root" data-composition-id="main" data-start="0" data-duration="{toplam}" data-width="{W}" data-height="{H}" data-fps="30">
      <div id="sahne" class="sahne clip" data-start="0" data-duration="{toplam}" data-track-index="1">{svg_sahne()}</div>
      {"".join(altyazilar)}
    </div>
    <script>{js}    </script>
  </body>
</html>
"""
    (AYRI / "index.html").write_text(html, encoding="utf-8")
    print(f"index.html yazıldı: {len(SATIRLAR)} cümle, toplam {toplam} sn")
    for i, k in enumerate(TIMING["cumleler"], 1):
        print(f"  {i}: {k['bas']:.2f} -> {k['bit']:.2f} sn ({k['sure']:.2f}) {SATIRLAR[i - 1][0]}")


if __name__ == "__main__":
    main()
