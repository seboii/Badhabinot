# Faz 1 — Davranış Tespiti Değerlendirme Harness'ı

Bu paket, davranış tespiti pipeline'ının **doğruluğunu etiketli bir veri seti
üzerinde sayısal olarak ölçer**: confusion matrix, sınıf-başına precision / recall /
F1, macro & weighted ortalamalar ve toplam doğruluk. Üretilen sayılar, mevcut
heuristik + landmark pipeline'ının **baseline'ını** oluşturur ve tezin "Deneysel
Sonuçlar" bölümünün temelidir. Faz 2'de eğitilecek model bu baseline'a karşı
kıyaslanacaktır.

## Sınıflar (tek-etiketli)

Her kare tek bir baskın sınıfa atanır:

| Sınıf | Tanım |
|-------|-------|
| `normal` | Baskın riskli davranış yok; nötr/odaklı oturma |
| `poor_posture` | Eğik/çökmüş duruş, öne uzanma |
| `hand_movement_pattern` | El-yüz teması, tekrarlayan el hareketi |
| `smoking_like_gesture` | El-ağız teması (içme/yeme nesnesi olmadan) |

> Not: Gerçekte davranışlar çok-etiketli olabilir (aynı karede hem `poor_posture`
> hem `hand_movement_pattern`). Bu baseline bilinçli olarak **tek-etiketli**dir;
> pipeline'ın en yüksek güven skorlu tespiti baskın sınıf sayılır. Çok-etiketli
> değerlendirme gelecek bir genişlemedir.

## Veri toplama protokolü

1. **İzin/etik:** Yalnızca açık rıza veren gönüllülerin görüntülerini topla. KVKK
   kapsamında ham görüntüler repoya **girmez** (`.gitignore` ile dışlanır), yerelde kalır.
2. **Çeşitlilik:** Farklı kişi, ışık, mesafe ve kamera açısı kullan. Sınıf başına
   en az 30–50 kare hedefle; dengeyi koru (`evaluate.py` dağılımı raporlar).
3. **Yakalama aracı:**
   ```bash
   cd python-services/vision-service
   python -m evaluation.capture --label poor_posture --count 40 --out data
   python -m evaluation.capture --label normal --count 40 --out data
   python -m evaluation.capture --label hand_movement_pattern --count 40 --out data
   python -m evaluation.capture --label smoking_like_gesture --count 40 --out data
   ```
   Her komut `data/frames/` altına JPEG yazar ve `data/labels.jsonl`'a satır ekler.
4. **Etiketleme kuralı:** Bir oturum boyunca tek bir davranış sergilenir ve o
   oturumun tüm kareleri o sınıfla etiketlenir. Belirsiz kareleri elle ayıkla/sil
   ve manifest'ten ilgili satırı çıkar.

## Manifest formatı (`data/labels.jsonl`)

Her satır bir JSON nesnesi (yollar manifest dizinine göreli):

```json
{"image": "frames/poor_posture-20260528-101500-000001.jpg", "label": "poor_posture", "frame_id": "..."}
{"image": "frames/normal-20260528-101600-000002.jpg", "label": "normal", "frame_id": "..."}
```

Boş satırlar ve `#` ile başlayan satırlar yok sayılır.

## Değerlendirmeyi çalıştırma

```bash
cd python-services/vision-service
python -m evaluation.evaluate --manifest data/labels.jsonl
# Metrikleri dosyaya da yaz:
python -m evaluation.evaluate --manifest data/labels.jsonl --json-out results.json
```

Çıktı: sınıf dağılımı, confusion matrix (satır = gerçek, sütun = tahmin) ve
sınıf-başına precision/recall/F1 + macro/weighted ortalamalar + accuracy.

## Çıktıların yorumu

- **Confusion matrix** hangi sınıfların birbirine karıştığını gösterir (ör. çok
  sayıda `smoking_like_gesture` → `normal` kayması, mevcut el-ağız tespitinin
  kaçırdığını işaret eder).
- **Recall** düşükse pipeline o davranışı *kaçırıyor*; **precision** düşükse
  *yanlış alarm* üretiyor.
- Bu baseline'ı tezde tablo olarak ver; Faz 2 modelinin macro-F1'i bu sayıyı
  geçmelidir.

## Mimari ve test

- `metrics.py` — saf numpy; harici ML bağımlılığı yok, `tests/test_evaluation_metrics.py`
  ile doğrulanır (CI'da çalışır, veri/model gerektirmez).
- `dataset.py` / `labels.py` — manifest okuma ve sınıf çıkarımı.
- `predict.py` — her kareyi `VisionAnalysisService`'ten geçirir (kareye özel
  session_id ile state izolasyonu sağlar).
- `evaluate.py` / `capture.py` — CLI araçları.

## Sınırlamalar

- Tek-etiketli; çok-etiketli değerlendirme henüz yok.
- Küçük veri setlerinde metrikler yüksek varyanslıdır — örnek sayısını ve sınıf
  dengesini raporla.
- Toplanan veri kişiseldir ve repoya dahil edilmez.
