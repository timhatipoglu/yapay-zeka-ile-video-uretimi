#!/usr/bin/env python3
"""Çok örnek demolar için ortak SVG sahne üretici.

demo-*/animasyon içinde değil; proje kökünden:
  python3 scripts/ornek_sahne_uret.py demo-liman
Sahne teması demo-*/sahne.json'dan, süreler timing.json'dan gelir.
"""
from __future__ import annotations

import json
import sys
import wave
from array import array
from html import escape
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
W, H = 1280, 720
NAVY = "#1d2b4a"
SKIN, SKIN2 = "#f0c49a", "#e0a574"

TEMA = {
    "liman": {
        "gok": ("#4a7aa8", "#c8dff0", "#e8f0f6"),
        "zemin": "#6b7c8a",
        "vurgu": "#e8a04a",
        "etiket_a": "#3aa0d8",
        "etiket_b": "#e8a04a",
        "vin": "#0a1a28",
    },
    "okul": {
        "gok": ("#f2d6a0", "#f8e8c8", "#fff6e4"),
        "zemin": "#d4c4a0",
        "vurgu": "#c45c3a",
        "etiket_a": "#5a8fd8",
        "etiket_b": "#c45c3a",
        "vin": "#2a1808",
    },
    "tren": {
        "gok": ("#3a4a5a", "#6a7a8a", "#9aa8b4"),
        "zemin": "#4a4a4a",
        "vurgu": "#d0a040",
        "etiket_a": "#d0a040",
        "etiket_b": "#70a0c8",
        "vin": "#101018",
    },
}


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
        blok = ham[i : i + adim]
        if blok:
            rms.append((sum(x * x for x in blok) / len(blok)) ** 0.5)
    p90 = sorted(rms)[int(len(rms) * 0.9)] or 1.0
    v = [min(1.0, r / p90) for r in rms]
    v = [0.0 if x < 0.14 else x for x in v]
    n = len(v)
    sm = [0.25 * v[max(0, i - 1)] + 0.5 * v[i] + 0.25 * v[min(n - 1, i + 1)] for i in range(n)]
    return [int(round(x * 20)) * 5 for x in sm]


def uzuv(x1, y1, x2, y2, w, renk):
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{NAVY}" stroke-width="{w + 6}" stroke-linecap="round"/>'
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{renk}" stroke-width="{w}" stroke-linecap="round"/>'
    )


def karakter(p, x, y, *, cocuk=False, ceket="#4a6a8a", pantolon="#2a3a4a", sac="#3a2a1a", etek=False):
    olcek = 0.78 if cocuk else 1.0
    # gövde
    gx, gy = x, y - 95 * olcek
    hx, hy = x, y - 155 * olcek
    br = 28 * olcek
    out = [f'<g class="{p}" data-ox="{x:.1f}" data-oy="{y:.1f}">']
    # bacaklar
    out.append(f'<g class="{p}-bL" data-ox="{x - 12 * olcek:.1f}" data-oy="{y - 55 * olcek:.1f}">')
    out.append(uzuv(x - 12 * olcek, y - 55 * olcek, x - 16 * olcek, y - 5, 10 * olcek, pantolon))
    out.append("</g>")
    out.append(f'<g class="{p}-bR" data-ox="{x + 12 * olcek:.1f}" data-oy="{y - 55 * olcek:.1f}">')
    out.append(uzuv(x + 12 * olcek, y - 55 * olcek, x + 16 * olcek, y - 5, 10 * olcek, pantolon))
    out.append("</g>")
    # gövde
    if etek:
        out.append(
            f'<path d="M{x - 28 * olcek:.1f},{gy:.1f} L{x + 28 * olcek:.1f},{gy:.1f} '
            f'L{x + 36 * olcek:.1f},{y - 40 * olcek:.1f} L{x - 36 * olcek:.1f},{y - 40 * olcek:.1f} Z" '
            f'fill="{ceket}" stroke="{NAVY}" stroke-width="3.5"/>'
        )
    else:
        out.append(
            f'<rect x="{x - 26 * olcek:.1f}" y="{gy:.1f}" width="{52 * olcek:.1f}" height="{55 * olcek:.1f}" '
            f'rx="8" fill="{ceket}" stroke="{NAVY}" stroke-width="3.5"/>'
        )
    # kollar
    for taraf, sx in (("L", x - 26 * olcek), ("R", x + 26 * olcek)):
        d = -1 if taraf == "L" else 1
        out.append(f'<g class="{p}-a{taraf}" data-ox="{sx:.1f}" data-oy="{gy + 12 * olcek:.1f}">')
        out.append(uzuv(sx, gy + 12 * olcek, sx + d * 8, gy + 55 * olcek, 9 * olcek, ceket))
        out.append(f'<g class="{p}-f{taraf}" data-ox="{sx + d * 8:.1f}" data-oy="{gy + 55 * olcek:.1f}">')
        out.append(f'<circle cx="{sx + d * 8:.1f}" cy="{gy + 62 * olcek:.1f}" r="{7 * olcek:.1f}" fill="{SKIN}" stroke="{NAVY}" stroke-width="3"/>')
        out.append("</g></g>")
    # kafa
    out.append(f'<g class="{p}-bas" data-ox="{hx:.1f}" data-oy="{hy:.1f}">')
    out.append(f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="{br:.1f}" fill="{SKIN}" stroke="{NAVY}" stroke-width="3.5"/>')
    out.append(f'<path d="M{hx - br * 0.9:.1f},{hy - 4:.1f} Q{hx:.1f},{hy - br * 1.35:.1f} {hx + br * 0.9:.1f},{hy - 4:.1f}" fill="{sac}" stroke="{NAVY}" stroke-width="3"/>')
    out.append(f'<g class="{p}-goz" data-ox="{hx:.1f}" data-oy="{hy - 4:.1f}">')
    out.append(f'<circle cx="{hx - 9 * olcek:.1f}" cy="{hy - 4:.1f}" r="3.2" fill="{NAVY}"/>')
    out.append(f'<circle cx="{hx + 9 * olcek:.1f}" cy="{hy - 4:.1f}" r="3.2" fill="{NAVY}"/>')
    out.append("</g>")
    out.append(f'<path class="{p}-gulus" d="M{hx - 10:.1f},{hy + 12:.1f} Q{hx:.1f},{hy + 18:.1f} {hx + 10:.1f},{hy + 12:.1f}" fill="none" stroke="{NAVY}" stroke-width="3" stroke-linecap="round"/>')
    out.append(
        f'<ellipse class="{p}-agiz" cx="{hx:.1f}" cy="{hy + 14:.1f}" rx="{9 * olcek:.1f}" ry="{7 * olcek:.1f}" '
        f'fill="#3b2116" stroke="{NAVY}" stroke-width="2" opacity="0" data-ox="{hx:.1f}" data-oy="{hy + 14:.1f}"/>'
    )
    out.append("</g></g>")
    return "".join(out)


def arka_liman():
    return f"""
  <rect x="-400" y="-200" width="2200" height="420" fill="url(#gok)"/>
  <rect x="-400" y="380" width="2200" height="500" fill="#3a6a88"/>
  <path d="M-400,400 Q0,380 400,405 T1200,390 T1800,410 L1800,900 L-400,900 Z" fill="#2a5570"/>
  <rect x="-400" y="470" width="2200" height="40" fill="#8a6a4a" stroke="{NAVY}" stroke-width="3"/>
  <rect x="80" y="200" width="28" height="280" fill="#6a5a4a" stroke="{NAVY}" stroke-width="3"/>
  <rect x="980" y="180" width="32" height="300" fill="#6a5a4a" stroke="{NAVY}" stroke-width="3"/>
  <g class="tekne" data-ox="1000" data-oy="430">
    <path d="M860,430 L1180,430 L1140,490 L900,490 Z" fill="#c45c3a" stroke="{NAVY}" stroke-width="3.5"/>
    <rect x="980" y="360" width="14" height="70" fill="#5a4a3a" stroke="{NAVY}" stroke-width="2.5"/>
  </g>
  <circle class="kus" cx="200" cy="120" r="4" fill="{NAVY}"/>
  <circle class="kus" cx="260" cy="150" r="3" fill="{NAVY}"/>
"""


def arka_okul():
    return f"""
  <rect x="-400" y="-200" width="2200" height="520" fill="url(#gok)"/>
  <rect x="120" y="80" width="1040" height="420" fill="#e8dcc0" stroke="{NAVY}" stroke-width="4"/>
  <rect x="160" y="120" width="200" height="140" fill="#9ec9e8" stroke="{NAVY}" stroke-width="3"/>
  <rect x="420" y="120" width="200" height="140" fill="#9ec9e8" stroke="{NAVY}" stroke-width="3"/>
  <rect x="680" y="120" width="200" height="140" fill="#9ec9e8" stroke="{NAVY}" stroke-width="3"/>
  <rect x="940" y="120" width="160" height="140" fill="#9ec9e8" stroke="{NAVY}" stroke-width="3"/>
  <rect x="200" y="300" width="880" height="18" fill="#8a5a3a" stroke="{NAVY}" stroke-width="2"/>
  <rect x="-400" y="480" width="2200" height="400" fill="#c8b88a"/>
  <rect x="360" y="360" width="560" height="140" fill="#f4ead0" stroke="{NAVY}" stroke-width="3.5"/>
  <text x="640" y="445" text-anchor="middle" font-size="48" font-weight="800" fill="{NAVY}" font-family="system-ui">A + B = ?</text>
"""


def arka_tren():
    return f"""
  <rect x="-400" y="-200" width="2200" height="420" fill="url(#gok)"/>
  <rect x="-400" y="360" width="2200" height="80" fill="#5a5a5a"/>
  <rect x="-400" y="430" width="2200" height="20" fill="#d0a040"/>
  <rect x="-400" y="450" width="2200" height="400" fill="#3a3a3a"/>
  <g class="vagon" data-ox="200" data-oy="300">
    <rect x="40" y="200" width="520" height="200" rx="8" fill="#c45c3a" stroke="{NAVY}" stroke-width="4"/>
    <rect x="80" y="230" width="100" height="80" fill="#9ec9e8" stroke="{NAVY}" stroke-width="3"/>
    <rect x="220" y="230" width="100" height="80" fill="#9ec9e8" stroke="{NAVY}" stroke-width="3"/>
    <rect x="360" y="230" width="100" height="80" fill="#9ec9e8" stroke="{NAVY}" stroke-width="3"/>
    <circle cx="120" cy="410" r="28" fill="#2a2a2a" stroke="{NAVY}" stroke-width="3"/>
    <circle cx="420" cy="410" r="28" fill="#2a2a2a" stroke="{NAVY}" stroke-width="3"/>
  </g>
  <rect x="700" y="160" width="18" height="220" fill="#6a6a6a" stroke="{NAVY}" stroke-width="2"/>
  <rect x="1000" y="140" width="18" height="240" fill="#6a6a6a" stroke="{NAVY}" stroke-width="2"/>
"""


ARKA = {"liman": arka_liman, "okul": arka_okul, "tren": arka_tren}

CSS = """
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { margin: 0; width: 1280px; height: 720px; overflow: hidden; background: #111; }
      #root { position: relative; width: 1280px; height: 720px; overflow: hidden;
              font-family: system-ui, -apple-system, sans-serif; }
      .sahne { position: absolute; left: 0; top: 0; width: 1280px; height: 720px; overflow: hidden; }
      .sahne svg { position: absolute; left: 0; top: 0; }
      .altyazi { position: absolute; left: 70px; right: 70px; bottom: 32px; text-align: center; }
      .altyazi .ad { display: inline-block; margin-bottom: 8px; padding: 3px 16px 4px; border-radius: 12px;
                     font-size: 24px; font-weight: 800; color: #1d2b4a; letter-spacing: 0.6px; }
      .altyazi .metin { display: block; }
      .altyazi .metin span { display: inline-block; max-width: 1140px; padding: 10px 28px 12px; border-radius: 18px;
                      background: rgba(20, 12, 8, 0.82); color: #ffffff; font-size: 40px; font-weight: 700;
                      line-height: 1.22; }
"""

JS = r"""
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });
      document.querySelectorAll("[data-ox]").forEach(function (el) {
        gsap.set(el, { svgOrigin: el.dataset.ox + " " + el.dataset.oy });
      });
      const SEG = __SEG__;
      const LIP = __LIP__;
      const TOTAL = __TOTAL__;
      function Q(s) { return document.querySelector(s); }
      const ANG = {}, EL = {};
      function mv(p, k, to, t, dur) {
        const s = "." + p + "-" + k;
        if (!EL[s]) { EL[s] = Q(s); ANG[s] = 0; }
        if (!EL[s]) return;
        tl.fromTo(EL[s], { rotation: ANG[s] }, { rotation: to, duration: dur, ease: "power2.inOut", immediateRender: false }, t);
        ANG[s] = to;
      }
      SEG.forEach(function (s, idx) {
        const ag = Q("." + s.p + "-agiz"), gu = Q("." + s.p + "-gulus"), bas = Q("." + s.p + "-bas");
        if (gu) tl.set(gu, { opacity: 0 }, s.S);
        if (ag) tl.set(ag, { opacity: 1 }, s.S);
        let prev = -1;
        (LIP[idx] || []).forEach(function (v, k) {
          if (v === prev || !ag) return;
          prev = v;
          tl.set(ag, { scaleY: 0.14 + 0.86 * v / 100, scaleX: 1 - 0.22 * v / 100 }, s.S + k / 30);
          if (bas) tl.set(bas, { y: -2.2 * v / 100 }, s.S + k / 30);
        });
        if (ag) tl.set(ag, { opacity: 0 }, s.S + s.D - 0.001);
        if (gu) tl.set(gu, { opacity: 1 }, s.S + s.D - 0.001);
        if (bas) tl.set(bas, { y: 0 }, s.S + s.D - 0.001);
        // hafif jest
        mv(s.p, "aR", s.p === "a" ? -40 : -25, s.S + 0.1, 0.35);
        mv(s.p, "aL", s.p === "a" ? 20 : 35, s.S + 0.15, 0.35);
        mv(s.p, "aR", -8, s.S + s.D - 0.35, 0.3);
        mv(s.p, "aL", 8, s.S + s.D - 0.35, 0.3);
      });
      // dinleyen hafif sallanır
      tl.fromTo(Q(".kamera"), { scale: 1 }, { scale: 1.04, duration: TOTAL, ease: "sine.inOut", yoyo: true, repeat: 1, immediateRender: false }, 0);
      window.__timelines["main"] = tl;
      tl.seek(0);
"""


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    demo = KOK / sys.argv[1]
    sahne = json.loads((demo / "sahne.json").read_text(encoding="utf-8"))
    timing = json.loads((demo / "timing.json").read_text(encoding="utf-8"))
    satirlar = []
    for ham in (demo / "cumleler.txt").read_text(encoding="utf-8").splitlines():
        if ham.strip():
            ad, _, metin = ham.partition(":")
            satirlar.append((ad.strip(), metin.strip()))
    assert len(satirlar) == len(timing["cumleler"])
    tema_ad = sahne["tema"]
    T = TEMA[tema_ad]
    kisiler = sahne["karakterler"]  # [{id, etiket, rol, ...}]
    id_map = {k["id"]: k for k in kisiler}
    # p harfi: ilk iki karakter a/b
    harf = {kisiler[0]["id"]: "a", kisiler[1]["id"]: "b"}
    etiket = {kisiler[0]["id"]: kisiler[0]["etiket"], kisiler[1]["id"]: kisiler[1]["etiket"]}

    segler, lip, alts = [], [], []
    for i, ((ad, metin), kayit) in enumerate(zip(satirlar, timing["cumleler"])):
        p = harf[ad]
        S, D = kayit["bas"], kayit["sure"]
        segler.append({"p": p, "S": S, "D": D})
        lip.append(zarf(demo / "ses" / kayit["dosya"]))
        renk = "a" if p == "a" else "b"
        bg = T["etiket_a"] if p == "a" else T["etiket_b"]
        alts.append(
            f'<div id="alt{i+1}" class="altyazi clip" data-start="{S}" data-duration="{D}" data-track-index="{i+2}">'
            f'<span class="ad" style="background:{bg}">{escape(etiket[ad])}</span>'
            f'<div class="metin"><span>{escape(metin)}</span></div></div>'
        )

    k0, k1 = kisiler[0], kisiler[1]
    svg = f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <defs>
    <linearGradient id="gok" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{T['gok'][0]}"/><stop offset="0.55" stop-color="{T['gok'][1]}"/><stop offset="1" stop-color="{T['gok'][2]}"/>
    </linearGradient>
    <radialGradient id="vin" cx="0.5" cy="0.45" r="0.75">
      <stop offset="0.55" stop-color="{T['vin']}" stop-opacity="0"/><stop offset="1" stop-color="{T['vin']}" stop-opacity="0.4"/>
    </radialGradient>
  </defs>
  <g class="kamera" data-ox="640" data-oy="400">
    {ARKA[tema_ad]()}
    {karakter('a', 420, 620, cocuk=k0.get('cocuk', False), ceket=k0.get('ceket', '#4a6a8a'), pantolon=k0.get('pantolon', '#2a3a4a'), sac=k0.get('sac', '#3a2a1a'), etek=k0.get('etek', False))}
    {karakter('b', 820, 610, cocuk=k1.get('cocuk', False), ceket=k1.get('ceket', '#6a4a3a'), pantolon=k1.get('pantolon', '#3a2a2a'), sac=k1.get('sac', '#2a1a10'), etek=k1.get('etek', False))}
  </g>
  <rect width="{W}" height="{H}" fill="url(#vin)"/>
</svg>"""

    js = JS.replace("__SEG__", json.dumps(segler)).replace("__LIP__", json.dumps(lip)).replace("__TOTAL__", str(timing["toplam"]))
    html = f"""<!doctype html>
<html lang="tr">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>{CSS}
      .altyazi .ad {{ background: #ddd; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{timing['toplam']}" data-width="{W}" data-height="{H}" data-fps="30">
      <div id="sahne" class="sahne clip" data-start="0" data-duration="{timing['toplam']}" data-track-index="1">{svg}</div>
      {"".join(alts)}
    </div>
    <script>{js}</script>
  </body>
</html>
"""
    anim = demo / "animasyon"
    anim.mkdir(exist_ok=True)
    (anim / "index.html").write_text(html, encoding="utf-8")
    # hyperframes stubs
    if not (anim / "package.json").exists():
        (anim / "package.json").write_text(
            '{\n  "name": "animasyon",\n  "private": true,\n  "type": "module",\n  "scripts": {\n'
            '    "render": "npx --yes hyperframes@0.8.184 render"\n  }\n}\n',
            encoding="utf-8",
        )
    if not (anim / "hyperframes.json").exists():
        (anim / "hyperframes.json").write_text('{"version":1}\n', encoding="utf-8")
    if not (anim / "meta.json").exists():
        (anim / "meta.json").write_text(json.dumps({"width": W, "height": H, "fps": 30}, indent=2) + "\n")
    (anim / ".gitignore").write_text("renders/\n.hyperframes/\n")
    print(f"OK {demo.name}: {timing['toplam']} sn, {len(satirlar)} cümle, tema={tema_ad}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
