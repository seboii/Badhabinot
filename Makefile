.PHONY: yardim up down build rebuild smoke backend-build frontend-build python-check ci

yardim:
	@echo "Kullanilabilir hedefler:"
	@echo "  make up              -> Docker stack baslatir"
	@echo "  make down            -> Docker stack kapatir"
	@echo "  make build           -> Docker image'lari build eder"
	@echo "  make rebuild         -> down + build + up"
	@echo "  make smoke           -> smoke test calistirir"
	@echo "  make backend-build   -> Maven package"
	@echo "  make frontend-build  -> Frontend build"
	@echo "  make python-check    -> Python servis compile kontrolu"
	@echo "  make ci              -> Tum lokal CI adimlarini calistirir"

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

rebuild:
	docker compose down
	docker compose build
	docker compose up -d

smoke:
	powershell -ExecutionPolicy Bypass -File infra/docker/scripts/smoke-test.ps1 -GatewayBaseUrl http://localhost:8080

backend-build:
	mvn -B -ntp -DskipTests package

frontend-build:
	cd apps/web/frontend-app && npm ci && npm run build

python-check:
	pip install -r apps/python-services/ai-service/requirements.txt
	python -m compileall apps/python-services/ai-service/app
	pip install -r apps/python-services/vision-service/requirements.txt
	python -m compileall apps/python-services/vision-service/app

ci: backend-build frontend-build python-check
