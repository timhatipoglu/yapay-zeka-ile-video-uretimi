# Animasyon ve render: HTML ile video

Claude animasyonu **HTML/JS** olarak yazar, bir araç onu kare kare çekip MP4 yapar. İki yaygın araç:

| | **HyperFrames** (HeyGen) | **Remotion** |
|---|---|---|
| Yazım | HTML + CSS + GSAP | React (TypeScript) |
| Lisans | Apache-2.0 | Özel "Remotion Lisansı": bireyler, en çok 3 çalışanlı kâr amaçlı şirketler ve kâr amacı gütmeyenler ücretsiz; daha büyük kâr amaçlı şirketler ücretli lisans almalı (remotion.pro/license). Lisans 5.0'da küçük ölçüde değişecek (LICENSE.md) |
| Gereken | Node.js 22+ ve FFmpeg | Node.js 16+; macOS'ta 15 (Sequoia) ve üzeri (Remotion belgesindeki gereksinim; kurmadan önce güncelini kontrol et); FFmpeg Remotion'la gelir, ayrıca kurulmaz (gerekirse `npx remotion ffmpeg`) |
| Başlat | `HYPERFRAMES_SKIP_SKILLS=1 npx hyperframes@0.8.184 init animasyon --non-interactive --skip-skills` | `npx create-video@latest` (etkileşimli); betikte `npx create-video@latest --yes --blank remotion` (proje `remotion/` klasörüne kurulur) |
| Kontrol | `(cd animasyon && npx hyperframes@0.8.184 check --json)` (lint, yerleşim, kontrast) | `(cd remotion && npx remotion preview)` |
| Render | `(cd animasyon && npx hyperframes@0.8.184 render --quality looks -o render.mp4)` | `(cd remotion && npx remotion render src/index.ts MyComposition out/video.mp4)` (`MyComposition` yer tutucudur: `remotion/src/Root.tsx`'teki `<Composition id=...>` değerini yaz; boş şablonda bu kimlik `MyComp`'tur, ya da Claude'a kompozisyonu `id="MyComposition"` ile kaydettir) |
| Claude skill'i | `claude plugin marketplace add heygen-com/hyperframes` + `claude plugin install hyperframes@hyperframes` | `npx skills add remotion-dev/skills` |

HTML bilen biri için HyperFrames daha az kurulum ister; React ekosistemini seviyorsan ya da hazır bileşenler gerekiyorsa Remotion. İkisi de Claude Code ile aynı akışta çalışır.

HyperFrames komutlarını `0.8.184` sürümüne sabitledik; `demo/` klasöründeki videoyu bu sürümle ürettik. Yeni bir sürümde bayraklar değişebilir: komutları `npx hyperframes@<sürüm> --help` ile doğrula ve render süresini yeniden ölç.

HyperFrames projesi proje kökündeki `animasyon/`, Remotion projesi `remotion/` klasöründe durur; ikisini aynı klasöre kurma. Kontrolü ve render'ı kökten, zincirleyerek çalıştır:

```bash
# HyperFrames (çıktı: animasyon/render.mp4)
(cd animasyon && npx hyperframes@0.8.184 check --json && npx hyperframes@0.8.184 render --quality looks -o render.mp4)

# Remotion (çıktı: remotion/out/video.mp4)
(cd remotion && npx remotion render src/index.ts MyComposition out/video.mp4)
```

Belgeye göre `create-video --yes` mevcut bir git deposunun içinde hata verir; proje klasörün git deposuysa kurulumu depo dışında yapıp klasörü `remotion/` adıyla projeye taşı.

## Süreyi sesten al

Animasyonun her segmentinin süresi `scripts/sure_olc.py`'nin yazdığı `timing.json`'daki **ölçülmüş ses süresi**dir (segment = `timing.json`'daki bir cümle satırı; sahne = mekân, yani bir arka plan birimi). Süreyi cümle sayısına bölerek eşit dağıtma: 6 cümleyi 30 sn'ye eşit bölünce her biri 5 sn olur ama gerçek sesler 2,4 / 3,2 / 2,2 / 3,7 / 3,4 / 1,9 sn sürebilir; fark 13 saniyeye çıkar, görüntü sesten kopar. Ses uzatılamaz, görüntü ona uyar.

Segment planı, `demo/timing.json`'daki gerçek 3. ve 4. segmentle (iki segment aynı mekânda):

```
segment 3: 8.00 → 13.12 sn  (003_anlatici.wav)  mekân: vapur güvertesi, hareket: martılar kanat çırpıyor
segment 4: 13.12 → 16.32 sn (004_anlatici.wav)  mekân: vapur güvertesi, hareket: çocuk simidi havaya uzatıyor
```

Raster arka plan kullandığında (ör. `guverte.png`) o mekândaki segmentler dosyayı bir kez yükleyip paylaşır; segmentler yalnız karakterin ve yazının hareketini değiştirir.

Demoda raster arka plan yoktur: 6 segment var, hepsi kodla çizilmiş SVG. Repodaki `demo/animasyon/sahne_uret.py`, `timing.json`'daki her segment için `data-start` ve `data-duration` değerleri ölçülmüş süreden gelen ayrı bir blok yazar ve SVG'yi (gök, deniz, vapur, karakterler) her segmentte yeniden çizer; altyazı `cumleler.txt`'den gelir.

## Çöp adam

Karakteri **SVG** olarak çiz (baş daire, gövde/kol/bacak çizgi). Eklemleri `transform: rotate()` ile döndür, GSAP zaman çizelgesiyle hareket ettir. Konuşurken baş hafif sallanır, ağız sesin yüksekliğiyle açılıp kapanabilir. Dirsek ve diz açısını mutlak yönle değil, kısa yoldan interpole et; yoksa kol fırıl fırıl döner.

## Altyazı

- Basit yol: segment başına bir altyazı, süreler `timing.json`'dan.
- Kelime kelime: HyperFrames'in `transcribe` komutu Whisper çalıştırır. Varsayılan model İngilizce `small.en`'dir (`transcribe --help` yalnız `.en` modelleri ve `large-v3`'ü sayar). Türkçede `--language tr` ver: CLI model adından `.en` ekini atıp çok dilli `small` modele geçer (dil verilmezse ses İngilizce sanılır ve metin bozuk çıkar):

  ```bash
  npx hyperframes@0.8.184 transcribe kayit.wav --language tr
  ```

  İlk `transcribe` koşusu Whisper çalışma zamanını ve modeli indirir (bir kez); indirmeyi istemiyorsan `--no-runtime-install` ver. Ses dosyası makineden çıkmaz, indirilen yalnız model ve çalışma zamanıdır.

## Sık hatalar

- `check` komutunu render'dan önce çalıştır: harf aralığı animasyonu ve eksik yazı tipi gibi gerçek hataları yakalar. `composition_file_too_large` ve `nested_structure_needs_subcomposition` uyarıdır, hata değil; render devam eder. Hata (error) varsa düzelt.
- **Yazı tipi yığını:** `font-family: system-ui, -apple-system, sans-serif`. `Helvetica Neue`, `Helvetica`, `Arial` gibi adlar HyperFrames derleyicisinde Inter'e eşlenir ve Google Fonts'tan indirilir (dosyalar `~/.cache/hyperframes/fonts/` altına yazılır). Genel aileler indirme tetiklemez.
- **GSAP CDN'den gelir:** `init` iskeleti GSAP'i `cdn.jsdelivr.net`'ten yükler; `check` ve `render` ağ erişimiyle çalışır. Çevrimdışı yeniden üretmek için GSAP dosyasını `animasyon/` içine kopyala ve `<script src>` yolunu yerele çevir.
- **GSAP + SVG yön tuzağı:** `scale(-1,1)` ile yönü çevrilmiş statik bir sarmalın içindeki grubun x/y hareketi ölçekli uzayda işler; yönü çevrilmiş martı ters yöne uçar, kadrajdan çıkar. Ölçeği en iç gruba taşı. Uzuv pivotu için `gsap.set(el, { svgOrigin: "x y" })` iç içe gruplarda doğru çalışır. Döngülü hareketlerde döngü sayısını `round(süre / döngü süresi)` ile hesapla; segment sonunda donma olmaz.
- **`init` skill kontrolü:** 0.8.184'te `--skip-skills` bayrağı yok sayılır ve `init` GitHub'da yapay zekâ skill'lerini kontrol eder; bunu `HYPERFRAMES_SKIP_SKILLS=1` ortam değişkeni kapatır, bu yüzden komutta ikisini birlikte yazıyoruz.
- **`init` dosya bırakır:** projeye `AGENTS.md` ve `CLAUDE.md` (ajan talimatı) yazar. Kendi talimatlarınla çakışmasın diye sil ya da gözden geçir. 1280x720 hazır ön ayar değil (`--resolution` 1080p, 4k gibi ön ayarları alır); 720p istiyorsan kök `data-width`/`data-height` ile html/body boyutunu elle yaz.
- **Kaliteyi açık ver:** `render --quality looks` yaz, varsayılana güvenme.
- **Telemetri:** HyperFrames telemetrisi varsayılan açıktır; komutlara `HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1` ver. `snapshot` ortamda `GEMINI_API_KEY` varsa görüntüyü Gemini'ye gönderir; `--describe false` ver.
- **Kare ızgarası:** 30 fps'te 23,36 sn'lik ses 701 kare = 23,367 sn olur (fark 7 ms, 50 ms kapısının altında). Kök `data-duration` değerini toplam ses süresi yap.
- Bazı ffmpeg derlemelerinde `drawtext` filtresi yoktur (Homebrew'daki ffmpeg 9'da yok). Yazıyı ffmpeg ile bindirmek yerine HTML'de yaz.
- Render ağırdır: HyperFrames 0.8.184 ile, müzikli ve harf harf yazı/ekolayzır animasyonlu 12 saniyelik 1080p30 pilot bir giriş bizde 3 worker ile yaklaşık 41 saniye sürdü, ana süreç ~850 MB kullandı. İçerik, çözünürlük ve sürüm değişirse süre değişir; kendi videonun render süresini ilk koşuda ölç. **Paralel render açma**; sırayla çalıştır. Dört paralel ffmpeg bir Mac'i iki kez kilitledi.
- Ses ve görüntü farkı: `scripts/birlestir.sh` çıktıdaki toplam görüntü ve ses süresini karşılaştırır. 50 ms'den fazla fark çıkarsa çıkış kodu 1 olur, `video.mp4` yazılmaz (var olan dosyaya dokunulmaz); animasyonu `timing.json`'a göre yeniden kur. Kapı yalnız toplamı ölçer; tek tek segmentlerin süresini ayrıca denetlemez, onlar `timing.json`'dan kurulur.
- Pro özellikler: HyperFrames'in `/reverse-any-video` ve `/style-sampling` skill'leri ücretli HyperFrames Pro ister; skill'ler telemetri sinyali gönderir. Kurmadan önce `SKILL.md` dosyalarını oku.

## Ses ile birleştirme

HyperFrames ya da Remotion sessiz video çıkardıysa proje kökünden birleştir:

```bash
# HyperFrames
./scripts/birlestir.sh ses animasyon/render.mp4 30 video.mp4

# Remotion (çıktı: remotion/out/video.mp4)
./scripts/birlestir.sh ses remotion/out/video.mp4 30 video.mp4
```

Betik ses dosyalarını sırayla birleştirir, görüntüye ekler ve toplam süre farkını ölçer; fark 50 ms'yi aşarsa `video.mp4` yazılmaz. Üretilen cümlelerin seviyesi birbirinden ayrışabilir (ham üretilmiş cümleler arasında çoğu kez birkaç dB, kötü bir koşuda 10 dB'den fazla fark çıkar; demonun ham seslerinde fark 2,6 LU, eşitlemeden sonra 0,1 LU); betik cümleler arası seviyeyi varsayılan olarak eşitler, `SES_DENGELE=0` ile kapanır.
