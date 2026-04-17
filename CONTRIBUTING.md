# Projeye Katkı

## Branch yapısı

- `main` — kararlı, doğrudan commit atılmaz
- `develop` — her şey buradan açılır
- `feature/...` — yeni özellik eklerken
- `fix/...` — bir şeyi düzeltirken
- `chore/...` — CI veya config değişikliği
- `docs/...` — sadece dokümantasyon

Yeni branch açmak için:
```bash
git checkout develop
git pull origin develop
git checkout -b feature/ne-yapacagini-yaz
```

## Commit mesajı

```
type(scope): ne yaptığını türkçe yaz
```

type değerleri: feat / fix / chore / test / docs / refactor
scope değerleri: backend / frontend / python / docker / ci / repo

Örnekler:
```
feat(backend): analiz sonuçları için yeni endpoint eklendi
fix(frontend): kamera bağlantısı kesilince sayfa donuyordu, düzeltildi
chore(ci): ci workflow dosyası tek dosyaya indirildi
test(python): uyarı servisi testleri yazıldı
```

## CI ne yapıyor?

Push ya da PR açınca otomatik çalışıyor (`ci.yml`):
- backend: maven build + testler + JaCoCo coverage
- python: pip install + pytest (ai-service ve vision-service)
- frontend: npm ci + typecheck + build
- docker: compose config doğrulama + image build (push yok)

Hepsi geçmeden develop'a merge açma.
