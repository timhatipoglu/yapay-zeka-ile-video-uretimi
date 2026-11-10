---
name: ses-yonetmeni
description: Bir metni cümlelere (segment) bölüp her cümleye duygu, hız, vurgu ve duraklama atayarak aynı ses kimliğiyle duygulu seslendirir (yerel VoxCPM2 stil talimatı ya da Gemini TTS üslup alanı). Kullanıcı "heyecanlı/üzgün/öfkeli/fısıltıyla seslendir", "anlatıcı tekdüze olmasın", "stil kontrolü", "duygu haritası", "sahneler.json" ya da "gülme, iç çekme efekti" dediğinde kullan.
---

# Ses yönetmeni

Claude bu işi doğrudan yapar: metni okur, hangi cümlenin hangi duyguyla okunacağına karar verir, her cümleye bir seslendirme talimatı yazar, betiği çalıştırır, sonucu ölçer ve dinleme listesi verir. Kullanıcı yalnız referans sesi (ya da hazır ses seçimini) ve son dinlemeyi yapar.

Ses dosyasını VoxCPM2 ya da Gemini TTS üretir; Claude **yönetir**. Kurulum ve ses yolları: `video-hatti` skill'inin `ses.md` ve `voxcpm.md` dosyaları. Betikler proje kökündeki `scripts/` klasöründe durur; komutlar proje kökünden çalışır.

Terim: dosya adı `sahneler.json` olsa da bir öğe bir **cümledir (segment)**. "Sahne" mekân (arka plan birimi) demektir.

## Akış

Bu akış hattın Ses (2) ve Ölçüm (3) istasyonlarını yürütür; animasyon (5) üretilen sürelere göre kurulur.

1. **Metni cümlelere böl.** Tam cümle, ortadan bölme. Her cümlenin tek bir ana duygusu olsun.
2. **Duygu haritası çıkar.** Hikâyenin gerilim eğrisine bak: sakin giriş, yükseliş, doruk, düşüş. Duyguyu ani ve gerekçesiz değiştirme; geçişi bir önceki cümlenin stiliyle komşu tut.
3. **`sahneler.json` yaz** (aşağıdaki biçim). Stil talimatı **İngilizce**, metin Türkçe kalır; satır içi etiketler motora göre yazılır (Kurallar).
4. **Kuru çalıştır.** `python3 scripts/voxcpm_diyalog.py sahneler.json ses/ --sesler sesler.json --okunus okunus.json --kuru`. Tanımsız konuşmacı ya da stilli satırda `reference`/`design` eksikse betik hata verir; düzelt.
5. **Üret.** Aynı komutu `--kuru` olmadan çalıştır. Gemini için: `python3 scripts/gemini_tts.py sahneler.json ses/ --ses anlatici=Kore` (kurulum ve `--model`: `ses.md` Yol 2).
6. **Kapı: stilli satırlar.** Stil talimatı hafif tutulur ve stilli her satır ayrıca denetlenir; ölçülmüş nedeni Kurallar'daki "Stilli satırda ses kimliği kayabilir" maddesinde. Her stilli satır için:
   - **Dinle.** Ses anlatıcıyla aynı kişi mi, perde ya da tını belirgin kaydı mı?
   - **Transkriptle doğrula.** Satırı Whisper gibi bir transkriptle metne çevir (HyperFrames: `npx hyperframes@0.8.184 transcribe ses/003_anlatici.wav --language tr`; ayrıntı `animasyon.md`). Çıktı satırın metniyle uyuşmalı; talimattan gelen İngilizce sözcük (`slow and mysterious` gibi) ya da düşen kelime varsa talimat metne sızmıştır.
   - **Kayma ya da sızıntı varsa** stili yumuşat (`Speaking sadly` yerine `slightly sad`) ve yalnız o satırı yeniden ürettir (`--sadece 3`); düzelmezse o satırı stilsiz üret.
7. **Ölç.** `python3 scripts/sure_olc.py ses/ timing.json`.
8. **Dinleme listesi ver.** Her duygudan en az bir cümle ve şüpheli süreler. Beğenilmeyen satırın stilini değiştirip yalnız onu yeniden ürettir (`--sadece 7`), sonra yeniden ölç.
9. **Birleştir.** `./scripts/birlestir.sh ses animasyon/render.mp4 30 video.mp4`.

## `sahneler.json`

Her öğe bir cümledir. Stilsiz, tek tonlu iş için `cumleler.txt` (satır: `ad: cümle`) yeter.

```json
[
  {"konusmaci": "anlatici", "metin": "Her şey sıradan bir sabah başlamıştı.",
   "stil": "Warm, calm storytelling voice with gentle pacing", "sonra_ms": 250},
  {"konusmaci": "anlatici", "metin": "Ama birden kapı açıldı! İnanamıyorum!",
   "stil": "Speaking with excitement, surprised, a bit faster", "sonra_ms": 150},
  {"metin": "Fakat artık çok geçti.", "stil": "Speaking sadly with a trembling voice, slow", "sonra_ms": 600}
]
```

| Alan | Anlamı |
|---|---|
| `konusmaci` | `sesler.json`'daki ad, küçük harfle (`ece`, `Ece` değil); yoksa `anlatici` |
| `metin` | Okunacak Türkçe cümle; satır içi etiketler burada durur (biçim motora göre: VoxCPM `[laughing]`, Gemini `<laugh>`) |
| `stil` | İngilizce seslendirme talimatı (isteğe bağlı) |
| `sonra_ms` | Cümleden sonra eklenecek sessizlik; ses dosyasının içine yazılır, bu yüzden `timing.json` süreyi zaten içerir |

Sayısal yoğunluk ya da hız alanı yoktur. Bunları **stil cümlesine çevirirsin**: "slightly", "very", "almost crying", "speaking faster", "slow".

## Duygu → talimat örnekleri

Bunlar doğal dil talimatlarıdır; modelin sabit duygu kodları değildir. Türkçe metinde etkisini dinleyerek test et, işe yaramazsa kelimeyi değiştir.

| Duygu | Talimat |
|---|---|
| Heyecanlı | `Speaking with excitement and enthusiasm` |
| Üzgün | `Speaking sadly with a trembling voice` |
| Öfkeli | `Speaking angrily with a raised voice` |
| Şaşkın | `Speaking with genuine surprise and disbelief` |
| Fısıltı | `Whispering softly and mysteriously` |
| Duygusal | `Speaking emotionally with a soft, breaking voice` |
| Güçlü vurgu | `Speaking emphatically, stressing important words` |
| Masal anlatıcısı | `Warm, expressive storytelling with dramatic pauses` |
| Hızlı | `Speaking very fast, bright and full` |

VoxCPM2 talimatı metnin başına parantez olarak alır: `(Speaking sadly with a trembling voice)O gün gitti...` Tarifle seste tarif ve stil birlikte girer: `(tarif, stil)metin`. Betik parantezi kendisi kurar.

## Kurallar

- **Stil tam klonda çalışmaz.** Referans kaydın yazısını da veren "tam klon" (`prompt_wav` + `prompt_text`) stil talimatını kullanamaz: VoxCPM'in komut satırı `--control` ile `prompt_text`'i birlikte reddeder, bizim denememizde talimat da sesli okundu. `voxcpm_diyalog.py` bu yüzden **stilli satırı yalnız `reference` ile üretir** (tam klon o satır için bırakılır); stilsiz satırlar tam klonla gider. Stilli satırda konuşmacının `reference` ya da `design` alanı yoksa betik açık hata verir.
- **Stilli satırda ses kimliği kayabilir ve talimat metne sızabilir (ölçüldü).** Kendi denememizde (tek cümle, tek talimat) `(whispering, slow and mysterious)` talimatı prompt ile birlikte verilince sesli okundu; yalnız referans kipinde okunmadı ama ses uzaklaştı: tını uzaklığı düz klondaki 0,2-0,3 aralığından 0,52'ye çıktı, perde %21 pes kaydı. Bu tek cümlelik bir ölçümdür, genel oran değildir; stilin istenen duyguyu taşıyıp taşımadığını da ölçüm göstermez, karar kulakla verilir. Yöntem: referans en az 5 saniye ve temiz olsun, stili yalnız gereken cümlelere ver, her stilli satırı Kapı adımıyla denetle. Bu repo tını/perde ölçüsü vermez; kimlik kontrolü kulakla ve transkriptle yapılır.
- **Tarifle ses her çağrıda yeniden örneklenir.** `design` sesiyle diyalog kuruyorsan sesi bir kez kilitle (`ses.md` Yol 1'deki kilit yöntemi); yoksa aynı konuşmacı her cümlede başka biri gibi duyulur.
- **Etiketler motora özgüdür ve seyrek kullanılır.** VoxCPM kare parantez ister: `[laughing]`, `[sigh]`, `[Uhm]`, `[Shh]`, `[Question-ah]`, `[Surprise-wa]`, `[Dissatisfaction-hnn]` resmî rehberdeki önerilen etiketlerdir; listedeki yazımıyla kullan (küçük harfli olanlar küçük harfle). Gemini 3.8 TTS açı parantez ister: `<short pause>`, `<long pause>`, `<sigh>`, `<laugh>`, `<cough>`, `<gasp>`, `<breath>`; örnek: `Wait... <short pause> did you hear that? <sigh>`. Betik etiketi çevirmez, metni üreteceğin motorun biçiminde yaz. Bir cümleye birden fazla etiket yığma; Türkçede etkisini dinleyerek doğrula.
- **Tek kelimeye vurgu garanti değil.** Önce noktalama (virgül, üç nokta, ünlem) ve `Emphasize the word "yapma" with a sharp, forceful stress` talimatını dene. Olmazsa cümleyi vurgu değişen yerden ikiye bölüp ayrı üret ve birleştir; birleşme yerini dinle.
- **Gemini TTS aynı `sahneler.json` girdisini okur; etiketler motora göre yazılır.** `gemini_tts.py` `.json` girdide satırın `stil` alanını `speech_metadata.style` olarak gönderir; `stil` ve `sonra_ms` aynı dosyadan gider. `--stil` bütün satırlar için genel üsluptur; satır stili onu geçer. `sonra_ms`, 24 kHz tek kanal 16-bit WAV'ın sonuna sessizlik ekler.
- **Süre yine sesten gelir.** Duygu hızı değiştirir; animasyonu duygu atandıktan **sonra** ölçülen süreye göre kur.
- **Ses değiştirme kimlik değil, sunumdur.** Aynı konuşmacıda duygu değişir; ses kimliği değişmez. Farklı kişi için `sesler.json`'a yeni konuşmacı ekle.
- **İzin.** VoxCPM'de klon yalnız kullanıcının kendi sesi ya da açık izin aldığı ses için kullanılır; taklit, dolandırıcılık ve dezenformasyon yasak. Gemini Voice Replication'da yalnız sesin sahibinin kendi sesiyle kaydettiği rıza kaydı kabul edilir. Yapay sesli videoyu yüklerken YouTube'daki AI use (Yapay zeka kullanımı) sorusunun kuralı: `ses.md` "Yüklerken".
