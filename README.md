# BADHABINOT Monorepo

BADHABINOT; web, Spring Boot backend servisleri ve Python analiz servislerinden olusan davranis-analiz platformudur.

## Depo Yapisi

```text
backend/
  pom.xml
  src/
    main/
      java/
        com/badhabinot/backend/
      resources/
    test/
      java/
frontend/
python-services/
  vision-service/
  ai-service/
infra/
  docker/
    compose/
    dockerfiles/
    scripts/
  db/
    postgres/
      init/
  nginx/
  redis/
  monitoring/
docs/
  architecture/
  api/
  setup/
  workflows/
  decisions/
packages/
  shared-config/
  shared-contracts/
  shared-docs/
.github/
  workflows/
  ISSUE_TEMPLATE/
  pull_request_template.md
```

## Servis Sorumluluklari

- `frontend`: Kamera erisimi, dashboard, raporlar, hatirlatici UI, sohbet UI.
- `backend/src/main/java/com/badhabinot/backend`: Tek Spring Boot backend; auth, user ve monitoring alanlarini tek uygulamada toplar.
- `python-services/vision-service`: Goruntu on-isleme ve davranis sinyal cikarimi.
- `python-services/ai-service`: Harici AI saglayici uyarlama katmani.

## Hizli Baslangic (Docker)

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Tüm gercek ortam degiskenleri depo kokundeki `.env` dosyasinda toplanmistir. Servis klasorlerinde ayri `.env` dosyalari kullanilmaz.

Temel endpointler:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8080`
- Health: `http://localhost:8080/actuator/health/readiness`

Smoke test:

```powershell
powershell -ExecutionPolicy Bypass -File infra/docker/scripts/smoke-test.ps1 -GatewayBaseUrl http://localhost:8080
```

Kapatma:

```powershell
docker compose down
```

## Lokal Gelistirme

Backend build:

```powershell
mvn -B -ntp -f backend/pom.xml verify
```

Frontend build:

```powershell
cd frontend
npm ci
npm run build
```

Python testleri:

```powershell
cd python-services/ai-service
pip install -r requirements.txt -r requirements-dev.txt
pytest tests

cd ../vision-service
pip install -r requirements.txt -r requirements-dev.txt
pytest tests
```

## Git Dallanma Modeli (Turkce)

Ana dallar:

- `master`: Uretim adayi
- `develop`: Entegrasyon

Calisma dali on ekleri:

- `ozellik/*`
- `duzeltme/*`
- `sicakduzeltme/*`
- `duzenleme/*`
- `dokumantasyon/*`
- `refaktor/*`

Ornek calisma dallari:

- `duzenleme/depo-yeniden-yapilandirma`
- `duzenleme/docker-entegrasyonu`
- `ozellik/on-yuz-kamera-izleme`
- `ozellik/gorus-davranis-analizi`
- `ozellik/hatirlatici-raporlama`
- `ozellik/sohbet-davranis-icgoru`
- `dokumantasyon/muhendislik-standartlari`

Detayli surec: [`docs/workflows/git-dallanma-stratejisi.md`](docs/workflows/git-dallanma-stratejisi.md)
