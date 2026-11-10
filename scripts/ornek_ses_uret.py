#!/usr/bin/env python3
"""Kısa örnek demolar için VoxCPM sunucusundan diyalog sesi üretir (kilitlemeli).

Kullanım (proje kökünden):
  python3 scripts/ornek_ses_uret.py demo-liman
Önkoşul: http://127.0.0.1:8123/health → loaded
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

SUNUCU = "http://127.0.0.1:8123/tts"
KOK = Path(__file__).resolve().parents[1]


def f0(path: Path) -> float:
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
        capture_output=True, check=True,
    ).stdout
    a = np.frombuffer(raw, np.float32)
    n = len(a)
    a = a[n // 4 : 3 * n // 4] - a.mean()
    if a.std() < 1e-4:
        return 0.0
    min_lag, max_lag = int(16000 / 450), int(16000 / 80)
    best, bl = 0.0, min_lag
    for lag in range(min_lag, max_lag):
        c = float(np.dot(a[:-lag], a[lag:]))
        if c > best:
            best, bl = c, lag
    return 16000 / bl


def tts(payload: dict, hedef: Path, retries: int = 4) -> None:
    """curl daha kararlı; urllib ara sıra 500 dönüyor."""
    body = json.dumps(payload)
    last = ""
    for i in range(retries):
        r = subprocess.run(
            ["curl", "-sS", "-X", "POST", SUNUCU,
             "-H", "Content-Type: application/json",
             "-d", body, "-o", str(hedef), "-w", "%{http_code}"],
            capture_output=True, text=True,
        )
        code = (r.stdout or "").strip()
        if code == "200" and hedef.exists() and hedef.stat().st_size > 20000:
            return
        last = f"http={code} size={hedef.stat().st_size if hedef.exists() else 0} err={r.stderr.strip()[:120]}"
        print(f"  tts retry {i + 1}: {last}")
        time.sleep(1.5 + i)
    raise RuntimeError(f"TTS başarısız: {last}")


def design_al(ad: str, metin: str, design: str, band: tuple[float, float], takes: int = 4) -> Path:
    tmp = KOK / "_tmp_ses" / ad
    tmp.mkdir(parents=True, exist_ok=True)
    adaylar = []
    hedef_orta = (band[0] + band[1]) / 2
    for t in range(1, takes + 1):
        p = tmp / f"{ad}_t{t}.wav"
        tts({
            "text": metin,
            "voice_design": design,
            "character_name": f"ornek_{ad}_t{t}",
            "language": "tr",
            "force_new_reference": True,
            "take": t,
            "cfg_value": 2.0,
        }, p)
        hz = f0(p)
        skor = abs(hz - hedef_orta)
        ok = band[0] <= hz <= band[1]
        print(f"  {ad} take{t}: F0≈{hz:.0f}Hz {'OK' if ok else 'x'} {p.name}")
        adaylar.append((0 if ok else 1, skor, -p.stat().st_size, p, hz))
    adaylar.sort()
    best = adaylar[0][3]
    print(f"  → seçilen {best.name} F0≈{adaylar[0][4]:.0f}Hz")
    return best


def klonla(metin: str, ref: Path, prompt: str, hedef: Path, kim: str,
           band: tuple[float, float], takes: int = 4) -> None:
    tmp = KOK / "_tmp_ses" / f"{kim}_klon"
    tmp.mkdir(parents=True, exist_ok=True)
    adaylar = []
    hedef_orta = (band[0] + band[1]) / 2
    for t in range(1, takes + 1):
        p = tmp / f"{hedef.stem}_t{t}.wav"
        tts({
            "text": metin,
            "reference_wav_path": str(ref.resolve()),
            "prompt_wav_path": str(ref.resolve()),
            "prompt_text": prompt,
            "character_name": f"ornek_{kim}_k{hedef.stem}_{t}",
            "language": "tr",
            "cfg_value": 2.0,
        }, p)
        hz = f0(p)
        ok = band[0] <= hz <= band[1]
        skor = abs(hz - hedef_orta)
        print(f"  klon {hedef.name} take{t}: F0≈{hz:.0f}Hz {'OK' if ok else 'x'}")
        adaylar.append((0 if ok else 1, skor, p, hz))
        if ok:
            break  # ilk band içi yeterli
    adaylar.sort()
    best, hz = adaylar[0][2], adaylar[0][3]
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(best), "-ac", "1", "-ar", "48000", str(hedef)],
        check=True,
    )
    print(f"  → {hedef.name} F0≈{hz:.0f}Hz")


def band_bul(kim: str, kart: dict) -> tuple[float, float]:
    if "perde" in kart:
        return tuple(kart["perde"])  # type: ignore[return-value]
    if any(k in kim for k in ("cocuk", "torun", "ogrenci", "elif", "kiz")):
        return (220, 400)
    if any(k in kim for k in ("dede", "baba", "konduktor", "adam", "yolcu")):
        return (90, 180)
    if any(k in kim for k in ("anne", "teyze", "kadin", "ogretmen")):
        return (160, 260)
    return (120, 280)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    demo = KOK / sys.argv[1]
    cumleler = []
    for ham in (demo / "cumleler.txt").read_text(encoding="utf-8").splitlines():
        if ham.strip():
            kim, _, metin = ham.partition(":")
            cumleler.append((kim.strip(), metin.strip()))
    sesler = json.loads((demo / "sesler.json").read_text(encoding="utf-8"))
    ses_dir = demo / "ses"
    ses_dir.mkdir(exist_ok=True)
    ref_dir = demo / "referans"
    ref_dir.mkdir(exist_ok=True)

    ilk: dict[str, tuple[str, Path, tuple[float, float]]] = {}
    for kim, metin in cumleler:
        if kim in ilk:
            continue
        kart = sesler[kim]
        band = band_bul(kim, kart)
        if "reference" in kart and (demo / kart["reference"]).is_file():
            ref = demo / kart["reference"]
            print(f"{kim}: mevcut referans {ref} F0≈{f0(ref):.0f}Hz")
        else:
            print(f"{kim}: tarif → {kart['design'][:60]}… band={band}")
            ref = design_al(kim, metin, kart["design"], band)
            hedef_ref = ref_dir / f"{kim}.wav"
            subprocess.run(
                ["ffmpeg", "-y", "-v", "error", "-i", str(ref), "-ac", "1", "-ar", "48000", str(hedef_ref)],
                check=True,
            )
            ref = hedef_ref
            sesler[kim] = {
                "reference": f"referans/{kim}.wav",
                "prompt_wav": f"referans/{kim}.wav",
                "prompt_text": metin,
                "perde": list(band),
            }
        ilk[kim] = (metin, ref, band)

    (demo / "sesler.json").write_text(json.dumps(sesler, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for i, (kim, metin) in enumerate(cumleler, 1):
        out = ses_dir / f"{i:03d}_{kim}.wav"
        prompt, ref, band = ilk[kim]
        if i == min(j for j, (k, _) in enumerate(cumleler, 1) if k == kim):
            subprocess.run(
                ["ffmpeg", "-y", "-v", "error", "-i", str(ref), "-ac", "1", "-ar", "48000", str(out)],
                check=True,
            )
            print(f"{out.name}: referans kopyası F0≈{f0(out):.0f}Hz")
        else:
            klonla(metin, ref, prompt, out, kim, band)

    print("TAMAM", demo.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
