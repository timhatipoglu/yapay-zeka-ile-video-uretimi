#!/usr/bin/env bash
# Görüntüyü (kare dizisi YA DA sessiz video) cümle cümle ses dosyalarıyla tek MP4'e birleştirir,
# cümleler arası ses seviyesini eşitler ve ses/görüntü süresini denetler.
#
# Kullanım (proje kökünden):
#   ./scripts/birlestir.sh SES_KLASORU GORUNTU FPS CIKIS.mp4
# GORUNTU: kare deseni ("kareler/%05d.png") ya da sessiz bir video dosyası ("animasyon/render.mp4").
# FPS: kare dizisi için kare hızı; video dosyası verdiysen yok sayılır (yine de bir sayı yaz).
#
# Örnekler:
#   ./scripts/birlestir.sh ses "kareler/%05d.png" 30 video.mp4
#   ./scripts/birlestir.sh ses animasyon/render.mp4 30 video.mp4    # HyperFrames çıktısı
#   ./scripts/birlestir.sh ses remotion/out/video.mp4 30 video.mp4  # Remotion çıktısı
#
# Görüntü: .mp4/.m4v olduğu gibi kopyalanır (yeniden kodlanmaz). .mov/.webm/.mkv (ProRes,
# VP8/VP9 ...) MP4'e kopyalanamaz, H.264'e yeniden kodlanır; alfa kanalı (şeffaflık) gider.
#
# Ses: SES_KLASORU'ndaki dosyalar ada göre (bayt sırası, sure_olc.py ile aynı) sıralanır,
# boşluksuz art arda eklenir; gizli dosyalar (._001.wav) sayılmaz. Klasör ve dosya adlarında
# boşluk olabilir. Örnekleme hızı karışık olabilir (Gemini 24 kHz + VoxCPM 48 kHz): her dosya
# önce 48 kHz tek kanala çevrilir, sonra eklenir. Desteklenen biçimler: wav, flac, mp3, m4a,
# aiff. ogg/opus desteklenmez: atlanır ve uyarılır (sure_olc.py da atlar), wav ya da flac'e çevir.
# Kırık bağ (symlink) hatadır; sure_olc.py da aynı dosyada durur.
#
# Seviye eşitleme (varsayılan AÇIK): her cümlenin ses şiddeti (LUFS) ölçülür, cümleler ortanca
# değere getirilir; kazanç en çok ±15 dB, yükseltmede alimiter kırpmayı önler. Süre değişmez.
# Kapatmak için (sesi kendin mastırladıysan): SES_DENGELE=0 ./scripts/birlestir.sh ...
# (0, false, no, off ve hayir kapatır; büyük/küçük harf fark etmez. Tanınmayan değer uyarı
# verir ve eşitleme açık kalır.)
#
# Kapı: görüntü ile ses toplam süresi arasında 50 ms'den fazla fark varsa çıkış kodu 1 olur ve
# CIKIS dosyası YAZILMAZ (var olan dosyaya da dokunulmaz). Kapı yalnız toplam süreyi karşılaştırır.
#
# Gereken: ffmpeg + ffprobe + python3.
# Çıkış kodları: 0 tamam · 1 ses/görüntü farkı 50 ms'den büyük ya da girdi/ffmpeg hatası
# (kırık bağ dahil) · 2 yanlış kullanım.
set -euo pipefail

if [ "$#" -ne 4 ]; then
  # Başlık yorumunu (ilk yorum bloğunu) kullanım olarak yaz
  awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "$0"
  exit 2
fi
SES_KLASORU="$1"; GORUNTU="$2"; FPS="$3"; CIKIS="$4"

hata() { echo "$1" >&2; exit 1; }

[ -d "$SES_KLASORU" ] || hata "Ses klasörü yok: $SES_KLASORU"

# Seviye eşitleme anahtarı: SES_DENGELE yaygın "kapalı" değerlerinden biriyse kapanır.
DENGELE=1
case "$(printf '%s' "${SES_DENGELE:-1}" | tr '[:upper:]' '[:lower:]')" in
  0|false|no|off|hayir|hayır) DENGELE=0 ;;
  1|true|yes|on|evet) ;;
  *) echo "UYARI: SES_DENGELE='$SES_DENGELE' tanınmadı; seviye eşitleme AÇIK kalıyor (kapatmak için 0, false, no, off ya da hayir yaz)." >&2 ;;
esac

CALISMA="$(mktemp -d)"
trap 'rm -rf "$CALISMA"' EXIT
# Ctrl-C / kill: ilk basışta bile dur (ses_oku içindeki ikinci deneme yutmasın).
trap 'exit 130' INT
trap 'exit 143' TERM

# 1) Ses dosyalarını sırala. find -print0 + sort -z: boşluklu ve kesme işaretli adlar güvenli
#    (ls | grep döngüsü boşlukta dosya adını parçalıyordu). LC_ALL=C: sure_olc.py ile aynı sıra.
DOSYALAR=()
while IFS= read -r -d '' f; do
  DOSYALAR+=("$f")
done < <(find -H "$SES_KLASORU" -maxdepth 1 \( -type f -o -type l \) ! -name '.*' \
           \( -iname '*.wav' -o -iname '*.mp3' -o -iname '*.m4a' -o -iname '*.aiff' \
              -o -iname '*.aif' -o -iname '*.flac' \) -print0 | LC_ALL=C sort -z)
# ogg/opus desteklenmez (sure_olc.py ile aynı küme): sessizce yutma, uyar.
while IFS= read -r -d '' f; do
  echo "UYARI: $f: ogg/opus desteklenmiyor, atlandı (wav, flac, mp3, m4a ya da aiff'e çevir)." >&2
done < <(find -H "$SES_KLASORU" -maxdepth 1 \( -type f -o -type l \) ! -name '.*' \
           \( -iname '*.ogg' -o -iname '*.opus' \) -print0 | LC_ALL=C sort -z)
[ "${#DOSYALAR[@]}" -gt 0 ] || hata "Ses dosyası yok: $SES_KLASORU"

# ffmpeg dosya türünü içerikten sezer; saf bir ses tonu yanlışlıkla başka bir türe (mpegts)
# benzeyebilir. Uzantıdan bilinen türü zorla; tutmazsa (uzantı yanlışsa) içerikten sezmeye dön.
# kullanım: ses_oku DOSYA ffmpeg-çıkış-argümanları...
ses_oku() {
  local f="$1" t=""
  shift
  case "$(printf '%s' "$f" | tr '[:upper:]' '[:lower:]')" in
    *.wav) t=wav ;; *.flac) t=flac ;; *.mp3) t=mp3 ;; *.aif|*.aiff) t=aiff ;;
  esac
  if [ -n "$t" ] && ffmpeg -nostdin -v error -y -f "$t" -i "$f" "$@" 2>/dev/null; then
    return 0
  fi
  ffmpeg -nostdin -v error -y -i "$f" "$@"
}

# 2) Her dosyayı tek tek 48 kHz tek kanal ham PCM'e (s16le) çevir. Ham PCM'in başlığı olmadığı
#    için art arda eklemek düz bir `cat`tir ve örnekleme hızı karışsa da süre ve perde bozulmaz
#    (concat demuxer 24 kHz ile 48 kHz dosyayı aynı hızla okurdu). ffmpeg'ler sırayla çalışır
#    (paralel değil); -nostdin ffmpeg'in girdiyi yutmasını önler.
i=0
for f in "${DOSYALAR[@]}"; do
  i=$((i + 1))
  [ -f "$f" ] || hata "Ses dosyası okunamadı (kırık bağ ya da dosya değil): $f"
  ses_oku "$f" -vn -ar 48000 -ac 1 -f s16le "$CALISMA/$(printf '%05d.pcm' "$i")" \
    || hata "Ses dosyası okunamadı: $f"
  [ -s "$CALISMA/$(printf '%05d.pcm' "$i")" ] || hata "Ses dosyasında örnek yok (boş ses): $f"
done

# 3) Seviye eşitleme: cümleleri ortanca ses şiddetine getir (SES_DENGELE=0/false/no/off/hayir
#    ile kapanır). Ölçülemeyen cümleye (400 ms'den kısa ya da sessiz) dokunulmaz.
if [ "$DENGELE" = "1" ] && [ "$i" -gt 1 ]; then
  : > "$CALISMA/olcum.txt"
  for ((k = 1; k <= i; k++)); do
    L="$(ffmpeg -nostdin -hide_banner -nostats -v info -f s16le -ar 48000 -ac 1 \
           -i "$CALISMA/$(printf '%05d.pcm' "$k")" -af ebur128=framelog=quiet -f null - 2>&1 \
         | awk '/Integrated loudness:/ { g = 1; next } g && $1 == "I:" && !d { print $2; d = 1 }' \
         || true)"
    echo "$k ${L:-yok}" >> "$CALISMA/olcum.txt"
  done
  python3 - "$CALISMA/olcum.txt" "$CALISMA/kazanc.txt" <<'PY'
import statistics
import sys

olcum, cikis = sys.argv[1], sys.argv[2]
open(cikis, "w").close()
olculen = []
for satir in open(olcum):
    k, _, v = satir.partition(" ")
    try:
        lufs = float(v)
    except ValueError:
        continue
    if lufs > -69.0:  # -70 ve altı: ölçülemedi (çok kısa ya da sessiz); nan karşılaştırmayı geçmez
        olculen.append((int(k), lufs))
if len(olculen) < 2:
    print("Ses seviyesi: ölçülebilir cümle 2'den az, eşitleme atlandı.")
    sys.exit(0)
hedef = statistics.median(v for _, v in olculen)
kazanclar = []
with open(cikis, "w") as f:
    for k, v in olculen:
        g = max(-15.0, min(15.0, hedef - v))
        if abs(g) >= 0.5:  # yarım dB altı farkı duymazsın, dosyaya dokunma
            f.write(f"{k} {g:.2f}\n")
            kazanclar.append(g)
if kazanclar:
    print(f"Ses seviyesi: {len(olculen)} cümle ölçüldü, ortanca {hedef:.1f} LUFS; "
          f"{len(kazanclar)} cümleye kazanç uygulandı ({min(kazanclar):+.1f} ile {max(kazanclar):+.1f} dB).")
else:
    print(f"Ses seviyesi: {len(olculen)} cümle ölçüldü, ortanca {hedef:.1f} LUFS; cümleler zaten dengeli.")
PY
  while read -r k g; do
    p="$CALISMA/$(printf '%05d.pcm' "$k")"
    case "$g" in
      -*) FILTRE="volume=${g}dB" ;;
      # Yükseltmede kırpma olmasın: alimiter 5 ms ileri bakar ve sesi 5 ms geciktirir; sona 5 ms
      # (240 örnek) sessizlik ekleyip baştan aynısını kırpmak cümleyi yerinde ve aynı uzunlukta tutar.
      *) FILTRE="volume=${g}dB,apad=pad_len=240,alimiter=limit=0.95:attack=5:level=disabled,atrim=start_sample=240,asetpts=N/SR/TB" ;;
    esac
    ffmpeg -nostdin -v error -y -f s16le -ar 48000 -ac 1 -i "$p" -af "$FILTRE" \
      -ar 48000 -ac 1 -f s16le "$p.yeni" || hata "Ses seviyesi ayarlanamadı: $p"
    mv -f "$p.yeni" "$p"
  done < "$CALISMA/kazanc.txt"
fi

: > "$CALISMA/ses.pcm"
for ((k = 1; k <= i; k++)); do
  cat "$CALISMA/$(printf '%05d.pcm' "$k")" >> "$CALISMA/ses.pcm"
done

# 4) Görüntü + ses -> geçici MP4. CIKIS'a ancak 5. adımdaki kapı geçince dokunulur: reddedilen
#    çıktı diskte kalmasın, var olan iyi dosya ezilmesin.
GECICI="$CALISMA/cikis.mp4"
SES_GIRDI=(-f s16le -ar 48000 -ac 1 -i "$CALISMA/ses.pcm")
case "$(printf '%s' "$GORUNTU" | tr '[:upper:]' '[:lower:]')" in
  *.mp4|*.m4v)
    # hazır H.264 video: yalnız ses ekle (görüntü yeniden kodlanmaz)
    ffmpeg -nostdin -v error -y -i "$GORUNTU" "${SES_GIRDI[@]}" -map 0:v:0 -map 1:a:0 \
      -c:v copy -c:a aac -b:a 192k -movflags +faststart "$GECICI" \
      || hata "ffmpeg birleştirmeyi tamamlayamadı: $GORUNTU"
    ;;
  *.mov|*.webm|*.mkv)
    # ProRes 4444 (HyperFrames --format mov) ve VP8/VP9 MP4'e kopyalanamaz: H.264'e yeniden kodla.
    # yuv420p alfa kanalını atar.
    ffmpeg -nostdin -v error -y -i "$GORUNTU" "${SES_GIRDI[@]}" -map 0:v:0 -map 1:a:0 \
      -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart "$GECICI" \
      || hata "ffmpeg birleştirmeyi tamamlayamadı: $GORUNTU"
    ;;
  *)
    ffmpeg -nostdin -v error -y -framerate "$FPS" -i "$GORUNTU" "${SES_GIRDI[@]}" \
      -c:v libx264 -pix_fmt yuv420p -r "$FPS" -c:a aac -b:a 192k -movflags +faststart "$GECICI" \
      || hata "ffmpeg birleştirmeyi tamamlayamadı: $GORUNTU"
    ;;
esac

# 5) Süre denetimi: Audio Lock — görüntü ile ses arasında 50 ms'den fazla fark olmamalı.
#    Kapı sys.exit(1) ile çıkarsa set -e betiği durdurur, mv çalışmaz, trap geçici dosyayı siler.
sure() { ffprobe -v error -select_streams "$2" -show_entries stream=duration -of csv=p=0 "$1"; }
V="$(sure "$GECICI" v:0)"; A="$(sure "$GECICI" a:0)"
python3 - "$V" "$A" <<'PY'
import sys
try:
    v, a = float(sys.argv[1]), float(sys.argv[2])
except ValueError:
    print("UYARI: çıktıdaki görüntü ya da ses süresi okunamadı. Çıktı yazılmadı.")
    sys.exit(1)
fark = abs(v - a)
print(f"görüntü {v:.3f} sn · ses {a:.3f} sn · fark {fark*1000:.0f} ms")
if fark > 0.05:
    print("UYARI: fark 50 ms'yi aşıyor. Animasyonu timing.json'daki ses sürelerine göre yeniden kur. Çıktı yazılmadı.")
    sys.exit(1)
PY
mkdir -p "$(dirname -- "$CIKIS")"
mv -f "$GECICI" "$CIKIS"
echo "Hazır: $CIKIS"
