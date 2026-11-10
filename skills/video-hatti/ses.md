# Ses: metinden konuşmaya

Hatta ses şu üç yoldan biriyle gelir. Hangisini seçersen seç sonraki adımlar aynı: cümle cümle üret, `scripts/sure_olc.py` ile ölç, `scripts/birlestir.sh` ile birleştir.

| Yol | Kimin sesi | Maliyet | Ne zaman |
|---|---|---|---|
| **1. Yerel VoxCPM** | Kendi sesin (klon) ya da tarifle oluşturulmuş ses | Ek ücret yok, bilgisayarın çalışır | Kendi sesinle çok video; kota derdi olmasın |
| **2. Gemini TTS** (AI Studio / API) | Hazır sesler; kendi sesin için AI Studio'da çoğaltma (ücretli katman) | Hazır seslerde ücretsiz katman var, sınırlı | Kurulum istemeyen, hızlı başlayan |
| **3. Kendi kaydın** | Sen | Yok | En doğal sonuç; metne çevirmek için Whisper (bkz. `atolye.md`) |

**Claude'un rolü:** Claude ses dosyası üretmez; ses modeli değildir. Claude yönetir: metni cümlelere böler, okunuşu düzeltir, doğru komutu çalıştırır, süreleri ölçer, diyaloğu sıralar, parçaları birleştirir. Sesi VoxCPM ya da Gemini TTS üretir. ChatGPT aboneliği de bu hatta ses kaynağı değildir: OpenAI'ın konuşma API'si ayrı faturalanan bir üründür ve ChatGPT planının kullanım hakkına dahil değildir (bazı planlarla ayrı bir API kredisi gelebilir; güncel koşul OpenAI'ın yardım sayfasında). OpenAI'ın mevcut TTS modelleri (`tts-1`, `tts-1-hd`, `gpt-4o-mini-tts`) 6 Ocak 2027'de kapanıyor; bu yüzden rehberde kullanılmıyor.

## Yol 1: Yerel VoxCPM, Claude yönetir

Kurulum `voxcpm.md` içinde (sürüm 2.0.3'e sabit). Kurulduktan sonra Claude Code'a şunu söylemen yeter:

> Yerelde kurulu VoxCPM ile `cumleler.txt` dosyasını seslendir. Referans sesim `referans/ben.wav`, kaydın yazısı `referans/ben.txt`. Önce `scripts/voxcpm_diyalog.py` ile kuru çalıştır, sonra üret, `sure_olc.py` ile ölç, kısa kalan cümleleri bana söyle.

Claude'un yaptığı işler:

1. **Referansı hazırlar.** Telefon kaydını wav'a çevirir: `ffmpeg -i kayit.m4a -ac 1 referans/ben.wav`. VoxCPM2 referansı kendisi 16 kHz tek kanala indirir; 48 kHz'e çevirmek gerekmez. Kayıt en az 5 saniye, temiz, gürültüsüz ve tek konuşmacılı olsun. Tam klon için kaydın birebir yazısını `prompt_text` olarak alır (Ultimate Cloning'de otomatik yazı Türkçeyi tanımadığı için yazıyı sen doğrularsın).
2. **Doğru metni verir.** Metni tam cümlelere böler, rakam ve kısaltmaları yazıyla açar, yabancı terimleri `okunus.json` ile okunuşa çevirir (`"Claude": "Klod"`). Altyazıda özgün yazım kalır, yalnız sese giden metin değişir.
3. **Diyaloğu kurar.** Her konuşmacıya bir ses tanımlar (`sesler.json`): biri senin klonun, diğeri tarifle ses. Konuşmacı adı küçük harfle başlar; satırlar `ece: Nereye gidiyoruz?` biçiminde yazılır.
4. **Cümle cümle üretir.** `scripts/voxcpm_diyalog.py` modeli bir kez yükler ve her satır için `ses/003_ece.wav` yazar. Üretilmiş dosya atlanır, yarıda kalan iş kaldığı yerden devam eder. Tek cümleyi yenilemek için `--sadece 3` verilir.
5. **Ölçer ve birleştirir.** `sure_olc.py` → `timing.json`, animasyon sonra `birlestir.sh` ile sese bağlanır.

`cumleler.txt` örneği:

```
anlatici: Sabah vapuru iskeleden ayrılırken martılar peşinden gelir.
ece: Dede, bu vapur nereye gidiyor?
anlatici: Karşı kıyıya, ama asıl yolculuk şimdi başlıyor.
```

`sesler.json` örneği (tarifi İngilizce yaz; okunan metin Türkçe kalır):

```json
{
  "anlatici": {"reference": "referans/ben.wav", "prompt_wav": "referans/ben.wav", "prompt_text": "Kaydın birebir yazısı."},
  "ece": {"design": "A young, cheerful woman, clear voice"}
}
```

**Tarifle ses her çağrıda yeniden örneklenir.** Aynı İngilizce tarifle iki çekim iki ayrı kişi gibi çıkabilir: bizim ölçümümüzde perde 149 Hz ile 213 Hz oldu. VoxCPM belgesi de Voice Design sonuçlarının koşudan koşuya değiştiğini, istenen sesi bulmak için 1-3 çekim gerekebileceğini söylüyor. Diyalogda `ece` her cümlede başka biri gibi duyulmasın diye sesi bir kez kilitle:

1. Ece'nin ilk cümlesini tarifle üret (`--sadece 2`, 2 o satırın sıra numarası). Dinle; beğenmediysen aynı komutu tekrar çalıştır. Beğendiğin dosyayı `referans/ece.wav` olarak kaydet.
2. `sesler.json`'da `ece`nin `design` alanını sil, yerine `"reference": "referans/ece.wav"` yaz. İstersen aynı dosyayı `prompt_wav`, o cümlenin sese giden metnini `prompt_text` olarak da ekle (tam klon). Stilli satırlar yine yalnız `reference` ile üretilir.
3. Kalan satırları bu klonla üret (`--sadece` vermeden; var olan 2. dosya atlanır). Ece'nin sesi artık sabit.

Aynı kişi başka videoda da dönecekse `referans/ece.wav` dosyasını sakla.

Komutlar:

```bash
# önce kuru çalışma: satırları ve ses tanımlarını doğrular, model yüklemez
python3 scripts/voxcpm_diyalog.py cumleler.txt ses/ --sesler sesler.json --okunus okunus.json --kuru

# üretim
python3 scripts/voxcpm_diyalog.py cumleler.txt ses/ --sesler sesler.json --okunus okunus.json

# beğenmediğin cümleyi yeniden üret (1 tabanlı sıra numarası)
python3 scripts/voxcpm_diyalog.py cumleler.txt ses/ --sesler sesler.json --okunus okunus.json --sadece 3
```

VoxCPM'de klonu yalnız **kendi sesin** ya da **açık izin aldığın** bir ses için kullan; taklit, dolandırıcılık ve dezenformasyon yasak. Gemini'nin Voice Replication yolunda kural daha dar: yalnız sesin sahibinin kendi sesiyle kaydettiği rıza kaydı kabul edilir (aşağıda Yol 2).

## Yol 2: Gemini TTS (AI Studio ve API)

- Önce tarayıcıda dene: <https://aistudio.google.com/generate-speech>. Ses seç, metni yapıştır, dinle.
- Model seçimi (aynı API şeması; betikte `--model` bayrağıyla değişir, **varsayılan `gemini-3.8-flash-lite-tts`**):
  - `gemini-3.8-flash-tts`: en iyi kalite, uzun anlatımda ses ve oda tonu kararlılığı, zor telaffuz. Kullanmak için `--model gemini-3.8-flash-tts` ver.
  - `gemini-3.8-flash-lite-tts`: hızlı ve ucuz, toplu üretim; bayrak yazmazsan bu çalışır.
  - Türkçe iki modelde de destekli diller listesinde.
- Çıktı 24 kHz tek kanal WAV. Bir istekte en çok 2 konuşmacı olur; betik her cümleyi ayrı istekle üretir, böylece tek cümleyi ötekilere dokunmadan yenileyebilirsin (`--sadece 7`).
- **Üslup** metne değil `speech_metadata.style` alanına yazılır ("sakin, net, biraz yavaş"). Betikte `--stil` bütün satırlara uygulanır; `sahneler.json`'daki satır `stil`i `--stil`'i geçer.
- **Satır içi etiketler** metne açı parantezle yazılır: `<short pause>`, `<long pause>`, `<sigh>`, `<laugh>`, `<cough>`, `<gasp>`, `<breath>`. Örnek: `Wait... <short pause> did you hear that? <sigh>`. VoxCPM'in kare parantezli etiketleri (`[laughing]`) Gemini'nin biçimi değildir; ayrımın ayrıntısı aşağıda "Duygu, hız, duraklama" bölümünde.
- **Kendi sesin:** AI Studio'daki Voice Replication ile kısa bir örnekten sesini çoğaltırsın. Bu özellik **ücretli (Tier 1 ve üzeri) bir Gemini API projesi** ister; ücretsiz katmanda yalnız hazır sesler kullanılır. İki ayrı kayıt gerekir: (a) aynı yetişkin konuşmacının 10-30 sn temiz, gerçek konuşması; (b) aynı kişinin rıza cümlesini okuduğu kayıt (Türkçe dahil 30 yerel ayar destekli). Yapay ses ya da SynthID/C2PA damgalı ses doğrulamada reddedilir. Rıza kaydını yalnız sesin sahibi kendi sesiyle yapar: başkasının sesi için bir izin yazısı ya da onay bu yolda yetmez. Çıkan `voice_...` kimliğini `--ses anlatici=voice_XXXX` olarak verirsin.

Kurulum ve çalıştırma (Homebrew Python'da ortamsız `pip install` reddedilir; ayrı, küçük bir ortam kur):

```bash
python3 -m venv .venv-gemini && source .venv-gemini/bin/activate
pip install "google-genai>=2.25.0,<3"
export GEMINI_API_KEY=...        # https://aistudio.google.com/apikey

# önce istek atmadan kontrol
python3 scripts/gemini_tts.py cumleler.txt ses/ --ses anlatici=Kore --ses ece=Puck --kuru

# üretim (varsayılan model: gemini-3.8-flash-lite-tts)
python3 scripts/gemini_tts.py cumleler.txt ses/ --ses anlatici=Kore --ses ece=Puck --stil "sakin, net"

# en iyi kalite için flash modeli
python3 scripts/gemini_tts.py cumleler.txt ses/ --ses anlatici=Kore --ses ece=Puck --stil "sakin, net" --model gemini-3.8-flash-tts
```

Bilmen gerekenler:

- SDK sürümü 2.x ile sınırlı (`<3`): betik 2.x belgesindeki `client.interactions.create` çağrısına göre yazıldı.
- Ücretsiz katmanda standart istekler **ücretsiz** (Flash ve Flash-Lite için); ücretli katmanda fiyat sesin saniyesine göre. Güncel fiyat sayfası: <https://ai.google.dev/gemini-api/docs/pricing>. 31 Aralık 2026'ya kadar Flash için 10 sn ses yaklaşık 0,00225 dolar, 1 Ocak 2027'den itibaren 0,0045 dolar.
- Günlük/dakikalık istek sınırları projenin kota ekranında görünür (<https://aistudio.google.com/rate-limit>) ve kullanım katmanına göre değişir. Yüzlerce saatlik ses üreteceksen ilk koşuyu kısa tut, kotayı ekrandan oku.
- Ücretsiz katmanda içerik Google'ın ürünlerini geliştirmek için kullanılabilir; gizli metni ücretsiz katmanda seslendirme.
- Google AI aboneliğinin avantajları AI Studio web arayüzünde geçerli; API kullanımı ayrı faturalanır/ayrı kotayla çalışır. Betik API anahtarıyla çalıştığı için API kotasına bağlıdır.
- Gemini'nin ürettiği ses SynthID ile işaretlenir.

## Yol 3: Kendi kaydın

Ses kaydını sen alırsın, Claude metne çevirip kurguyu kurar. Ayrıntı: `atolye.md`.

## Duygu, hız, duraklama

Her cümleye ayrı duygu, hız ve bekleme vermek için `cumleler.txt` yerine `sahneler.json` yaz. Dosyadaki her öğe bir cümledir (segment):

```json
[
  {"konusmaci": "anlatici", "metin": "Her şey sıradan bir sabah başlamıştı.",
   "stil": "Warm, calm storytelling voice", "sonra_ms": 250},
  {"konusmaci": "anlatici", "metin": "Ama birden kapı açıldı!",
   "stil": "Speaking with excitement, a bit faster"}
]
```

- `stil`: İngilizce seslendirme talimatı; metin Türkçe kalır. VoxCPM'e metnin başına parantezle gider (`(stil)metin`), Gemini'de `speech_metadata.style` olur. Stilli satırda konuşmacının `reference` ya da `design` alanı olmalı; tam klon (`prompt_wav`) stili desteklemez. VoxCPM'de stilli satır ses kimliğini kaydırabilir ya da talimat metne sızabilir; stili hafif tut ve her stilli satırı `ses-yonetmeni` skill'indeki Kapı adımıyla denetle.
- `sonra_ms`: cümleden sonra ses dosyasının içine eklenen sessizlik. `sure_olc.py` süreyi bu sessizlikle birlikte ölçer, `timing.json` zaten içerir.
- `konusmaci` yazılmazsa `anlatici` okur.
- `--sadece 3,7`: yalnız bu sıra numaralarını yeniden üretir.

```bash
python3 scripts/voxcpm_diyalog.py sahneler.json ses/ --sesler sesler.json --sadece 7
python3 scripts/gemini_tts.py sahneler.json ses/ --ses anlatici=Kore
```

**Aynı `sahneler.json` iki motorda da çalışır, ama etiketler motora göre yazılır.** `stil` ve `sonra_ms` aynı dosyadan iki motora da gider. Metin içindeki etiketlerin biçimi motora özgüdür ve betik etiketi çevirmez:

| Motor | Etiket biçimi | Örnek |
|---|---|---|
| VoxCPM | kare parantez, listedeki yazımıyla, seyrek | `[laughing]`, `[sigh]`, `[Uhm]` |
| Gemini 3.8 TTS | açı parantez | `<short pause>`, `<long pause>`, `<sigh>`, `<laugh>`, `<cough>`, `<gasp>`, `<breath>` |

Hangi motorla üreteceksen metni o biçimde yaz; etiketin Türkçede işe yarayıp yaramadığını dinleyerek doğrula. Duygu → talimat tablosu, VoxCPM etiket listesi, vurgu yöntemleri ve stilli satır denetimi: `ses-yonetmeni` skill'i.

## Her yolda geçerli kurallar

- **Cümle cümle üret, ortadan bölme.** Tam cümle verince tonlama doğru çıkar; uzun metni tek seferde verirsen sonlarda hız ve ses kayar.
- **Tek cümleyi yenile.** `--sadece 7` yalnız 7. cümleyi yeniden üretir, ötekilere dokunmaz. Var olan dosya normalde atlanır; `--yeniden` bütün klasörü baştan üretir, yalnız hepsini istiyorsan ver.
- **Süre ses ölçümünden gelir (Audio Lock).** Görüntü süresi cümle sayısına bölünmez; `timing.json`'daki ölçülmüş süreden alınır. `birlestir.sh` çıktıdaki toplam görüntü süresini toplam ses süresiyle karşılaştırır; fark 50 ms'yi aşarsa hata verir ve `video.mp4` yazılmaz (var olan dosyaya dokunulmaz). Kapı yalnız toplamı ölçer, tek tek segmentlerin süresini denetlemez; segment süreleri animasyonda `timing.json`'dan kurulduğu için ayrı bir kapı yoktur.
- **Ses dosyası biçimi.** `sure_olc.py` ve `birlestir.sh` wav, flac, mp3, m4a ve aiff okur; ogg/opus desteklenmez. Kendi kaydını `ses/` klasörüne koyarsan bu biçimlerden birinde ver (gerekirse `ffmpeg` ile wav'a çevir) ve dosyaları ada göre doğru sıralanacak şekilde adlandır (`001_anlatici.wav`).
- **Seviye eşit gelir.** `birlestir.sh` cümleler arası ses seviyesini varsayılan olarak eşitler; kapatmak için `SES_DENGELE=0` ver (`0`, `false`, `no`, `off`, `hayir` kapatır; büyük/küçük harf fark etmez).
- **`cumleler.txt` biçimi.** `#` ile başlayan satır yorumdur ve atlanır; cümlen `#` ile başlıyorsa başına konuşmacıyı yaz (`anlatici: #1 numaralı vapur`). 999 cümleden uzun metinde dosya adları dört haneli olur (`0001_anlatici.wav`) ki ada göre sıralama bozulmasın.
- **0,8 sn'den kısa cümle** çoğu zaman yutulmuş demektir; `sure_olc.py` uyarır. O cümleyi `--sadece N` ile yeniden üret.
- **Terimler yazımla düzeltilir.** "Claude" bulut gibi okunuyorsa metinde `Klod` yaz (okunuş sözlüğü); altyazıyı özgün bırak.
- **Dinle.** Şüpheli dosyaları ve rastgele iki dosyayı kulakla kontrol et; ölçüm tonu ve telaffuzu yakalamaz.
- **Yüklerken:** YouTube Studio'daki **AI use** sorusunu (Attributes bölümü; Türkçe arayüzde "Yapay zeka kullanımı") doğru yanıtla. Yalnız gerçekçi görünen yapay zekâ içeriği bildirilir: gerçek birine söylemediği şeyi söylettiren ses ya da görüntü, gerçek bir olay ya da yerin değiştirilmiş görüntüsü, yaşanmamış gerçekçi bir sahne, ana odağı yapay zekâ müziği olan video. Çöp adam animasyonu gibi gerçekçi olmayan içerik ile kendi sesinin klonuyla yapılan seslendirme ya da dublaj bildirim gerektirmez. Başkasının sesini klonladıysan (izinle bile) "Evet" de. Kural zamanla değişir; yüklemeden önce [YouTube yardımını](https://support.google.com/youtube/answer/14328491) oku.
