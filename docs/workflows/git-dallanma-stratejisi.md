# Git Dallanma Stratejisi

## Hedef

Karismis degisiklikleri engellemek, PR kalitesini arttirmak ve release riskini dusurmek.

## Dallar

Kalici:

- `master`: Uretime alinabilir kod
- `develop`: Entegrasyon ve birlesim dali

Gecici calisma dallari:

- `ozellik/*`: Yeni fonksiyonlar
- `duzeltme/*`: Hata duzeltmeleri
- `sicakduzeltme/*`: Acil canli sistem duzeltmeleri
- `duzenleme/*`: Repo, tooling, altyapi temizlikleri
- `dokumantasyon/*`: Dokuman degisiklikleri
- `refaktor/*`: Davranis degistirmeyen kod iyilestirmeleri

## Merge Sirasi

Oncelikli entegrasyon sirası:

1. `duzenleme/depo-yeniden-yapilandirma`
2. `duzenleme/docker-entegrasyonu`
3. `ozellik/on-yuz-kamera-izleme`
4. `ozellik/gorus-davranis-analizi`
5. `ozellik/hatirlatici-raporlama`
6. `ozellik/sohbet-davranis-icgoru`
7. `dokumantasyon/muhendislik-standartlari`
8. `develop`
9. `master`

## Commit Standarti

Kural:

- Her commit tek bir amaca hizmet etmeli.
- Frontend/backend/python/infra degisiklikleri ayri commit olmali.

Ornekler:

- `chore(repo): monorepo standart dosyalarini ekle`
- `fix(docker): compose host-port ve healthcheck akisini duzelt`
- `feat(web): kamera izin ve izleme durumunu stabilize et`
- `feat(vision): davranis olay ciktilarini normalize et`
- `docs(workflow): dallanma ve PR surecini guncelle`

## PR Kurali

Her PR su bolumleri icermeli:

1. Ozet
2. Kapsam disi kalanlar
3. Test kaniti
4. Risk/geri donus plani

PR basligi:

- `<tur>/<alan>: <kisa aciklama>`
- Ornek: `feat(web): canli kamera izleme akisinda durum tutarliligi`
