# Python toolchain
PY  ?= python3
PIP ?= $(PY) -m pip

# Project folders
CHROMA_DIR ?= chroma_store
OUTPUT_DIR ?= output
AUX_DIR    ?= images_auxiliar_fold

# Config file
CONFIG ?= modal_endpoint_app/config/base.yaml

# Docker/Compose
DC       := docker compose
SERVICE  ?= backend
PORT     ?= 8000

# Targets
.PHONY: help install local_run api clear reset deploy stop_deploy \
        docker-build docker-up docker-down docker-logs docker-ps docker-shell \
        docker-restart docker-rebuild docker-down-v docker-reset \
        frontend-build frontend-up frontend-logs frontend-shell

help:
	@echo "Targets:"
	@echo "  install        - Install Python dependencies"
	@echo "  local_run      - Run local pipeline (scripts/local.py)"
	@echo "  api            - Start FastAPI backend locally (port $(PORT))"
	@echo "  clear          - Remove caches and output folders"
	@echo "  reset          - Clean + run pipeline locally"
	@echo "  deploy         - Deploy API to Modal"
	@echo "  stop_deploy    - Stop Modal app"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build   - Build backend+frontend  images"
	@echo "  docker-up      - Start backend+frontend"
	@echo "  docker-down    - Stop all containers"
	@echo "  docker-down-v  - Stop and remove volumes"
	@echo "  docker-logs    - Tail logs from backend"
	@echo "  docker-ps      - List running containers"
	@echo "  docker-shell   - Open bash inside backend"
	@echo "  frontend-logs  - Tail logs from frontend"

# Local
install:
	$(PIP) install -U pip
	$(PIP) install -r requirements.txt

local_run:
	$(PY) -m modal_endpoint_app.scripts.local --config $(CONFIG)

api:
	uvicorn backend.app:app --host 0.0.0.0 --port $(PORT) --reload

clear:
	rm -rf "$(CHROMA_DIR)" "$(OUTPUT_DIR)" "$(AUX_DIR)"
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	clear

reset: clear local_run

deploy:
	modal deploy -m modal_endpoint_app.endpoint

stop_deploy:
	modal app stop enter_document_parsing_system

# Docker global
docker-build:
	mkdir -p eval_data/files eval_data/out
	$(DC) build

docker-up:
	$(DC) up -d

docker-down:
	$(DC) down

docker-down-v:
	$(DC) down -v

docker-ps:
	$(DC) ps

docker-restart:
	$(DC) restart $(SERVICE)

docker-rebuild:
	$(DC) build $(SERVICE)
	$(DC) up -d $(SERVICE)

backend-logs:
	$(DC) logs -f $(SERVICE)

frontend-logs:
	$(DC) logs -f frontend

# Shortcut
api_docker: docker-up
	@echo "API: http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"
	@echo "Frontend: http://localhost:3000"
