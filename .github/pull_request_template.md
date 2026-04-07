## Ozet

Bu PR neyi cozuyor?

## Degisiklik Kapsami

- [ ] Frontend
- [ ] Backend
- [ ] Python servisleri
- [ ] Infra/Docker
- [ ] Dokumantasyon

## Test Kaniti

Calistirilan komutlar:

```text
mvn -B -ntp -DskipTests package
cd apps/web/frontend-app && npm ci && npm run build
```

Varsa ek smoke-test ciktilari:

```text
powershell -ExecutionPolicy Bypass -File infra/docker/scripts/smoke-test.ps1 -GatewayBaseUrl http://localhost:8080
```

## Risk ve Geri Donus

- Risk:
- Geri donus plani:

## Kontrol Listesi

- [ ] Dal adi stratejiye uygun
- [ ] Commitler mantiksal ve ayrik
- [ ] Gizli bilgi yok
- [ ] Dokuman guncellendi (gerekiyorsa)
