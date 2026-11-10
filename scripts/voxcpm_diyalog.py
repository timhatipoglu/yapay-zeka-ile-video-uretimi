#!/usr/bin/env python3
"""Yerel VoxCPM ile cümle cümle (ve çok konuşmacılı) seslendirme.

Modeli BİR KEZ yükler, her satır için ayrı bir wav üretir. Claude Code'a "şu metni
seslendir" dediğinde çalıştırdığı betik budur.

Girdi iki biçimde olur.

cumleler.txt, her satır "[ad: ]cümle":
    anlatici: Bugün bir vapura biniyoruz.
    ece: Nereye gidiyoruz?
    Bu satırda konuşmacı yok, varsayılan konuşmacı (anlatici) okur.
  Konuşmacı adı küçük HARFLE başlar (rakamla değil), iki nokta ve boşlukla biter. Büyük harfle
  başlayan ("Not: ...") ya da iki noktadan sonra boşluksuz ("Saat 10:30'da") satırlar konuşmacı
  sayılmaz, tümü metindir. İstisna: büyük harfle yazılmış ad sesler.json'daki bir konuşmacıysa
  ("Ece: ..." ama "ece" tanımlı; "Isik:" ve "ISIK:" için "isik" tanımlıysa da) betik DURUR;
  yoksa "Ece:" sese girerdi. sesler.json'da tanımlı olmayan bir ad görürse de DURUR (sessizce
  başka sesle okumaz). Dosyalar UTF-8'dir; baştaki BOM (Windows Not Defteri) yok sayılır.
  "#" ile başlayan satır YORUMDUR, atlanır (atlananların sayısı ve satır numaraları stderr'e
  yazılır). Cümlen "#" ile başlıyorsa ("#1 haber: ...") başına "anlatici: " koy ya da sahneler.json
  kullan.

sahneler.json, bir liste; her öğe bir cümle (segment):
    [{"konusmaci": "ece", "metin": "Nereye gidiyoruz?",
      "stil": "Speaking with excitement, a bit faster", "sonra_ms": 250}]
    konusmaci  sesler.json'daki ad (yazılmazsa "anlatici")
    metin      okunacak cümle
    stil       isteğe bağlı İngilizce seslendirme talimatı; VoxCPM'e metnin başına parantezle
               gider: "(stil)metin". Sesin design alanı varsa "(tarif, stil)metin".
    sonra_ms   isteğe bağlı; cümleden sonra ses dosyasının İÇİNE eklenen sessizlik (ms).
               sure_olc.py süreyi bununla birlikte ölçer, timing.json zaten içerir.

sesler.json:
    {
      "anlatici": {"reference": "referans/ben.wav",
                   "prompt_wav": "referans/ben.wav",
                   "prompt_text": "Referans kaydın birebir yazısı."},
      "ece":      {"design": "A young, cheerful woman, clear voice"}
    }
    reference  -> klon için referans ses: wav (ya da başka ses dosyası), en az 5 sn temiz kayıt.
                  48 kHz'e çevirmek gerekmez; VoxCPM2 referansı kendisi 16 kHz'e indirir.
    prompt_wav + prompt_text -> "tam klon": kaydın birebir yazısını da verirsen benzerlik artar
    design     -> kayıt olmadan, tarifle ses; tarifi İngilizce yaz (metnin başına "(tarif)"
                  olarak eklenir). Tarifle ses her çağrıda yeniden örneklenir: aynı tarif
                  cümleden cümleye farklı bir kişi gibi çıkabilir. Sesi sabitlemek için ilk
                  cümleyi tarifle üret, beğendiğin wav'ı reference yap (istersen yazısıyla
                  prompt_wav + prompt_text de ver; o zaman design'ı sesler.json'dan kaldır) ve
                  kalan cümleleri o referansla üret.
    design, prompt_wav/prompt_text ile BİRLİKTE verilmez; design + reference olabilir.
    Göreli yollar betiği çalıştırdığın klasöre göre çözülür.

Stil ve tam klon: VoxCPM, stil talimatıyla prompt_text'i birlikte reddeder. Bu yüzden stilli
satır YALNIZ reference (ya da design) ile üretilir; o satır için tam klon bırakılır. Stilsiz
satırlar tam klonla gider. Stilli satırda konuşmacıda reference de design de yoksa (yalnız
prompt_wav varsa) betik açık hatayla DURUR.

Satır içi etiketler (metnin içinde, motora özgü): VoxCPM kare parantez kullanır: [laughing]
[sigh] [Uhm] [Shh] [Question-ah] [Surprise-wa] [Dissatisfaction-hnn]; seyrek kullan. Gemini TTS
açı parantez kullanır (gemini_tts.py). Aynı sahneler.json iki motorda çalışır ama etiketler
motora göre yazılır. Metnin BAŞINDAKİ yuvarlak parantez VoxCPM'de stil talimatıdır; bu yüzden
"(" ile başlayan cümle hata verir, stili "stil" alanına yaz.

okunus.json (isteğe bağlı): {"Claude": "Klod"} gibi, yalnız SESE giden metni değiştirir.
Altyazıda özgün yazım kalır. Tam sözcük eşleşir ("ağ" -> "dağ"ı değiştirmez), büyük/küçük harf
duyarlıdır, uzun yazım önce denenir ("Claude Code" > "Claude") ve bir okunuşun çıktısı başka
kuralla yeniden değiştirilmez.

Kullanım:
    python3 scripts/voxcpm_diyalog.py GIRDI ses/ --sesler sesler.json [--okunus okunus.json]
                                      [--sadece 3,7] [--yeniden] [--kuru]
    python3 scripts/voxcpm_diyalog.py cumleler.txt ses/ --sesler sesler.json --kuru   # model yüklemeden kontrol
    python3 scripts/voxcpm_diyalog.py sahneler.json ses/ --sesler sesler.json --sadece 7

Çıktı: ses/001_anlatici.wav, ses/002_ece.wav ... (ada göre sıralı; sure_olc.py ve
birlestir.sh bu sırayla okur). Numara 999 cümleye kadar 3 hanedir; daha uzun girdide hane sayısı
cümle sayısına göre artar (0001_...), sıralama bozulmaz. Var olan dosya atlanır; hepsini
yeniden üretmek için --yeniden. --sadece 3,7 yalnız 3. ve 7. cümleyi (1 tabanlı sıra numarası)
yeniden üretir, ötekilere dokunmaz. Atlama yalnız dosya adına bakar: cümleyi değiştirdiysen
o dosyayı sil, --yeniden ya da --sadece ver.

Çıkış kodları: 0 tamam · 2 girdi/ses tanımı/kurulum hatası, çıktı klasörü bir dosya ya da
oluşturulamıyor (hiçbir şey üretilmedi) · 3 model yüklenemedi ya da bir cümle üretilemedi
(kalan cümleler üretilmeden DURUR; aynı komutu yeniden çalıştırınca kaldığı yerden sürer).

Gereken: VoxCPM kurulu bir Python ortamı (kurulum: video-hatti skill'inin voxcpm.md dosyası;
bu depoda skills/video-hatti/voxcpm.md), soundfile ve numpy.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shlex
import sys
import time
from pathlib import Path
from typing import NamedTuple, NoReturn

# Ad harfle başlar: "12: Kasım ayında" bir konuşmacı satırı değil, düz metindir.
AD = r"[a-zçğıöşü][a-zçğıöşü0-9_]{1,23}"
KONUSMACI = re.compile(rf"^({AD}):\s+(.+)$")
AD_DESENI = re.compile(AD)
# Büyük harfle başlayan aday ("Ece: ..."): tanımlı bir konuşmacının büyük harfli hâli mi?
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


def json_nesne(yol: Path, ne: str) -> dict:
    try:
        veri = json.loads(oku(yol, ne))
    except json.JSONDecodeError as e:
        hata(f"{ne} geçerli JSON değil: {yol} ({e})")
    if not isinstance(veri, dict):
        hata(f"{ne} bir JSON nesnesi ({{...}}) olmalı: {yol}")
    return veri


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
                f"{yer}: '{b.group(1)}:' büyük harfle başlıyor ama '{kucuk}' tanımlı bir "
                f"konuşmacı; böyle yazılırsa '{b.group(1)}:' anlatıcıya okutulur. Konuşmacı "
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


def okunus_uygula(metin: str, sozluk: dict[str, str]) -> str:
    # Tek geçiş, uzun yazım önce: sözlük sırası sonucu etkilemez, bir okunuş tekrar değişmez.
    # Karşılık lambda ile verilir; yoksa "\" içeren okunuş re.sub'da şablon sayılıp çöker.
    anahtarlar = sorted((k for k in sozluk if k), key=len, reverse=True)
    if not anahtarlar:
        return metin
    desen = "|".join(re.escape(k) for k in anahtarlar)
    return re.sub(rf"(?<!\w)(?:{desen})(?!\w)", lambda m: str(sozluk[m.group(0)]), metin)


def talimat_temizle(s: str) -> str:
    # Parantez talimatı erken kapatır: "(" ve ")" çıkarılır.
    return " ".join(s.replace("(", " ").replace(")", " ").split())


def sesi_kur(tanim: dict, satir: Satir, sozluk: dict[str, str]) -> dict:
    """Bir satır için VoxCPM generate() argümanları (cfg/adım hariç).

    Stilli satır: "(stil)metin" ya da "(tarif, stil)metin"; yalnız reference, tam klon YOK.
    Stilsiz satır: design varsa "(tarif)metin"; prompt_wav/prompt_text varsa tam klon.
    """
    metin = okunus_uygula(satir.metin, sozluk)
    stil = talimat_temizle(satir.stil)
    tarif = talimat_temizle(tanim.get("design") or "")
    talimat = ", ".join(x for x in (tarif, stil) if x)
    if talimat:
        metin = f"({talimat}){metin}"
    kwargs: dict = {"text": metin}
    if tanim.get("reference"):
        kwargs["reference_wav_path"] = tanim["reference"]
    if tanim.get("prompt_wav") and not stil:
        kwargs["prompt_wav_path"] = tanim["prompt_wav"]
        kwargs["prompt_text"] = tanim["prompt_text"]
    return kwargs


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
    ap = argparse.ArgumentParser(description="VoxCPM ile cümle cümle seslendirme")
    ap.add_argument("cumleler", type=Path, help="cumleler.txt ya da sahneler.json")
    ap.add_argument("cikti_klasoru", type=Path)
    ap.add_argument("--sesler", type=Path, required=True, help="konuşmacı -> ses tanımı (json)")
    ap.add_argument("--okunus", type=Path, help="yazım -> okunuş sözlüğü (json)")
    ap.add_argument("--sadece", metavar="N,N",
                    help="yalnız bu sıra numaralarını (1 tabanlı) yeniden üret, ör. 3,7")
    ap.add_argument("--model", default="openbmb/VoxCPM2")
    ap.add_argument("--cfg", type=float, default=2.0)
    ap.add_argument("--adim", type=int, default=10, help="inference_timesteps (düşük = hızlı)")
    ap.add_argument("--yeniden", action="store_true", help="var olan dosyaları da yeniden üret")
    ap.add_argument("--kuru", action="store_true", help="yalnız satırları ve sesleri doğrula")
    a = ap.parse_args()

    # sesler.json önce yüklenir: büyük harfli ad denetimi tanımlı konuşmacıları bilmek ister.
    sesler = json_nesne(a.sesler, "sesler.json")
    sozluk = json_nesne(a.okunus, "okunus.json") if a.okunus else {}
    for ad in sesler:
        if not AD_DESENI.fullmatch(ad):
            print(f"UYARI: sesler.json'daki '{ad}' konuşmacı adı olarak kullanılamaz (küçük harfle "
                  "başlayan, 2-24 karakterli ad gerekir: a-z, rakam, _); hiçbir satır bu sese "
                  "eşleşmez.", file=sys.stderr)
    satirlar, hatalar, uyarilar = satirlari_oku(a.cumleler, set(sesler))
    for u in uyarilar:
        print(u, file=sys.stderr)
    if not satirlar and not hatalar:
        hata("Girdi dosyasında cümle yok.")

    # Üretimden önce hepsini doğrula: eksik konuşmacı ya da referans dosyası varsa hiç başlama.
    for s in satirlar:
        if okunus_uygula(s.metin, sozluk).lstrip().startswith("("):
            hatalar.append(
                f"{s.yer}: cümle '(' ile başlıyor. VoxCPM metnin başındaki parantezi stil "
                "talimatı sayar (tam klonlu konuşmacıda üretim reddedilir). Stil istiyorsan "
                "sahneler.json'da 'stil' alanına yaz; parantez metnin parçasıysa cümleyi "
                "parantezsiz başlat.")
        if s.ad not in sesler:
            karsilik = tanimli_karsilik(s.ad, set(sesler))
            ipucu = (f" ('{karsilik}' tanımlı; konuşmacı adı küçük harfle yazılır)"
                     if karsilik else "")
            hatalar.append(f"{s.yer}: '{s.ad}' sesler.json'da tanımlı değil{ipucu}")
        elif s.stil and isinstance(sesler[s.ad], dict):
            t = sesler[s.ad]
            if not (t.get("reference") or t.get("design")):
                hatalar.append(
                    f"{s.yer}: stilli satır için '{s.ad}' konuşmacısında reference ya da design "
                    "olmalı. Yalnız prompt_wav/prompt_text (tam klon) stil talimatını kabul "
                    "etmez, VoxCPM ikisini birlikte reddeder. sesler.json'a 'reference' ekle "
                    "ya da satırdan 'stil'i kaldır.")
    for ad, tanim in sesler.items():
        if not isinstance(tanim, dict):
            hatalar.append(f"'{ad}': ses tanımı bir JSON nesnesi ({{...}}) olmalı")
            continue
        yanlis_tip = [k for k in ("reference", "prompt_wav", "prompt_text", "design")
                      if k in tanim and not isinstance(tanim[k], str)]
        if yanlis_tip:
            hatalar.append(f"'{ad}': {', '.join(yanlis_tip)} yazı olmalı")
            continue
        if not (tanim.get("reference") or tanim.get("design") or tanim.get("prompt_wav")):
            hatalar.append(f"'{ad}': reference, prompt_wav ya da design vermelisin")
        for anahtar in ("reference", "prompt_wav"):
            if tanim.get(anahtar) and not Path(tanim[anahtar]).is_file():
                hatalar.append(f"'{ad}': {anahtar} bir ses dosyası olmalı (yok ya da klasör): "
                               f"{tanim[anahtar]}")
        if tanim.get("prompt_text") and not tanim.get("prompt_wav"):
            hatalar.append(f"'{ad}': prompt_text verdin ama prompt_wav (kaydın kendisi) yok; "
                           "ikisi birlikte verilir")
        if tanim.get("prompt_wav") and not tanim.get("prompt_text"):
            hatalar.append(f"'{ad}': prompt_wav verdin, prompt_text (kaydın yazısı) eksik")
        if tanim.get("design") and (tanim.get("prompt_wav") or tanim.get("prompt_text")):
            hatalar.append(f"'{ad}': design, prompt_wav/prompt_text ile birlikte verilmez "
                           "(stil kontrolü devam moduyla çalışmaz; design + reference kullan)")
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
    print(f"{len(satirlar)} cümle, {len({s.ad for s in satirlar})} konuşmacı{ek}")
    if a.kuru:
        for sira, s in enumerate(satirlar, 1):
            if secili is not None and sira not in secili:
                continue
            print(f"  {sira:0{gen}d} {s.ad}: {okunus_uygula(s.metin, sozluk)}")
            ayrinti = []
            if s.stil:
                ayrinti.append(f"stil: {s.stil}")
                if sesler[s.ad].get("prompt_wav"):
                    ayrinti.append("tam klon bu satırda bırakıldı, yalnız reference")
            if s.sonra_ms:
                ayrinti.append(f"sonra: {s.sonra_ms:g} ms sessizlik")
            if ayrinti:
                print(f"      {' · '.join(ayrinti)}")
        print("Kuru çalışma tamam; model yüklenmedi, ses üretilmedi.")
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
        from voxcpm import VoxCPM  # geç içe aktar: kuru çalışma modelsiz de çalışsın
        import numpy as np
        import soundfile as sf
    except ImportError as e:
        hata(f"Gerekli paket kurulu değil: {e.name} (VoxCPM kurulumu: video-hatti skill'inin "
             "voxcpm.md dosyası; ses yazmak için: pip install soundfile)")

    # Model yüklenmeden önce: klasör açılamıyorsa dakikalar süren yükleme boşa gitmesin.
    try:
        a.cikti_klasoru.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        hata(f"Çıktı klasörü oluşturulamadı: {a.cikti_klasoru} ({e})")

    t0 = time.time()
    try:
        model = VoxCPM.from_pretrained(a.model, load_denoiser=False)
        sr = int(model.tts_model.sample_rate)
    except Exception as e:  # noqa: BLE001
        hata(f"Model yüklenemedi ({a.model}): {e}", 3)
    print(f"Model {time.time() - t0:.1f} sn'de yüklendi, çıkış {sr} Hz")

    for s, hedef in isler:
        kwargs = sesi_kur(sesler[s.ad], s, sozluk)
        kwargs.update(cfg_value=a.cfg, inference_timesteps=a.adim)
        t1 = time.time()
        yazmaya_basladi = False
        try:
            wav = np.asarray(model.generate(**kwargs))
            if wav.size == 0:
                raise RuntimeError("model boş ses döndürdü (0 örnek); dosya yazılmadı")
            if s.sonra_ms:
                # Bekleme ses dosyasının içine yazılır: sure_olc.py süreyi bununla ölçer.
                n = int(round(sr * s.sonra_ms / 1000))
                wav = np.concatenate([wav, np.zeros((n, *wav.shape[1:]), dtype=wav.dtype)])
            yazmaya_basladi = True
            sf.write(str(hedef), wav, sr)
        except Exception as e:  # noqa: BLE001
            # Uydurma yok: hata verirse dur, kalan cümleleri sessizce atlama.
            # Yazma yarıda kaldıysa yarım dosya silinir, yoksa sonraki koşuda "var" diye atlanır.
            if yazmaya_basladi:
                hedef.unlink(missing_ok=True)
            print(f"DURDU: {hedef.name} üretilemedi: {e}", file=sys.stderr)
            return 3
        sn = len(wav) / sr
        bekleme = f" (+{s.sonra_ms:g} ms sessizlik dahil)" if s.sonra_ms else ""
        print(f"  {hedef.name}  {sn:5.2f} sn ses{bekleme}, {time.time() - t1:5.1f} sn üretim")

    print("Bitti. Sıradaki adım: python3 scripts/sure_olc.py", shlex.quote(str(a.cikti_klasoru)),
          "timing.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
