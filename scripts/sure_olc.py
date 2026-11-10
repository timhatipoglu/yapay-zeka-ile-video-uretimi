#!/usr/bin/env python3
"""Cümle cümle üretilmiş ses dosyalarının GERÇEK süresini ölçer ve zaman çizelgesi yazar.

Neden: video süresini ses belirler (Audio Lock). Süreyi "toplam / cümle sayısı" diye eşit
bölersen görüntü sesten kopar. Önce sesi üret, sonra bu betikle ölç, animasyonu o sürelere kur.

Kullanım (proje kökünden):
  python3 scripts/sure_olc.py SES_KLASORU [timing.json]
  python3 scripts/sure_olc.py ses/ timing.json       # belgelerdeki biçim: timing.json proje kökünde
İkinci argüman yazılmazsa timing.json SES_KLASORU'nun İÇİNE yazılır; animasyon betikleri onu
proje kökünde beklediği için yolunu ver.

SES_KLASORU içindeki dosyalar ada göre sıralanır (001_anlatici.wav, 002_ece.wav ...); sıra
birlestir.sh ile aynıdır. Gizli dosyalar (._001.wav gibi) sayılmaz, adda boşluk olabilir.
Numaralı adlarda hane sayısı sabit olmalı (001 ... 999, ya da 0001 ...); "100_x" ile "1000_x"
karışırsa betik uyarır. Cümleler boşluksuz art arda eklenir; sahneler.json'daki sonra_ms
sessizliği ses dosyasının içinde olduğu için ölçülen süreye zaten dahildir.
Desteklenen biçimler: wav, flac, mp3, m4a, aiff. ogg/opus desteklenmez (Opus'ta başlıktaki süre
ile çözülmüş süre ayrışabilir); betik bu dosyaları atlar ve uyarır, wav ya da flac'e çevir.
Çıkış kodları: 0 tamam · 1 klasör yok / ses dosyası yok / bir dosya okunamadı (kırık bağ dahil) /
timing.json yazılamadı · 2 yanlış kullanım.
Gereken: Python 3 ve ffprobe (ffmpeg ile gelir).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

UZANTILAR = {".wav", ".mp3", ".m4a", ".aiff", ".aif", ".flac"}
DESTEKSIZ = {".ogg", ".opus"}  # uyarılır ve atlanır; birlestir.sh da aynı kümeyi görmez
COK_KISA = 0.8   # saniye: bundan kısa cümle çoğu zaman yutulmuş/bozuk ses demektir
COK_UZUN = 20.0  # saniye: bundan uzun cümleyi ikiye bölmeyi düşün


# ffprobe dosya türünü içerikten sezer; saf bir ses tonu yanlışlıkla başka bir türe (mpegts)
# benzeyebilir. Uzantıdan bilinen türü zorla, tutmazsa (uzantı yanlışsa) içerikten sezmeye dön.
TUR = {".wav": "wav", ".flac": "flac", ".mp3": "mp3", ".aif": "aiff", ".aiff": "aiff"}


def sure(yol: Path) -> float:
    for tur in (TUR.get(yol.suffix.lower()), None):
        komut = ["ffprobe", "-v", "error", *(["-f", tur] if tur else []),
                 "-show_entries", "format=duration", "-of", "csv=p=0", str(yol)]
        try:
            return float(subprocess.check_output(komut, stderr=subprocess.PIPE))
        except FileNotFoundError:
            raise SystemExit("ffprobe bulunamadı: ffmpeg'i kur (brew install ffmpeg).")
        except (subprocess.CalledProcessError, ValueError):
            continue
    raise SystemExit(f"Ses dosyası okunamadı (bozuk ya da ses değil): {yol}")


def main() -> int:
    if not 2 <= len(sys.argv) <= 3:  # fazla argüman sessizce yutulmasın
        print(__doc__)
        return 2
    klasor = Path(sys.argv[1])
    cikis = Path(sys.argv[2]) if len(sys.argv) > 2 else klasor / "timing.json"
    if not klasor.is_dir():
        print(f"Ses klasörü yok: {klasor}", file=sys.stderr)
        return 1
    # Yazma hatası yüzlerce ses ölçüldükten sonra değil, başta görünsün.
    if not cikis.parent.is_dir() or cikis.is_dir():
        print(f"timing.json yazılamaz: {cikis} (üst klasör yok ya da bu ad bir klasör)",
              file=sys.stderr)
        return 1

    # Kırık bağ (symlink) da listelenir: birlestir.sh de görür, ikisi aynı kümeyi okur.
    tum = sorted(p for p in klasor.iterdir() if not p.name.startswith("."))
    for p in tum:
        if p.suffix.lower() in DESTEKSIZ and (p.is_file() or p.is_symlink()):
            print(f"UYARI: {p.name}: ogg/opus desteklenmiyor, atlandı (wav, flac, mp3, m4a ya da "
                  "aiff'e çevir).", file=sys.stderr)
    dosyalar = [p for p in tum if p.suffix.lower() in UZANTILAR and (p.is_file() or p.is_symlink())]
    if not dosyalar:
        print(f"Ses dosyası bulunamadı: {klasor}", file=sys.stderr)
        return 1
    kirik = [p for p in dosyalar if not p.is_file()]
    if kirik:
        print("Ses dosyası okunamadı (kırık bağ ya da dosya değil): "
              + ", ".join(str(p) for p in kirik), file=sys.stderr)
        return 1

    genislikler = {len(m.group(1)) for m in (re.match(r"(\d+)_", p.name) for p in dosyalar) if m}
    if len(genislikler) > 1:
        print("UYARI: dosya adlarındaki numaranın hane sayısı karışık (ör. 100_x ile 1000_x); ada "
              "göre sıralama cümle sırasını bozabilir. Numarayı aynı genişliğe getir (001, 0001).",
              file=sys.stderr)

    satirlar, t = [], 0.0
    for i, p in enumerate(dosyalar, 1):
        ham = sure(p)
        # Ham süre toplanır, yalnız yazılan değer yuvarlanır: yüzlerce cümlede yuvarlama hatası
        # birikip bas/bit/toplam'ı gerçek sesten kaydırmasın.
        satirlar.append({"sira": i, "dosya": p.name, "sure": round(ham, 3),
                         "bas": round(t, 3), "bit": round(t + ham, 3)})
        t += ham
    toplam = round(t, 3)

    try:
        cikis.write_text(json.dumps({"toplam": toplam, "cumleler": satirlar},
                                    ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as e:
        print(f"timing.json yazılamadı: {cikis} ({e})", file=sys.stderr)
        return 1

    print(f"{'#':>3}  {'dosya':<24}{'süre':>8}{'başlangıç':>11}")
    for r in satirlar:
        uyari = "  ⚠ çok kısa (yutulmuş olabilir)" if r["sure"] < COK_KISA else (
            "  ⚠ çok uzun (ikiye böl)" if r["sure"] > COK_UZUN else "")
        print(f"{r['sira']:>3}  {r['dosya']:<24}{r['sure']:>7.2f}s{r['bas']:>10.2f}s{uyari}")
    print(f"\nToplam: {toplam:.2f} sn  ->  {cikis}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
