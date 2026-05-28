.PHONY: yardim help up dev local-up local-rebuild local-down \
        down build rebuild logs log status shell clean clean-containers smoke \
        backend-build frontend-build python-check ci \
        ngrok-start ngrok-stop gen-cert \
        android-debug android-release android-install android-clean android-test \
        prod-up prod-down prod-rebuild prod-logs ssl-init ssl-renew

# ── Compose dosyaları ─────────────────────────────────────
BASE    = docker-compose.yml
LOCAL   = docker-compose.local.yml
DEV     = docker-compose.dev.yml
PROD    = docker-compose.prod.yml

# ══════════════════════════════════════════════════════════
# LOCAL KOMUTLARI
# ══════════════════════════════════════════════════════════

## Local ortamı başlat (Nginx :80 + debug portları)
local-up:
	docker compose -f $(BASE) -f $(LOCAL) up -d
	@echo ""
	@echo "Badhabinot baslatildi!"
	@echo ""
	@echo "  Web:     http://localhost"
	@echo "  API:     http://localhost/api/v1/platform/info"
	@echo ""
	@echo "  Android (sanal cihaz):  http://10.0.2.2"
	@echo "  Android (fiziksel):     http://BILGISAYAR_IP"
	@echo ""

## Local ortamı yeniden build et ve başlat
local-rebuild:
	docker compose -f $(BASE) -f $(LOCAL) down --remove-orphans
	docker compose -f $(BASE) -f $(LOCAL) build --no-cache
	docker compose -f $(BASE) -f $(LOCAL) up -d

## Local ortamı durdur
local-down:
	docker compose -f $(BASE) -f $(LOCAL) down --remove-orphans

## Servis durumlarını göster
status:
	docker compose -f $(BASE) -f $(LOCAL) ps

## Belirli servis logu: make log SVC=backend
log:
	docker compose -f $(BASE) -f $(LOCAL) logs -f $(SVC)

# ── Eski komutlar (geriye uyumluluk) ─────────────────────

## Docker stack başlat (port binding yok)
up:
	docker compose up -d

## Docker stack + host port binding ile başlat
dev:
	docker compose -f $(BASE) -f $(DEV) up -d

## Docker stack kapat
down:
	docker compose down --remove-orphans

## Docker image'ları build et (cache ile)
build:
	docker compose build

## Cache'siz temiz build + up
rebuild:
	docker compose down --remove-orphans
	docker compose build --no-cache
	docker compose up -d

## Tüm servislerin loglarını canlı izle
logs:
	docker compose -f $(BASE) -f $(LOCAL) logs -f

## Servise bash shell aç: make shell SVC=backend
shell:
	docker compose -f $(BASE) -f $(LOCAL) exec $(SVC) bash

## Her şeyi temizle (veriler dahil!)
clean:
	docker compose -f $(BASE) -f $(LOCAL) down --remove-orphans --volumes --rmi local
	docker system prune -f

## Sadece container'ları temizle (volume'lar korunur)
clean-containers:
	docker compose -f $(BASE) -f $(LOCAL) down --remove-orphans

# ── Smoke Test ────────────────────────────────────────────

## Temel sağlık kontrolleri
smoke:
	@echo "Backend health..."
	@curl -sf http://localhost/actuator/health/readiness && echo " OK" || echo " HATA"
	@echo "API info..."
	@curl -sf http://localhost/api/v1/platform/info && echo " OK" || echo " HATA"

# ── Ngrok (telefon testi) ──────────────────────────────────

## Ngrok başlat (NGROK_AUTHTOKEN .env'de olmalı)
ngrok-start:
	docker compose -f $(BASE) -f $(LOCAL) --profile ngrok up -d ngrok
	@echo ""
	@echo "Ngrok arayüzü: http://localhost:4040"
	@echo "Public URL'yi oradan kopyalayip android-app/build.gradle'a yaz"
	@echo ""

## Ngrok durdur
ngrok-stop:
	docker compose -f $(BASE) -f $(LOCAL) stop ngrok

## SSL sertifikası oluştur (web kamera için HTTPS gerekli)
## Tarayıcı uyarısı → Gelişmiş → Devam et (self-signed, local only)
gen-cert:
	@mkdir -p infra/nginx/ssl
	@docker run --rm \
		-v "$(CURDIR)/infra/nginx/ssl:/certs" \
		alpine sh -c 'apk add -q --no-cache openssl 2>/dev/null && \
			openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
			-keyout /certs/local.key -out /certs/local.crt \
			-subj "/C=TR/O=Badhabinot/CN=local" \
			-addext "subjectAltName=IP:192.168.1.26,IP:127.0.0.1,DNS:localhost" \
			2>/dev/null && echo "SSL sertifikasi olusturuldu: infra/nginx/ssl/"'
	@docker compose -f $(BASE) -f $(LOCAL) restart nginx 2>/dev/null || true

# ── CI ────────────────────────────────────────────────────

## Backend test + build
backend-build:
	mvn -B -ntp -f backend/pom.xml -DskipTests package

## Frontend type check + build
frontend-build:
	cd frontend && npm ci && npm run build

## Python servisleri compile kontrolu
python-check:
	pip install -r python-services/ai-service/requirements.txt
	python -m compileall python-services/ai-service/app
	pip install -r python-services/vision-service/requirements.txt
	python -m compileall python-services/vision-service/app

## Tüm CI adımları
ci: backend-build frontend-build python-check

# ── Android ──────────────────────────────────────────────

android-debug:
	cd android-app && ./gradlew assembleDebug

android-release:
	cd android-app && ./gradlew assembleRelease

android-install:
	cd android-app && ./gradlew installDebug

android-clean:
	cd android-app && ./gradlew clean

android-test:
	cd android-app && ./gradlew test lint

# ══════════════════════════════════════════════════════════
# SUNUCU KOMUTLARI (yorumda — docker-compose.prod.yml aktif et)
# ══════════════════════════════════════════════════════════

## SUNUCU — Başlat (önce .env.prod oluştur)
# prod-up:
# 	docker compose -f $(BASE) -f $(PROD) --env-file .env.prod up -d
# 	@echo "Production baslatildi: https://api.badhabinot.com"

## SUNUCU — Durdur
# prod-down:
# 	docker compose -f $(BASE) -f $(PROD) --env-file .env.prod down

## SUNUCU — Yeniden build et
# prod-rebuild:
# 	docker compose -f $(BASE) -f $(PROD) --env-file .env.prod down
# 	docker compose -f $(BASE) -f $(PROD) --env-file .env.prod build --no-cache
# 	docker compose -f $(BASE) -f $(PROD) --env-file .env.prod up -d

## SUNUCU — Logları izle
# prod-logs:
# 	docker compose -f $(BASE) -f $(PROD) --env-file .env.prod logs -f

## SUNUCU — SSL sertifikası al (alan adı aktif olduktan sonra, sunucuda çalıştır)
# ssl-init:
# 	sudo certbot certonly --standalone \
# 		-d api.badhabinot.com \
# 		--email admin@badhabinot.com \
# 		--agree-tos --no-eff-email

## SUNUCU — SSL sertifikasını yenile
# ssl-renew:
# 	sudo certbot renew
# 	docker compose -f $(BASE) -f $(PROD) --env-file .env.prod exec nginx nginx -s reload

# ── Yardım ───────────────────────────────────────────────

yardim: help
help:
	@echo ""
	@echo "Badhabinot — Kullanilabilir Komutlar"
	@echo "======================================"
	@echo ""
	@echo "LOCAL:"
	@echo "  make local-up       -> Local ortami baslatir (Nginx :80)"
	@echo "  make local-rebuild  -> Yeniden build et ve baslatir"
	@echo "  make local-down     -> Durdur"
	@echo "  make logs           -> Tum loglari izle"
	@echo "  make log SVC=xxx    -> Belirli servis logu"
	@echo "  make status         -> Servis durumlari"
	@echo "  make shell SVC=xxx  -> Servisin icine gir"
	@echo "  make smoke          -> Saglik kontrolleri"
	@echo ""
	@echo "TESTING:"
	@echo "  make ci             -> Tum testler"
	@echo "  make backend-build  -> Backend testleri"
	@echo "  make frontend-build -> Frontend kontrol"
	@echo "  make ngrok-start    -> Telefon test URL'si"
	@echo ""
	@echo "ANDROID:"
	@echo "  make android-debug  -> Debug APK olustur"
	@echo "  make android-install-> Cihaza yukle"
	@echo ""
	@echo "TEMIZLIK:"
	@echo "  make clean          -> Her seyi temizle (VERI SILINIR)"
	@echo "  make clean-containers -> Sadece containerlar"
	@echo ""
	@echo "ESKI (geriye uyumluluk):"
	@echo "  make up / dev / down / rebuild"
	@echo ""
	@echo "SUNUCU (yorumda — Makefile'da aktif et):"
	@echo "  make prod-up / prod-down / ssl-init"
	@echo ""
