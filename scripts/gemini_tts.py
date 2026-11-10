#!/usr/bin/env python3
"""Gemini API ile cümle cümle seslendirme (gemini-3.8-flash-tts / flash-lite-tts).

Her satır için ayrı istek atar, ses/001_anlatici.wav gibi dosyalar yazar. Gelen ses WAV
olarak yazılır (ham PCM gelirse 24 kHz, 16 bit, tek kanal varsayılıp WAV başlığı eklenir);
sure_olc.py ve birlestir.sh bu dosyaları olduğu gibi okur.

Hazırlık:
    pip install "google-genai>=2.25.0,<3"
    export GEMINI_API_KEY=...        # https://aistudio.google.com/apikey

Girdi iki biçimde olur (voxcpm_diyalog.py ile aynı).

cumleler.txt, her satır "[ad: ]cümle":
    anlatici: Bugün bir vapura biniyoruz.
    ece: Nereye gidiyoruz?
    Konuşmacısı yazılmamış satırı varsayılan konuşmacı (anlatici) okur.
  Konuşmacı adı küçük harfle başlar ("Not: ..." ya da "Saat 10:30'da" konuşmacı sayılmaz,
  tümü metindir). İstisna: büyük harfle yazılmış ad --ses ile tanımladığın bir konuşmacıysa
  ("Ece: ..." ama --ses ece=... var; "Isik:" ve "ISIK:" için --ses isik=... varsa da) betik
  DURUR; yoksa "Ece:" sese girerdi. --ses verilmemiş bir ad görürse de DURUR.
  Dosya UTF-8'dir; baştaki BOM yok sayılır. "#" ile başlayan satır YORUMDUR, atlanır
  (atlananların sayısı ve satır numaraları stderr'e yazılır). Cümlen "#" ile başlıyorsa
  ("#1 haber: ...") başına "anlatici: " koy ya da sahneler.json kullan.

sahneler.json, bir liste; her öğe bir cümle (segment):
    [{"konusmaci": "ece", "metin": "Nereye gidiyoruz?",
      "stil": "Speaking with excitement, a bit faster", "sonra_ms": 250}]
    konusmaci  --ses ile tanımladığın ad (yazılmazsa "anlatici")
    metin      okunacak cümle
    stil       isteğe bağlı üslup talimatı; speech_metadata.style alanına gider. Satırın stili
               --stil'i geçer (birleşmez).
    sonra_ms   isteğe bağlı; cümleden sonra WAV'ın sonuna eklenen sessizlik (ms, 24 kHz tek
               kanal 16 bit). sure_olc.py süreyi bununla birlikte ölçer.

Kullanım:
    python3 scripts/gemini_tts.py GIRDI ses/ --ses ad=SES [--ses ad=SES ...] [--stil GLOBAL]
                                  [--okunus okunus.json] [--sadece 3,7] [--yeniden] [--kuru]
    python3 scripts/gemini_tts.py cumleler.txt ses/ --ses anlatici=Kore --ses ece=Puck
    python3 scripts/gemini_tts.py cumleler.txt ses/ --ses anlatici=voice_XXXX    # AI Studio'da çoğalttığın kendi sesin
    python3 scripts/gemini_tts.py cumleler.txt ses/ --ses anlatici=Kore --stil "sakin, net, biraz yavaş"
    python3 scripts/gemini_tts.py sahneler.json ses/ --ses anlatici=Kore --sadece 7
    python3 scripts/gemini_tts.py cumleler.txt ses/ --ses anlatici=Kore --kuru   # istek atmadan kontrol

--ses değerleri: hazır ses adı (Kore, Puck, Charon, Zephyr, Sulafat ...), Extended Voice
Library'den bir ses ya da AI Studio / API ile oluşturduğun özel ses kimliği (voice_...).
30 hazır ses: https://aistudio.google.com/docs/speech-generation#prebuilt-voices
Kitaplığın tamamı (yüzlerce ses): AI Studio'da (aistudio.google.com/generate-speech) ya da
client.voices.list() / GET /v1beta/voices ile; ayrıntı:
https://aistudio.google.com/docs/speech-generation#voice-library

--okunus okunus.json: voxcpm_diyalog.py ile aynı ({"Claude": "Klod"}); yalnız SESE giden
metni değiştirir, tam sözcük eşler, uzun yazım önce denenir.

Satır içi etiketler (metnin içinde, motora özgü): Gemini 3.8 TTS açı parantez kullanır;
belgedeki etiketler <short pause> <long pause> <sigh> <laugh> <cough> <gasp> <breath>, belge
örneği "Wait... <short pause> did you hear that? <sigh>". VoxCPM kare parantez kullanır
([laughing] [sigh] ...; voxcpm_diyalog.py). Aynı sahneler.json iki motorda çalışır ama
etiketler motora göre yazılır.

Çıktı adı: ses/001_anlatici.wav ... (ada göre sıralı; sure_olc.py ve birlestir.sh bu sırayla
okur). Numara 999 cümleye kadar 3 hanedir; daha uzun girdide hane sayısı cümle sayısına göre
artar (0001_...), sıralama bozulmaz.

Var olan dosya atlanır (cümleyi değiştirdiysen dosyayı sil, --yeniden ya da --sadece ver).
--sadece 3,7 yalnız 3. ve 7. cümleyi (1 tabanlı sıra numarası) yeniden üretir, ötekilere
dokunmaz; --yeniden hepsini baştan üretir.

Kota: istekler SIRAYLA gider. 429 / RESOURCE_EXHAUSTED gelirse betik DURUR; yeniden
çalıştırırsan var olan dosyaları atlayıp kaldığı yerden devam eder. Aynı satırı
sessizce tekrar tekrar denemez.

Çıkış kodları: 0 tamam · 2 girdi/--ses/--bekle/kurulum hatası, çıktı klasörü bir dosya ya da
oluşturulamıyor (istek atılmadı) · 3 istek başarısız (kalan cümleler üretilmeden DURUR) ·
4 kota doldu (429 / RESOURCE_EXHAUSTED).
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import math
import re
import shlex
import sys
import time
import wave
from pathlib import Path
from typing import NamedTuple, NoReturn

# Ad harfle başlar: "12: Kasım ayında" bir konuşmacı satırı değil, düz metindir.
AD = r"[a-zçğıöşü][a-zçğıöşü0-9_]{1,23}"
KONUSMACI = re.compile(rf"^({AD}):\s+(.+)$")
AD_DESENI = re.compile(AD)
# Büyük harfle başlayan aday ("Ece: ..."): --ses ile tanımlı bir konuşmacının büyük harfli hâli mi?
BUYUK_ADAY = re.compile(r"^([A-ZÇĞİÖŞÜ][A-Za-zÇĞİÖŞÜçğıöşü0-9_]{1,23}):\s+\S")
VARSAYILAN = "anlatici"
# ogg/opus desteklenmez (sure_olc.py ve birlestir.sh de görmez); wav/flac/mp3/m4a/aiff okunur.
SES_UZANTILARI = {".wav", ".mp3", ".m4a", ".aiff", ".aif", ".flac"}
MAKS_SONRA_MS = 30000  # bundan uzun bekleme büyük olasılıkla yazım hatasıdır (250000 gibi)
ALANLAR = {"konusmaci", "metin", "stil", "sonra_ms"}


class Satir(NamedTuple):
    ad: str
    metin: str
    stil: str = ""
    sonra_ms: float = 0
    yer: str = ""  # hata iletisinde gösterilen kaynak: "satır 5" (txt) ya da "öğe 3" (json)


def hata(mesaj: str, kod: int = 2) -> NoReturn:
    print(mesaj, file=sys.stderr)
    raise SystemExit(kod)


def oku(yol: Path, ne: str) -> str:
    try:
        return yol.read_text(encoding="utf-8-sig")  # -sig: baştaki BOM'u yutar
    except (OSError, UnicodeDecodeError) as e:
        hata(f"{ne} okunamadı: {yol} ({e})")


def kucult(s: str) -> str:
    # Türkçe duyarlı: İ -> i, I -> ı (str.lower() "İ"yi iki karakterli bir diziye çevirir).
    return s.replace("İ", "i").replace("I", "ı").lower()


def tanimli_karsilik(ad: str, bilinen: set[str]) -> str | None:
    """Büyük harfle yazılmış adın tanımlı küçük harfli karşılığı (yoksa None).

    ASCII "I" ile yazılan ad iki türlü okunabilir: "Isik" -> Türkçe duyarlı "ısık" ya da düz
    "isik". Tanımlı olan hangisiyse o döner; "Işık" -> "ışık", "İlker" -> "ilker".
    """
    for aday in dict.fromkeys((kucult(ad), ad.lower())):
        if aday in bilinen:
            return aday
    return None


def dosya_adi(sira: int, ad: str, genislik: int) -> str:
    return f"{sira:0{genislik}d}_{ad}.wav"


def numara_genisligi(cumle_sayisi: int) -> int:
    # 999 cümleye kadar 001; ötesinde hane artar ki "1000_x" ile "100_x" ada göre karışmasın.
    return max(3, len(str(cumle_sayisi)))


def bekle_sayisi(deger: str) -> float:
    """--bekle için argparse türü: 0 ile 3600 arası sonlu sayı (negatif sleep traceback verirdi)."""
    try:
        x = float(deger)
    except ValueError:
        raise argparse.ArgumentTypeError(f"saniye cinsinden bir sayı olmalı: {deger!r}")
    if not math.isfinite(x) or not 0 <= x <= 3600:
        raise argparse.ArgumentTypeError(f"0 ile 3600 arasında bir sayı olmalı: {deger!r}")
    return x


def metin_satirlari(yol: Path, bilinen: set[str]) -> tuple[list[Satir], list[str], list[str]]:
    satirlar: list[Satir] = []
    hatalar: list[str] = []
    yorumlar: list[int] = []
    for no, ham in enumerate(oku(yol, "Cümle dosyası").splitlines(), 1):
        satir = ham.strip()
        if not satir:
            continue
        if satir.startswith("#"):
            yorumlar.append(no)
            continue
        yer = f"satır {no}"
        m = KONUSMACI.match(satir)
        if m:
            satirlar.append(Satir(m.group(1), m.group(2).strip(), yer=yer))
            continue
        b = BUYUK_ADAY.match(satir)
        kucuk = tanimli_karsilik(b.group(1), bilinen) if b else None
        if b and kucuk:
            hatalar.append(
                f"{yer}: '{b.group(1)}:' büyük harfle başlıyor ama '{kucuk}' için --ses "
                f"verilmiş; böyle yazılırsa '{b.group(1)}:' anlatıcıya okutulur. Konuşmacı "
                f"adı küçük harfle yazılır ('{kucuk}: ...'). Gerçekten anlatıcı metniyse "
                f"satırı '{VARSAYILAN}: {satir[:30]}...' diye başlat.")
            continue
        satirlar.append(Satir(VARSAYILAN, satir, yer=yer))
    uyarilar: list[str] = []
    if yorumlar:
        gosterilen = ", ".join(str(n) for n in yorumlar[:8]) + (" ..." if len(yorumlar) > 8 else "")
        uyarilar.append(
            f"NOT: {len(yorumlar)} satır '#' ile başladığı için yorum sayıldı ve atlandı "
            f"(satır {gosterilen}). Cümlen '#' ile başlıyorsa başına '{VARSAYILAN}: ' koy ya da "
            "sahneler.json kullan.")
    return satirlar, hatalar, uyarilar


def json_satirlari(yol: Path) -> tuple[list[Satir], list[str], list[str]]:
    try:
        veri = json.loads(oku(yol, "Cümle dosyası"))
    except json.JSONDecodeError as e:
        hata(f"Cümle dosyası geçerli JSON değil: {yol} ({e})")
    if not isinstance(veri, list):
        hata(f"Cümle dosyası bir JSON listesi ([...]) olmalı: {yol}")
    satirlar: list[Satir] = []
    hatalar: list[str] = []
    uyarilar: list[str] = []
    for no, oge in enumerate(veri, 1):
        yer = f"öğe {no}"
        if not isinstance(oge, dict):
            hatalar.append(f"{yer}: bir JSON nesnesi ({{...}}) olmalı")
            continue
        fazla = sorted(set(oge) - ALANLAR)
        if fazla:
            uyarilar.append(f"UYARI: {yer}: bilinmeyen alan yok sayıldı: {', '.join(fazla)} "
                            "(hız, yoğunluk gibi ayarları 'stil' cümlesine yaz)")
        ad = oge.get("konusmaci", VARSAYILAN)
        metin = oge.get("metin")
        stil = oge.get("stil", "")
        sonra = oge.get("sonra_ms", 0)
        ok = True
        if not isinstance(ad, str) or not AD_DESENI.fullmatch(ad):
            hatalar.append(f"{yer}: konusmaci küçük harfle başlayan bir ad olmalı "
                           f"(a-z, rakam, _; 2-24 karakter, ör. 'ece'): {ad!r}")
            ok = False
        if not isinstance(metin, str) or not metin.strip():
            hatalar.append(f"{yer}: 'metin' dolu bir yazı olmalı")
            ok = False
        if stil is None:
            stil = ""
        if not isinstance(stil, str):
            hatalar.append(f"{yer}: 'stil' bir yazı olmalı")
            ok = False
        if sonra is None:
            sonra = 0
        if (isinstance(sonra, bool) or not isinstance(sonra, (int, float))
                or not math.isfinite(sonra) or not 0 <= sonra <= MAKS_SONRA_MS):
            hatalar.append(f"{yer}: 'sonra_ms' 0 ile {MAKS_SONRA_MS} arasında bir sayı olmalı "
                           f"(milisaniye): {sonra!r}")
            ok = False
        if ok:
            satirlar.append(Satir(ad, metin.strip(), stil.strip(), sonra, yer))
    return satirlar, hatalar, uyarilar


def satirlari_oku(yol: Path, bilinen: set[str]) -> tuple[list[Satir], list[str], list[str]]:
    """(satırlar, hatalar, uyarılar). .json -> sahneler.json, ötesi -> cumleler.txt."""
    if yol.suffix.lower() == ".json":
        return json_satirlari(yol)
    return metin_satirlari(yol, bilinen)


def okunus_oku(yol: Path) -> dict[str, str]:
    try:
        sozluk = json.loads(oku(yol, "okunus.json"))
    except json.JSONDecodeError as e:
        hata(f"okunus.json geçerli JSON değil: {yol} ({e})")
    if not isinstance(sozluk, dict):
        hata(f"okunus.json bir JSON nesnesi ({{...}}) olmalı: {yol}")
    return sozluk


def okunus_uygula(metin: str, sozluk: dict[str, str]) -> str:
    # Tek geçiş, uzun yazım önce: sözlük sırası sonucu etkilemez, bir okunuş tekrar değişmez.
    # Karşılık lambda ile verilir; yoksa "\" içeren okunuş re.sub'da şablon sayılıp çöker.
    anahtarlar = sorted((k for k in sozluk if k), key=len, reverse=True)
    if not anahtarlar:
        return metin
    desen = "|".join(re.escape(k) for k in anahtarlar)
    return re.sub(rf"(?<!\w)(?:{desen})(?!\w)", lambda m: str(sozluk[m.group(0)]), metin)


def kota_hatasi(e: Exception, mesaj: str) -> bool:
    # "voice_4290" gibi bir kimlikteki 429'u kota sanma: 429 yalnız tam sayı olarak sayılır.
    return (getattr(e, "code", None) == 429 or "RESOURCE_EXHAUSTED" in mesaj
            or re.search(r"\b429\b", mesaj) is not None)


def wav_baytlari(veri: bytes) -> bytes:
    """Yanıt WAV ise olduğu gibi; ham PCM gelirse (24 kHz, 16 bit, tek kanal) WAV başlığı ekler."""
    if veri[:4] == b"RIFF":
        try:
            with wave.open(io.BytesIO(veri), "rb") as r:
                bos = r.getnframes() == 0
        except (wave.Error, EOFError):
            bos = False  # PCM dışı WAV'ı bu modül açamaz; denetlenemez, sure_olc.py yakalar
        if bos:
            raise RuntimeError("yanıtta ses verisi yok (WAV'da hiç örnek yok)")
        return veri
    if len(veri) < 2:
        raise RuntimeError("yanıtta ses verisi yok (ham PCM boş)")
    tampon = io.BytesIO()
    with wave.open(tampon, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(veri)
    return tampon.getvalue()


def sessizlik_ekle(wav: bytes, ms: float) -> bytes:
    """WAV'ın sonuna ms milisaniye sessizlik ekler; başlık ve biçim aynı kalır, geçerli WAV döner."""
    if not ms:
        return wav
    try:
        with wave.open(io.BytesIO(wav), "rb") as r:
            kanal, genislik, hiz = r.getnchannels(), r.getsampwidth(), r.getframerate()
            kareler = r.readframes(r.getnframes())
    except (wave.Error, EOFError) as e:
        raise RuntimeError(f"sonra_ms eklenemedi, yanıt okunabilir bir PCM WAV değil: {e}")
    n = int(round(hiz * ms / 1000))
    bos = (b"\x80" if genislik == 1 else b"\x00") * (n * kanal * genislik)  # 8 bit PCM işaretsizdir
    tampon = io.BytesIO()
    with wave.open(tampon, "wb") as w:
        w.setnchannels(kanal)
        w.setsampwidth(genislik)
        w.setframerate(hiz)
        w.writeframes(kareler + bos)
    return tampon.getvalue()


def istek_govdesi(metin: str, ses: str, stil: str | None) -> dict:
    parca: dict = {"type": "text", "text": metin}
    if stil:
        # Belge: üslup/tempo talimatı metne değil speech_metadata.style alanına yazılır.
        parca["annotations"] = [{"type": "speech_metadata", "style": stil}]
    return dict(
        input=[{"type": "user_input", "content": [parca]}],
        response_format={"type": "audio"},
        generation_config={"speech_config": [{"voice": ses}]},
    )


def sadece_coz(deger: str, toplam: int) -> set[int]:
    secili: set[int] = set()
    for parca in deger.split(","):
        parca = parca.strip()
        if not re.fullmatch(r"[0-9]+", parca):
            hata(f"--sadece sıra numaralarını virgülle ister (ör. 3,7): {deger!r}")
        n = int(parca)
        if not 1 <= n <= toplam:
            hata(f"--sadece: {n} diye bir cümle yok (1 ile {toplam} arası)")
        secili.add(n)
    return secili


def main() -> int:
    ap = argparse.ArgumentParser(description="Gemini TTS ile cümle cümle seslendirme")
    ap.add_argument("cumleler", type=Path, help="cumleler.txt ya da sahneler.json")
    ap.add_argument("cikti_klasoru", type=Path)
    ap.add_argument("--ses", action="append", default=[], metavar="AD=SES",
                    help="konuşmacı=Gemini sesi (birden çok kez verilebilir)")
    ap.add_argument("--model", default="gemini-3.8-flash-lite-tts",
                    help="gemini-3.8-flash-lite-tts (toplu iş) ya da gemini-3.8-flash-tts (en iyi kalite)")
    ap.add_argument("--stil", help="tüm satırlara üslup talimatı, ör. 'sakin, net' (satır stili bunu geçer)")
    ap.add_argument("--okunus", type=Path, help="yazım -> okunuş sözlüğü (json)")
    ap.add_argument("--sadece", metavar="N,N",
                    help="yalnız bu sıra numaralarını (1 tabanlı) yeniden üret, ör. 3,7")
    ap.add_argument("--bekle", type=bekle_sayisi, default=2.0,
                    help="istekler arası saniye (0 ile 3600 arası, varsayılan 2)")
    ap.add_argument("--yeniden", action="store_true", help="var olan dosyaları da yeniden üret")
    ap.add_argument("--kuru", action="store_true")
    a = ap.parse_args()

    sesler: dict[str, str] = {}
    for tanim in a.ses:
        ad, _, ses = tanim.partition("=")
        if not ad.strip() or not ses.strip():
            hata(f"--ses AD=SES biçiminde olmalı: {tanim}")
        sesler[ad.strip()] = ses.strip()
    for ad in sesler:
        if not AD_DESENI.fullmatch(ad):
            print(f"UYARI: --ses '{ad}': konuşmacı adı küçük harfle başlar (2-24 karakter: a-z, "
                  "rakam, _); hiçbir satır bu sese eşleşmez.", file=sys.stderr)

    sozluk = okunus_oku(a.okunus) if a.okunus else {}
    satirlar, hatalar, uyarilar = satirlari_oku(a.cumleler, set(sesler))
    for u in uyarilar:
        print(u, file=sys.stderr)
    if not satirlar and not hatalar:
        hata("Girdi dosyasında cümle yok.")
    eksik = sorted({s.ad for s in satirlar} - set(sesler))
    if eksik:
        hatalar.append("Şu konuşmacılara --ses verilmedi: " + ", ".join(
            f"{ad} (küçük harfle '{tanimli_karsilik(ad, set(sesler))}' için --ses var; "
            "konuşmacı adı küçük harfle yazılır)"
            if tanimli_karsilik(ad, set(sesler)) else ad for ad in eksik))
    if a.cikti_klasoru.exists() and not a.cikti_klasoru.is_dir():
        hatalar.append(f"Çıktı klasörü adında bir dosya var: {a.cikti_klasoru} (başka bir klasör "
                       "adı ver ya da dosyayı kaldır).")
    if hatalar:
        hata("\n".join(hatalar))
    # "is not None": boş değer (--sadece "") sessizce yok sayılmaz, hata verir.
    secili = sadece_coz(a.sadece, len(satirlar)) if a.sadece is not None else None

    # Klasörde bu girdiye ait olmayan ses dosyası kalmışsa birlestir.sh onu da ekler.
    gen = numara_genisligi(len(satirlar))
    beklenen = {dosya_adi(i, s.ad, gen) for i, s in enumerate(satirlar, 1)}
    if a.cikti_klasoru.is_dir():
        yabanci = sorted(p.name for p in a.cikti_klasoru.iterdir()
                         if p.is_file() and not p.name.startswith(".")
                         and p.suffix.lower() in SES_UZANTILARI and p.name not in beklenen)
        if yabanci:
            print(f"UYARI: {a.cikti_klasoru}/ içinde bu girdiye ait olmayan ses dosyası var "
                  f"({', '.join(yabanci[:5])}{' ...' if len(yabanci) > 5 else ''}); "
                  "birlestir.sh klasördeki bütün ses dosyalarını ekler. Gereksizse sil.",
                  file=sys.stderr)

    ek = f", --sadece: {len(secili)} cümle" if secili is not None else ""
    print(f"{len(satirlar)} cümle, model {a.model}{ek}")
    if a.kuru:
        for sira, s in enumerate(satirlar, 1):
            if secili is not None and sira not in secili:
                continue
            print(f"  {sira:0{gen}d} {s.ad} [{sesler[s.ad]}]: {okunus_uygula(s.metin, sozluk)}")
            stil = s.stil or a.stil
            ayrinti = []
            if stil:
                ayrinti.append(f"stil: {stil}")
            if s.sonra_ms:
                ayrinti.append(f"sonra: {s.sonra_ms:g} ms sessizlik")
            if ayrinti:
                print(f"      {' · '.join(ayrinti)}")
        print("Kuru çalışma tamam; istek atılmadı.")
        return 0

    # Hangi cümleler üretilecek? --sadece verilmişse o cümleler var olsa bile yeniden üretilir.
    isler = []
    for sira, s in enumerate(satirlar, 1):
        if secili is not None and sira not in secili:
            continue
        hedef = a.cikti_klasoru / dosya_adi(sira, s.ad, gen)
        if hedef.exists() and not (a.yeniden or secili is not None):
            print(f"  {hedef.name} var, atlandı")
            continue
        isler.append((s, hedef))
    if not isler:
        print("Üretilecek cümle yok (hepsi var). Yeniden üretmek için --yeniden ya da --sadece N.")
        return 0

    try:
        from google import genai
    except ImportError:
        hata('google-genai kurulu değil: pip install "google-genai>=2.25.0,<3"')
    try:
        client = genai.Client()  # GEMINI_API_KEY ortam değişkenini okur
    except Exception as e:  # noqa: BLE001
        hata(f"Gemini istemcisi açılamadı (GEMINI_API_KEY tanımlı mı?): {e}")

    # İlk (ücretli) istekten önce: klasör açılamıyorsa betik istek atmadan durur.
    try:
        a.cikti_klasoru.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        hata(f"Çıktı klasörü oluşturulamadı: {a.cikti_klasoru} ({e})")
    for sayac, (s, hedef) in enumerate(isler, 1):
        # Satır stili genel --stil'i geçer (birleşmez).
        govde = istek_govdesi(okunus_uygula(s.metin, sozluk), sesler[s.ad], s.stil or a.stil)
        t0 = time.time()
        try:
            sonuc = client.interactions.create(model=a.model, **govde)
            veri = getattr(getattr(sonuc, "output_audio", None), "data", None)
            if not veri:
                raise RuntimeError("yanıtta ses verisi yok")
            hedef.write_bytes(sessizlik_ekle(wav_baytlari(base64.b64decode(veri)), s.sonra_ms))
        except Exception as e:  # noqa: BLE001
            mesaj = str(e) or type(e).__name__
            if kota_hatasi(e, mesaj):
                print(f"KOTA DOLDU ({hedef.name}): {mesaj[:300]}\n"
                      "Bekle (dakikalık sınırsa bir dakika; günlük kota gece yarısı Pasifik "
                      "saatinde yenilenir) ve aynı komutu yeniden çalıştır; üretilenler atlanır.",
                      file=sys.stderr)
                return 4
            print(f"DURDU: {hedef.name} üretilemedi: {mesaj[:300]}", file=sys.stderr)
            return 3
        bekleme = f" (+{s.sonra_ms:g} ms sessizlik)" if s.sonra_ms else ""
        print(f"  {hedef.name}  {time.time() - t0:4.1f} sn{bekleme}")
        if sayac < len(isler):
            time.sleep(a.bekle)

    print("Bitti. Sıradaki adım: python3 scripts/sure_olc.py", shlex.quote(str(a.cikti_klasoru)),
          "timing.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
