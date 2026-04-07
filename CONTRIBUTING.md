# Katki Rehberi

Bu depo cok servisli bir monorepodur. Katki yaparken degisiklikleri net sinirlarda tutun.

## Dal (Branch) Kurali

Ana dallar:

- `master` (uretim adayi, korunmali)
- `develop` (entegrasyon dali)

Calisma dali on ekleri:

- `ozellik/*` yeni ozellik
- `duzeltme/*` bug fix
- `sicakduzeltme/*` kritik canli sistem duzeltmesi
- `duzenleme/*` repo/tooling/altyapi duzenleri
- `dokumantasyon/*` dokumantasyon
- `refaktor/*` davranisi degistirmeyen kod sadeleme

Ornekler:

- `ozellik/on-yuz-kamera-izleme`
- `duzeltme/docker-ag-gecidi`
- `duzenleme/depo-standartlari`

## Commit Kurali

Kucuk, izole ve mantiksal commitler yapin. Tek committe karisik degisiklik yapmayin.

Mesaj formati:

- `feat(web): kamera onizleme durum yonetimini duzelt`
- `fix(monitoring): vision-service timeout yonetimini duzelt`
- `chore(repo): .github workflow ve issue template ekle`
- `docs(workflow): dallanma ve PR surecini belgeledi`

## PR Kurali

Her dal tek bir is akisina ait olmali.

PR acmadan once:

1. Gerekli testleri calistirin.
2. README/CONTRIBUTING etkileniyorsa guncelleyin.
3. Gizli bilgi olmadigini dogrulayin.
4. Degisiklik kapsamini net yazin.

PR icinde su bolumler olmali:

- Ozet
- Kapsam
- Test kaniti
- Riskler/Geri donus plani

## Kod Inceleme Beklentisi

Inceleyenler asagidakilere bakar:

- Kontrat uyumu (frontend-backend-python)
- Geriye donuk uyumluluk
- Hata durumlari ve loglama
- Test kapsami
- Guvenlik/gizli bilgi riski

## Test Beklentileri

Minimum:

- `mvn -B -ntp -DskipTests package`
- `cd apps/web/frontend-app && npm ci && npm run build`
- `cd apps/python-services/ai-service && pip install -r requirements.txt && python -m compileall app`
- `cd apps/python-services/vision-service && pip install -r requirements.txt && python -m compileall app`

Docker dogrulama:

- `docker compose -f infra/docker/compose/docker-compose.yml -f infra/docker/compose/docker-compose.dev.yml up -d`
- `powershell -ExecutionPolicy Bypass -File infra/docker/scripts/smoke-test.ps1 -GatewayBaseUrl http://localhost:8080`
- `docker compose -f infra/docker/compose/docker-compose.yml -f infra/docker/compose/docker-compose.dev.yml down`
