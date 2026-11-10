# Yerelde ücretsiz TTS: VoxCPM (kendi bilgisayarında)

Videoda anlattığımız yol: https://www.youtube.com/watch?v=Y1uh7mrCT4Y

Kullanımı basit. Videodaki sürümle birebir aynı sonucu almak için **2.0.3** sürümünü kur; bu, yayımlanmış en son sürümdür (PyPI ve GitHub etiketi). `main` dalı 2.0.3'ten ileride ve yayımlanmamış değişiklikler içerir, o yüzden aşağıda `--branch 2.0.3` ile sabitliyoruz. Kurduktan sonra istediğin bir yapay zekâ aracına (Claude Code, Codex vb.) "yerelde çalışan bu TTS'i kullanarak şu metni cümle cümle seslendir" diyebilirsin; ya da komutları aşağıdan kendin çalıştırırsın.

Komutlar videodaki gibi (Kasım 2026, `voxcpm 2.0.3`). `~/girdi` referans kaydın ve yazısı, `~/cikti` çıktılar.

```bash
# 1) kurulum: Python 3.10–3.12 ve Git gerekli
git clone --branch 2.0.3 https://github.com/OpenBMB/VoxCPM
cd VoxCPM
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .

# 2) web arayüzü → tarayıcıda http://localhost:8808
python3 app.py --port 8808
#    (README komutu; ağdaki diğer cihazlara da açar. Yalnız kendi bilgisayarında açmak için:)
python3 -c "import app; app.run_demo(server_name='127.0.0.1')"

# 3) tek satır (ilk çalıştırmada model iner, ~5 GB)
voxcpm clone --text "Bu cümleyi terminalde tek bir satırla ürettim." --reference-audio ~/girdi/referans_ses.wav --output ~/cikti/tek_satir.wav

# telefon kaydını wav'a çevir (örnekleme hızı fark etmez, model 16 kHz'e indirir)
ffmpeg -i ~/girdi/telefon_kaydi.m4a -ac 1 ~/girdi/kaydim.wav

# tam klon (kaydın birebir yazısıyla)
voxcpm clone --text "Kaydımın yazısını da verince klon bana daha çok benziyor." --prompt-audio ~/girdi/referans_ses.wav --prompt-file ~/girdi/referans_metin.txt --reference-audio ~/girdi/referans_ses.wav --output ~/cikti/tam_klon.wav

# stil talimatı (yalnız --reference-audio ile; --prompt-audio/--prompt-file ile birlikte verilmez)
voxcpm clone --text "Bu cümleyi biraz daha neşeli ve hızlı söylüyorum." --control "slightly faster, cheerful tone" --reference-audio ~/girdi/referans_ses.wav --output ~/cikti/stil.wav

# tarifle ses (tarifi İngilizce yaz)
voxcpm design --text "Bu sesi hiçbir kayıt olmadan, yalnızca bir tarifle oluşturdum." --control "A middle-aged woman, calm and clear news anchor" --output ~/cikti/tarif_en.wav
```

Mac'te `torch.compile` kaynaklı bir hata alırsan resmî hızlı başlangıçtaki gibi komuta `--device mps --no-optimize` ekle (bizde gerekmedi).

## Referans kaydı ve stil

- Referans için **en az 5 sn temiz kayıt** al: tek konuşmacı, gürültüsüz, net. VoxCPM2 referansı kendisi 16 kHz tek kanala indirir; 48 kHz'e çevirmek gerekmez.
- **`--control` ile Ultimate Cloning birlikte kullanılamaz.** `--control` verdiysen `--prompt-audio`, `--prompt-text` ve `--prompt-file` veremezsin; CLI ikisini birlikte reddeder. Stil istiyorsan tam klonu bırak, yalnız `--reference-audio` kullan.
- **Tarifle sesler her çalıştırmada değişir.** Aynı İngilizce tarifle iki çekim iki ayrı kişi gibi çıkabilir (bizim ölçümümüzde perde 149 Hz ve 213 Hz). Sabit ses için ilk cümleyi tarifle üret, beğendiğin çıktıyı `--reference-audio` yap (istersen yazısıyla `--prompt-audio` ve `--prompt-file` da ver), kalan cümleleri o referansla üret. Üç adımlı yöntem: `ses.md`.
- **Stilli satırı denetle.** `--control` ile üretilen satırda ses kimliği kayabilir (bizim tek cümlelik ölçümümüzde perde %21 pes kaydı); Python tarafında talimat prompt ile birlikte verildiğinde ise talimat sesli okundu. Her stilli satırı dinle ve transkriptle doğrula: `ses-yonetmeni` skill'indeki Kapı adımı.

Arayüzde **Ultimate Cloning** açınca otomatik yazı Türkçeyi tanımıyor: kutuya kaydının gerçek yazısını yapıştır.

Çok cümle için videoda Python ile modeli bir kez yükleyip cümle cümle üretmeyi gösterdik; her CLI komutu modeli yeniden yüklediği için çok cümlede bu yol çok daha hızlı. Hazır hâli bu repodaki `scripts/voxcpm_diyalog.py`: modeli bir kez yükler, `cumleler.txt` ya da `sahneler.json` okur, her cümle için ayrı wav yazar.

## Claude ile birlikte kullan

VoxCPM kurulduktan sonra Claude Code'a şunu söylemen yeter: "Yerelde kurulu VoxCPM ile bu metni, referans sesimle cümle cümle seslendir; diyalogları ayrı seslerle yap; ölç ve birleştir." Claude referansı hazırlar, metni cümlelere böler, `scripts/voxcpm_diyalog.py` ile üretir, `scripts/sure_olc.py` ile ölçer, `scripts/birlestir.sh` ile birleştirir. Adım adım anlatım: `ses.md`.

## Ne zaman hangi ses yolu?

| | Yerel VoxCPM | Gemini TTS (AI Studio / API) |
|---|---|---|
| Ek ücret | yok (elektrik ve donanım senin) | ücretsiz katmanda ücret yok, ücretli katmanda saniyeye göre |
| Kendi sesinin klonu | evet (referans kayıt) | evet (AI Studio'da Voice Replication; ücretli Tier 1+ proje, 10-30 sn gerçek kayıt + rıza kaydı) |
| Kurulum | Python ortamı, ~5 GB model | Model indirmez; küçük Python ortamı + API anahtarı |
| Hız | Bizim Mac'te (M4 Max, 36 GB, `mps`, voxcpm 2.0.3) 3–6 sn'lik bir cümle çoğunlukla 5–20 sn sürdü (gerçek zamanın yaklaşık 1,5–3 katı). Oturumun ilk isteği ya da meşgul makinede bir dakikayı bulabilir ya da aşabilir (kayıtlarımızda 51–110 sn); donanımına göre değişir | servise ve kotaya bağlı |
| Kota | yok | proje kotası (RPM/RPD) |
| Gizlilik | metin bilgisayarından çıkmaz | ücretsiz katmanda içerik ürün geliştirmede kullanılabilir |

Claude ve ChatGPT abonelikleri bu hatta ses kaynağı değildir; ses VoxCPM ya da Gemini TTS'ten gelir.

VoxCPM'de klonu yalnız **kendi sesin** ya da **açık izin aldığın** bir ses için kullan; paketin belgesi taklit, dolandırıcılık ve dezenformasyonu yasaklıyor. Gemini'nin Voice Replication yolunda kural daha dar: yalnız sesin sahibinin kendi sesiyle kaydettiği rıza kaydı kabul edilir; başkasının sesi için izin yetmez.
