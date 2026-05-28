# Faz 2 — Landmark-Tabanlı Davranış Sınıflandırma (Eğitim İskeleti)

Faz 2, davranış kararını **elle ayarlanmış heuristik eşiklerden** çıkarıp
landmark özelliklerinden **öğrenen bir modele** taşır. Davranış tek karede değil
bir hareket dizisinde belirir; bu yüzden model bir **kare penceresi (window)**
üzerinde çalışan bir temporal sınıflandırıcıdır (1D-CNN).

> Durum: İskelet hazır. Gerçek doğruluk için etiketli landmark dizisi toplanmalı
> ve model eğitilmelidir. Karşılaştırma Faz 1 baseline'ına karşı yapılır.

## Neden landmark, neden temporal?

- **Gizlilik:** Model girdisi landmark koordinatları + türevlerdir (poz açıları,
  el-ağız yakınlığı, EAR/MAR). **Ham görüntü modele girmez** — bu, tezin
  "gizlilik-koruyan davranış analizi" anlatısını kod düzeyinde destekler.
- **Temporal:** Sigara çekişi / tekrarlayan el hareketi bir *dizidir*. Pencere
  üzerinde 1D konvolüsyon, tek-kare heuristiğin kaçırdığı zamansal örüntüyü yakalar.

## Mimari

```
webcam → VisionAnalysisService → landmark'lar
       → features_from_response → (FEATURE_DIM,) vektör        [landmark_features.py]
       → window kare biriktir   → (window, FEATURE_DIM) dizi   [collect.py]
       → 1D-CNN                 → sınıf                         [model.py]
```

- `landmark_features.py` — sabit-boyutlu özellik vektörü (saf numpy, test edilebilir).
- `model.py` — `LandmarkSequenceClassifier` (Conv1d ×2 → adaptive pool → linear).
- `sequence_dataset.py` — npz dizi veri seti (PyTorch Dataset).
- `train.py` / `infer.py` — eğitim ve çıkarım CLI'ları.
- `collect.py` — webcam'den etiketli landmark dizisi toplama.

Sınıf kümesi Faz 1 ile **aynıdır** (`evaluation.labels.LABELS`), böylece
sonuçlar doğrudan baseline'a karşı kıyaslanabilir.

## Kurulum

PyTorch runtime ve CI'ye dahil değildir; yalnızca eğitim için gerekir:

```bash
cd python-services/vision-service
pip install torch --index-url https://download.pytorch.org/whl/cpu   # CPU sürümü
# Gerçek landmark çıkarımı için ana ML bağımlılıkları da gerekir:
pip install -r requirements.txt
```

## İş akışı

1. **Veri topla** (sınıf başına çok sayıda dizi, çeşitli kişi/ışık):
   ```bash
   python -m training.collect --label normal               --sequences 30 --window 16 --out data/sequences.npz
   python -m training.collect --label poor_posture         --sequences 30 --window 16 --out data/sequences.npz
   python -m training.collect --label hand_movement_pattern --sequences 30 --window 16 --out data/sequences.npz
   python -m training.collect --label smoking_like_gesture  --sequences 30 --window 16 --out data/sequences.npz
   ```
2. **Eğit:**
   ```bash
   python -m training.train --data data/sequences.npz --epochs 40 --out model.pt
   ```
   Her epoch train loss + val accuracy basar; model `model.pt` olarak kaydedilir.
3. **Çıkarım / kıyaslama:** `infer.SequencePredictor` ile diziler sınıflandırılır.
   Test seti tahminlerini `evaluation.metrics.compute_report` ile metriklere çevir
   ve **Faz 1 baseline'ı ile yan yana koy** (tez: model heuristiği geçmeli).

## Test

- `tests/test_training_features.py` — özellik çıkarımı (saf numpy, her zaman çalışır).
- `tests/test_training_model.py` — model şekli + öğrenme (torch yoksa **skip**;
  `pip install torch` sonrası çalışır, küçük batch'i ezberleyebildiğini doğrular).

## Sınırlamalar ve sonraki adım

- Veri olmadan model boştur; gerçek doğruluk toplanan veriye bağlıdır.
- Özellik seti kompakttır (~58 boyut); ham 468-nokta face mesh dahil edilerek
  genişletilebilir.
- **Pipeline entegrasyonu** (eğitilmiş modeli `VisionAnalysisService` içinde
  heuristik `_build_detections` yerine/yanında kullanmak) Faz 2'nin son adımıdır;
  model baseline'ı geçtikten sonra yapılmalıdır.

---

# Faz 3 — Açıklanabilirlik (XAI) + Kişiselleştirme

Faz 3, Faz 2'nin "kara kutu" modelinin üstüne iki bilimsel katman ekler:

- **XAI (`explain.py`)** — "Neden bu karar verildi?" sorusunu gradient × input
  saliency ile yanıtlar. Tahmin edilen sınıfın logit'i üzerinden geri yayılım
  alır; her zaman adımı ve her özelliğin karara katkısını ölçer. `top_features`
  insan-okunur adlarla döner (ör. `kp_left_wrist_y`, `hand0_near_mouth`).
- **Kişiselleştirme (`personalizer.py`)** — Her kullanıcının "normal davranışı"
  farklıdır. Welford online algoritmasıyla landmark istatistiklerinin
  kayan ortalama/varyansı saklanır; yeni bir kare kişiye özel z-skoruyla
  değerlendirilir. Sabit global eşiklere bağımlılık ortadan kalkar.

> Durum: İskelet hazır. XAI eğitilmiş bir modele ihtiyaç duyar (Faz 2 çıktısı);
> kişiselleştirme yalnızca özellik vektörü akışı gerektirir, bağımsız çalışır.

## Neden gradient × input?

- Saf gradient ("vanilla saliency") sıfır-değerli özelliklerde de yüksek skor
  üretebilir. Gradient × input, "bu özellik gerçekten orada vardı ve karara
  katkı sağladı" yorumunu güçlendirir.
- Tek bir kare için değil, **tüm zaman penceresi** üzerinden çalışır — Faz 2'nin
  temporal anlatısıyla tutarlıdır.

## Neden kişisel baseline?

- "Kötü duruş" eşiği herkes için aynı değildir; vücut yapısı, kamera açısı ve
  alışkanlık farklıdır. Welford istatistikleri ilk birkaç oturumda kullanıcıya
  özgü dağılımı öğrenir.
- **Ham görüntü kaydedilmez**; yalnızca özellik vektörü `n`, `mean` ve
  ikinci-moment `M2` toplamı saklanır → tezin gizlilik anlatısını destekler.

## Kurulum

`explain.py` PyTorch gerektirir (Faz 2 ile aynı):
```bash
cd python-services/vision-service
pip install -r requirements-train.txt
```
`personalizer.py` saf numpy — ek bağımlılık gerekmez.

## İş akışı

1. **Bir karar için XAI açıklaması üret:**
   ```bash
   python -m training.explain --model model.pt --data data/sequences.npz --index 0
   ```
   Çıktıda tahmin sınıfı, güven, en etkili 5 özellik ve zaman adımı önemi
   (ASCII bar) yer alır. `--json-out path.json` ile sonuç makineye-okunur
   biçimde kaydedilir (tez grafikleri için).

2. **Kullanıcıya özel baseline öğret:**
   ```bash
   python -m training.personalizer --user demo-user --learn data/normal_session.npz
   python -m training.personalizer --user demo-user --stats
   ```
   `--learn` dosyadaki tüm kareleri Welford istatistiğine ekler; `--stats` ile
   örnek sayısı, ortalama std ve en değişken özellikler yazdırılır.

3. **Yeni bir oturumu baseline'a karşı kontrol et:**
   ```bash
   python -m training.personalizer --user demo-user --check data/new_session.npz --index 0
   ```
   Pencerenin ortalama vektörü için z-skoru ve en sapma gösteren özellikler
   listelenir. Eşik 2.0 olarak alınır (kişisel sapmanın iki standart sapmanın
   üstüne çıkması = ilgi çekici durum).

## Test

- `tests/test_personalizer.py` — saf numpy (5+ test): ilk durum, minimum örnek
  altında skor, normal vs sapmalı vektör karşılaştırması, `top_deviations`
  ad eşleşmesi, persist/reload, reset, geçersiz şekil reddi.
- `tests/test_explain.py` — torch-gated (5 test): ExplanationResult şekilleri,
  sınıfa özgü sinyalin `top_features`'a yansıması, saliency'nin sıfır olmaması,
  `to_dict` JSON-serileştirilebilirliği, render yardımcıları.

## Sınırlamalar ve sonraki adım

- XAI çıktısı yalnızca eğitim sırasında modele gerçekten geçen sinyalleri
  vurgular — toplanan veri ne kadar çeşitli olursa açıklama da o kadar
  güvenilir olur.
- Personalizer mevcut hali Gauss varsayımı yapar (z-skor). Heavy-tailed
  davranışlar için robust varyans (median absolute deviation) eklenebilir.
- **Pipeline entegrasyonu**: `UserBaseline.anomaly_score`'u
  `VisionAnalysisService` içine takıp olay severity'sini kişisel sapmayla
  ölçeklemek opsiyonel ileri adımdır; tez demosu için CLI çıktıları yeterlidir.

---

# Faz 4 — Multimodal Füzyon (LLM + Vision)

Faz 4, vision çıktısının ham olay listesi olarak değil **yapılandırılmış sinyal**
olarak LLM'e geçmesini sağlar. İki ayrı taraf vardır:

- **Backend (Java) — zaman serisi örüntüsü**: `TemporalPatternAnalyzer`
  davranış olaylarından her event_type için saat/gün piki ve trend
  (artıyor/azalıyor/stabil) çıkarır. `AiChatRequest.Context.behavioralPatterns`
  alanı LLM'e geçer; `OllamaProvider` "ZAMANSAL ÖRÜNTÜLER (SON 7 GÜN)"
  bloğunu prompt'a ekler, grounded_facts/follow_up'ı bu örüntülerden besler.
- **Vision (Python) — anlık özet**: `training/insights.py` →
  `BehavioralInsight` Faz 2 model tahmini + Faz 3 saliency top_features +
  Faz 3 kişisel anomaly_score + top_deviations'ı tek dataclass'ta toplar.
  `to_dict()` ile JSON, `summary_tr` ile doğrudan Türkçe koçluk cümlesi.

> Durum: İskelet hazır. `TemporalPatternAnalyzer` üretim akışındaki gerçek
> olaylarla çalışır. `BehavioralInsight` pipeline'a entegre edilmemiş —
> eğitilmiş model olunca `VisionAnalysisService`'in opsiyonel bir alanı
> olarak gönderilebilir.

## Neden örüntü, neden tek dataclass?

- "Sigara-benzeri jest sabah 10-11 arası yoğun" cümlesini LLM tek başına
  ham olay listesinden çıkarmaya zorlanmamalı; bu sayısal işin Java tarafında
  deterministik yapılması hem ucuz hem güvenilirdir.
- `BehavioralInsight` model + XAI + kişisel sapmayı tek payload'ta birleştirir;
  LLM'in görmesi gereken **yalnızca yorumlanabilir özet** olur, ham
  landmark vektörü değil → gizlilik tarafıyla da uyumlu.

## Kullanım

```python
from training.insights import build_insight
insight = build_insight(
    predicted_label="smoking_like_gesture",
    confidence=0.81,
    top_features=[("hand0_near_mouth", 0.92), ("mar", 0.34)],
    anomaly_score=2.3,
    top_deviations=[("kp_left_wrist_y", 3.1)],
)
payload = insight.to_dict()           # LLM'e gönder
print(insight.summary_tr)              # TR koçluk cümlesi
```

Backend tarafında değişiklik gerekmez — eğitim sonrası `VisionAnalysisService`
opsiyonel `behavioral_insight: BehavioralInsight | None` alanını response'a
ekleyebilir; backend bunu `AiChatRequest.Context`'e geçirir.

## Test

- `tests/test_insights.py` — 7 test (saf python, hep çalışır): confidence/anomaly
  etiketleri, summary_tr içeriği, JSON serileştirme/yuvarlama, varsayılan
  boş koleksiyonlar.
- Backend tarafında `TemporalPatternAnalyzerTest` (Java/JUnit 5) — boş liste,
  eşik altı dışlanma, peak hour/day doğruluğu, intensity etiketi, artan/azalan
  trend, total count sıralaması.
