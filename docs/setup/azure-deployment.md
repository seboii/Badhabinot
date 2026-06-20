# Azure VM Canlıya Geçiş Rehberi (Adım Adım)

Bu rehber Badhabinot'u **8 GB RAM / 30 GB disk** bir Azure Linux VM'inde, ücretsiz
Azure FQDN + Caddy otomatik HTTPS ile yayına almayı ve **GitHub Actions CD** (her
`master` push'unda otomatik deploy) kurmayı anlatır.

İmajlar GitHub Actions'ta derlenir, **GHCR**'a push edilir; VM yalnızca **çeker** —
böylece 8 GB VM build sırasında belleği şişirmez ve deploy saniyeler sürer.

---

## 0) Kaynak yeterli mi? (30 GB disk / 8 GB RAM)

**Evet, coach-only modunda rahat çalışır.** 7B base modeli atlanır; yalnızca
fine-tune edilmiş ~1 GB'lık coach (Qwen2.5-1.5B) kullanılır.

| Bileşen | Disk (yaklaşık) | RAM (çalışırken) |
|---|---|---|
| Ollama imajı + coach GGUF modeli | ~1.5 GB + ~1.2 GB | ~1.5–2 GB |
| vision-service (torch+TF + gömülü modeller) | ~4 GB | ~2–2.5 GB |
| ai-service | ~1.2 GB | ~0.3 GB |
| backend (JRE + app, `-Xmx640m`) | ~0.4 GB | ~0.6–0.7 GB |
| frontend + caddy + postgres + redis | ~0.5 GB | ~0.6 GB |
| **Toplam** | **~9–10 GB imaj + veri** | **~6–6.5 GB** |

- **Disk:** ~10 GB imaj/model + Postgres verisi → 30 GB rahat yeter. `docker image prune`
  deploy'da otomatik çalışır.
- **RAM:** ~6.5 GB tipik kullanım; 8 GB içinde kalır. **Güvenlik için 2–4 GB swap önerilir**
  (aşağıda). Backend heap'i `.env.prod`'da `BACKEND_JAVA_OPTS=-Xms256m -Xmx640m` ile sınırlı.

Swap açmak (bir kez):
```bash
sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## 1) Azure VM hazırlığı

1. **VM:** Ubuntu 22.04 LTS, en az 8 GB RAM / 30 GB disk (B2s yetersiz olabilir; **B2ms** önerilir).
2. **Azure ücretsiz FQDN:** Portal → VM'in **Public IP** kaynağı → **Configuration** →
   **DNS name label** ver (ör. `badhabinot`). Oluşan adres:
   `badhabinot.<bölge>.cloudapp.azure.com` → bu senin `PUBLIC_DOMAIN`'in.
3. **NSG (güvenlik duvarı):** Gelen kurallarda **80** ve **443** portlarını AÇ
   (Let's Encrypt + HTTPS). 22 (SSH) zaten açık. Başka port AÇMA (iç servisler iç ağda kalır).
4. **Docker kur:**
   ```bash
   curl -fsSL https://get.docker.com | sudo sh
   sudo usermod -aG docker $USER && newgrp docker
   ```

---

## 2) Repo, sırlar, model ve Firebase

```bash
cd ~ && git clone https://github.com/seboii/Badhabinot.git && cd Badhabinot
cp .env.prod.example .env.prod
```

`.env.prod` içinde **mutlaka** doldur:
- `POSTGRES_PASSWORD` → güçlü şifre
- `SECURITY_JWT_SECRET` → `openssl rand -hex 32`
- `INTERNAL_API_KEY` → `openssl rand -hex 24`
- `PUBLIC_DOMAIN` → Azure FQDN'in
- `TLS_EMAIL` → geçerli e-posta (Let's Encrypt bildirimleri)
- `PASSWORD_RESET_URL_TEMPLATE` → `https://<FQDN>/reset-password?token={token}`
- `MAIL_USERNAME` / `MAIL_PASSWORD` → Gmail app password (şifre sıfırlama)
- `GHCR_OWNER=seboii`, `IMAGE_TAG=latest` (zaten varsayılan)

**Fine-tune coach modeli (GGUF, ~1 GB — git'te değil):** bilgisayarından VM'e kopyala:
```bash
# yerel makinede:
scp python-services/ai-service/finetune/outputs/badhabinot-coach.gguf \
    <vm-user>@<FQDN>:~/Badhabinot/python-services/ai-service/finetune/outputs/
```
Dosya yoksa stack yine kalkar ama coach yerine düz model kullanılır.

**Firebase (telefon push/alarm için):**
- Service account JSON'u VM'e koy: `~/Badhabinot/infra/firebase/firebase-service-account.json`
  (backend buraya `/app/config` olarak mount eder; `.env.prod`'daki yol bununla eşleşir).
- Yoksa push sessizce devre dışı kalır (uygulama çalışır).

---

## 3) İlk kurulum (elle, bir kez)

İlk deploy'u elle yap (CD sonraki push'larda devralır). İmajları GHCR'dan çek:
```bash
echo <GHCR_PAT> | docker login ghcr.io -u seboii --password-stdin
export IMAGE_TAG=latest
docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.ghcr.yml \
    --env-file .env.prod pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.ghcr.yml \
    --env-file .env.prod up -d
```
> GHCR imajlarının var olması için önce `master`'a bir kez push edip Actions'ın
> `build-push` işini tamamlamasını bekle (Adım 4). Alternatif: ilk sefer
> `--env-file .env.prod up -d --build` ile VM'de derle (yavaş, RAM yoğun — önerilmez).

Caddy birkaç dakika içinde Let's Encrypt sertifikasını otomatik alır. Site:
`https://<FQDN>`

İlk admin hesabı Flyway ile gelir: **admin@badhabinot.com / Admin123!** (girer girmez şifreyi değiştir).

---

## 4) GitHub Actions CD (otomatik deploy)

`.github/workflows/deploy.yml` `master`'a her push'ta:
1. 4 imajı (backend, ai-service, vision-service, frontend) derler ve GHCR'a push eder.
2. VM'e SSH ile bağlanıp `git pull` + `compose pull` + `up -d` + `image prune` yapar.

**Repo Secrets** (GitHub → Settings → Secrets and variables → Actions → New secret):

| Secret | Değer |
|---|---|
| `VM_HOST` | Azure FQDN veya public IP |
| `VM_USER` | VM kullanıcı adı (ör. `azureuser`) |
| `VM_SSH_KEY` | VM'e erişen **private** SSH anahtarı (tüm PEM içeriği) |
| `GHCR_USER` | `seboii` |
| `GHCR_PAT` | `read:packages` yetkili GitHub PAT (VM imaj çeker) |

> İlk push'tan sonra GHCR paketleri **private** gelir. İstersen GitHub → Packages →
> her paket → Package settings → **Make public** dersen VM'de `docker login` gerekmez
> (yine de PAT'lı login zararsız).

Sonraki her güncelleme: kodu `master`'a push et → otomatik canlıya çıkar.

---

## 5) Mobil (Android APK) — canlıya bağla

APK'yı canlı siteye bağlı derle (her zaman güncel kalır, push/alarm çalışır):
```bash
cd frontend
CAP_SERVER_URL=https://<FQDN> npm run android:sync
npm run android:open   # Android Studio → Build → Generate Signed APK
```
- `google-services.json` → `frontend/android/app/google-services.json` (Firebase Android app).
- Telefon, kamera izlemeyi yapmaz (web'e özel); **dashboard + bildirim/alarm** alır.
- Bilgisayarda kamera izleme açıkken üretilen "duruşunu düzelt / su iç / dinlen"
  hatırlatıcıları backend tarafından FCM ile telefona push edilir (yüksek öncelik + ses).

---

## 6) Doğrulama ve bakım

```bash
# sağlık
curl -fsS https://<FQDN>/healthz && echo OK
docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.ghcr.yml ps

# loglar
docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.ghcr.yml logs -f backend

# coach modeli yüklendi mi?
docker compose ... exec ollama ollama list   # badhabinot-coach:latest görünmeli
```

- **Yedek:** Postgres verisi `postgres-data` volume'unda. Düzenli `pg_dump` al.
- **Sertifika:** Caddy otomatik yeniler; `caddy-data` volume'u silinmesin.
- **Güncelleme:** sadece `master`'a push — gerisi otomatik.
