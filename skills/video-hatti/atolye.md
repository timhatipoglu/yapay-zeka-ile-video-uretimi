# Atölye düzeni: ajanlar işi hızlandırmaz, etraflarındaki düzen hızlandırır

Ajan eklemek kolay; zor olan, birbirinin işini bozmadan birlikte çalıştırmak. Aşağıdaki kurallar uzun videoda (10 dakika ve üstü) ajanları yan yana çalıştırırken işimizi kurtarıyor. Hepsini birebir uygulamana gerek yok; hangisi işine yarıyorsa onu al.

## 1. Tek şef

Konuştuğun tek bir Claude Code oturumu olsun. Alt ajanlar şefe bağlıdır; sen onlarla doğrudan uğraşmazsın. Plan, görev dağıtımı ve son karar şefte.

## 2. Önce pano haritası

Hiçbir şey üretmeden önce şef senaryoyu/transkripti baştan sona okur ve her bölüm için tek soru sorar: **Bunu yalnız dinleyen biri anlar mı?** Anlıyorsa ekrana ek bir şey koymayız. Anlamıyorsa o bölümün notuna ekranda ne görüneceğini, hangi logo ve kaynağın çıkacağını yazar. Bölümler bu haritaya göre ajanlara dağılır; bu yüzden ajanlar birbirine karışmaz.

## 3. Devir dosyaları (konuşma değil, dosya)

Ajanlar birbirine konuşarak bilgi aktarmaz; dosya bırakır. Şef yazar, alt ajanlar kendi bölümünü okur. Hattın dosyaları proje kökünde durur ve komutların hepsi kökten çalışır; ajanların birbirine bıraktığı notlar `devir/` altına gider.

```
cumleler.txt           # tam cümleler (seslendirme girdisi)
timing.json            # ölçülmüş ses süreleri (python3 scripts/sure_olc.py ses/ timing.json)
ses/  gorseller/  animasyon/
devir/
  transkript.md        # videonun metni
  kesim_listesi.json   # nerede ne kesilecek
  bolum_01_brief.md    # bölümün hedefi, önceki ve sonraki bölüm
  bolum_01_teslim.md   # ajan işi bitirince yaptığını buraya yazar
```

**Teslim notu yazılmadıysa iş bitmemiştir.** Şef bunu sürekli denetler. Bağlantı koparsa ya da bir ajan çökerse iş dosyalardan kaldığı yerden sürer; hiçbir şey sohbet belleğine bağlı değildir.

## 4. Alt ajana ne verilir

Üç şey: **değişmeyecek kararlar** (karakter, renk, süre), **kalite çıtası** (ölçülebilir) ve **bilerek boş bırakılan yerler** (ajan kendisi çözsün). Ayrıntıyı fazla vermeyiz; fazla talimat çıktıyı düzleştiriyor. Sayıyla verilebilen her şeyi sayıyla veririz: "10 saniyede 10 hareket", "göz rengi #4A3B2A", "kapakta en çok 4 kelime".

## 5. Kapılar: geçmeyen şey üretime çıkmaz

Her istasyonun çıkışında bir kontrol bekler. Bir ajan yapar, başka bir kontrol eder. Bizdeki kapılar:

- Çıktıdaki toplam görüntü ve ses süresi arasında 50 ms'den fazla fark varsa `scripts/birlestir.sh` hata verir (çıkış kodu 1) ve `video.mp4`'ü yazmaz; şef o çıktıyı teslim etmez. Kapı yalnız toplamı ölçer, segmentleri tek tek denetlemez.
- Render'dan önce `npx hyperframes@0.8.184 check --json` hata veriyorsa `render-kosucu` render'a geçmez.

Kapı olmayan, yalnız uyarı veren kontrol: `scripts/sure_olc.py` 0,8 sn'den kısa (yutulmuş olabilir) ya da 20 sn'den uzun cümleyi işaretler, ama çıkış kodu 0 döner ve hiçbir şeyi durdurmaz. Şef bu uyarıyı görünce o cümleyi yeniden ürettirmeden animasyona geçmez (`SKILL.md` adım 3).

**Aynı hatayı ikinci kez yaşarsak onu nota değil koda yazarız.** Not unutulur, kapı unutulmaz. Hata bir kapıya dönüşünce kapıdan geçmeyen video çıkmaz.

## 6. Kod paralel, render sıralı

Ajanlar aynı anda kendi bölümlerinin kodunu yazabilir (yalnız kod yazan ajanlar; ses, görsel ve render ajanları asla eşzamanlı çalıştırılmaz). Render'ları **tek sırayla** alırız; aynı anda birden çok render/ffmpeg açmak makineyi ve ajanları birbirine düşürür (bir Mac'imiz paralel ffmpeg'de iki kez kilitlendi). Görsel ve ses üretiminde de abonelik kotası ortak: koşu sürerken ikinci bir üretim açma.

## 7. Limite göre ayrıntı

Kotanın bol olduğu gün hareket ve ayrıntıyı artırırız; dar olduğu gün sadeleştiririz. Bu bir brief satırıdır: "bugün sade". Pahalı üretimde (video klibi gibi) önce küçük/ucuz bir taslak üretir, onaylayınca tam kaliteye çıkarız.

## 8. Marka ve karakter kilidi

Karakter/marka bilgisi bir skill'de ve dosyada durur; ajan her oturumda sıfırdan başlar, yoksa ortalamaya kayar.

- Karakter kartı: kimlik görseli + oran görseli. Her görsel işine aynı ikisi verilir.
- Yasaklar listesi: "bacak ekleme", "parmak sayısına dikkat", "neon yok", "mor gradyan yok".
- Renk **koduyla** verilir (`#4A3B2A`); tarif değil sayı. Görsel modeller sayıyı iyi izler.
- Her onaylanan görsel/klip etiketlenir (`kutuphane.json`: ne, hangi sahne, hangi sürüm onaylı) ve yeniden kullanılır. Yeni üretmeden önce rafa bakılır.

## 9. Sen kendi sesini kaydediyorsan

1. Sesi kaydet (az işle; ses ne kadar az işlenirse o kadar doğal durur).
2. **Whisper ile yerelde metne çevir** (ses dışarı çıkmaz, ek ücret yok). Ajanlar sesi duyamaz, metne ihtiyaç duyar. HyperFrames ile: `npx hyperframes@0.8.184 transcribe kayit.wav --language tr`. Varsayılan model İngilizce `small.en`'dir; `--language tr` çok dilli modele geçirir (ayrıntı: `animasyon.md`).
3. Bir ajan transkripti temize geçirir: Claude'un "bulut" yazılması gibi hataları düzeltir, terimleri doğru yazar.
4. Ajan boşlukları ve tekrarları keser; kesim listesini `kesim_listesi.json`'a yazar.
5. Konuşma ses seviyesini sabit bir hedefe çek, müziği kısık tut.
6. Pano haritası (2. madde) → bölümlere dağıt.

## 10. Son söz sende

Ajanın raporuna ya da transkripte körü körüne güvenme. Çıkan videoyu kendin izle; beğenmediğin her şeyi tarihiyle bir dosyaya yazdır (`begenilmeyenler.md`). Düzen böyle iyileşir.

## 11. Kısa videolar

Uzun videodan kesit çıkarırken ilk 20–30 saniye (açılış) çoğu zaman iyi bir kesittir. Tutan kesitin geldiği videodan daha fazla kesit çıkar. Dikey videoyu yatay videoyu kırparak değil, kompozisyonu baştan dikey kurarak yap.
