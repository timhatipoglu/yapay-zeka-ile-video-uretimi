#!/usr/bin/env python3
"""index.html üretici (HyperFrames kompozisyonu).

Segment sayısı, süreleri ve başlangıçları demo/timing.json'dan (sure_olc.py çıktısı), altyazılar
demo/cumleler.txt'den gelir (betik demo/animasyon içinde olduğu için yollar ../timing.json ve
../cumleler.txt). Süre eşit bölünmez: her segmentin data-duration değeri ölçülmüş
ses süresidir (Audio Lock). Çizimlerin hepsi koddur (SVG); bu demoda görsel modeli kullanılmadı.

Kullanım (demo/animasyon içinde):  python3 sahne_uret.py
"""
import json
from html import escape
from pathlib import Path

AYRI = Path(__file__).resolve().parent
TIMING = json.loads((AYRI.parent / "timing.json").read_text(encoding="utf-8"))
CUMLELER = [s.strip() for s in (AYRI.parent / "cumleler.txt").read_text(encoding="utf-8").splitlines() if s.strip()]
assert len(CUMLELER) == len(TIMING["cumleler"]), "cümle sayısı ile ses sayısı aynı olmalı"

W, H = 1280, 720
NAVY = "#1d2b4a"
CREAM = "#fff4e4"
RED = "#d6382f"
YELLOW = "#f2c230"
HULL = "#f6f2e8"
WIN = "#9ec9e8"
DECK = -138  # güvertenin yerel y'si (vapur koordinatı)
SHIP_X, SHIP_Y = 620, 520  # vapurun su hattı merkezi (tuval koordinatı)


# ---------------------------------------------------------------- yardımcılar
def dalga_yolu(y, genlik=9, bas=-200, bitis=1500, kapali=False):
    """Periyodu 160 px olan dalga çizgisi; x'te -160 kaydırınca kesintisiz döner."""
    parca = f"q40,{-genlik} 80,0 t80,0 "
    adet = (bitis - bas) // 160 + 1
    yol = f"M{bas},{y} " + parca * adet
    if kapali:
        yol += f"L{bas + adet * 160},{H + 60} L{bas},{H + 60} Z"
    return yol


def bulut(x, y, olcek):
    return (
        f'<g class="bulut"><g transform="translate({x} {y}) scale({olcek})" fill="#ffffff" opacity="0.92">'
        '<ellipse cx="0" cy="6" rx="64" ry="17"/><circle cx="-24" cy="-8" r="22"/>'
        '<circle cx="10" cy="-18" r="28"/><circle cx="42" cy="-4" r="19"/></g></g>'
    )


def ufuk_cizgisi():
    """Uzak İstanbul siluetleri: tepeler, kubbe + minareler, kule. Taban y=400."""
    s = ['<g fill="#a8bcd6">']
    s.append(
        '<path d="M-80,400 L-80,380 Q40,352 160,374 T330,372 T520,376 Q600,356 700,372 T880,370 '
        'T1080,374 T1240,366 T1360,376 L1360,400 Z"/>'
    )
    # ev blokları
    for x, w, h in [(40, 38, 20), (96, 30, 28), (420, 44, 22), (470, 30, 30), (560, 40, 18),
                    (640, 36, 26), (760, 44, 22), (960, 40, 26), (1010, 34, 18), (1190, 44, 24)]:
        s.append(f'<rect x="{x}" y="{384 - h}" width="{w}" height="{h + 16}"/>')
    s.append("</g>")
    s.append('<g fill="#93abc9">')
    # büyük cami: kubbe + iki minare
    s.append('<path d="M246,376 A44,44 0 0 1 334,376 Z"/><rect x="246" y="376" width="88" height="24"/>')
    s.append('<path d="M258,376 A22,22 0 0 1 302,376 Z" transform="translate(-4 4)"/>')
    for mx in (222, 358):
        s.append(f'<rect x="{mx - 4}" y="326" width="8" height="74"/>')
        s.append(f'<path d="M{mx - 5},326 L{mx + 5},326 L{mx},306 Z"/>')
        s.append(f'<rect x="{mx - 7}" y="344" width="14" height="4"/>')
    # Galata benzeri kule
    s.append('<rect x="846" y="338" width="30" height="62"/><rect x="840" y="334" width="42" height="6"/>')
    s.append('<path d="M842,334 L880,334 L861,300 Z"/>')
    # ikinci cami
    s.append('<path d="M1086,378 A34,34 0 0 1 1154,378 Z"/><rect x="1086" y="378" width="68" height="22"/>')
    for mx in (1070, 1170):
        s.append(f'<rect x="{mx - 3.5}" y="340" width="7" height="60"/>')
        s.append(f'<path d="M{mx - 4.5},340 L{mx + 4.5},340 L{mx},322 Z"/>')
    s.append("</g>")
    return "\n".join(s)


def iskele():
    """Kadıköy iskelesi (yalnız 2. segment): ahşap iskele, bilet kulübesi, 08:30 saati."""
    return f"""
<g class="iskele"><g transform="translate(70 -52)">
  <rect x="-40" y="540" width="330" height="14" fill="#7b5a3c"/>
  <rect x="-40" y="554" width="330" height="6" fill="#5b422d"/>
  {''.join(f'<rect x="{x}" y="554" width="12" height="90" fill="#5b422d"/>' for x in (-20, 60, 140, 220))}
  <rect x="-20" y="418" width="250" height="122" fill="#efe3cf"/>
  <path d="M-34,420 L-6,386 L246,386 L262,420 Z" fill="#b4533c"/>
  <rect x="150" y="470" width="50" height="70" fill="#8a5a3a"/>
  <rect x="-2" y="470" width="120" height="44" fill="#9ec9e8" stroke="{NAVY}" stroke-width="4"/>
  <rect x="14" y="428" width="104" height="28" rx="6" fill="{NAVY}"/>
  <text x="66" y="449" text-anchor="middle" font-size="19" font-weight="700" fill="#ffffff"
        font-family="system-ui, -apple-system, sans-serif" letter-spacing="1">KADIKÖY</text>
  <circle cx="178" cy="436" r="24" fill="#ffffff" stroke="{NAVY}" stroke-width="4"/>
  <line x1="178" y1="436" x2="170" y2="452" stroke="{NAVY}" stroke-width="4" stroke-linecap="round"/>
  <line x1="178" y1="436" x2="178" y2="418" stroke="{NAVY}" stroke-width="3" stroke-linecap="round"/>
  <circle cx="178" cy="436" r="3" fill="{NAVY}"/>
</g></g>"""


# ---------------------------------------------------------------- martı, simit, çöp adam
def simit(sinif="", opaklik=1):
    """Susamlı simit; (0,0) halkanın merkezi."""
    susam = "".join(
        f'<circle cx="{round(14 * __import__("math").cos(a), 1)}" cy="{round(14 * __import__("math").sin(a), 1)}" r="1.5" fill="#fff1c9" stroke="none"/>'
        for a in [i * 0.9 for i in range(7)]
    )
    return (f'<g class="{sinif}" opacity="{opaklik}"><circle r="14" fill="none" stroke="#c9782b" stroke-width="9"/>'
            f'<circle r="14" fill="none" stroke="#e0a14b" stroke-width="3" opacity="0.7"/>{susam}</g>')


def marti(p, x, y, olcek=1.0, don=False, simitli=False):
    """Martı. Dış sarmal yalnız konum (translate); ölçek/yön en içte, böylece GSAP x/y ölçeksiz uzayda çalışır.
    Kanatlar gövdenin arkasında çizilir; pivotları (0,2)."""
    sx = -olcek if don else olcek
    kol = "#5f7389"
    ekstra = f'<g transform="translate(37 12)">{simit(p + "-simit", 0)}</g>' if simitli else ""
    return f"""
<g transform="translate({x} {y})">
  <g class="{p}" data-ox="0" data-oy="0">
   <g transform="scale({sx} {olcek})">
    <g class="{p}-wl" data-ox="0" data-oy="2">
      <path d="M0,2 C-8,-14 -30,-20 -54,-6 C-36,-6 -18,0 0,10 Z" fill="#ffffff" stroke="{kol}" stroke-width="2.4" stroke-linejoin="round"/>
      <path d="M-54,-6 C-48,-6 -42,-5 -37,-4 L-44,1 Z" fill="#3d4f66"/>
    </g>
    <g class="{p}-wr" data-ox="0" data-oy="2">
      <path d="M0,2 C8,-14 30,-20 54,-6 C36,-6 18,0 0,10 Z" fill="#ffffff" stroke="{kol}" stroke-width="2.4" stroke-linejoin="round"/>
      <path d="M54,-6 C48,-6 42,-5 37,-4 L44,1 Z" fill="#3d4f66"/>
    </g>
    <path d="M-16,5 L-34,2 L-31,13 L-16,10 Z" fill="#ffffff" stroke="{kol}" stroke-width="2.2" stroke-linejoin="round"/>
    <ellipse cx="0" cy="7" rx="19" ry="9" fill="#ffffff" stroke="{kol}" stroke-width="2.4"/>
    <circle cx="16" cy="2" r="6.8" fill="#ffffff" stroke="{kol}" stroke-width="2.2"/>
    <path d="M21,1 L33,4.5 L21,7 Z" fill="#f2a516"/>
    <circle cx="18.5" cy="0.5" r="1.6" fill="#1f2937"/>
    {ekstra}
   </g>
  </g>
</g>"""


def cop_adam(p, fx, fy, s=1.0, sapka=False, atki=False):
    """Çöp adam. Her uzvun pivotu data-ox/data-oy'de (vapur yerel koordinatı); GSAP svgOrigin ile döndürür."""
    sw = round(6.2 * max(s, 0.8), 1)
    bacak, govde, ust, on = 56 * s, 50 * s, 30 * s, 28 * s
    r = 23 * s
    kalca = fy - bacak
    omuz = kalca - govde
    bas_y = omuz - 25 * s
    ox = lambda v: round(v, 1)  # noqa: E731
    sx, sy = fx, omuz + 4 * s

    def kol(taraf):
        d = -1 if taraf == "L" else 1
        elx, ely = sx + d * 10 * s, sy + ust
        elx2, ely2 = elx + d * 6 * s, ely + on
        return (
            f'<g class="{p}-a{taraf}" data-ox="{ox(sx)}" data-oy="{ox(sy)}">'
            f'<line x1="{ox(sx)}" y1="{ox(sy)}" x2="{ox(elx)}" y2="{ox(ely)}"/>'
            f'<g class="{p}-f{taraf}" data-ox="{ox(elx)}" data-oy="{ox(ely)}">'
            f'<line x1="{ox(elx)}" y1="{ox(ely)}" x2="{ox(elx2)}" y2="{ox(ely2)}"/>'
            f'<circle cx="{ox(elx2)}" cy="{ox(ely2)}" r="{ox(3.2 * s + 1.5)}" fill="{NAVY}" stroke="none"/>'
            f'<g transform="translate({ox(elx2)} {ox(ely2 - 4 * s)})">{simit(p + "-s" + taraf, 1) if atki == taraf else ""}</g>'
            f"</g></g>"
        )

    yuz = (
        f'<circle cx="{ox(fx - 7 * s)}" cy="{ox(bas_y - 2 * s)}" r="{ox(2.4 * s + 0.6)}" fill="{NAVY}" stroke="none"/>'
        f'<circle cx="{ox(fx + 7 * s)}" cy="{ox(bas_y - 2 * s)}" r="{ox(2.4 * s + 0.6)}" fill="{NAVY}" stroke="none"/>'
        f'<path class="{p}-gulus" d="M{ox(fx - 8 * s)},{ox(bas_y + 6 * s)} Q{ox(fx)},{ox(bas_y + 14 * s)} {ox(fx + 8 * s)},{ox(bas_y + 6 * s)}" fill="none" stroke-width="{ox(sw * 0.55)}"/>'
        f'<path class="{p}-agiz" d="M{ox(fx - 8 * s)},{ox(bas_y + 5 * s)} Q{ox(fx)},{ox(bas_y + 22 * s)} {ox(fx + 8 * s)},{ox(bas_y + 5 * s)} Z" fill="#7a2230" stroke-width="{ox(sw * 0.4)}" opacity="0"/>'
    )
    hw = (r * r - (10 * s) ** 2) ** 0.5  # şapka kenarı göz hizasının üstünde kalsın
    kafa_ust = (
        f'<path d="M{ox(fx - hw)},{ox(bas_y - 10 * s)} A{ox(r)},{ox(r)} 0 0 1 {ox(fx + hw)},{ox(bas_y - 10 * s)} Z" fill="{YELLOW}"/>'
        f'<circle cx="{ox(fx)}" cy="{ox(bas_y - r - 1.5 * s)}" r="{ox(4 * s + 1)}" fill="{RED}" stroke-width="2"/>'
        if sapka else ""
    )
    atki_boyun = (
        f'<path d="M{ox(fx - 12 * s)},{ox(omuz - 1 * s)} Q{ox(fx)},{ox(omuz + 8 * s)} {ox(fx + 12 * s)},{ox(omuz - 1 * s)}" '
        f'fill="none" stroke="{RED}" stroke-width="{ox(sw * 1.1)}"/>' if atki is not None and not sapka else ""
    )
    return f"""
<g class="{p}" data-ox="{ox(fx)}" data-oy="{ox(fy)}" fill="none" stroke="{NAVY}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">
  <g class="{p}-govde" data-ox="{ox(fx)}" data-oy="{ox(kalca)}">
    <line x1="{ox(fx)}" y1="{ox(kalca)}" x2="{ox(fx - 19 * s)}" y2="{ox(fy)}"/>
    <line x1="{ox(fx)}" y1="{ox(kalca)}" x2="{ox(fx + 19 * s)}" y2="{ox(fy)}"/>
    <line x1="{ox(fx)}" y1="{ox(kalca)}" x2="{ox(fx)}" y2="{ox(omuz)}"/>
    {atki_boyun}
    {kol("L")}
    {kol("R")}
    <g class="{p}-bas" data-ox="{ox(fx)}" data-oy="{ox(omuz - 2 * s)}">
      <circle cx="{ox(fx)}" cy="{ox(bas_y)}" r="{ox(r)}" fill="{CREAM}"/>
      {kafa_ust}
      {yuz}
    </g>
  </g>
</g>"""


# ---------------------------------------------------------------- vapur
def vapur(n, icerik_on="", icerik_arka="", dumanli=True):
    """Yerel koordinat: (0,0) su hattı merkezi, baş sağda. icerik_*: karakterler, martılar."""
    hull_yol = ("M-300,-70 L262,-70 Q300,-72 336,-98 Q322,-40 286,-4 Q276,10 250,10 L-250,10 "
                "Q-285,10 -292,-12 L-300,-70 Z")
    portholes = "".join(f'<circle cx="{x}" cy="-52" r="5.5" fill="{WIN}" stroke="{NAVY}" stroke-width="1.8"/>'
                        for x in range(-252, 256, 38))
    pencere1 = "".join(f'<rect x="{x}" y="-118" width="30" height="26" rx="5" fill="{WIN}" stroke="{NAVY}" stroke-width="2"/>'
                       for x in range(-236, 214, 46))
    pencere2 = "".join(f'<rect x="{x}" y="-178" width="17" height="24" rx="3" fill="{WIN}" stroke="{NAVY}" stroke-width="2"/>'
                       for x in (126, 148, 170))
    direk = "".join(f'<line x1="{x}" y1="{DECK}" x2="{x}" y2="{DECK - 26}"/>' for x in range(-250, 222, 34))
    duman = ""
    if dumanli:
        duman = "".join(
            f'<circle class="duman" cx="{fx}" cy="-204" r="11" fill="#eef1f5" opacity="0"/>'
            for fx in (-216, -166) for _ in range(2)
        )
    return f"""
<g transform="translate({SHIP_X} {SHIP_Y})">
  <g class="vapur">
    {icerik_arka}
    <g class="iz" data-ox="-300" data-oy="4" fill="none" stroke="#ffffff" stroke-linecap="round" opacity="0.8">
      <path d="M-306,2 Q-380,-2 -470,4" stroke-width="7"/><path d="M-306,9 Q-400,8 -520,12" stroke-width="5" opacity="0.7"/>
    </g>
    <clipPath id="govde-{n}"><path d="{hull_yol}"/></clipPath>
    <path d="{hull_yol}" fill="{HULL}" stroke="{NAVY}" stroke-width="3"/>
    <g clip-path="url(#govde-{n})">
      <rect x="-320" y="-22" width="680" height="40" fill="#27406b"/>
      <rect x="-320" y="-34" width="680" height="12" fill="{RED}"/>
    </g>
    {portholes}
    <rect x="-250" y="-130" width="460" height="60" fill="{HULL}" stroke="{NAVY}" stroke-width="3"/>
    {pencere1}
    <rect x="-262" y="{DECK}" width="484" height="8" rx="2" fill="#d9d3c3" stroke="{NAVY}" stroke-width="3"/>
    <rect x="-232" y="-198" width="32" height="60" fill="{YELLOW}" stroke="{NAVY}" stroke-width="3"/>
    <rect x="-232" y="-198" width="32" height="14" fill="{NAVY}"/>
    <rect x="-182" y="-198" width="32" height="60" fill="{YELLOW}" stroke="{NAVY}" stroke-width="3"/>
    <rect x="-182" y="-198" width="32" height="14" fill="{NAVY}"/>
    <rect x="118" y="-188" width="84" height="50" fill="{HULL}" stroke="{NAVY}" stroke-width="3"/>
    {pencere2}
    <rect x="110" y="-196" width="100" height="9" rx="2" fill="#3a4a63"/>
    <line x1="160" y1="-196" x2="160" y2="-236" stroke="{NAVY}" stroke-width="4" stroke-linecap="round"/>
    <line x1="146" y1="-224" x2="174" y2="-224" stroke="{NAVY}" stroke-width="4" stroke-linecap="round"/>
    {icerik_on}
    <g stroke="#6f819d" stroke-width="3.2" stroke-linecap="round">
      {direk}
      <line x1="-250" y1="{DECK - 26}" x2="216" y2="{DECK - 26}"/>
      <line x1="-250" y1="{DECK - 13}" x2="216" y2="{DECK - 13}" opacity="0.7"/>
    </g>
    {duman}
    <ellipse class="kopuk" cx="322" cy="-2" rx="36" ry="7" fill="#ffffff" opacity="0.85" data-ox="322" data-oy="-2"/>
  </g>
</g>
<path class="onsu" d="{dalga_yolu(SHIP_Y - 6, 5, kapali=True)}" fill="#2f7db4" opacity="0.96"/>
<path class="onsu-ust" d="{dalga_yolu(SHIP_Y - 6, 5)}" fill="none" stroke="#bfe0f5" stroke-width="3" opacity="0.7"/>"""


# ---------------------------------------------------------------- segment
# Her segment: güneşin yeri, kamera yakınlaşması, karakter/martı yerleşimi.
SAHNE = {
    1: dict(gunes=(1040, 150)),
    2: dict(gunes=(1010, 170)),
    3: dict(gunes=(980, 140)),
    4: dict(gunes=(1000, 160)),
    5: dict(gunes=(1030, 150)),
    6: dict(gunes=(1060, 120)),
}


def sahne_icerigi(n):
    gx, gy = SAHNE[n]["gunes"]
    adam_x = {1: -40, 2: -20, 3: -30, 4: -95, 5: -95, 6: -95}[n]
    iki = n >= 4
    on = cop_adam("a", adam_x, DECK, 1.0, atki="L" if n == 1 else None)
    if iki:
        on += cop_adam("c", 15, DECK, 0.68, sapka=True, atki="R" if n in (4, 5) else None)

    arka = ""
    if n == 5:
        # simiti kapacak martı vapur koordinatında (diğerleri tuvalde); karakterlerin önünde çizilir
        on += marti("g5", 340, -430, 1.25, don=True, simitli=True)

    gul = []
    if n == 1:
        gul = [marti("g1", 330, 210, 1.2), marti("g2", 440, 120, 1.0), marti("g3", 250, 300, 0.95)]
    elif n == 2:
        gul = [marti("g1", 160, 150, 1.0), marti("g2", 300, 215, 0.8)]
    elif n == 3:
        gul = [marti("g1", 470, 190, 1.25, don=True), marti("g2", 600, 135, 1.1),
               marti("g3", 730, 200, 1.2, don=True), marti("g4", 850, 150, 1.0)]
    elif n == 4:
        gul = [marti("g1", 1150, 130, 0.9, don=True)]
    elif n == 5:
        gul = []
    elif n == 6:
        gul = [marti("g1", 330, 235, 1.15), marti("g2", 450, 160, 1.0), marti("g3", 230, 150, 0.95),
               marti("g4", 400, 290, 0.85), marti("g5", 170, 255, 0.8)]

    bulutlar = {
        1: [(250, 120, 1.0), (860, 90, 0.8), (1120, 220, 0.6)],
        2: [(520, 100, 1.0), (1000, 80, 0.7)],
        3: [(180, 150, 0.9), (900, 100, 1.0)],
        4: [(300, 110, 1.0), (940, 150, 0.8)],
        5: [(210, 90, 0.8), (780, 130, 1.0)],
        6: [(420, 100, 1.0), (1040, 70, 0.75), (140, 190, 0.6)],
    }[n]
    bulut_svg = "".join(bulut(*b) for b in bulutlar)
    dalga_y = [430, 452, 486, 560, 600, 648, 690]
    dalgalar = "".join(
        f'<path class="dalga" d="{dalga_yolu(y)}" fill="none" stroke="#ffffff" stroke-width="3" opacity="{0.22 if y < 540 else 0.3}"/>'
        for y in dalga_y
    )
    return f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <defs>
    <linearGradient id="gok-{n}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#6fb1e8"/><stop offset="0.75" stop-color="#bfe0f5"/><stop offset="1" stop-color="#fde7c9"/>
    </linearGradient>
    <linearGradient id="deniz-{n}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#4a98cf"/><stop offset="1" stop-color="#1b5588"/>
    </linearGradient>
    <radialGradient id="parlak-{n}"><stop offset="0" stop-color="#fff6cf" stop-opacity="0.95"/><stop offset="1" stop-color="#fff6cf" stop-opacity="0"/></radialGradient>
  </defs>
  <g class="kamera" data-ox="640" data-oy="400">
    <rect x="-100" y="-100" width="{W + 200}" height="{400 + 100}" fill="url(#gok-{n})"/>
    <g class="gunes" data-ox="{gx}" data-oy="{gy}">
      <circle cx="{gx}" cy="{gy}" r="110" fill="url(#parlak-{n})"/><circle cx="{gx}" cy="{gy}" r="44" fill="#fff3bd"/>
    </g>
    {bulut_svg}
    <g class="ufuk">{ufuk_cizgisi()}</g>
    <rect x="-100" y="400" width="{W + 200}" height="{H - 400 + 120}" fill="url(#deniz-{n})"/>
    {dalgalar}
    {iskele() if n == 2 else ""}
    {vapur(n, icerik_on=on, icerik_arka=arka)}
    {"".join(gul)}
  </g>
</svg>"""


def sahne_blogu(n, kayit, cumle):
    return f"""
    <div id="sahne{n}" class="sahne clip" data-start="{kayit['bas']}" data-duration="{kayit['sure']}" data-track-index="{n}">
      {sahne_icerigi(n)}
      <div class="altyazi"><span>{escape(cumle)}</span></div>
    </div>"""


CSS = """
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { margin: 0; width: 1280px; height: 720px; overflow: hidden; background: #0b1a33; }
      #root { position: relative; width: 1280px; height: 720px; overflow: hidden;
              font-family: system-ui, -apple-system, sans-serif; }
      .sahne { position: absolute; left: 0; top: 0; width: 1280px; height: 720px; overflow: hidden; }
      .sahne svg { position: absolute; left: 0; top: 0; }
      .altyazi { position: absolute; left: 70px; right: 70px; bottom: 38px; text-align: center; }
      .altyazi span { display: inline-block; max-width: 1140px; padding: 12px 28px 14px; border-radius: 18px;
                      background: rgba(10, 21, 42, 0.84); color: #ffffff; font-size: 42px; font-weight: 700;
                      line-height: 1.22; letter-spacing: 0.2px; }
"""

JS = r"""
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });

      // uzuv/grup pivotları: svgOrigin ile (vapur ya da tuval koordinatında)
      document.querySelectorAll("[data-ox]").forEach(function (el) {
        gsap.set(el, { svgOrigin: el.dataset.ox + " " + el.dataset.oy });
      });

      function sahne(n) {
        const el = document.getElementById("sahne" + n);
        return { el: el, n: n, S: parseFloat(el.dataset.start), D: parseFloat(el.dataset.duration) };
      }
      function q(sc, sel) { return sc.el.querySelector(sel); }
      function qa(sc, sel) { return Array.prototype.slice.call(sc.el.querySelectorAll(sel)); }
      // segmenti tam dolduran gidip-gelen döngü (süre tam bölünür, segment sonunda donma olmaz)
      function git(sc, el, from, to, per, ease, at) {
        const bas = at || 0;
        const N = Math.max(1, Math.round((sc.D - bas) / per));
        tl.fromTo(el, from, Object.assign({ duration: (sc.D - bas) / N, ease: ease || "sine.inOut", repeat: N - 1, yoyo: true }, to), sc.S + bas);
      }
      // tek yönlü döngü (dalga, duman)
      function kos(sc, el, from, to, per, ease) {
        const N = Math.max(1, Math.round(sc.D / per));
        tl.fromTo(el, from, Object.assign({ duration: sc.D / N, ease: ease || "none", repeat: N - 1 }, to), sc.S);
      }
      function gecis(sc, el, from, to, t0, t1, ease) {
        tl.fromTo(el, from, Object.assign({ duration: t1 - t0, ease: ease || "power2.inOut" }, to), sc.S + t0);
      }
      function kanat(sc, p, per) {
        git(sc, q(sc, "." + p + "-wl"), { rotation: -24 }, { rotation: 26 }, per, "sine.inOut");
        git(sc, q(sc, "." + p + "-wr"), { rotation: 24 }, { rotation: -26 }, per, "sine.inOut");
        git(sc, q(sc, "." + p), { y: -7 }, { y: 7 }, per * 3.1, "sine.inOut");
      }
      function mutlu(sc, p, t0) {
        tl.set(q(sc, "." + p + "-gulus"), { opacity: 0 }, sc.S + t0);
        tl.set(q(sc, "." + p + "-agiz"), { opacity: 1 }, sc.S + t0);
      }

      // ortak: altyazı girişi, kamera, dalga, bulut, duman, köpük, vapur sallanması
      function ortak(sc, o) {
        tl.fromTo(q(sc, ".altyazi span"), { y: 16 }, { y: 0, duration: 0.28, ease: "power2.out" }, sc.S);
        tl.fromTo(q(sc, ".kamera"), { scale: o.z0 || 1, x: 0 }, { scale: o.z1, x: o.px || 0, duration: sc.D, ease: "none" }, sc.S);
        qa(sc, ".dalga").forEach(function (w, i) { kos(sc, w, { x: 0 }, { x: -160 }, 2.5 + i * 0.6); });
        kos(sc, q(sc, ".onsu"), { x: 0 }, { x: -160 }, 2.2);
        kos(sc, q(sc, ".onsu-ust"), { x: 0 }, { x: -160 }, 2.2);
        qa(sc, ".bulut").forEach(function (b, i) {
          tl.fromTo(b, { x: 0 }, { x: (o.bulut || 26) + i * 12, duration: sc.D, ease: "none" }, sc.S);
        });
        tl.fromTo(q(sc, ".ufuk"), { x: 0 }, { x: o.ufuk || -12, duration: sc.D, ease: "none" }, sc.S);
        git(sc, q(sc, ".gunes"), { scale: 0.96 }, { scale: 1.05 }, 2.4);
        qa(sc, ".duman").forEach(function (d, i) {
          kos(sc, d, { y: 0, x: 0, scale: 0.6, opacity: 0.85 }, { y: -84, x: -58, scale: 1.9, opacity: 0 }, 1.05 + i * 0.31, "none");
        });
        git(sc, q(sc, ".kopuk"), { scaleX: 0.8 }, { scaleX: 1.2 }, 0.5);
        git(sc, q(sc, ".iz"), { scaleX: 0.75 }, { scaleX: 1.1 }, 0.9);
        git(sc, q(sc, ".vapur"), { y: -2 }, { y: 3 }, 1.7);
        if (o.drift) { tl.fromTo(q(sc, ".vapur"), { x: o.drift[0] }, { x: o.drift[1], duration: sc.D, ease: "none" }, sc.S); }
      }
      function sallan(sc, p, per, aci, y) {
        git(sc, q(sc, "." + p), { rotation: -aci }, { rotation: aci }, per, "sine.inOut");
        if (y) { git(sc, q(sc, "." + p + "-govde"), { y: 0 }, { y: y }, per / 2, "sine.inOut"); }
      }
      function sal(sc, el, aci, per) { git(sc, el, { rotation: -aci }, { rotation: aci }, per, "sine.inOut"); }

      // ---- Segment 1: kanca. Elinde simit, martılar bekliyor
      (function () {
        const sc = sahne(1);
        ortak(sc, { z0: 1, z1: 1.06 });
        sallan(sc, "a", 1.7, 2.2);
        tl.set(q(sc, ".a-aL"), { rotation: 72 }, sc.S);
        tl.set(q(sc, ".a-fL"), { rotation: -34 }, sc.S);
        tl.set(q(sc, ".a-aR"), { rotation: -116 }, sc.S);
        sal(sc, q(sc, ".a-fR"), 34, 0.42);
        kanat(sc, "g1", 0.3); kanat(sc, "g2", 0.34); kanat(sc, "g3", 0.28);
        tl.fromTo(q(sc, ".g1"), { x: 0 }, { x: 55, duration: sc.D, ease: "none" }, sc.S);
        tl.fromTo(q(sc, ".g3"), { x: 0 }, { x: 60, duration: sc.D, ease: "none" }, sc.S);
      })();

      // ---- Segment 2: Kadıköy iskelesinden kalkış
      (function () {
        const sc = sahne(2);
        ortak(sc, { z0: 1.0, z1: 1.02, drift: [30, 150], ufuk: -20, bulut: 18 });
        tl.fromTo(q(sc, ".iskele"), { x: 0 }, { x: -30, duration: sc.D, ease: "power1.in" }, sc.S);
        sallan(sc, "a", 1.8, 2);
        tl.set(q(sc, ".a-aL"), { rotation: 116 }, sc.S);
        sal(sc, q(sc, ".a-fL"), 30, 0.4);
        kanat(sc, "g1", 0.3); kanat(sc, "g2", 0.32);
        tl.fromTo(q(sc, ".g1"), { x: 0 }, { x: 760, duration: sc.D, ease: "none" }, sc.S);
        tl.fromTo(q(sc, ".g2"), { x: 0 }, { x: 640, duration: sc.D, ease: "none" }, sc.S);
      })();

      // ---- Segment 3: martılar güvertede yolcuları izliyor
      (function () {
        const sc = sahne(3);
        ortak(sc, { z0: 1.0, z1: 1.12, drift: [10, 40] });
        sallan(sc, "a", 1.9, 2);
        tl.set(q(sc, ".a-aL"), { rotation: 8 }, sc.S);
        tl.set(q(sc, ".a-aR"), { rotation: -8 }, sc.S);
        git(sc, q(sc, ".a-bas"), { rotation: 6 }, { rotation: 11 }, 1.3);
        kanat(sc, "g1", 0.27); kanat(sc, "g2", 0.31); kanat(sc, "g3", 0.29); kanat(sc, "g4", 0.33);
        tl.fromTo(q(sc, ".g2"), { x: 0 }, { x: 34, duration: sc.D, ease: "none" }, sc.S);
        tl.fromTo(q(sc, ".g4"), { x: 0 }, { x: 40, duration: sc.D, ease: "none" }, sc.S);
        tl.fromTo(q(sc, ".g1"), { x: 0 }, { x: -40, duration: sc.D, ease: "none" }, sc.S);
      })();

      // ---- Segment 4: çocuk simidi havaya uzatıyor
      (function () {
        const sc = sahne(4);
        ortak(sc, { z0: 1.02, z1: 1.12, drift: [40, 60] });
        sallan(sc, "a", 2.0, 1.6);
        tl.set(q(sc, ".a-aR"), { rotation: -112 }, sc.S);
        tl.set(q(sc, ".a-fR"), { rotation: -6 }, sc.S);
        mutlu(sc, "a", 0.2);
        sallan(sc, "c", 0.9, 1.6, -3);
        gecis(sc, q(sc, ".c-aR"), { rotation: 0 }, { rotation: -124 }, 0.35, 1.15, "power2.out");
        git(sc, q(sc, ".c-fR"), { rotation: -4 }, { rotation: 8 }, 0.5, "sine.inOut", 1.15);
        kanat(sc, "g1", 0.3);
        tl.fromTo(q(sc, ".g1"), { x: 0 }, { x: -150, duration: sc.D, ease: "none" }, sc.S);
      })();

      // ---- Segment 5: martı simidi kapıyor, herkes gülüyor
      (function () {
        const sc = sahne(5);
        ortak(sc, { z0: 1.1, z1: 1.14, drift: [60, 62] });
        tl.set(q(sc, ".c-aR"), { rotation: -124 }, sc.S);
        tl.set(q(sc, ".a-aR"), { rotation: -112 }, sc.S);
        tl.set(q(sc, ".a-fR"), { rotation: -6 }, sc.S);
        // simiti kapacak martı: sağ üstten dalış, kapış, sol üste kaçış
        kanat(sc, "g5", 0.26);
        gecis(sc, q(sc, ".g5"), { x: 0, y: 0 }, { x: -260, y: 180 }, 0, 1.0, "power1.inOut");
        tl.set(q(sc, ".c-sR"), { opacity: 0 }, sc.S + 1.08);
        tl.set(q(sc, ".g5-simit"), { opacity: 1 }, sc.S + 1.08);
        gecis(sc, q(sc, ".g5"), { x: -260, y: 180 }, { x: -640, y: -130 }, 1.08, sc.D, "power2.in");
        // gülme
        mutlu(sc, "a", 1.0); mutlu(sc, "c", 1.0);
        git(sc, q(sc, ".a-govde"), { y: 0 }, { y: -6 }, 0.26, "sine.inOut", 1.0);
        git(sc, q(sc, ".c-govde"), { y: 0 }, { y: -7 }, 0.24, "sine.inOut", 1.0);
        sal(sc, q(sc, ".a-bas"), 9, 0.5);
        sal(sc, q(sc, ".c-bas"), 11, 0.46);
        git(sc, q(sc, ".c-fR"), { rotation: -14 }, { rotation: 18 }, 0.34, "sine.inOut", 1.1);
      })();

      // ---- Segment 6: vapur boğazda ilerliyor, martılar peşinden
      (function () {
        const sc = sahne(6);
        ortak(sc, { z0: 1.0, z1: 1.0, drift: [-40, 75], ufuk: -46, bulut: 40 });
        sallan(sc, "a", 1.8, 1.8);
        sallan(sc, "c", 1.0, 1.8, -3);
        tl.set(q(sc, ".a-aR"), { rotation: -146 }, sc.S);
        sal(sc, q(sc, ".a-fR"), 32, 0.42);
        tl.set(q(sc, ".c-aL"), { rotation: 118 }, sc.S);
        sal(sc, q(sc, ".c-fL"), 30, 0.38);
        mutlu(sc, "c", 0.3);
        ["g1", "g2", "g3", "g4", "g5"].forEach(function (g, i) {
          kanat(sc, g, 0.27 + i * 0.015);
          tl.fromTo(q(sc, "." + g), { x: 0 }, { x: 70 + i * 10, duration: sc.D, ease: "power1.out" }, sc.S);
        });
      })();

      window.__timelines["main"] = tl;
      tl.seek(0);
"""


def main():
    bloklar = "".join(sahne_blogu(i + 1, TIMING["cumleler"][i], CUMLELER[i]) for i in range(len(CUMLELER)))
    toplam = TIMING["toplam"]
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
    <div id="root" data-composition-id="main" data-start="0" data-duration="{toplam}" data-width="{W}" data-height="{H}" data-fps="30">{bloklar}
    </div>
    <script>{JS}    </script>
  </body>
</html>
"""
    (AYRI / "index.html").write_text(html, encoding="utf-8")
    print(f"index.html yazıldı: {len(CUMLELER)} sahne, toplam {toplam} sn")
    for i, k in enumerate(TIMING["cumleler"], 1):
        print(f"  sahne {i}: {k['bas']:.2f} -> {k['bit']:.2f} sn ({k['sure']:.2f})")


if __name__ == "__main__":
    main()
