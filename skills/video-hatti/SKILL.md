---
name: video-hatti
description: Konudan bitmiş MP4'e video hattını yönetir; senaryo, cümle cümle ses (yerel VoxCPM ya da Gemini TTS), arka plan/kapak görseli (Codex ya da elle ChatGPT/Gemini), HTML animasyon (HyperFrames/Remotion), render ve ses-görüntü birleştirme. Kullanıcı "video üret", "seslendirme + animasyon", "çöp adam anlatımlı video", "VoxCPM ile seslendir", "HyperFrames ile render" ya da "tek abonelikle video hattı" dediğinde kullan. Duygulu, diyaloglu ya da stil kontrollü seslendirme istenirse ses-yonetmeni skill'ini de aç.
---

# Video hattı

Claude **yönetmen ve kodcudur**: senaryoyu yazar, sesi ve görseli ürettirir, animasyonu HTML olarak kodlar, süreleri ölçer, birleştirir. Claude ses ve raster görsel **üretmez**; onları ses modeli (VoxCPM, Gemini TTS) ve görsel modeli (ChatGPT/Codex, Gemini) üretir.

Betikler repodaki `scripts/` klasöründedir; bu skill'i kullanacağın projeye `scripts/` klasörünü de kopyala. Ayrıntılar yalnız ihtiyaç olunca açılır:

| Konu | Dosya |
|---|---|
| Ses yolları, VoxCPM ile Claude'un yönettiği klon/diyalog, Gemini TTS | `ses.md` |
| Yerel VoxCPM kurulumu (2.0.3), klon ve komutlar | `voxcpm.md` |
| Duygulu, diyaloglu, stil kontrollü seslendirme (duygu haritası, duraklama) | `ses-yonetmeni` skill'i (`../ses-yonetmeni/SKILL.md`) |
| Arka plan ve kapak görseli, hangi araç, tarif şablonu | `gorsel.md` |
| HyperFrames / Remotion, çöp adam, altyazı, render hataları | `animasyon.md` |
| Çok ajanla çalışma düzeni: devir dosyaları, kapılar, marka kilidi | `atolye.md` |

İki skill birlikte kurulur: `cp -R skills/* ~/.claude/skills/`. Kullanıcı duygu, hız, fısıltı, öfke gibi bir seslendirme tarzı ya da iki kişilik diyalog isterse seslendirme adımını `ses-yonetmeni` ile yürüt.

## Proje düzeni

Tüm komutlar proje kökünden çalışır:

```
cumleler.txt            # ya da sahneler.json (stilli satırlar)
sesler.json  okunus.json
ses/  timing.json
gorseller/  animasyon/  kapak/
scripts/  video.mp4
```

`animasyon/` HyperFrames projesidir; onun komutlarını `(cd animasyon && ...)` ile çalıştır.

## Terimler

- **Sahne** = mekân (bir arka plan birimi).
- **Segment** = `timing.json`'daki bir cümle satırı.

Bir sahnede birden çok segment olur.

## Değişmez kurallar

1. **Ses ana saattir (Audio Lock).** Görüntü süresi ölçülmüş ses süresinden gelir, eşit bölünmez. Fark 50 ms'yi aşarsa birleştirme hata verir (çıkış kodu 1).
2. **Doldurulamayan yuva düşer, uydurulmaz.** Görsel ya da ses üretilemediyse rapor et; sahte dosya koyma, başka araca sessizce düşme.
3. **Üretimler sırayla.** Aynı hesaba paralel görsel/ses isteği açma, aynı turda iki alt ajan çağırma; render'lar tek sırayla. Kota mesajı gelince dur.
4. **Üretilen her görseli aç ve bak**; her sesten en az şüphelileri dinle.
5. **Bir sahne (mekân) = bir arka plan.** Aynı mekândaki tüm cümleler (segmentler) aynı arka planı paylaşır; karakter ve yazı arka planın üstünde hareket eder, aynı sahnede arka planı yeniden üretme. Görsel sayısı cümle sayısına değil mekân sayısına eşittir.

## Akış

**Hazırlık (numarasız).** Sınıfla: süre, dil, sesler (tek anlatıcı mı diyalog mu), görsel stil, kanal/marka. Eksikse sor; varsayılan: 16:9, 30 fps, Türkçe.

1. **Senaryo.** Tam cümlelerden oluşan `cumleler.txt` yaz (diyalog için `ece: ...` biçimi). Bölüm başı kanca: ilk cümle videonun değerini söylesin. Terimlerin okunuşunu `okunus.json`'a yaz. Her cümlenin hangi mekânda geçtiğini de çıkar (ör. vapur: cümle 1-3, iskele: cümle 4).
2. **Ses.** `ses-ajani` alt ajanını kullan (voxcpm ya da gemini). Duygulu ya da diyaloglu isteklerde `ses-yonetmeni` skill'iyle `sahneler.json` yaz. Çıktı `ses/001_anlatici.wav ...`. `ses/` doluysa (kota ya da zaman aşımından sonra kaldığı yerden devam, tek cümleyi yenileme, baştan üretme) görev metnine `DEVAM`, `--sadece N` ya da `--yeniden` yaz; yazmazsan ajan eski işten kalmış dosyalara karışmamak için `DURDU:` döner.
3. **Ölçüm.** `python3 scripts/sure_olc.py ses/ timing.json`. Uyarı betiği durdurmaz (çıkış kodu 0); uyarı varsa o cümleyi yeniden ürettir, sonra animasyona geç.
4. **Görsel.** Mekân listesindeki her mekân için `gorsel-ajani` ile bir arka plan ürettir (cümle başına değil); aynı stil bloğunu her tarife koy. Görseller `gorseller/` altına gider. Kapak zeminini yazısız iste. `gorsel-ajani` üç sonuçtan birini döner: `TAMAM`, `SORUNLU` (dosya `gorseller/_sorunlu/` altına taşınmıştır; yeniden üretim kararı sende) ya da `HATA:`.
5. **Animasyon.** `timing.json`'daki her segmentin süresini o segmentin süresi yap; segmentler kendi mekânlarının arka planını paylaşır. Projeyi `HYPERFRAMES_SKIP_SKILLS=1 npx hyperframes@0.8.184 init animasyon --non-interactive --skip-skills` ile aç (0.8.184'te `--skip-skills` yok sayılır, skill kontrolünü ortam değişkeni kapatır), görselleri kopyala (`mkdir -p animasyon/assets && cp gorseller/*.png animasyon/assets/`; HTML'de `assets/arka.png` diye okunur), animasyonu HTML + SVG + GSAP olarak kodla; karakteri SVG çiz. Önce `check`. Remotion seçersen projeyi `remotion/` alt klasörüne kur (`animasyon.md`).
6. **Render.** `render-kosucu` alt ajanını kullan (yalnız HyperFrames projesi `animasyon/` içindir); tek render açık olsun. `KONTROL: N hata` ya da `KONTROL: ÇALIŞMADI` dönerse render'a geçme, önce düzelt. Elle: `(cd animasyon && npx hyperframes@0.8.184 check --json && npx hyperframes@0.8.184 render --quality looks -o render.mp4)`. Remotion'da render'ı kendin al: `(cd remotion && npx remotion render src/index.ts MyComposition out/video.mp4)`.
7. **Birleştir.** `./scripts/birlestir.sh ses animasyon/render.mp4 30 video.mp4` (Remotion: `./scripts/birlestir.sh ses remotion/out/video.mp4 30 video.mp4`). Betik cümle seslerini art arda ekler; cümleler arası ses seviyesi eşitleme varsayılan açıktır (`SES_DENGELE=0` ile kapanır). 50 ms kapısı değişmez: kapı toplam görüntü ve ses süresini karşılaştırır, fark bunu aşarsa `video.mp4` yazılmaz (var olan dosyaya dokunulmaz); animasyonu `timing.json`'a göre yeniden kur. Tek tek segmentlerin süresi ayrıca denetlenmez, onlar `timing.json`'dan kurulur.
8. **Kapak.** Zemin görseli (`gorseller/kapak_zemin.png`, yazısız) + HTML ile bindirilmiş başlık (en çok 4 kelime). `kapak/`, ana videodan ayrı, 2 sn'lik tek kompozisyonlu bir HyperFrames projesidir: `index.html`'i 1280x720 yaz (zemin `<img>`, başlık `<div>`), sonra ekran görüntüsü al:

   ```bash
   HYPERFRAMES_SKIP_SKILLS=1 npx hyperframes@0.8.184 init kapak --non-interactive --skip-skills
   mkdir -p kapak/assets && cp gorseller/kapak_zemin.png kapak/assets/
   npx hyperframes@0.8.184 snapshot kapak --at 1.0 --no-end --describe false -o kapak/out
   cp kapak/out/frame-00-at-1s.png kapak/kapak.png   # 1280x720 PNG
   ```

   `--describe false`: ortamda `GEMINI_API_KEY` varsa `snapshot` görüntüyü Gemini'ye göndermesin.
9. **Kontrol.** Videoyu baştan sona izle; altyazı, ses seviyesi, ekrandaki yazı hataları. Beğenmediğin her şeyi `begenilmeyenler.md`'ye tarihle yaz.
10. **Yayın.** Yüklerken YouTube Studio'daki **AI use** sorusunu (Attributes bölümü; Türkçe arayüzde "Yapay zeka kullanımı") doğru yanıtla. Yalnız gerçekçi görünen yapay zekâ içeriği bildirilir: gerçek birine söylemediği şeyi söylettiren ses ya da görüntü, gerçek bir olay ya da yerin değiştirilmiş görüntüsü, yaşanmamış gerçekçi bir sahne, ana odağı yapay zekâ müziği olan video. Çöp adam animasyonu gibi gerçekçi olmayan içerik ile kendi sesinin klonuyla yapılan seslendirme ya da dublaj bildirim gerektirmez. Başkasının sesini klonladıysan (izinle bile) "Evet" de. Kural zamanla değişir; yüklemeden önce [YouTube yardımını](https://support.google.com/youtube/answer/14328491) oku. Yüklemeyi kullanıcı onayıyla yap.

HyperFrames komutlarını `0.8.184` sürümüne sabitledik; ayrıntı ve sürüm notu `animasyon.md` içinde.

## Alt ajan kullanımı

| Alt ajan | Model | Ne zaman | Döndürdüğü |
|---|---|---|---|
| `ses-ajani` | haiku | cümle listesini seslendirir, ölçer, şüphelileri listeler | Başarıda `SES:` + `ŞÜPHELİ:` (ya da `ŞÜPHELİ: yok`) + `DİNLE:` satırları; girdideki cümle sayısı ile `ses/` dosya sayısı tutmazsa `FARK:`; karar gerekirse `DURDU:` |
| `gorsel-ajani` | sonnet | tek görsel üretir (Codex `$imagegen`), bakar, yolu döner | `TAMAM gorseller/<ad>.png ...`, `SORUNLU gorseller/_sorunlu/<ad>.png ...` ya da `HATA:` |
| `render-kosucu` | haiku | `check` + `render`, yalnız özeti döner | `KONTROL: temiz`, `KONTROL: N hata` ya da `KONTROL: ÇALIŞMADI`; kontrol temizse ayrıca `RENDER: animasyon/render.mp4, ...`, `RENDER: HATA` ya da `RENDER: BEKLİYOR` |

**Çağrı sırası.** Claude Code, ana konuşmadan başlatılan alt ajanları varsayılan olarak arka planda çalıştırır; Agent çağrısı sonucu beklemeden döner. Bu yüzden `ses-ajani`, `gorsel-ajani` ve `render-kosucu` birer birer çağrılır: aynı turda ikinci bir Agent çağrısı açma, bir ajanın sonuç mesajı (`SES:`/`FARK:`/`DURDU:`, `TAMAM`/`SORUNLU`/`HATA:`, `KONTROL:` ve `RENDER:`) gelmeden bir sonrakini başlatma. Birden çok mekânın arka planı gerekiyorsa mekânları ardışık çağır, hepsini aynı anda açma. Sonuç gelene kadar başka üretim, ffmpeg ya da render başlatma.

**Sonuca göre ne yaparsın.** Başarı satırları `SES:`, `TAMAM` ve `RENDER: animasyon/render.mp4, ...`; `DİNLE:` bir sonuç değil, dinleme hatırlatmasıdır (şüpheli dosyaları ve rastgele iki dosyayı dinlemeden birleştirmeye geçme). Geri kalan her sonuç (`FARK:`, `DURDU:`, `SORUNLU`, `HATA:`, `KONTROL: N hata`/`ÇALIŞMADI`, `RENDER: HATA`) karar için sana, yani şefe döner; ajanlar kendi başlarına ikinci deneme yapmaz, çünkü yeniden üretim kota harcar. `RENDER: BEKLİYOR` başka bir render ya da ffmpeg'in açık olduğunu gösterir: o iş bitince `render-kosucu`'yu yeniden çağır. `ses-ajani` kuru çalışma hatasında, kota/429'da ya da sıfırdan farklı çıkış kodunda hata satırını olduğu gibi bildirir.

Ajan dosyalarını `~/.claude/agents/` (tüm projeler) ya da proje içinde `.claude/agents/` altına koy. Şef bu skill'i yürüten ana oturumdur; alt ajanlar günlük ve uzun çıktıyı ana konuşmadan uzak tutar, ana konuşmaya yalnız tek satırlık sonuç döner. Planı, karar gerektiren işi ve animasyon kodunu ana oturum (güçlü model) yazar; mekanik işleri (ölçüm, render, üretim komutları) küçük modele ver. Model seçimi için bkz. [token ekonomisi rehberi](https://github.com/timhatipoglu/claude-code-game-studios-rehber).

## Üçüncü taraf skill'ler

Hazır skill'lerin listesi ve kurulum komutları repo `README.md` içinde. Topluluk skill'lerini kurmadan önce `SKILL.md` dosyalarını oku.
