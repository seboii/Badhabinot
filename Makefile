.PHONY: yardim up dev down build rebuild logs shell clean smoke backend-build frontend-build python-check ci

yardim:
	@echo "Kullanilabilir hedefler:"
	@echo "  make up              -> Docker stack baslatir (port binding yok)"
	@echo "  make dev             -> Docker stack + host port binding ile baslatir"
	@echo "  make down            -> Docker stack kapatir"
	@echo "  make build           -> Docker image'lari build eder (cache ile)"
	@echo "  make rebuild         -> Cache'siz temiz build + up"
	@echo "  make logs            -> Tum servislerin loglarini canli izler"
	@echo "  make shell SVC=<ad>  -> Servise bash shell acar (ornek: make shell SVC=backend)"
	@echo "  make clean           -> Stack + volume + image siler"
	@echo "  make smoke           -> Smoke test calistirir"
	@echo "  make backend-build   -> Maven package"
	@echo "  make frontend-build  -> Frontend build"
	@echo "  make python-check    -> Python servis compile kontrolu"
	@echo "  make ci              -> Tum lokal CI adimlarini calistirir"

up:
	docker compose up -d

# Start with host port bindings (postgres:5432, redis:6379, backend:8080, frontend:3000, etc.)
dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

down:
	docker compose down --remove-orphans

build:
	docker compose build

rebuild:
	docker compose down --remove-orphans
	docker compose build --no-cache
	docker compose up -d

logs:
	docker compose logs -f

# Usage: make shell SVC=vision-service
shell:
	docker compose exec $(SVC) bash

clean:
	docker compose down --remove-orphans --volumes --rmi local
	docker system prune -f

smoke:
	powershell -ExecutionPolicy Bypass -File infra/docker/scripts/smoke-test.ps1 -GatewayBaseUrl http://localhost:8080

backend-build:
	mvn -B -ntp -f backend/pom.xml -DskipTests package

frontend-build:
	cd frontend && npm ci && npm run build

python-check:
	pip install -r python-services/ai-service/requirements.txt
	python -m compileall python-services/ai-service/app
	pip install -r python-services/vision-service/requirements.txt
	python -m compileall python-services/vision-service/app

ci: backend-build frontend-build python-check
