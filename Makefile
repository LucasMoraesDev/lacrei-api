# ─────────────────────────────────────────────────────────────────────────────
# Lacrei Saúde API — Makefile
# Atalhos para os comandos mais usados no dia a dia
# ─────────────────────────────────────────────────────────────────────────────

.PHONY: help install run test lint format migrate seed docker-up docker-down shell

# Configuração padrão
SETTINGS ?= config.settings.development
PYTHON   = poetry run python
MANAGE   = $(PYTHON) manage.py --settings=$(SETTINGS)

help: ## Mostra esta ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Setup ─────────────────────────────────────────────────────────────────────
install: ## Instala dependências com Poetry
	poetry install

env: ## Copia .env.example para .env
	@test -f .env || (cp .env.example .env && echo "✅ .env criado — edite as variáveis!")

# ── Desenvolvimento ───────────────────────────────────────────────────────────
run: ## Inicia o servidor de desenvolvimento
	$(MANAGE) runserver

migrate: ## Executa as migrações
	$(MANAGE) migrate

makemigrations: ## Cria novas migrações
	$(MANAGE) makemigrations

seed: ## Carrega dados iniciais (fixtures)
	$(MANAGE) loaddata apps/professionals/fixtures/initial_professionals.json

shell: ## Abre o shell interativo do Django
	$(MANAGE) shell_plus 2>/dev/null || $(MANAGE) shell

superuser: ## Cria superusuário para o admin Django
	$(MANAGE) createsuperuser

collectstatic: ## Coleta arquivos estáticos
	$(MANAGE) collectstatic --noinput

# ── Qualidade de código ───────────────────────────────────────────────────────
lint: ## Executa Ruff + Black (check only)
	poetry run ruff check .
	poetry run black --check .

format: ## Formata o código com Black + Ruff fix
	poetry run black .
	poetry run ruff check --fix .

typecheck: ## Verifica tipos com Mypy
	poetry run mypy apps/

# ── Testes ────────────────────────────────────────────────────────────────────
test: ## Executa todos os testes com cobertura
	DJANGO_SETTINGS_MODULE=config.settings.test \
		poetry run pytest -v --cov=apps --cov-report=term-missing

test-fast: ## Executa testes sem cobertura (feedback rápido)
	DJANGO_SETTINGS_MODULE=config.settings.test \
		poetry run pytest -x -q --tb=short

test-prof: ## Executa apenas testes de profissionais
	DJANGO_SETTINGS_MODULE=config.settings.test \
		poetry run pytest tests/test_professionals.py -v

test-appt: ## Executa apenas testes de consultas
	DJANGO_SETTINGS_MODULE=config.settings.test \
		poetry run pytest tests/test_appointments.py -v

test-cov-html: ## Gera relatório HTML de cobertura
	DJANGO_SETTINGS_MODULE=config.settings.test \
		poetry run pytest --cov=apps --cov-report=html
	@echo "Abra htmlcov/index.html no browser"

# ── Docker ────────────────────────────────────────────────────────────────────
docker-up: ## Sobe API + PostgreSQL com Docker Compose
	docker compose up -d
	@echo "✅ API em http://localhost:8000 | Docs em http://localhost:8000/api/docs/"

docker-down: ## Para e remove containers
	docker compose down

docker-logs: ## Mostra logs da API em tempo real
	docker compose logs -f api

docker-rebuild: ## Reconstrói e sobe a imagem
	docker compose up -d --build

docker-test: ## Executa testes no container Docker (modo CI)
	docker compose -f docker-compose.ci.yml up --abort-on-container-exit

docker-shell: ## Abre shell no container da API
	docker compose exec api python manage.py shell

# ── Utilitários ───────────────────────────────────────────────────────────────
check-migrations: ## Verifica se há migrações pendentes
	$(MANAGE) makemigrations --check --dry-run

check-deploy: ## Verifica configurações de segurança para deploy
	DJANGO_SETTINGS_MODULE=config.settings.production \
		$(PYTHON) manage.py check --deploy 2>&1 | head -50 || true

schema: ## Gera o schema OpenAPI em arquivo
	$(MANAGE) spectacular --color --file openapi-schema.yml
	@echo "✅ Schema gerado em openapi-schema.yml"

clean: ## Remove arquivos temporários
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage coverage.xml htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/
	@echo "✅ Limpeza concluída"
