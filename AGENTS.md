# AGENTS.md

## Amac

Bu depo davranis-analiz platformudur. AI/otonom kod ajanlari bu depoda calisirken:

1. mevcut mimariyi korumali,
2. uretim kalitesinde kod yazmali,
3. tum degisiklikleri test ve entegrasyon odakli yapmalidir.

## Mimari Sinirlar

- `apps/web`:
  - tarayici arayuzu, kamera akisi, dashboard, rapor, sohbet.
- `apps/backend`:
  - Spring Boot servisleri, orkestrasyon, veri kaliciligi, API.
- `apps/python-services`:
  - goruntu isleme, davranis tespiti, AI normalize ciktilari.
- `infra`:
  - docker, nginx, db, redis, scriptler.

## Zorunlu Uygulama Kurallari

1. Yeni proje olusturma, mevcut depoda calis.
2. Frontend/Backend/Python kontratlarini acik sekilde koru.
3. Mock/fake akislari "gercek" gibi gostermeden, kisitlari net belirt.
4. Kamera-analiz hattinda sadece `health` degil, uctan uca akis dogrula.
5. Gizli bilgi/API key dosyalarini commitleme.
6. Docker calisirligini bozma; degisiklikten sonra ayaga kaldir ve kontrol et.
7. Birden fazla konu varsa degisiklikleri ayri commitlerde tut.

## Git ve Teslimat Disiplini

- Dal adlari:
  - `ozellik/*`
  - `duzeltme/*`
  - `sicakduzeltme/*`
  - `duzenleme/*`
  - `dokumantasyon/*`
  - `refaktor/*`
- Conventional Commit benzeri mesaj kullan:
  - `feat(web): ...`
  - `fix(monitoring): ...`
  - `chore(repo): ...`
  - `docs(workflow): ...`

## Dogrulama Kontrol Listesi

Degisiklik tamamlanmis sayilmasi icin en az:

- frontend build gecmeli,
- backend build gecmeli,
- python servisleri import/derleme seviyesinde hatasiz olmali,
- docker compose smoke-test calismali.
