# Görsel: arka plan ve kapak nereden gelir

**Claude görsel (raster) üretemez.** Anthropic'in belgesi bunu açıkça söylüyor: Claude görüntüyü anlar ama oluşturmaz. Claude'un yaptığı: SVG/HTML ile çizim (çöp adam, grafik, diyagram, yazı). Fotoğraf gibi arka planları ve kapağın zeminini ChatGPT ya da Gemini üretir; Claude bunları alıp animasyona yerleştirir.

## Yollar

| Yol | Nasıl | Not |
|---|---|---|
| **Codex CLI + ChatGPT girişi** | `curl -fsSL https://chatgpt.com/codex/install.sh \| sh`, sonra `codex login` (tarayıcıdan ChatGPT ile giriş). Görsel: `codex exec ... "\$imagegen ile <tarif> görselini üret."` | Yerleşik görsel aracı `gpt-image-2` kullanır. Genel Codex kotasından düşer; Free planda yok. Çıktı `$CODEX_HOME/generated_images/` altına düşer (`-o` ile gelmez), oradan projeye kopyalanır. `gorsel-ajani` alt ajanı bunu yapar: görseli ürettirir, `generated_images/` altında oluşan yeni PNG'yi bulup `gorseller/` altına kopyalar, açıp bakar. |
| **ChatGPT uygulaması (elle)** | Tarifi yaz, görseli indir, `gorseller/` klasörüne koy | CLI kurmak istemeyenler için. Claude tarifleri `gorsel_istekleri.md` dosyasına yazar, sen sırayla yapıştırırsın. |
| **Gemini uygulaması (elle)** | Aynı yöntem: tarifi yapıştır, görseli indir | Google hesabına bağlı kota. |
| **Antigravity uygulaması (elle)** | Uygulamanın içinde görsel iste; yerleşik görsel aracı Nano Banana 2 kullanır | Çıktı konuşmanın artifact'lerine kaydedilir, oradan klasöre taşı. |

**Bireysel hesaplarda Gemini CLI artık bir yol değil:** Ücretsiz hesap (Gemini Code Assist for individuals), Google AI Pro ve Google AI Ultra için Gemini CLI 18 Haziran 2026'da kapandı, yerine Antigravity CLI (`agy`) geldi. Gemini Code Assist Standard/Enterprise lisansı ve ücretli Gemini API anahtarıyla Gemini CLI çalışmaya devam ediyor. Nano Banana uzantısı da abonelik yerine Gemini API anahtarı ister, yani ücretsiz hat değildir.

**`agy`'yi başka bir ajanın içinden çağırma.** [Antigravity SSS](https://antigravity.google/docs/faq)'ye göre `agy`'yi üçüncü taraf kodlama ajanlarının ya da uygulamaların içine sarmak ve hesap döndürmeyi otomatikleştirmek tüketici planlarında desteklenmiyor; [Kullanım Şartları](https://antigravity.google/terms)'nın 6. maddesi de üçüncü taraf yazılım, araç ya da hizmetle erişimi ihlal sayıyor ve hesabın askıya alınması için gerekçe yapıyor. Üçüncü taraf bir ajanla Gemini kullanmak istiyorsan SSS'nin önerdiği yol Gemini Enterprise ya da Google AI Studio API anahtarıdır (anahtar kredi harcar; bu rehberin ücretsiz hattı değildir). Abonelik hattında Gemini görselini Antigravity ya da Gemini uygulamasından elle al, Claude Code'dan `agy` çağırma.

## Tarif şablonu (arka plan)

Aynı videodaki tüm arka planlarda **aynı stil bloğunu** kullan; yoksa arka planlar arasında stil kayar.

```
STİL (her tarifte aynen): düz vektör illüstrasyon, yumuşak pastel renkler, kalın olmayan ince kontur, temiz gökyüzü gradyanı.
MEKÂN: <mekân, saat, hava>. Yatay 16:9. Ortada ve alt üçte birde karakter için boş alan bırak.
YOK: yazı, logo, filigran, insan, el.
```

Karakteri arka plana **görselle üretme**; Claude SVG ile çizsin. Böylece aynı çöp adam her sahnede aynı kalır ve hareket ettirilebilir.

## Aynı sahnede arka planı değiştirme

Bir sahne (mekân) = bir arka plan. Aynı mekândaki tüm cümleler (segmentler) aynı arka planı paylaşır; görsel sayısı cümle sayısına değil mekân sayısına eşittir. Konuşan karakter ve ekran yazısı arka planın **üstünde** hareket eder; arka plan sahne içinde yeniden üretilmez. Yeni mekân = yeni sahne = yeni görsel.

## Kapak (küçük resim)

- Zemini **yazısız** iste (`yazı yok`) ve `gorseller/kapak_zemin.png` olarak kaydet. Başlığı (en çok 4 kelime) HTML/CSS ile bindir. Böylece yazı net, doğru yazılmış ve kanalın yazı tipiyle olur.
- `kapak/`, ana videodan ayrı, 2 sn'lik tek kompozisyonlu bir HyperFrames projesidir: `index.html`'i 1280x720 yaz (zemin `<img>`, başlık `<div>`). Ekran görüntüsünü proje kökünden, sürümü sabitleyerek al:

  ```bash
  HYPERFRAMES_SKIP_SKILLS=1 npx hyperframes@0.8.184 init kapak --non-interactive --skip-skills
  mkdir -p kapak/assets && cp gorseller/kapak_zemin.png kapak/assets/
  npx hyperframes@0.8.184 snapshot kapak --at 1.0 --no-end --describe false -o kapak/out
  cp kapak/out/frame-00-at-1s.png kapak/kapak.png   # 1280x720 PNG
  ```

  `--describe false`: ortamda `GEMINI_API_KEY` varsa `snapshot` görüntüyü Gemini'ye göndermesin.
- Yazıyı görsel modele yazdırmak istersen OpenAI'ın kendi önerisi: üretim için kritik yazılarda her kelimeyi gözden geçir, gerekirse tasarım aracında bitir. Metni tam ve "verbatim" ver, zor kelimeleri harf harf yaz.
- Örnek kanallardaki gibi bir kapak için: 2–3 başarılı kapağın ortak yönünü yaz (yüz yakın planı, 3 kelimeye kadar büyük yazı, tek vurgu rengi), tarifte bunu tarif et, kendi kanalının renklerini ver. Birebir kopya değil, aynı kalıp.

## Her görseli aç ve bak

Üretilen her görseli kullanmadan önce gözle kontrol et: istenmeyen yazı, filigran, bozuk el/yüz, yanlış oran, stil uyumsuzluğu. Kötü görseli at; yerine uydurma görsel koyma, sahneyi yeniden iste.

## Sıra ve kota

- Çağrıları **sırayla** yap; aynı hesaba paralel istek açma.
- "usage limit … try again at …" gibi bir mesaj gelirse dur, mesajdaki saati bekle. Aynı görseli üçüncü kez üretme.
- Kotayı abonelik planın belirler (Plus ve Pro farklıdır). Güncel sınırlar için ChatGPT'nin kullanım ekranına ve Antigravity'nin plan sayfasına bak; rakamlar sık değişiyor.
