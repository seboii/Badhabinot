# BADHABINOT Monorepo

BADHABINOT; web, Spring Boot backend servisleri ve Python analiz servislerinden olusan davranis-analiz platformudur.

## Depo Yapisi

```text
apps/
  web/
    frontend-app/
  backend/
    api-gateway/
    auth-service/
    monitoring-service/
    user-service/
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

- `apps/web/frontend-app`: Kamera erisimi, dashboard, raporlar, hatirlatici UI, sohbet UI.
- `apps/backend/api-gateway`: Dis API girisi, route forwarding.
- `apps/backend/auth-service`: Kimlik dogrulama ve token yasam dongusu.
- `apps/backend/user-service`: Kullanici profili, ayarlar, onaylar.
- `apps/backend/monitoring-service`: Izleme orkestrasyonu, davranis olaylari, rapor ve hatirlatici veri akis.
- `apps/python-services/vision-service`: Goruntu on-isleme ve davranis sinyal cikarimi.
- `apps/python-services/ai-service`: Harici AI saglayici uyarlama katmani.

## Hizli Baslangic (Docker)

```powershell
Copy-Item .env.example .env
docker compose -f infra/docker/compose/docker-compose.yml -f infra/docker/compose/docker-compose.dev.yml up -d --build
```

Temel endpointler:

- Frontend: `http://localhost:3000`
- API Gateway: `http://localhost:8080`
- Health: `http://localhost:8080/actuator/health/readiness`

Smoke test:

```powershell
powershell -ExecutionPolicy Bypass -File infra/docker/scripts/smoke-test.ps1 -GatewayBaseUrl http://localhost:8080
```

Kapatma:

```powershell
docker compose -f infra/docker/compose/docker-compose.yml -f infra/docker/compose/docker-compose.dev.yml down
```

## Lokal Gelistirme

Backend build:

```powershell
mvn -B -ntp -DskipTests package
```

Frontend build:

```powershell
cd apps/web/frontend-app
npm ci
npm run build
```

Python compile kontrolu:

```powershell
cd apps/python-services/ai-service
pip install -r requirements.txt
python -m compileall app

cd ../vision-service
pip install -r requirements.txt
python -m compileall app
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

## Katki

PR sureci, commit kurallari ve inceleme beklentileri icin:

- [`CONTRIBUTING.md`](CONTRIBUTING.md)

AI ajan kurallari icin:

- [`AGENTS.md`](AGENTS.md)
